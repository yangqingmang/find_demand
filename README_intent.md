# 搜索意图分析工具

这个脚本用于分析关键词的搜索意图，是市场需求分析工具集的第三个组件。

## 功能特点

- 基于INCEB五层框架分析关键词搜索意图
- 支持从关键词文本判断意图
- 生成详细的意图分析报告和摘要
- 按意图类型分组保存关键词
- 提供针对每种意图的推荐行动

## 使用方法

### 基本用法

```bash
python intent_analyzer.py --input data/scored_2025-08-04.csv
```

### 指定关键词列名

```bash
python intent_analyzer.py --input data/scored_2025-08-04.csv --keyword-col keyword
```

### 参数说明

- `--input`: 输入CSV文件路径（必需）
- `--output`: 输出目录，默认为data
- `--keyword-col`: 关键词列名，默认为query

## 意图分类框架

INCEB五层框架将搜索意图分为五类：

1. **I - Informational（信息型）**
   - 用户目的：获取信息、背景知识
   - 关键词信号：what, how, guide, tutorial, idea
   - 推荐内容：入门指南、终极手册、清单/模板下载

2. **N - Navigational（导航型）**
   - 用户目的：直接到达目标站点
   - 关键词信号：brand, login, dashboard, pricing
   - 推荐内容：站点结构优化、登录/定价页加载加速

3. **C - Commercial（商业型）**
   - 用户目的：比较、评估、意向未定
   - 关键词信号：best, top, vs, review, pricing, features
   - 推荐内容：对比页、案例库、ROI计算器

4. **E - Transactional（交易型）**
   - 用户目的：立即购买/下载
   - 关键词信号：buy, order, coupon, template, download
   - 推荐内容：促销活动、一键试用、限时优惠弹窗

5. **B - Behavioral（行为型）**
   - 用户目的：使用后出现的问题或深度用法
   - 关键词信号：error, fix, tutorial, integration, API
   - 推荐内容：故障排查文档、教程视频、二次销售插件

## 输出文件

脚本会在指定的输出目录（默认为`data`）生成以下文件：

1. `intent_YYYY-MM-DD.csv`: 包含所有关键词的意图分析结果
2. `intent_summary_YYYY-MM-DD.json`: 意图分析摘要（JSON格式）
3. `intent_I_YYYY-MM-DD.csv`: 信息型关键词
4. `intent_N_YYYY-MM-DD.csv`: 导航型关键词
5. `intent_C_YYYY-MM-DD.csv`: 商业型关键词
6. `intent_E_YYYY-MM-DD.csv`: 交易型关键词
7. `intent_B_YYYY-MM-DD.csv`: 行为型关键词

## 输出字段说明

- 原始数据字段（如query、score等）
- `intent`: 主要意图（I/N/C/E/B）
- `intent_confidence`: 意图置信度（0.5-1.0）
- `secondary_intent`: 次要意图（如果有）
- `intent_description`: 意图描述
- `recommended_action`: 推荐行动

## 示例

分析已评分的关键词数据：

```bash
python intent_analyzer.py --input data/scored_2025-08-04.csv