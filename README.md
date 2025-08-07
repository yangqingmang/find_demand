# 搜索意图分析工具

基于规则的搜索意图分析工具，无需机器学习模型，通过词面分析和SERP结构分析来判断搜索关键词的意图。

## 功能概述

搜索意图分析工具用于分析关键词的搜索意图，基于6大主意图和24个子意图的分类体系：

- **I - 信息获取**：用户尚未决定行动，寻求信息
- **N - 导航直达**：指向特定站点或文件
- **C - 商业评估**：寻找最佳或比较多个方案
- **E - 交易购买**：已有明确交易意向
- **B - 行为后续**：已拥有产品，解决使用问题
- **L - 本地/到店**：O2O/地图式需求

## 使用方法

### 基本用法

```bash
python intent_analyzer.py --input data/keywords.csv
```

### 参数说明

- `--input`：输入CSV文件路径（必需）
- `--output`：输出目录，默认为data
- `--query-col`：关键词列名，默认为"query"
- `--keywords-dict`：关键词字典YAML文件路径（可选）
- `--serp-rules`：SERP规则YAML文件路径（可选）

### 输出说明

工具会生成以下文件：

1. `intent_YYYY-MM-DD.csv`：包含所有关键词的意图分析结果
2. `intent_summary_YYYY-MM-DD.json`：意图分析摘要（JSON格式）
3. `intent_I_YYYY-MM-DD.csv`：信息型关键词
4. `intent_N_YYYY-MM-DD.csv`：导航型关键词
5. `intent_C_YYYY-MM-DD.csv`：商业型关键词
6. `intent_E_YYYY-MM-DD.csv`：交易型关键词
7. `intent_B_YYYY-MM-DD.csv`：行为型关键词
8. `intent_L_YYYY-MM-DD.csv`：本地/到店型关键词
9. `pending_review_YYYY-MM-DD.txt`：未命中任何规则的关键词

## 自定义规则

### 关键词字典

可以创建自定义的关键词字典YAML文件：

```yaml
# keywords_dict.yaml
I1: [what is, definition, mean, 意味, 是什么, 定义]
I2: [architecture, algorithm, 原理, 源码, protocol]
# 更多规则...
```

### SERP规则

可以创建自定义的SERP规则YAML文件：

```yaml
# serp_rules.yaml
shopping_ads:
  E: 0.8
  E3: 0.5
price_snippet:
  E: 0.6
  E1: 0.4
# 更多规则...
```

## 输出示例

### CSV输出

```
query,intent_primary,intent_secondary,sub_intent,probability,probability_secondary,signals_hit
what is ai,I,,I1,0.85,0,词面:what is, 词面:是什么
best ai tools 2025,C,I,C1,0.64,0.36,词面:best, SERP:top_stories
buy ai writing tool,E,,E3,0.92,0,词面:buy, SERP:shopping_ads
```

### JSON摘要

```json
{
  "total_keywords": 25,
  "intent_counts": {
    "I": 19,
    "N": 1,
    "C": 4,
    "E": 1,
    "B": 0
  },
  "intent_percentages": {
    "I": 76.0,
    "N": 4.0,
    "C": 16.0,
    "E": 4.0,
    "B": 0.0
  },
  "intent_keywords": {
    "I": ["what is ai", "how to use ai tools", ...],
    "N": ["claude ai login"],
    "C": ["best ai tools 2025", "ai tools vs human", ...],
    "E": ["buy ai writing tool"],
    "B": []
  },
  "recommendations": {
    "I": "创建入门指南和教程内容",
    "N": "优化网站导航和登录页面",
    "C": "创建对比页和评测内容",
    "E": "优化购买流程和促销活动",
    "B": "提供故障排查和高级教程",
    "L": "优化本地搜索和地图展示"
  }
}
```

## 维护与扩展

1. 每周将未命中但搜索量超过阈值的关键词追加到 `pending_review.txt`，人工标注后更新YAML
2. SERP规则只增不删，历史分值可微调
3. 若需支持多语种，直接复制当前YAML，替换为目标语言关键词