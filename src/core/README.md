# 核心模块 (Core Module)

## 概述

核心模块包含市场需求分析工具的主要协调器和分析器。

## 模块说明

### MarketAnalyzer - 市场分析器

主要的分析协调器，负责整合各个子模块的功能，提供完整的市场需求分析流程。

#### 主要功能

1. **数据采集协调** - 调用Google Trends数据采集器
2. **关键词评分** - 调用关键词评分器进行评分
3. **意图分析** - 调用搜索意图分析器
4. **结果整合** - 生成综合分析报告
5. **日志记录** - 记录分析过程和结果

#### 使用方法

```python
from src.core.market_analyzer import MarketAnalyzer

# 创建分析器实例
analyzer = MarketAnalyzer(output_dir='data')

# 运行分析
result = analyzer.run_analysis(
    keywords=['ai tools', 'marketing automation'],
    geo='US',
    timeframe='today 3-m',
    min_score=10
)
```

#### 输出文件

分析完成后会在指定目录生成以下文件：

- `analysis_log_YYYY-MM-DD.txt` - 分析日志
- `analysis_report_YYYY-MM-DD.json` - 综合分析报告
- `trends_all_YYYY-MM-DD.csv` - Google Trends原始数据
- `scored_YYYY-MM-DD.csv` - 关键词评分结果
- `intent_YYYY-MM-DD.csv` - 搜索意图分析结果
- `intent_summary_YYYY-MM-DD.json` - 意图分析摘要

#### 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| keywords | list | 必需 | 要分析的关键词列表 |
| geo | str | '' | 地区代码(如US、GB)，空为全球 |
| timeframe | str | 'today 3-m' | 时间范围 |
| volume_weight | float | 0.4 | 搜索量权重 |
| growth_weight | float | 0.4 | 增长率权重 |
| kd_weight | float | 0.2 | 关键词难度权重 |
| min_score | int | None | 最低评分过滤 |
| enrich | bool | True | 是否丰富关键词数据 |

#### 返回结果

返回包含以下字段的字典：

```json
{
  "分析日期": "2025-01-04",
  "分析关键词": ["ai tools"],
  "地区": "全球",
  "时间范围": "today 3-m",
  "分析耗时(秒)": 45.2,
  "关键词总数": 150,
  "高分关键词数": 25,
  "意图分布": {
    "I": 45.2,
    "C": 30.1,
    "E": 15.3,
    "N": 9.4
  },
  "Top5关键词": [...],
  "输出文件": {...}
}
```

## 依赖关系

- `collectors.trends_collector.TrendsCollector` - Google Trends数据采集
- `analyzers.keyword_scorer.KeywordScorer` - 关键词评分
- `analyzers.intent_analyzer.IntentAnalyzer` - 搜索意图分析

## 错误处理

- 自动重试机制处理网络错误
- 数据验证确保输入参数正确
- 详细的错误日志记录
- 优雅的错误恢复机制

## 性能优化

- 批量处理关键词减少API调用
- 缓存机制避免重复请求
- 异步处理提高效率
- 内存优化处理大数据集