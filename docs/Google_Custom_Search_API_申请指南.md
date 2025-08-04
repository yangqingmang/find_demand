# Google Custom Search API 申请指南

本文档详细介绍如何申请和配置 Google Custom Search API，用于 SERP 分析工具的开发。

## 1. 创建 Google Cloud 项目

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 登录你的 Google 账号
3. 点击"选择项目" → "新建项目"
4. 输入项目名称（如："SERP分析工具"）
5. 点击"创建"

## 2. 启用 Custom Search API

1. 在项目控制台中，点击左侧菜单"API和服务" → "库"
2. 搜索 "Custom Search API"
3. 点击进入，然后点击"启用"

## 3. 创建 API 凭据

1. 点击"API和服务" → "凭据"
2. 点击"创建凭据" → "API密钥"
3. 复制生成的 API 密钥并保存好
4. （可选）点击"限制密钥"设置使用限制

## 4. 创建自定义搜索引擎

1. 访问 [Google Custom Search Engine](https://cse.google.com/cse/)
2. 点击"添加"创建新的搜索引擎
3. 在"要搜索的网站"中输入 `www.google.com`
4. 给搜索引擎起个名字
5. 点击"创建"

## 5. 配置搜索引擎

1. 在搜索引擎设置页面，点击"设置"
2. 在"基本信息"中找到"搜索引擎ID"并复制保存
3. 在"搜索功能"中：
   - 启用"图片搜索"
   - 启用"安全搜索"
4. 在"高级"选项中，选择"搜索整个网络"

## 6. 测试 API

使用以下 Python 代码测试：

```python
import requests

API_KEY = "你的API密钥"
CSE_ID = "你的搜索引擎ID"
query = "Python教程"

url = f"https://www.googleapis.com/customsearch/v1"
params = {
    'key': API_KEY,
    'cx': CSE_ID,
    'q': query,
    'num': 10
}

response = requests.get(url, params=params)
print(response.json())
```

## 7. 使用限制

- **免费配额**：每天100次查询
- **付费升级**：超出后每1000次查询收费$5
- **查询限制**：每秒最多10次查询

## 8. 注意事项

1. **保护API密钥**：不要在代码中硬编码，使用环境变量
2. **监控使用量**：在Google Cloud Console中查看API使用情况
3. **错误处理**：实现重试机制和错误处理
4. **缓存结果**：避免重复查询相同关键词

## 环境变量配置

创建 `.env` 文件：
```bash
GOOGLE_API_KEY=你的API密钥
GOOGLE_CSE_ID=你的搜索引擎ID
```

## SERP 分析工具实现准备

### 技术准备

#### 新增依赖包
```python
beautifulsoup4  # HTML解析
selenium        # 浏览器自动化
requests-html   # 渲染JavaScript页面
lxml           # XML/HTML解析器
```

#### 核心功能设计
```python
class SerpAnalyzer:
    def extract_serp_features(self, keyword):
        """提取SERP页面特征"""
        return {
            'ads_count': 0,           # 广告数量
            'organic_count': 0,       # 自然结果数量
            'has_paa': False,         # 是否有PAA问题
            'has_featured_snippet': False,  # 特色片段
            'has_shopping': False,    # 购物结果
            'has_video': False,       # 视频结果
            'has_images': False,      # 图片结果
            'has_local': False,       # 本地结果
            'competitor_urls': [],    # 竞争对手URL
            'title_keywords': []      # 标题关键词
        }
```

### 实现步骤

#### 第一阶段：基础框架
1. 创建 `serp_analyzer.py` 文件
2. 实现基本的搜索结果获取
3. 解析HTML结构，提取基础特征

#### 第二阶段：特征提取
1. 识别不同类型的搜索结果元素
2. 统计各类结果的数量
3. 提取竞争对手URL和标题

#### 第三阶段：意图增强
1. 将SERP特征集成到现有的意图分析器
2. 调整置信度计算算法
3. 添加基于SERP的意图判断规则

### 数据获取方案

#### 方案A：Google Custom Search API（推荐）
- 官方API，稳定可靠
- 每天免费100次查询
- 需要申请API密钥

#### 方案B：第三方SERP API
- SerpApi、DataForSEO等
- 功能更丰富，但需付费
- 返回结构化数据

#### 方案C：网页抓取
- 使用Selenium模拟浏览器
- 免费但不稳定
- 需要处理反爬虫机制

### 测试数据准备

准备一批测试关键词，涵盖不同意图类型：
- 信息型：`"如何学习Python"`
- 交易型：`"购买iPhone 15"`
- 导航型：`"淘宝登录"`
- 商业型：`"最佳笔记本电脑对比"`

### 意图判断增强规则

基于SERP特征的规则：
- **广告多 + 购物结果** → 交易意图 (E)
- **PAA + 特色片段** → 信息意图 (I)  
- **视频结果多** → 学习意图 (I)
- **本地结果** → 导航意图 (N)

---

*创建日期：2025年1月27日*
*用途：SERP分析工具开发准备*