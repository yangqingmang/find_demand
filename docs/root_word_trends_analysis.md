# 51个词根趋势分析工具

这个工具专门用于分析你提到的51个词根（如Translator、Generator、Example等）在Google Trends上的趋势数据。

## 功能特性

- 🔍 **单个词根分析**: 深入分析特定词根的趋势
- 📊 **批量趋势分析**: 一次性分析所有51个词根
- 🔗 **相关关键词挖掘**: 发现每个词根的相关热门搜索
- 📈 **趋势方向判断**: 自动识别上升、下降或稳定趋势
- 💾 **多格式输出**: 支持JSON和CSV格式的结果保存
- 📋 **详细报告**: 生成包含统计摘要的分析报告

## 51个词根列表

工具内置了以下51个词根：

**工具类词根**:
- Translator, Generator, Converter, Calculator
- Editor, Processor, Analyzer, Compiler
- Builder, Maker, Creator, Designer

**功能类词根**:
- Online, Downloader, Uploader, Viewer
- Checker, Detector, Monitor, Tracker
- Manager, Explorer, Navigator, Syncer

**模板类词根**:
- Example, Sample, Template, Format
- Pattern, Scheme, Dashboard, Planner

**系统类词根**:
- Simulator, Assistant, Constructor, Comparator
- Verifier, Optimizer, Scheduler, Recorder
- Extractor, Notifier, Connector, Cataloger
- Responder, Sender, Receiver, Interpreter

## 安装依赖

```bash
pip install pytrends pandas
```

## 使用方法

### 1. 分析所有51个词根

```bash
python root_word_trends_cli.py
```

这将分析所有51个词根的12个月趋势数据，并生成完整报告。

### 2. 自定义时间范围

```bash
python root_word_trends_cli.py --timeframe 3-m
```

支持的时间范围：
- `1-m`: 过去1个月
- `3-m`: 过去3个月  
- `12-m`: 过去12个月（默认）
- `5-y`: 过去5年

### 3. 分析单个词根

```bash
python root_word_trends_cli.py --single-word "Generator"
```

### 4. 获取相关关键词

```bash
python root_word_trends_cli.py --get-keywords "Translator"
```

### 5. 调整批处理大小

```bash
python root_word_trends_cli.py --batch-size 3 --timeframe 3-m
```

较小的批处理大小可以减少API限制问题，但会增加总处理时间。

## 输出文件

分析完成后，会在 `data/root_word_trends/` 目录下生成：

1. **完整结果** (`root_word_trends_full_YYYY-MM-DD.json`)
   - 包含所有词根的详细趋势数据
   - 每个词根的趋势点、相关查询等

2. **分析摘要** (`root_word_trends_summary_YYYY-MM-DD.json`)
   - 按趋势方向分类的词根列表
   - 统计信息和排名

3. **CSV报告** (`root_word_trends_report_YYYY-MM-DD.csv`)
   - 表格格式的分析结果
   - 便于在Excel中查看和分析

## 编程接口使用

```python
from src.demand_mining.root_word_trends_analyzer import RootWordTrendsAnalyzer

# 创建分析器
analyzer = RootWordTrendsAnalyzer()

# 分析单个词根
result = analyzer.analyze_single_root_word("AI", timeframe="12-m")

# 获取相关关键词
keywords = analyzer.get_trending_keywords_for_root("Generator", limit=20)

# 批量分析所有词根
results = analyzer.analyze_all_root_words(timeframe="12-m", batch_size=5)
```

## 运行示例

```bash
python example_root_word_analysis.py
```

这个示例脚本展示了各种使用方法。

## 分析结果解读

### 趋势方向
- **rising**: 上升趋势（近期平均值比早期高10%以上）
- **declining**: 下降趋势（近期平均值比早期低10%以上）
- **stable**: 稳定趋势

### 兴趣度数值
- 范围：0-100
- 100表示该时间段内的峰值热度
- 相对数值，用于比较不同时间点的热度

### 相关查询
- **Top**: 最相关的搜索查询
- **Rising**: 增长最快的相关查询
- **Value**: 相对搜索量或增长百分比

## 注意事项

1. **API限制**: Google Trends有请求频率限制，工具已内置延迟机制
2. **数据可用性**: 某些词根可能没有足够的搜索数据
3. **地区设置**: 默认分析全球数据，可通过修改代码指定特定地区
4. **时间延迟**: 完整分析51个词根大约需要15-20分钟

## 故障排除

### 常见问题

1. **连接超时**
   ```bash
   # 减少批处理大小
   python root_word_trends_cli.py --batch-size 2
   ```

2. **无数据返回**
   - 某些词根可能搜索量太低
   - 尝试不同的时间范围

3. **API限制错误**
   - 工具会自动重试和延迟
   - 如果持续出现，请稍后再试

## 高级用法

### 自定义词根列表

如果你想分析其他词根，可以修改 `RootWordTrendsAnalyzer` 类中的 `root_words` 列表：

```python
analyzer = RootWordTrendsAnalyzer()
analyzer.root_words = ["你的", "自定义", "词根", "列表"]
results = analyzer.analyze_all_root_words()
```

### 地区特定分析

```python
# 修改trends_collector的geo参数
# 例如：geo='US' 表示美国地区
```

这个工具将帮助你全面了解这51个词根的搜索趋势，为你的需求挖掘和关键词策略提供数据支持。