# 市场需求分析工具集

一套完整的市场需求分析工具，包含Google Trends数据采集、关键词评分、搜索意图分析等功能。

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基础使用

```bash
# 分析单个关键词
python main.py "ai tools"

# 分析多个关键词
python main.py "ai tools" "chatgpt" "claude ai"

# 指定地区和时间范围
python main.py "ai tools" --geo US --timeframe "today 6-m"

# 设置最低评分过滤
python main.py "ai tools" --min-score 50

# 静默模式（只显示结果摘要）
python main.py "ai tools" --quiet
```

## 📁 项目结构

```
find_demand/
├── src/                          # 源代码目录
│   ├── __init__.py              # 包初始化文件
│   ├── core/                    # 核心模块
│   │   ├── __init__.py
│   │   ├── market_analyzer.py   # 市场分析器主类
│   │   └── README.md           # 核心模块文档
│   ├── collectors/              # 数据采集模块
│   │   ├── __init__.py
│   │   ├── trends_collector.py  # Google Trends数据采集器
│   │   └── README.md           # 采集模块文档
│   ├── analyzers/               # 分析器模块
│   │   ├── __init__.py
│   │   ├── keyword_scorer.py    # 关键词评分器
│   │   ├── intent_analyzer.py   # 搜索意图分析器
│   │   └── README.md           # 分析器模块文档
│   └── utils/                   # 工具模块
│       ├── __init__.py
│       ├── config.py           # 配置管理
│       └── README.md           # 工具模块文档
├── data/                        # 数据输出目录
├── docs/                        # 详细文档目录
├── main.py                      # 主入口文件
├── requirements.txt             # 依赖包列表
└── README.md                   # 项目说明文档
```

## 🔧 核心功能

### 1. Google Trends数据采集
- 支持单个和批量关键词查询
- 多地区数据获取
- 灵活的时间范围选择
- 自动获取相关搜索词

### 2. 关键词评分
- 基于搜索量、增长率、竞争度的多维度评分
- 可自定义权重配置
- 自动分级（A/B/C/D等级）
- 高分关键词筛选

### 3. 搜索意图分析
- 自动识别5种搜索意图类型
- 提供置信度评估
- 生成针对性内容策略建议
- 意图分布统计分析

### 4. 综合分析报告
- 完整的分析流程日志
- 多格式数据导出（CSV、JSON）
- 可视化结果展示
- 详细的分析建议

## 📊 输出文件说明

分析完成后会在`data`目录生成以下文件：

| 文件名 | 描述 |
|--------|------|
| `analysis_report_YYYY-MM-DD.json` | 综合分析报告 |
| `analysis_log_YYYY-MM-DD.txt` | 分析过程日志 |
| `trends_all_YYYY-MM-DD.csv` | Google Trends原始数据 |
| `scored_YYYY-MM-DD.csv` | 关键词评分结果 |
| `scored_high_score_YYYY-MM-DD.csv` | 高分关键词（≥70分） |
| `intent_YYYY-MM-DD.csv` | 搜索意图分析结果 |
| `intent_summary_YYYY-MM-DD.json` | 意图分析摘要 |
| `intent_[I/N/C/E/B]_YYYY-MM-DD.csv` | 按意图类型分组的关键词 |

## 🎯 搜索意图类型

| 代码 | 类型 | 描述 | 内容策略 |
|------|------|------|----------|
| I | 信息型 | 寻求信息和知识 | 创建教程、指南、解释性内容 |
| N | 导航型 | 寻找特定网站或页面 | 优化品牌页面和导航体验 |
| C | 商业型 | 研究产品或服务 | 创建对比、评测、功能介绍 |
| E | 交易型 | 准备购买或下载 | 优化购买流程和促销页面 |
| B | 行为型 | 解决问题或执行任务 | 提供操作指南和故障排除 |

## ⚙️ 配置参数

### 命令行参数

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `keywords` | 必需 | 要分析的关键词列表 |
| `--geo` | '' | 地区代码（US、GB、CN等），空为全球 |
| `--timeframe` | 'today 3-m' | 时间范围 |
| `--output` | 'data' | 输出目录 |
| `--min-score` | 10 | 最低评分过滤 |
| `--volume-weight` | 0.4 | 搜索量权重 |
| `--growth-weight` | 0.4 | 增长率权重 |
| `--kd-weight` | 0.2 | 关键词难度权重 |
| `--quiet` | False | 静默模式 |
| `--no-enrich` | False | 不丰富关键词数据 |

### 时间范围选项

- `today 1-m` - 过去1个月
- `today 3-m` - 过去3个月
- `today 12-m` - 过去12个月
- `today 5-y` - 过去5年

### 常用地区代码

- `US` - 美国
- `GB` - 英国
- `CN` - 中国
- `DE` - 德国
- `JP` - 日本
- `KR` - 韩国

## 📈 使用示例

### 基础分析
```bash
python main.py "人工智能工具"
```

### 多关键词分析
```bash
python main.py "chatgpt" "claude ai" "gemini" --geo US
```

### 高级配置
```bash
python main.py "ai tools" \
  --geo US \
  --timeframe "today 12-m" \
  --min-score 50 \
  --volume-weight 0.5 \
  --growth-weight 0.3 \
  --kd-weight 0.2
```

### 静默模式
```bash
python main.py "ai tools" --quiet
```

## 🔍 分析结果解读

### 评分等级
- **A级 (70-100分)**: 优秀关键词，重点投入资源
- **B级 (50-69分)**: 良好关键词，适度投入
- **C级 (30-49分)**: 一般关键词，谨慎考虑
- **D级 (0-29分)**: 较差关键词，不建议投入

### 意图分布建议
- **信息型占主导 (>60%)**: 创建教育性内容和指南
- **商业型较多 (>30%)**: 优化产品页面和比较内容
- **交易型较多 (>20%)**: 优化购买流程和着陆页

## 🛠️ 开发说明

### 模块架构
- **core**: 核心分析器和协调器
- **collectors**: 数据采集器（Google Trends等）
- **analyzers**: 分析器（评分、意图分析等）
- **utils**: 工具和配置管理

### 扩展开发
项目采用模块化设计，可以轻松扩展：
- 添加新的数据源采集器
- 开发新的分析算法
- 集成更多外部API
- 添加可视化功能

## 📋 依赖要求

- Python 3.7+
- pandas
- numpy
- pytrends
- requests

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 常见问题

### Q: Google Trends数据获取失败怎么办？
A: 检查网络连接，适当增加请求间隔，或使用代理。

### Q: 如何提高关键词评分的准确性？
A: 根据业务需求调整权重配置，或集成更多数据源。

### Q: 支持哪些语言的关键词分析？
A: 目前主要支持中英文，其他语言需要扩展意图识别词典。

### Q: 如何批量处理大量关键词？
A: 使用脚本循环调用，或修改代码支持文件输入。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件
- 加入讨论群

---

**市场需求分析工具集** - 让数据驱动您的市场决策！