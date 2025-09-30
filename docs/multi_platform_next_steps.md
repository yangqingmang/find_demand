# 多平台发现 & SERP 优化计划

## 目标
- 聚焦可转化的长尾需求，降低品牌词/泛化词在结果中的占比。
- 在本地配额达到上限或连续失败时自动停止 SERP 请求，避免 429／时间浪费。
- 多样化种子来源，优先挖掘痛点类关键词，为下一轮验证打基础。

---

## 阶段 & 优先级

### Phase A：强化品牌过滤 （优先级 ★★★★★）
1. **扩充品牌黑名单**  
   - 更新 `config/integrated_workflow_config.json` 的 `discovery_filters.brand_phrases / brand_modifiers`，覆盖常见 AI、汽车、硬件等品牌。  
   - 将 `min_non_brand_tokens` 提升至 `>= 2`，并考虑新增 `HARD_EXCLUDE_BRAND_SEEDS=true` 开关（默认启用）。

2. **发现阶段二次过滤**  
   - 在 `prepare_search_terms` 与 `discover_all_platforms` 之前复检种子；命中品牌词时直接丢弃或替换。  
   - 日志打印被过滤掉的品牌词数量，方便调试与后续调优。

### Phase B：SERP 配额 & 失败控制 （优先级 ★★★★☆）
1. **配额控制**  
   - 使用配置项 `SERP_API_MONTHLY_LIMIT`（默认 250）并在 `serp_usage_state.json` 中按月记录；达到上限时跳过后续请求。  
   - 将 `SERP_API_FAILURE_LIMIT` 设为较小阈值（建议 5），连续失败后暂停，并输出提示“多次失败但尚未达到配额，请检查 SerpAPI 状态”。

2. **可选降级模式**  
   - 若短期内无法恢复 SERP 额度，可将 `SERP_API_ENABLED=false` 或增加 `SERP_API_SKIP_ON_FAILURE=true`，直接跳过 SERP，改用 Google CSE 等备用方案。

### Phase C：种子池质量提升 （优先级 ★★★☆☆）
1. **补充非品牌种子**  
   - 新增 `config/manual_seed_keywords.json`（或类似配置）放置痛点/动词型关键词（例如 “workflow automation issue”）。

2. **限制单源品牌比例**  
   - 整合 TrendingKeywords/RSS 后，控制品牌词占比（例如不超过 30%）；超出时自动补充手动种子。  
   - 在 telemetry 中记录最终种子的品牌过滤命中率，便于迭代调整。

3. **视情况恢复 SERP**  
   - 完成 Phase B 后，根据配额情况决定是否重新启用 SERP；若继续禁用，需在文档中说明替代数据来源。

---

## 推荐执行顺序
1. **Phase A**：优先上线品牌过滤增强，立刻改善结果质量。
2. **Phase B**：紧接处理 SERP 配额与失败逻辑，杜绝 429 重试。
3. **Phase C**：逐步完善手动种子、品牌占比监控，必要时再扩展数据源。

完成上述调整后，运行 `python main.py --all --resume`，并通过 telemetry 观测：
- 品牌过滤命中率是否下降；
- SERP 请求是否在限额/失败后自动停止；
- Top 关键词是否出现更多可转化的长尾需求。

如仍有品牌词泄漏或 SERP 频繁失败，可在 Phase A/B 的配置中继续调优。

