# Google Trends 数据采集工具

这个脚本用于自动化获取 Google Trends 的 Rising Queries（上升查询）数据，是市场需求分析工具集的第一个组件。

## 功能特点

- 获取指定关键词的 Rising Queries 数据
- 支持多个种子关键词批量处理
- 内置重试机制，提高数据获取稳定性
- 自动保存结果到CSV文件
- 支持地区筛选和时间范围设置

## 使用方法

### 基本用法

```bash
python trends_collector.py --keywords "ai营销工具" "内容生成"
```

### 指定地区和时间范围

```bash
python trends_collector.py --keywords "ai营销工具" "内容生成" --geo "US" --timeframe "today 12-m"
```

### 参数说明

- `--keywords`: 要查询的关键词列表（必需）
- `--geo`: 地区代码，如US、GB等，默认为全球
- `--timeframe`: 时间范围，默认为过去3个月（today 3-m）
- `--output`: 输出目录，默认为data

## 输出文件

脚本会在指定的输出目录（默认为`data`）生成以下文件：

1. `trends_all_YYYY-MM-DD.csv`: 包含所有关键词的合并结果
2. `trends_关键词_YYYY-MM-DD.csv`: 每个关键词的单独结果文件

## 输出字段说明

- `query`: 相关查询词
- `value`: 相关性得分
- `growth`: 增长率（%）
- `seed_keyword`: 原始种子关键词

## 示例

获取"ai营销工具"在美国市场过去12个月的上升查询：

```bash
python trends_collector.py --keywords "ai营销工具" --geo "US" --timeframe "today 12-m"
```

## 注意事项

- 为避免Google API限制，脚本在处理多个关键词时会在请求之间添加延迟
- 如果Rising Queries不可用，脚本会返回Top Queries（热门查询）
- 对于非英语关键词，建议将`hl`参数设置为相应的语言代码