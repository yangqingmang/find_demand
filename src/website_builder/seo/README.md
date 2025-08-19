# SEO优化工具集

本目录包含完整的SEO优化工具集，用于自动化网站SEO优化工作流程。

## 文件说明

### 核心文件
- `seo_workflow_engine.py` - SEO工作流程引擎，执行程序化SEO优化
- `seo_optimization_workflow.json` - SEO优化配置文件，定义完整的优化流程
- `website_seo_optimizer.py` - 网站SEO优化工具，对现有网站进行SEO优化

### 文档文件
- `SEO工作流程使用指南.md` - SEO工作流程引擎的详细使用指南
- `SEO优化策略总结.md` - 项目中实施的SEO优化策略总结
- `README.md` - 本文件，工具集使用说明

### 示例文件
- `seo_integration_example.py` - SEO工具集成使用示例

## 快速开始

### 1. 使用SEO增强版建站工具

```bash
# 使用SEO增强版建站工具（默认启用SEO）
python -m src.website_builder.simple_intent_website_builder \
    --input data/test_intent_keywords.csv \
    --output seo_output \
    --action all

# 或者使用专门的SEO增强版工具
python -m src.website_builder.seo_enhanced_website_builder \
    --input data/test_intent_keywords.csv \
    --output seo_output \
    --enable-seo
```

### 2. 对现有网站进行SEO优化

```bash
# 分析现有网站结构
python -m src.seo.website_seo_optimizer \
    --website path/to/website \
    --action analyze

# 执行完整SEO优化
python -m src.seo.website_seo_optimizer \
    --website path/to/website \
    --output optimized_output \
    --action all
```

### 3. 运行完整演示

```bash
# 运行SEO工具集成演示
python src/seo/seo_integration_example.py
```

## 工具详细说明

### SEO工作流程引擎 (seo_workflow_engine.py)

程序化SEO自动化引擎，提供以下功能：

- **自动生成SEO Meta标签** - 根据关键词和搜索意图生成优化的标题、描述、关键词
- **内容模板管理** - 为不同搜索意图提供结构化的内容模板
- **URL结构优化** - 生成SEO友好的URL路径
- **SEO质量验证** - 检查页面SEO质量并提供优化建议
- **完整工作流程执行** - 自动化执行整个SEO优化流程

#### 基本使用

```python
from src.seo.seo_workflow_engine import SEOWorkflowEngine

# 初始化SEO引擎
seo_engine = SEOWorkflowEngine("src/seo/seo_optimization_workflow.json")

# 准备页面数据
page_data = {
    'primary_keyword': 'AI tools for content creation',
    'keywords': ['AI tools', 'content creation', 'artificial intelligence'],
    'intent': 'C',  # Commercial intent
    'search_volume': 5000,
    'competition': 'medium'
}

# 生成SEO优化的Meta标签
meta_tags = seo_engine.get_seo_meta_tags(page_data)

# 获取内容模板
template = seo_engine.get_content_template('C')

# 生成SEO友好URL
url = seo_engine.get_url_structure(page_data)

# 验证SEO质量
quality_check = seo_engine.validate_seo_quality(page_data)
```

### 网站SEO优化工具 (website_seo_optimizer.py)

专门用于对现有网站结构进行SEO优化的工具。

#### 主要功能

- **网站结构分析** - 分析现有网站的SEO状况
- **批量页面优化** - 为所有页面应用SEO优化
- **SEO问题识别** - 自动识别SEO问题和优化机会
- **优化报告生成** - 生成详细的SEO优化报告
- **网站地图生成** - 自动生成XML网站地图

#### 使用示例

```python
from src.seo.website_seo_optimizer import WebsiteSEOOptimizer

# 初始化优化工具
optimizer = WebsiteSEOOptimizer("src/seo/seo_optimization_workflow.json")

# 分析网站结构
analysis_result = optimizer.analyze_website_structure("path/to/website")

# 执行SEO优化
optimization_results = optimizer.optimize_website(
    analysis_result['website_data'], 
    "optimized_output"
)
```

### SEO增强版建站工具 (seo_enhanced_website_builder.py)

基于原有建站工具的SEO增强版本，集成了完整的SEO优化流程。

#### 主要特性

- **继承原有功能** - 保持原有建站工具的所有功能
- **集成SEO引擎** - 自动应用SEO优化到所有生成的页面
- **SEO质量监控** - 实时监控生成页面的SEO质量
- **优化报告** - 生成详细的SEO优化报告
- **增强内容计划** - 为内容计划添加SEO优化信息

## 配置文件说明

### seo_optimization_workflow.json

完整的SEO优化工作流程配置文件，包含5个主要步骤：

1. **数据采集与清洗** - 关键词数据处理和意图分类
2. **AI内容生成与结构化** - 基于模板生成SEO优化内容
3. **服务端渲染与网页结构** - 生成SEO友好的HTML结构
4. **长尾关键词页面自动构建** - 批量生成关键词页面
5. **定时更新Sitemap** - 自动化站点地图管理

#### 配置示例

```json
{
  "seo_workflow": {
    "workflow_steps": {
      "step_1": {
        "name": "数据采集与清洗",
        "config": {
          "data_sources": [...],
          "data_processing": {...}
        }
      }
    },
    "quality_assurance": {
      "content_quality_checks": [...],
      "technical_seo_checks": [...]
    }
  }
}
```

## 最佳实践

### 1. 关键词数据准备

确保输入数据包含以下字段：
- `query` - 关键词
- `intent_primary` - 主要搜索意图 (I/C/E/N/B/L)
- `search_volume` - 搜索量（可选）
- `competition` - 竞争程度（可选）

### 2. SEO配置优化

根据项目需求调整 `seo_optimization_workflow.json` 中的配置：
- 调整关键词密度阈值
- 修改内容模板结构
- 设置质量检查标准

### 3. 持续优化

- 定期运行SEO质量检查
- 监控关键词排名变化
- 根据数据反馈调整优化策略

## 故障排除

### 常见问题

1. **SEO引擎初始化失败**
   - 检查配置文件路径是否正确
   - 确认配置文件格式是否有效

2. **页面优化失败**
   - 检查页面数据是否包含必需字段
   - 确认关键词数据格式正确

3. **质量检查不通过**
   - 检查质量阈值设置是否合理
   - 确认页面内容是否符合SEO标准

### 调试模式

启用详细日志记录：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 扩展开发

### 添加自定义SEO检查

在配置文件中添加自定义质量检查：

```json
{
  "custom_quality_check": {
    "name": "custom_check",
    "threshold": "custom_threshold",
    "action_on_fail": "custom_action"
  }
}
```

### 自定义内容模板

为特定搜索意图添加自定义模板：

```json
{
  "custom_intent": {
    "template_name": "custom_template",
    "sections": [...]
  }
}
```

## 技术支持

如有问题或建议，请参考：
- `SEO工作流程使用指南.md` - 详细使用指南
- `SEO优化策略总结.md` - 策略说明
- `seo_integration_example.py` - 使用示例

## 更新日志

- v1.0 - 初始版本，包含基础SEO优化功能
- v1.1 - 添加网站SEO优化工具
- v1.2 - 集成SEO增强版建站工具