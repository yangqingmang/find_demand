# 关键词文件格式说明

## 📋 关键词文件是什么？

关键词文件是集成工作流的**输入数据源**，包含需要分析和处理的搜索关键词列表。系统会基于这些关键词进行需求挖掘、意图分析，并自动生成对应的网站。

## 📊 支持的文件格式

### 1. CSV格式（推荐）
```csv
query,search_volume,competition,cpc
ai image generator,12000,0.6,2.5
pdf converter online,8500,0.4,1.8
code formatter tool,3200,0.3,1.2
```

### 2. JSON格式
```json
[
  {
    "query": "ai image generator",
    "search_volume": 12000,
    "competition": 0.6,
    "cpc": 2.5
  },
  {
    "query": "pdf converter online", 
    "search_volume": 8500,
    "competition": 0.4,
    "cpc": 1.8
  }
]
```

## 📝 字段说明

| 字段名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `query` | 字符串 | ✅ | 搜索关键词（主要字段） |
| `search_volume` | 数字 | ❌ | 月搜索量 |
| `competition` | 数字 | ❌ | 竞争度（0-1之间） |
| `cpc` | 数字 | ❌ | 每次点击成本（美元） |
| `keyword` | 字符串 | ❌ | 关键词别名（与query等效） |

> **注意**：只有 `query` 字段是必需的，其他字段可选。如果没有提供可选字段，系统会使用默认值或模拟数据。

## 🎯 关键词来源

### 1. 手动收集
- Google Keyword Planner
- Ahrefs关键词工具
- SEMrush关键词研究
- Ubersuggest关键词建议

### 2. 自动挖掘
- Google搜索下拉建议
- 相关搜索推荐
- 竞品网站关键词分析
- 社交媒体热门话题

### 3. AI工具导航站
- theresanaiforthat.com
- Toolify.ai
- AI工具排行榜
- ProductHunt AI分类

## 📂 示例文件位置

```
data/
├── sample_keywords.csv          # 示例关键词文件
├── ai_tools_keywords.csv        # AI工具类关键词
├── converter_tools.csv          # 转换工具类关键词
└── generator_tools.csv          # 生成器工具类关键词
```

## 🚀 使用方法

### 1. 使用示例文件
```bash
python src/integrated_workflow.py --input data/sample_keywords.csv
```

### 2. 使用自定义文件
```bash
python src/integrated_workflow.py --input your_keywords.csv --min-score 70
```

### 3. 批量处理多个文件
```bash
# 处理多个关键词文件
for file in data/*.csv; do
    python src/integrated_workflow.py --input "$file" --max-projects 3
done
```

## 💡 关键词选择建议

### ✅ 优质关键词特征
- **工具类关键词**：包含generator、converter、editor等词根
- **AI相关关键词**：包含ai、artificial intelligence等前缀
- **明确意图**：用户搜索意图清晰，有明确需求
- **商业价值**：有付费意愿，CPC较高
- **竞争适中**：不过于激烈，有排名机会

### ❌ 避免的关键词类型
- 过于宽泛的关键词（如"AI"、"tool"）
- 品牌专有名词（如"Photoshop"、"ChatGPT"）
- 纯信息类查询（如"what is AI"）
- 本地化需求（如"near me"查询）
- 过时的技术关键词

## 📈 关键词质量评估

系统会自动对关键词进行多维度评分：

1. **AI相关性加分**（0-50分）
2. **词根匹配评分**（0-30分）
3. **新兴程度评分**（0-40分）
4. **商业价值评分**（0-50分）
5. **机会综合评分**（0-100分）

只有评分达到阈值的关键词才会被选中进行网站生成。

## 🔧 自定义配置

可以通过配置文件调整关键词处理参数：

```json
{
  "demand_mining": {
    "min_search_volume": 100,
    "max_competition": 0.8,
    "min_confidence": 0.7
  },
  "workflow_settings": {
    "min_opportunity_score": 60,
    "max_projects_per_batch": 5
  }
}
```

## 📋 常见问题

**Q: 关键词文件可以包含中文吗？**
A: 可以，但建议主要使用英文关键词，因为系统主要针对出海AI工具市场。

**Q: 一个文件最多可以包含多少关键词？**
A: 理论上没有限制，但建议单次处理不超过100个关键词，以确保处理效率。

**Q: 如果关键词文件格式不正确怎么办？**
A: 系统会自动检测并提示错误信息，请按照示例格式调整文件。

**Q: 可以使用Excel文件吗？**
A: 需要先将Excel文件另存为CSV格式，然后再使用。