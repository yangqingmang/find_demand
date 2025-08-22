# 分析器模块 (Analyzers)

## 概述

分析器模块包含各种数据分析和评分工具，负责对采集到的原始数据进行深度分析和价值评估。

## 模块列表

### KeywordScorer - 关键词评分器

基于多维度指标对关键词进行综合评分，帮助识别高价值关键词。

#### 主要功能

1. **多维度评分** - 基于搜索量、增长率、竞争度等指标
2. **权重配置** - 支持自定义各指标权重
3. **数据丰富** - 可选择性地丰富关键词相关数据
4. **结果过滤** - 支持按分数范围过滤结果
5. **排序排名** - 自动按评分排序关键词

#### 评分算法

```
总分 = (搜索量分数 × 搜索量权重) + 
       (增长率分数 × 增长率权重) + 
       (关键词难度分数 × 关键词难度权重)
```

默认权重配置：
- 搜索量权重：40%
- 增长率权重：40%
- 关键词难度权重：20%

#### 使用方法

```python
from src.analyzers.keyword_scorer import KeywordScorer

# 创建评分器
scorer = KeywordScorer(
    volume_weight=0.4,
    growth_weight=0.4,
    kd_weight=0.2
)

# 对关键词进行评分
scored_df = scorer.score_keywords(
    df,
    volume_col='value',
    growth_col='growth'
)

# 过滤高分关键词
high_score_df = scorer.filter_keywords(scored_df, min_score=70)
```

#### 评分等级

| 等级 | 分数范围 | 描述 | 建议行动 |
|------|----------|------|----------|
| A | 70-100 | 优秀 | 重点投入资源 |
| B | 50-69 | 良好 | 适度投入 |
| C | 30-49 | 一般 | 谨慎考虑 |
| D | 0-29 | 较差 | 不建议投入 |

---

### IntentAnalyzer - 搜索意图分析器

基于关键词文本特征判断用户的搜索意图，帮助制定针对性的内容策略。

#### 意图类型

| 代码 | 类型 | 中文名称 | 描述 | 内容策略 |
|------|------|----------|------|----------|
| I | Informational | 信息型 | 寻求信息和知识 | 创建教程、指南、解释性内容 |
| N | Navigational | 导航型 | 寻找特定网站或页面 | 优化品牌页面和导航体验 |
| C | Commercial | 商业型 | 研究产品或服务 | 创建对比、评测、功能介绍 |
| E | Transactional | 交易型 | 准备购买或下载 | 优化购买流程和促销页面 |
| B | Behavioral | 行为型 | 解决问题或执行任务 | 提供操作指南和故障排除 |

#### 主要功能

1. **关键词意图识别** - 基于文本特征自动判断意图
2. **置信度评估** - 提供意图判断的置信度分数
3. **次要意图检测** - 识别可能的次要搜索意图
4. **批量分析** - 支持大批量关键词的意图分析
5. **结果统计** - 生成意图分布统计和摘要

#### 使用方法

```python
from src.analyzers.intent_analyzer import IntentAnalyzer

# 创建意图分析器
analyzer = IntentAnalyzer()

# 分析关键词意图
result_df = analyzer.analyze_keywords(df, keyword_col='query')

# 生成意图分析摘要
summary = analyzer.generate_intent_summary(result_df)

# 保存结果
analyzer.save_results(result_df, summary, output_dir='data')
```

#### 意图识别规则

**信息型 (I)** 关键词特征：
- what, how, why, when, where, who, which
- guide, tutorial, learn, example, explain
- 什么, 如何, 为什么, 怎么, 教程, 学习

**导航型 (N)** 关键词特征：
- login, signin, download, official, website
- account, dashboard, home, page, site
- 登录, 下载, 官网, 官方, 应用

**商业型 (C)** 关键词特征：
- best, top, review, compare, vs, versus
- alternative, comparison, difference, better
- 最佳, 评测, 对比, 比较, 替代

**交易型 (E)** 关键词特征：
- buy, purchase, order, coupon, discount
- price, cheap, free, trial, subscription
- 购买, 订购, 优惠, 折扣, 价格

**行为型 (B)** 关键词特征：
- error, fix, issue, problem, bug
- help, support, troubleshoot, update
- 错误, 修复, 问题, 故障, 帮助

#### 输出结果

分析完成后会生成以下字段：

- `intent` - 主要意图代码
- `intent_confidence` - 置信度分数 (0.5-1.0)
- `secondary_intent` - 次要意图代码
- `intent_description` - 意图类型描述
- `recommended_action` - 推荐的内容策略

#### 意图分析摘要

```json
{
  "total_keywords": 150,
  "intent_counts": {
    "I": 68,
    "C": 45,
    "E": 23,
    "N": 14
  },
  "intent_percentages": {
    "I": 45.3,
    "C": 30.0,
    "E": 15.3,
    "N": 9.3
  },
  "intent_keywords": {
    "I": ["how to use ai tools", "what is chatgpt"],
    "C": ["best ai tools 2024", "chatgpt vs claude"],
    "E": ["buy ai tools", "ai tools free trial"],
    "N": ["chatgpt login", "openai website"]
  },
  "high_confidence_keywords": [...],
  "intent_descriptions": {...}
}
```

## 扩展功能

### 数据丰富化

KeywordScorer 支持通过外部API丰富关键词数据：

```python
# 使用Google Ads数据丰富关键词
enriched_df = scorer.enrich_with_ads_data(df)

# 添加的字段包括：
# - monthly_searches: 月搜索量
# - competition: 竞争度 (0-1)
# - cpc: 每次点击成本
```

### 自定义意图规则

可以扩展IntentAnalyzer的意图识别规则：

```python
# 添加自定义意图关键词
analyzer.intent_keywords['C'].extend(['pricing', 'cost', 'plans'])

# 重新编译正则表达式
analyzer.patterns['C'] = re.compile(
    r'\b(' + '|'.join(analyzer.intent_keywords['C']) + r')\b', 
    re.IGNORECASE
)
```

## 性能优化

1. **批量处理** - 支持大批量数据的高效处理
2. **内存管理** - 优化大数据集的内存使用
3. **缓存机制** - 避免重复计算相同数据
4. **并行处理** - 支持多线程加速分析过程

## 错误处理

- **数据验证** - 自动验证输入数据格式和完整性
- **异常恢复** - 优雅处理数据异常和缺失值
- **日志记录** - 详细记录分析过程和错误信息
- **结果验证** - 验证输出结果的合理性

## 依赖库

- `pandas` - 数据处理和分析
- `numpy` - 数值计算
- `re` - 正则表达式匹配
- `json` - JSON数据处理
- `datetime` - 时间处理
- `collections` - 数据结构工具

## 注意事项

1. **数据质量** - 确保输入数据的质量和完整性
2. **权重调整** - 根据业务需求调整评分权重
3. **意图准确性** - 意图识别基于规则，可能需要人工验证
4. **语言支持** - 目前支持中英文，其他语言需要扩展词典