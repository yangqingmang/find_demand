# 关键词评分工具

这个脚本用于对关键词进行综合评分和排序，是市场需求分析工具集的第二个组件。

## 功能特点

- 对关键词进行综合评分（搜索量、增长率、关键词难度）
- 支持自定义评分权重
- 关键词过滤功能（最低评分、最低搜索量等）
- 可选的数据丰富功能（模拟Google Ads数据）
- 自动保存评分结果和高分关键词

## 使用方法

### 基本用法

```bash
python keyword_scorer.py --input data/trends_all_2025-08-04.csv
```

### 自定义权重

```bash
python keyword_scorer.py --input data/trends_all_2025-08-04.csv --volume-weight 0.5 --growth-weight 0.3 --kd-weight 0.2
```

### 过滤低分关键词

```bash
python keyword_scorer.py --input data/trends_all_2025-08-04.csv --min-score 60
```

### 添加模拟的Ads数据

```bash
python keyword_scorer.py --input data/trends_all_2025-08-04.csv --enrich
```

### 参数说明

- `--input`: 输入CSV文件路径（必需）
- `--output`: 输出目录，默认为data
- `--volume-weight`: 搜索量权重，默认0.4
- `--growth-weight`: 增长率权重，默认0.4
- `--kd-weight`: 关键词难度权重，默认0.2
- `--min-score`: 最低评分过滤
- `--enrich`: 使用模拟的Ads数据丰富关键词

## 评分机制

评分公式：`score = volume_weight * volume_score + growth_weight * growth_score + kd_weight * kd_score`

其中：
- `volume_score`: 搜索量归一化到0-100
- `growth_score`: 增长率归一化到0-100
- `kd_score`: 关键词难度归一化到0-100（KD越低分数越高）

## 评分等级

- A级: 70-100分
- B级: 50-69分
- C级: 30-49分
- D级: 0-29分

## 输出文件

脚本会在指定的输出目录（默认为`data`）生成以下文件：

1. `scored_YYYY-MM-DD.csv`: 包含所有关键词的评分结果
2. `scored_high_score_YYYY-MM-DD.csv`: 仅包含高分关键词（分数>=70）

## 输出字段说明

- 原始数据字段（如query、value、growth等）
- `volume_score`: 搜索量评分(0-100)
- `growth_score`: 增长率评分(0-100)
- `kd_score`: 关键词难度评分(0-100)
- `score`: 综合评分(0-100)
- `grade`: 评分等级(A/B/C/D)

## 示例

对Google Trends数据进行评分：

```bash
python keyword_scorer.py --input data/trends_all_2025-08-04.csv --enrich