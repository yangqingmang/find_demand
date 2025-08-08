# 意图分析规则变化适应指南

## 概述

当意图分析规则发生变化时，建站脚本可以通过配置化的方式进行适应，而无需修改核心代码。

## 适应性评估

### ✅ 当前适应性良好的方面

1. **松耦合的接口设计** - 建站脚本通过标准接口调用意图分析器
2. **标准化数据格式** - 使用DataFrame和标准字段名进行数据交换
3. **配置化的意图描述** - 通过INTENT_DESCRIPTIONS字典管理意图信息

### ⚠️ 需要改进的方面

1. **硬编码的意图类型判断** - 在多个文件中硬编码了特定意图的处理逻辑
2. **固定的页面模板映射** - 意图到模板的映射关系固化在代码中
3. **意图特定的内容结构** - 不同意图的内容结构硬编码在代码中

## 改进方案

### 1. 意图配置管理器 (IntentConfigManager)

新增 `src/website_builder/intent_config.py` 文件，提供配置化的意图管理功能：

- 支持从JSON配置文件加载意图规则
- 提供默认配置作为后备方案
- 支持动态添加新的意图类型
- 统一管理意图名称、描述、模板、内容结构等信息

### 2. 配置文件格式

使用 `intent_config_example.json` 作为配置模板，包含：

```json
{
  "intent_types": {
    "I": {
      "name": "信息获取",
      "description": "用户寻求信息和知识",
      "page_template": "article_i",
      "content_sections": [...],
      "seo_priority": "medium",
      "word_count": 2000
    }
  }
}
```

### 3. 使用方式

#### 3.1 基本使用

```python
from src.website_builder.intent_config import IntentConfigManager

# 使用默认配置
config_manager = IntentConfigManager()

# 使用自定义配置文件
config_manager = IntentConfigManager('path/to/your/config.json')

# 获取意图信息
intent_name = config_manager.get_intent_name('I')
sections = config_manager.get_content_sections('I')
```

#### 3.2 在建站脚本中使用

```python
# 在builder_core.py中
builder = IntentBasedWebsiteBuilder(
    intent_data_path='data.csv',
    output_dir='output',
    config={
        'intent_config_path': 'custom_intent_config.json'
    }
)
```

## 适应新意图规则的步骤

### 步骤1：分析新的意图规则

当意图分析规则发生变化时，首先分析：
- 新增了哪些意图类型？
- 现有意图的定义是否发生变化？
- 意图的优先级或处理方式是否需要调整？

### 步骤2：更新配置文件

根据新的意图规则，更新或创建新的配置文件：

```json
{
  "intent_types": {
    "NEW_INTENT": {
      "name": "新意图类型",
      "description": "新意图的描述",
      "page_template": "article_new",
      "content_sections": [
        {"name": "新区块", "type": "new_section", "word_count": 500}
      ],
      "seo_priority": "high",
      "word_count": 1500
    }
  }
}
```

### 步骤3：更新页面模板（如需要）

如果新意图需要特殊的页面模板，在 `page_templates.py` 中添加：

```python
'article_new': {
    'title': '新意图文章模板',
    'description': '适用于新意图的文章页面',
    'sections': [...]
}
```

### 步骤4：测试验证

运行建站脚本，验证新的意图规则是否正确应用：

```bash
python -m src.website_builder.intent_based_website_builder \
  --input data.csv \
  --output output \
  --config custom_config.json
```

## 最佳实践

### 1. 版本控制

- 为不同版本的意图规则创建不同的配置文件
- 使用版本号命名：`intent_config_v2.0.json`

### 2. 向后兼容

- 保持默认配置的稳定性
- 新增意图类型时，提供合理的默认值

### 3. 配置验证

- 在加载配置时进行格式验证
- 提供清晰的错误信息

### 4. 文档更新

- 及时更新配置文件的说明文档
- 记录意图规则的变更历史

## 总结

通过引入配置化的意图管理机制，建站脚本现在具备了良好的适应性：

- ✅ **无需修改代码** - 通过配置文件适应新的意图规则
- ✅ **向后兼容** - 保持现有功能的稳定性
- ✅ **易于扩展** - 支持动态添加新的意图类型
- ✅ **配置灵活** - 支持细粒度的意图配置管理

当意图分析规则发生变化时，只需要更新配置文件，建站脚本就能自动适应新的规则，大大提高了系统的灵活性和可维护性。