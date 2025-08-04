# Google Trends 数据采集工具

**文件名**: `trends_collector.py`

## 功能概述

Google Trends 数据采集工具用于自动获取 Google Trends 的 Rising Queries（上升查询）数据，帮助发现新兴关键词和趋势。这些数据对于内容创作、SEO策略和市场趋势分析非常有价值。

## 使用方法

### 基本用法

```bash
python trends_collector.py --keywords "ai tools" --geo "US" --timeframe "today 3-m"
```

### 参数说明

- `--keywords`：要分析的种子关键词（必需），可以提供多个关键词
- `--geo`：地区代码，如US、GB等，默认为全球
- `--timeframe`：时间范围，默认为过去3个月（today 3-m）
  - 可选值：today 1-d, today 7-d, today 1-m, today 3-m, today 12-m, today 5-y
- `--output`：输出目录，默认为data
- `--hl`：语言设置，默认为en-US

### 输出说明

工具会生成以下文件：

1. `trends_all_YYYY-MM-DD.csv`：包含所有关键词的合并结果
2. `trends_KEYWORD_YYYY-MM-DD.csv`：每个关键词的单独结果

CSV文件包含以下字段：
- `query`：上升查询关键词
- `value`：相对搜索量/上升值
- `seed_keyword`：原始种子关键词

## 技术细节

### 数据源

工具使用 pytrends 库访问 Google Trends API，获取以下数据：
- Rising Queries（上升查询）：近期搜索量增长最快的相关查询

### 实现特性

- **多关键词支持**：可以同时分析多个种子关键词
- **重试机制**：API请求失败时自动重试，最多3次
- **错误处理**：全面的异常捕获和处理
- **结果合并**：自动合并多个关键词的结果
- **进度显示**：显示处理进度和状态信息

### 代码结构

```python
class TrendsCollector:
    def __init__(self, output_dir='data'):
        # 初始化设置
        
    def fetch_rising_queries(self, keyword, geo='', timeframe='today 3-m', hl='en-US'):
        # 获取单个关键词的上升查询
        
    def fetch_multiple_keywords(self, keywords, geo='', timeframe='today 3-m', hl='en-US'):
        # 批量处理多个关键词
        
    def save_results(self, results, all_df=None):
        # 保存结果到CSV文件
```

## 示例输出

```
query,value,seed_keyword
deepseek ai,27700,ai tools
napkin ai,11150,ai tools
n8n,4300,ai tools
cursor,1950,ai tools
notebooklm,1950,ai tools
...
```

## 注意事项

- Google Trends API 没有官方文档，可能会有变化
- 过于频繁的请求可能会导致 IP 被临时封禁
- 不同地区和时间范围的数据可能有显著差异
- 相对搜索量不代表绝对搜索量，仅表示相对趋势

## 未来改进

- 添加更多 Google Trends 数据类型（相关话题、地区兴趣等）
- 实现数据可视化功能
- 添加历史数据比较功能
- 支持更复杂的查询组合和过滤
- 添加代理支持，避免 IP 限制