# 数据采集模块 (Data Collectors)

## 概述

数据采集模块负责从各种外部数据源获取市场需求相关的数据，为后续分析提供数据基础。

## 模块列表

### TrendsCollector - Google Trends数据采集器

专门用于采集Google Trends数据的工具，支持批量关键词查询和多地区数据获取。

#### 主要功能

1. **单关键词查询** - 获取单个关键词的趋势数据
2. **批量关键词查询** - 同时处理多个关键词
3. **地区数据支持** - 支持全球和特定地区的数据
4. **时间范围灵活** - 支持多种时间范围选择
5. **相关查询获取** - 自动获取相关搜索词
6. **数据清洗** - 自动处理和清洗原始数据

#### 使用方法

```python
from src.collectors.trends_collector import TrendsCollector

# 创建采集器实例
collector = TrendsCollector()

# 单关键词查询
data = collector.fetch_trends_data('ai tools', geo='US', timeframe='today 3-m')

# 批量关键词查询
keywords = ['ai tools', 'marketing automation', 'seo tools']
results = collector.fetch_multiple_keywords(keywords, geo='US')
```

#### 支持的参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| keyword | str | 必需 | 要查询的关键词 |
| geo | str | '' | 地区代码(US、GB、CN等)，空为全球 |
| timeframe | str | 'today 3-m' | 时间范围 |
| include_related | bool | True | 是否包含相关查询 |
| max_related | int | 25 | 最大相关查询数量 |

#### 时间范围选项

- `today 1-m` - 过去1个月
- `today 3-m` - 过去3个月  
- `today 12-m` - 过去12个月
- `today 5-y` - 过去5年
- `all` - 所有时间

#### 地区代码

常用地区代码：
- `US` - 美国
- `GB` - 英国
- `CN` - 中国
- `DE` - 德国
- `JP` - 日本
- `KR` - 韩国
- `IN` - 印度
- `BR` - 巴西

#### 返回数据格式

```python
{
    'keyword': {
        'query': '关键词',
        'date': '日期',
        'value': '搜索热度值(0-100)',
        'geo': '地区代码',
        'timeframe': '时间范围'
    }
}
```

#### 错误处理

- **网络错误** - 自动重试机制，最多重试3次
- **API限制** - 智能延迟避免触发限制
- **数据验证** - 验证返回数据的完整性
- **异常记录** - 详细记录所有异常信息

#### 性能优化

- **批量处理** - 一次请求处理多个关键词
- **缓存机制** - 避免重复请求相同数据
- **并发控制** - 合理控制并发请求数量
- **内存管理** - 及时释放大数据集内存

#### 注意事项

1. **请求频率** - 避免过于频繁的请求，建议间隔1-2秒
2. **数据准确性** - Google Trends数据为相对值，不是绝对搜索量
3. **地区限制** - 某些关键词在特定地区可能没有数据
4. **时效性** - 数据更新可能有1-2天延迟

#### 示例代码

```python
# 基础使用
collector = TrendsCollector()

# 获取AI工具相关数据
ai_data = collector.fetch_trends_data(
    keyword='ai tools',
    geo='US',
    timeframe='today 3-m',
    include_related=True
)

# 批量处理多个关键词
keywords = ['chatgpt', 'claude ai', 'gemini ai']
batch_results = collector.fetch_multiple_keywords(
    keywords=keywords,
    geo='',  # 全球数据
    timeframe='today 12-m'
)

# 处理结果
for keyword, data in batch_results.items():
    print(f"{keyword}: {len(data)} 条数据")
    if not data.empty:
        print(f"平均热度: {data['value'].mean():.1f}")
```

## 扩展说明

该模块设计为可扩展架构，未来可以添加更多数据源：

- **关键词工具API** - SEMrush、Ahrefs等
- **社交媒体数据** - Twitter、Reddit等
- **电商平台数据** - Amazon、淘宝等
- **新闻媒体数据** - Google News等

## 依赖库

- **自定义实现** - 不再依赖第三方 pytrends 库
- `pandas` - 数据处理
- `requests` - HTTP请求
- `time` - 延迟控制

## 技术架构

### 自定义 Google Trends 实现

本模块已完全替换第三方 `pytrends` 库，使用自主开发的 Google Trends 数据采集器：

#### 核心组件

1. **CustomTrendsCollector** (`custom_trends_collector.py`)
   - 直接与 Google Trends API 交互
   - 完整的会话管理和错误处理
   - 智能重试机制和 429 错误处理

2. **TrendReq** (`trends_wrapper.py`) 
   - 提供与原 pytrends 完全兼容的 API 接口
   - 无缝替换，现有代码无需修改

3. **TrendsCollector** (`trends_collector.py`)
   - 高级业务逻辑封装
   - 批量处理和数据清洗功能

#### 技术优势

- **完全自主可控** - 不依赖第三方库更新
- **更强错误处理** - 针对 Google Trends API 优化
- **扩展功能** - 批量分析、数据导出、API 状态检查
- **向后兼容** - 与原 pytrends 接口完全兼容

#### 新增功能

- `top_charts()` - 年度热门图表
- `categories()` - 获取所有可用分类  
- `realtime_trending_searches()` - 实时热门搜索
- `today_searches()` - 今日搜索趋势
- `hourly_searches()` - 小时级搜索数据
- `batch_keyword_analysis()` - 批量关键词分析
- `export_data()` - 数据导出功能
- `get_api_status()` - API 状态监控
