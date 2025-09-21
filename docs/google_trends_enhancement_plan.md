# Google Trends 关键词挖掘提升计划

> 目标：进一步扩大潜藏机会关键词与新词的捕获范围，并提升对爆发趋势的监控/输出质量。

## 阶段 1 · 立即执行（P0）

- [ ] **扩充候选种子来源**
  - 接入 Twitter/X Trending、指定话题热帖（API 或 RSS），写入统一的种子收集器。
  - 抓取 Product Hunt 当日发布、Reddit 重点子版块（如 `/r/Futurology`、`/r/Entrepreneur`）的标题或话题词。
  - 将上述词汇追加到 `_collect_trends_related_candidates` 的 seed_pool，并保留来源标签。
- [ ] **强化 Google Trends 相关词抓取**
  - 提高 `per_category_limit`，对 Breakout 种子额外循环抓满相关词（20 条+）。
  - 若 `formattedValue == "Breakout"`，将候选标记为高优先级直接进入新词检测队列。
  - 统计/记录获取失败的 geo/timeframe，避免重复无效重试。
- [ ] **多地域多语言采集**
  - 在 `_fetch_trends_dataframe` 中迭代主要市场（示例：`['', 'US', 'IN', 'SG', 'DE']`）。
  - 报表与 CLI 输出新增“主要爆发区域”字段。

## 阶段 2 · 短期推进（P1）

- [ ] **Watchlist & 历史回溯机制**
  - 新增 `watchlist.yaml`，支持用户自定义重点词，每日强制跑新词检测。
  - 保留每日候选快照，输出“连续 N 天 Rising”列表。
- [ ] **增强趋势信号维度**
  - 对 Breakout 候选调用 Google News / Bing News，区分“新闻驱动”与“需求驱动”。
  - 评估引入 Ahrefs/SEMrush 等 API 的成本，将搜索量或付费竞价指标并入评分。

## 阶段 3 · 中期优化（P2）

- [ ] **异常告警与可视化**
  - 当 Breakout 数量较历史均值激增时，在 CLI + 报告中输出“重点关注”提示。
  - Dashboard JSON 加入 Breakout/Rising 历史折线，便于后续图表展示。
- [ ] **流程回放与回测**
  - 定期复盘导出的新词报表，对实际站点表现进行标注（成功/失败），回写到评分体系。

## 依赖与备注

- Twitter/X & Product Hunt 等接口若需 API Key，请先确认可用的访问方式（官方 API、RSS、中间服务）。
- 多地域采集会增加请求量，需留意 Trends 的限流与冷却策略，可配合代理或延迟控制。
- 若引入付费数据源（Ahrefs/SEMrush），需要在配置中统一管理凭据并避免泄漏。

