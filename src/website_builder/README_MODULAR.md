# 网站建设工具模块化重构说明

## 概述

我们已经成功将原来的大型`intent_based_website_builder.py`文件（4833行）拆分为多个功能模块，提高了代码的可维护性和可扩展性。

## 模块结构

### 核心模块

1. **`builder_core.py`** - 核心构建器类
   - `IntentBasedWebsiteBuilder` - 主要的网站建设工具类
   - 负责初始化、数据加载和协调其他模块

2. **`structure_generator.py`** - 网站结构生成器
   - `WebsiteStructureGenerator` - 网站结构生成器类
   - 负责生成网站的整体结构和页面布局

3. **`content_planner.py`** - 内容计划生成器
   - `ContentPlanGenerator` - 内容计划生成器类
   - 负责创建详细的内容计划和编辑日程

4. **`page_templates.py`** - 页面模板管理器
   - `PageTemplateManager` - 页面模板管理器类
   - 管理不同类型页面的模板和结构

5. **`utils.py`** - 工具函数
   - 包含各种实用工具函数
   - 文件操作、数据处理、文本处理等

### 辅助文件

6. **`simple_intent_website_builder.py`** - 简化版建设工具
   - 保持原有的简化版功能
   - 适用于快速原型和简单需求

7. **`cli.py`** - 命令行接口
   - 提供命令行操作接口
   - 支持不同的操作模式

8. **`__init__.py`** - 包初始化文件
   - 导出所有主要类和函数
   - 提供统一的导入接口

## 主要改进

### 1. 模块化设计
- 将4833行的大文件拆分为8个功能明确的模块
- 每个模块职责单一，便于维护和测试
- 支持独立开发和测试各个功能模块

### 2. 更好的代码组织
- 核心逻辑与工具函数分离
- 模板管理独立成模块
- 内容规划功能模块化

### 3. 增强的功能
- **页面模板系统**：支持多种页面类型的模板
- **内容计划生成**：更详细的内容规划功能
- **工具函数库**：丰富的实用工具函数

### 4. 向后兼容性
- 保持原有API接口不变
- 支持原有的使用方式
- 新的`intent_based_website_builder.py`作为统一入口

## 使用方法

### 1. 导入方式

```python
# 方式1：导入具体的类
from src.website_builder.builder_core import IntentBasedWebsiteBuilder
from src.website_builder.structure_generator import WebsiteStructureGenerator

# 方式2：从包级别导入
from src.website_builder import IntentBasedWebsiteBuilder, WebsiteStructureGenerator

# 方式3：导入所有（保持向后兼容）
from src.website_builder.intent_based_website_builder import IntentBasedWebsiteBuilder
```

### 2. 命令行使用

```bash
# 使用新的模块化版本
python src/website_builder/intent_based_website_builder.py --input data.csv --output output

# 使用CLI接口
python src/website_builder/cli.py --input data.csv --output output

# 使用简化版
python src/website_builder/simple_intent_website_builder.py --input data.csv
```

### 3. 编程接口

```python
from src.website_builder import IntentBasedWebsiteBuilder

# 创建构建器实例
builder = IntentBasedWebsiteBuilder(
    intent_data_path="data/keywords.csv",
    output_dir="output"
)

# 加载数据
builder.load_intent_data()

# 生成网站结构
structure = builder.generate_website_structure()

# 创建内容计划
content_plan = builder.create_content_plan()
```

## 测试

我们提供了完整的测试脚本来验证模块化结构：

```bash
python src/website_builder/test_modular_structure.py
```

测试包括：
- 模块导入测试
- 基本功能测试
- 模块集成测试

## 文件大小对比

- **重构前**：`intent_based_website_builder.py` - 4833行
- **重构后**：
  - `builder_core.py` - ~200行
  - `structure_generator.py` - ~300行
  - `content_planner.py` - ~400行
  - `page_templates.py` - ~300行
  - `utils.py` - ~200行
  - 其他文件 - ~500行
  - **总计**：~1900行（分布在8个文件中）

## 优势

1. **可维护性**：每个模块功能单一，易于理解和修改
2. **可测试性**：可以独立测试每个模块
3. **可扩展性**：容易添加新功能或修改现有功能
4. **代码复用**：模块可以在不同场景下复用
5. **团队协作**：不同开发者可以并行开发不同模块

## 下一步计划

1. 添加更多的页面模板类型
2. 增强内容计划的智能化程度
3. 添加更多的工具函数
4. 完善单元测试覆盖率
5. 添加配置文件支持