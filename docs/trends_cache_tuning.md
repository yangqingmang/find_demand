# Google Trends 请求优化方案（轻量级）

本方案在不改动整体架构的前提下，减少重复请求并更好地利用现有缓存，尽量规避 429。

## 1. 统一走 TrendManager 缓存
- 将所有直接调用 `TrendsCollector.get_keyword_trends()` 的入口改为使用 `TrendManager.get_trends_data(keyword, timeframe, use_cache=True)`。
- `TrendManager` 内部已经集成 `TrendsCache`（SQLite + 文件缓存），命中缓存时直接返回；未命中才真正访问 Google Trends。
- 适用位置：`RootWordTrendsAnalyzer`, `NewWordDetector`, 其他 ad-hoc 的调用。

## 2. 冷门关键词提前短路
- 依据配置 `new_word_detection.low_volume_threshold_*`（12 个月 / 90 天 / 30 天）添加前置判断：如果历史平均量级远低于阈值，直接返回“热度过低”状态，不再继续请求其他 timeframe。
- 可以在 `TrendManager` 中统一实现：当缓存数据或首个时间窗口表明 `avg_volume < MIN_VOLUME` 时，标记结果为 `skipped_low_volume`，并附带提示信息。
- 对新词检测逻辑同样适用，避免对同一冷门词反复触发 `today 12-m`, `today 3-m`, `now 7-d`, `now 1-d` 多轮请求。

## 3. 批量预热缓存
- 在批处理流程开始前，调用 `trend_manager.trends_cache.enable_offline_mode(keywords)` 对待分析关键词批量预热缓存。
- 若缓存中已有可用数据，后续分析阶段就无需再次访问 Trends 接口；即便 miss，也能统一调度 API 请求。

## 4. 辅助策略
- 动态调低 request limiter 的最低频率（例如默认每 10 秒 1 次），并在 429 后指数退避，降低再次触发的概率。
- 为低热度的关键词设置日志提醒，留待人工复核，避免在冷却期内重复尝试。

> 部署成本：**低**。主要是替换调用入口、补充阈值判断逻辑即可，测试重点是确保缓存命中路径与旧流程一致。***
