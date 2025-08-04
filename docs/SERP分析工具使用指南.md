# SERP分析工具使用指南

本文档介绍如何使用新集成的SERP分析功能来提高搜索意图分析的准确性。

## 配置完成情况

✅ **已完成的配置:**
- Google Custom Search API密钥已配置
- SERP分析器已创建
- 意图分析器已集成SERP功能
- 配置管理模块已创建
- 测试脚本已准备

⚠️ **待完成的配置:**
- 需要创建Google自定义搜索引擎并获取搜索引擎ID

## 完成配置步骤

### 1. 创建Google自定义搜索引擎

1. 访问 [Google Custom Search Engine](https://cse.google.com/cse/)
2. 点击"添加"创建新的搜索引擎
3. 在"要搜索的网站"中输入 `www.google.com`
4. 给搜索引擎起个名字（如："SERP分析工具"）
5. 点击"创建"

### 2. 获取搜索引擎ID

1. 在搜索引擎设置页面，点击"设置"
2. 在"基本信息"中找到"搜索引擎ID"并复制
3. 在"高级"选项中，选择"搜索整个网络"

### 3. 更新配置文件

编辑 `config/.env` 文件，将搜索引擎ID替换：

```bash
GOOGLE_CSE_ID=你复制的搜索引擎ID
```

## 测试配置

运行测试脚本验证配置：

```bash
python test_serp_config.py
```

如果所有测试通过，你将看到：
- ✓ API密钥配置正确
- ✓ 搜索引擎ID配置正确
- ✓ API连接成功
- ✓ SERP特征提取正常
- ✓ 意图分析功能正常

## 使用方法

### 1. 基础关键词意图分析（不使用SERP）

```bash
python src/analyzers/intent_analyzer.py --input data/keywords.csv --output results
```

### 2. SERP增强意图分析（推荐）

```bash
python src/analyzers/intent_analyzer.py --input data/keywords.csv --output results --use-serp
```

### 3. Python代码中使用

```python
from src.analyzers.intent_analyzer import IntentAnalyzer
import pandas as pd

# 创建分析器（启用SERP分析）
analyzer = IntentAnalyzer(use_serp=True)

# 读取关键词数据
df = pd.read_csv('data/keywords.csv')

# 分析意图
result_df = analyzer.analyze_keywords(df)

# 查看结果
print(result_df[['query', 'intent', 'intent_confidence', 'intent_description']])
```

## SERP分析的优势

### 1. 更高的准确性
- 基于真实搜索结果页面特征
- 考虑Google的意图判断
- 结合关键词文本和SERP特征

### 2. 丰富的特征信息
- 广告数量
- 特色片段
- People Also Ask
- 购物结果
- 视频结果
- 竞争对手URL

### 3. 智能回退机制
- SERP分析失败时自动使用关键词分析
- 双重验证提高可靠性

## 使用限制

### API配额限制
- 免费配额：每天100次查询
- 付费升级：超出后每1000次查询$5

### 性能考虑
- 每次查询有1秒延迟（可配置）
- 大批量分析需要较长时间
- 建议分批处理大量关键词

### 缓存机制
- 自动缓存搜索结果（1小时有效期）
- 避免重复查询相同关键词
- 缓存文件保存在 `data/serp_cache/`

## 故障排除

### 常见问题

1. **API密钥错误**
   ```
   错误: 401 Unauthorized
   解决: 检查config/.env中的GOOGLE_API_KEY是否正确
   ```

2. **搜索引擎ID错误**
   ```
   错误: 400 Bad Request
   解决: 检查GOOGLE_CSE_ID是否正确配置
   ```

3. **配额超限**
   ```
   错误: 429 Too Many Requests
   解决: 等待配额重置或升级到付费计划
   ```

4. **导入错误**
   ```
   错误: ModuleNotFoundError
   解决: 确保python-dotenv已安装，运行 pip3 install python-dotenv
   ```

### 调试模式

在代码中添加调试信息：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

analyzer = IntentAnalyzer(use_serp=True)
```

## 最佳实践

1. **小批量测试**: 先用少量关键词测试配置
2. **监控配额**: 定期检查API使用量
3. **缓存利用**: 重复分析时利用缓存节省配额
4. **错误处理**: 实现适当的错误处理和重试机制
5. **结果验证**: 人工验证部分结果确保准确性

## 下一步计划

- [ ] 添加更多SERP特征检测
- [ ] 实现批量分析进度条
- [ ] 添加结果可视化功能
- [ ] 集成其他搜索引擎API
- [ ] 优化意图判断规则

---

*更新日期：2025年1月27日*
*版本：1.0*