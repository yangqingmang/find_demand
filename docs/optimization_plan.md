# python main.py --all 优化计划

## 目标
- 降低 Google Trends 与多来源采集触发 429 的概率，确保完整流程稳定运行。
- 缩短 `python main.py --all` 的端到端执行时间，降低 CPU / I/O 峰值。
- 提高代码路径的可观察性与可维护性，为后续扩展奠定基础。

## 当前主要痛点
- **请求节流缺口**：部分 Trends 采集路径未接入全局 `RequestRateLimiter`，429 后冷却与其他线程未对齐。
- **清洗与中间数据过度落盘**：多次读写临时 CSV、重复调用 `langdetect`，开销高。
- **建议词/多平台采集串行且无缓存**：对每个 seed 顺序命中多个外部接口，缺少速率控制与结果缓存。
- **关键词分析串行执行**：意图/市场分析逐词计算，缺少批量/缓存机制，日志输出冗余。
- **多平台聚类成本高**：每次运行都加载 `SentenceTransformer`，执行 MinHash + 聚类，CPU/内存压力大。

## 优化路线图

### Phase 1：速率 & 清洗快速缓解（优先完成）
1. **统一 Trends 限流接入**  
   - 修改 `TrendsCollector` 及相关 helper，在所有对 `trends_session` 的请求前调用 `wait_for_next_request()`。
   - 为 `_fetch_trending_via_api`、`_collect_trends_related_candidates`、`related_queries` 重试逻辑增加“429 冷却中跳过”标记，避免风暴式重置。  
   - 交付：带测试日志的 MR，附运行 `python main.py --all` 的截断输出验证。

2. **清洗链路瘦身**  
   - 为 `clean_terms` 增加禁用语言检测的配置与缓存；默认在批量清洗时跳过或缓存结果。
   - 在 `handle_all_workflow` 中使用内存 DataFrame 传递而非临时文件传递，减少多余落盘。
   - 交付：单元测试覆盖新配置；运行耗时前后对比记录。

3. **Suggestion Collector 限速与采样**  
   - 增加全局 `asyncio.Semaphore` 或简单延迟控制，限制 `seed × source` 同步请求数。
   - 对大于阈值的 seed 池进行采样或批次化，记录命中率指标。
   - 交付：采集日志展示命中/跳过统计。

### Phase 2：分析与多平台调优
4. **关键词分析批量化**  
   - 引入批处理 API（每批 N 个关键词），对意图分析/市场分析复用同一 DataFrame。
   - 精简逐词 `print`，改为总结式日志；添加缓存层避免重复分析。
   - 交付：新增 profiling 结果，展示批量化效率提升。

5. **多平台发现异步化与缓存**  
   - 采用 `asyncio` + `aiohttp` 或线程池并发请求外部接口，统一速率控制。
   - 缓存热门 subreddit/HN 结果，设置有效期；减少重复调用。
   - 交付：配置项允许启用/禁用缓存；性能对比报告。

6. **SentenceTransformer 模型复用**  
   - 将模型加载放入模块级单例，支持可选的轻量模式（跳过聚类或使用简化算法）。
   - 引入关键词数量阈值，低量时直接跳过嵌入计算。
   - 交付：配置开关 + 基准数据。

### Phase 3：可观察性与持续优化
7. **流程指标与调试仪表**  
   - 增加执行阶段耗时、请求数、429 次数等指标输出；写入 `output/telemetry.json`。
   - 调整 `refresh_dashboard_data` 汇总新的指标，便于后续监控。

8. **流程断点与缓存策略**  
   - 支持 `--resume` 参数，复用上一轮的热点词/分析结果，跳过重复的外部请求。
   - 增加流程级缓存目录管理与过期策略。

## 资源需求
- 访问 Google Trends、TrendingKeywords、Reddit/HN/YouTube API 或公开接口的测试账号。
- 可用于性能对比的典型输入样例（data/keywords.csv + 实际生产配置）。
- Profiling 工具：`cProfile`、`py-spy` 或简化日志统计脚本。

## 里程碑
| 阶段 | 目标 | 预计完成 | 依赖 |
| ---- | ---- | -------- | ---- |
| Phase 1 | 限流 & 清洗改造上线，`--all` 流程稳定运行 | 1 周内 | 无 |
| Phase 2 | 分析器批量化 + 多平台异步化 | Phase 1 完成后 2 周 | 第三方接口限额 |
| Phase 3 | 监控 + 断点机制 | Phase 2 后 1 周 | 需 Phase 2 数据结构 |

---
后续迭代将根据 Phase 1 的真实运行数据再调整优先级与范围。
