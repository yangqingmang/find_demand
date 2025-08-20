# 需求挖掘分析工具

整合六大需求挖掘方法的智能分析系统，专注于出海AI工具需求发现。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行分析（使用默认词根分析）
python main.py

# 分析关键词文件
python main.py --input data/keywords.csv

# 多平台关键词发现
python main.py --discover "AI tool" "AI generator"

# 查看所有选项
python main.py --help
```

## 主要功能

- 🔍 **词根趋势分析** - 基于52个核心词根的趋势分析
- 📊 **关键词分析** - 搜索意图、市场机会评估
- 🌐 **多平台发现** - 整合多个平台的关键词发现
- 📈 **趋势预测** - 基于Google Trends的趋势分析
- 🏗️ **网站生成** - 基于关键词意图的自动建站

## 输出结果

分析结果保存在 `src/demand_mining/reports/` 目录下，包括：
- CSV格式的详细数据
- JSON格式的分析报告
- 按意图分类的关键词文件

## 配置

API配置文件位于 `config/` 目录，支持加密存储。

---

更多详细信息请运行 `python main.py --help` 查看。