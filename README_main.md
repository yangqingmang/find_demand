# 市场需求分析工具集

这个工具集用于自动化市场需求分析流程，包括关键词发现、评分排序和搜索意图分析。

## 功能概述

工具集包含以下组件：

1. **Google Trends 数据采集** (`trends_collector.py`)
   - 获取关键词的上升查询数据
   - 支持多个种子关键词批量处理
   - 内置重试机制，提高数据获取稳定性

2. **关键词评分** (`keyword_scorer.py`)
   - 对关键词进行综合评分（搜索量、增长率、关键词难度）
   - 支持自定义评分权重
   - 关键词过滤功能

3. **搜索意图分析** (`intent_analyzer.py`)
   - 基于INCEB五层框架分析关键词搜索意图
   - 生成详细的意图分析报告和摘要
   - 提供针对每种意图的推荐行动

4. **主流程控制** (`market_analyzer.py`)
   - 整合以上三个组件
   - 一键执行完整分析流程
   - 生成综合分析报告

## 安装

### 依赖项

```bash
pip install -r requirements.txt
```

### 依赖库

- pandas：数据处理和分析
- requests：HTTP请求
- scipy：科学计算（用于线性回归）
- pytrends：Google Trends API封装

## 使用方法

### 一键分析

```bash
python market_analyzer.py --keywords "ai工具" "内容生成" --geo "US"
```

### 参数说明

- `--keywords`: 要分析的关键词列表（必需）
- `--geo`: 地区代码，如US、GB等，默认为全球
- `--timeframe`: 时间范围，默认为过去3个月（today 3-m）
- `--output`: 输出目录，默认为data
- `--volume-weight`: 搜索量权重，默认0.4
- `--growth-weight`: 增长率权重，默认0.4
- `--kd-weight`: 关键词难度权重，默认0.2
- `--min-score`: 最低评分过滤
- `--no-enrich`: 不丰富关键词数据

### 单独使用各组件

也可以单独使用各个组件：

```bash
# 仅获取Google Trends数据
python trends_collector.py --keywords "ai工具" --geo "US"

# 仅进行关键词评分
python keyword_scorer.py --input data/trends_all_2025-08-04.csv --enrich

# 仅进行搜索意图分析
python intent_analyzer.py --input data/scored_2025-08-04.csv
```

## 输出文件

工具集会在指定的输出目录（默认为`data`）生成以下文件：

1. `trends_all_YYYY-MM-DD.csv`: Google Trends数据
2. `scored_YYYY-MM-DD.csv`: 关键词评分结果
3. `scored_high_score_YYYY-MM-DD.csv`: 高分关键词（分数>=70）
4. `intent_YYYY-MM-DD.csv`: 搜索意图分析结果
5. `intent_summary_YYYY-MM-DD.json`: 意图分析摘要
6. `intent_I/N/C/E/B_YYYY-MM-DD.csv`: 按意图分组的关键词
7. `analysis_report_YYYY-MM-DD.json`: 综合分析报告
8. `analysis_log_YYYY-MM-DD.txt`: 分析日志

## 搜索意图框架

INCEB五层框架将搜索意图分为五类：

1. **I - Informational（信息型）**
   - 用户目的：获取信息、背景知识
   - 推荐内容：入门指南、终极手册、清单/模板下载

2. **N - Navigational（导航型）**
   - 用户目的：直接到达目标站点
   - 推荐内容：站点结构优化、登录/定价页加载加速

3. **C - Commercial（商业型）**
   - 用户目的：比较、评估、意向未定
   - 推荐内容：对比页、案例库、ROI计算器

4. **E - Transactional（交易型）**
   - 用户目的：立即购买/下载
   - 推荐内容：促销活动、一键试用、限时优惠弹窗

5. **B - Behavioral（行为型）**
   - 用户目的：使用后出现的问题或深度用法
   - 推荐内容：故障排查文档、教程视频、二次销售插件

## 示例

分析"ai工具"和"内容生成"关键词：

```bash
python market_analyzer.py --keywords "ai工具" "内容生成"
```

## 注意事项

- 为避免Google API限制，脚本在处理多个关键词时会在请求之间添加延迟
- 评分权重总和应为1.0，如果不是，脚本会自动归一化
- 对于非英语关键词，建议将`hl`参数设置为相应的语言代码