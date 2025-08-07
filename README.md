# 市场需求分析工具集

专业的市场需求分析工具，专门用于挖掘和分析关键词需求，特别针对海外AI工具站进行了优化。

## 🚀 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 基础使用
python main.py "ai tools"

# 多关键词分析
python main.py "ai tools" "chatgpt" "claude ai" --geo US --min-score 50
```

## 📋 核心功能

- **Google Trends数据采集** - 自动收集趋势数据和相关查询
- **智能关键词评分** - 基于搜索量、增长率、竞争度的多维度评分
- **搜索意图分析** - 识别5种搜索意图类型并提供内容策略建议
- **SERP分析** - 搜索引擎结果页面特征分析（可选）
- **Google Ads集成** - 精确搜索量和竞争数据（可选）

## 📊 搜索意图类型

| 类型 | 描述 | 内容策略 |
|------|------|----------|
| 信息型 (I) | 寻求信息和知识 | 创建教程、指南、解释性内容 |
| 导航型 (N) | 寻找特定网站或页面 | 优化品牌页面和导航体验 |
| 商业型 (C) | 研究产品或服务 | 创建对比、评测、功能介绍 |
| 交易型 (E) | 准备购买或下载 | 优化购买流程和促销页面 |
| 行为型 (B) | 解决问题或执行任务 | 提供操作指南和故障排除 |

## 📁 输出文件

- `analysis_report_YYYY-MM-DD.json` - 综合分析报告
- `market_analysis_detailed_YYYY-MM-DD.csv` - 详细分析数据
- `keywords_[意图类型]_YYYY-MM-DD.csv` - 按意图分组的关键词

## 🔧 高级功能

```bash
# 批量分析
python batch_analysis.py --input keywords.txt

# 关键词聚类
python keyword_clustering.py --input scored_keywords.csv

# AI网站构建
python ai_website_builder.py --keywords "ai tools"
```

## 📖 完整文档

**详细使用说明请查看：[项目概述文档](docs/项目概述.md)**

该文档包含：
- 完整的功能介绍和使用方法
- 详细的配置参数说明
- 项目架构和扩展开发指南
- 常见问题解决方案
- 海外AI工具站特化功能说明

## 📋 其他文档

- [项目优化总结](docs/项目优化总结.md) - 最新优化内容和改进
- [完整操作手册](docs/完整操作手册.md) - 详细操作步骤
- [API密钥安全管理指南](docs/API密钥安全管理指南.md) - API配置说明（包含RSA+AES加密配置）

## 🛠️ 技术栈

- Python 3.7+
- pandas, numpy - 数据处理
- pytrends - Google Trends API
- requests - HTTP请求处理

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**让数据驱动您的市场决策！** 🎯
