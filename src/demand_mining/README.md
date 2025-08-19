# 需求挖掘模块 v2.0

## 🎯 模块概述

重构后的需求挖掘模块，提供统一、模块化的关键词分析和需求发现功能。

## 📁 模块结构

```
src/demand_mining/
├── __init__.py                  # 模块入口
├── unified_main.py             # 统一主程序
├── config.py                   # 配置管理
├── README.md                   # 模块文档
├── managers/                   # 管理器模块
│   ├── __init__.py
│   ├── base_manager.py        # 基础管理器
│   ├── keyword_manager.py     # 关键词分析管理器
│   ├── discovery_manager.py   # 关键词发现管理器
│   └── trend_manager.py       # 趋势分析管理器
├── analyzers/                 # 分析器模块
├── core/                      # 核心功能模块
├── tools/                     # 工具模块
└── reports/                   # 报告输出目录
```

## 🚀 快速开始

### 基本使用

```python
from src.demand_mining import DemandMiningManager

# 创建管理器
manager = DemandMiningManager()

# 分析关键词文件
result = manager.run_unified_analysis(
    analysis_type='keywords',
    input_file='data/keywords.csv'
)

# 多平台关键词发现
result = manager.run_unified_analysis(
    analysis_type='discovery',
    search_terms=['AI tool', 'AI generator']
)

# 词根趋势分析
result = manager.run_unified_analysis(
    analysis_type='root_trends'
)
```

### 命令行使用

```bash
# 分析关键词文件
python -m src.demand_mining.unified_main --analyze-file data/keywords.csv

# 分析指定关键词
python -m src.demand_mining.unified_main --analyze-keywords "ai tool" "ai generator"

# 多平台关键词发现
python -m src.demand_mining.unified_main --discover "AI image" "AI text"

# 词根趋势分析
python -m src.demand_mining.unified_main --root-trends

# 显示帮助
python -m src.demand_mining.unified_main --help
```

## 🔧 管理器说明

### KeywordManager
负责关键词分析功能：
- 意图分析
- 市场分析
- 机会评分
- 建站建议

### DiscoveryManager
负责多平台关键词发现：
- Reddit关键词发现
- Hacker News趋势分析
- YouTube搜索建议
- Google自动完成

### TrendManager
负责趋势分析：
- 词根趋势分析
- 关键词趋势预测
- Google Trends数据采集

## 📊 输出格式

所有分析结果统一返回以下格式：

```json
{
    "analysis_type": "keywords|discovery|root_trends",
    "analysis_time": "2025-08-19T11:37:00",
    "total_keywords": 100,
    "results": {...},
    "summary": {...},
    "recommendations": [...]
}
```

## 🎯 核心特性

- **统一接口**: 所有功能通过统一的API访问
- **模块化设计**: 功能按职责清晰分离
- **可扩展性**: 易于添加新的分析器和管理器
- **配置灵活**: 支持多种配置方式
- **输出标准**: 统一的结果格式和保存机制

## 🔄 版本历史

### v2.0.0 (2025-08-19)
- 完全重构模块架构
- 统一管理器接口
- 模块化设计
- 清理遗留代码

## 📝 开发指南

### 添加新管理器

1. 继承 `BaseManager` 类
2. 实现 `analyze()` 方法
3. 在 `managers/__init__.py` 中导出
4. 在 `unified_main.py` 中集成

### 扩展分析功能

1. 在对应管理器中添加新方法
2. 更新 `run_unified_analysis()` 方法
3. 添加命令行参数支持
4. 更新文档

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 📄 许可证

MIT License