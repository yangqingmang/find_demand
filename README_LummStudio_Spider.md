# LummStudio SEO小课堂爬虫

这是一个专门用于爬取 [路漫漫 LummStudio](https://www.lummstudio.com/docs/seo/miniclass) 网站上"哥飞小课堂"SEO文章的爬虫工具。

## 功能特点

- ✅ **完整爬取**: 自动爬取所有SEO小课堂文章
- ✅ **多格式输出**: 支持JSON、Markdown、HTML三种格式
- ✅ **单页保存**: 每篇文章保存为独立的HTML文件
- ✅ **离线阅读**: 生成的HTML文件包含完整样式，支持离线浏览
- ✅ **智能解析**: 自动提取文章标题、日期、内容等信息
- ✅ **友好界面**: 包含搜索功能的索引页面

## 项目结构

```
find_demand/
├── src/spider/
│   ├── lummstudio_spider.py      # 主爬虫程序
│   ├── html_pages/               # 生成的HTML文件目录
│   │   ├── index.html           # 文章索引页面
│   │   └── *.html               # 各篇文章的HTML文件
│   └── markdown/                 # Markdown格式文件
├── data/                         # JSON数据文件
├── run_lummstudio_spider.py      # 运行脚本
└── README_LummStudio_Spider.md   # 说明文档
```

## 使用方法

### 1. 安装依赖

```bash
pip install requests beautifulsoup4
```

### 2. 运行爬虫

```bash
python run_lummstudio_spider.py
```

### 3. 查看结果

爬取完成后，您将获得：

- **JSON文件**: `data/lummstudio_data_YYYYMMDD_HHMMSS.json`
- **Markdown文件**: `src/spider/markdown/lummstudio_articles_YYYYMMDD_HHMMSS.md`
- **HTML文件**: `src/spider/html_pages/` 目录下的各个HTML文件
- **索引页面**: `src/spider/html_pages/index.html`

## 爬取结果

### 最新爬取统计 (2025-09-03)

- 📊 **总文章数**: 51篇
- 🗓️ **时间范围**: 2024年1月 - 2024年9月
- 📁 **文件格式**: HTML、JSON、Markdown
- 🌐 **离线可读**: 是

### 文章主题涵盖

- 关键词研究与分析
- SEO技术优化
- 内容策略制定
- 流量获取方法
- 网站结构优化
- 工具使用技巧
- 案例分析分享

## 文件命名规则

- **HTML文件**: `YYYYMMDD_文章标题.html`
- **索引文件**: `index.html`
- **数据文件**: `lummstudio_data_YYYYMMDD_HHMMSS.json`
- **Markdown**: `lummstudio_articles_YYYYMMDD_HHMMSS.md`

## 特色功能

### 1. 智能内容提取
- 自动识别文章标题、发布日期
- 提取完整的文章内容
- 保留原始格式和图片链接

### 2. 美观的HTML输出
- 响应式设计，支持移动端
- 专业的排版样式
- 包含文章元信息（原链接、爬取时间等）

### 3. 便捷的索引页面
- 网格布局展示所有文章
- 实时搜索功能
- 统计信息展示

### 4. 多格式支持
- **JSON**: 结构化数据，便于程序处理
- **Markdown**: 纯文本格式，便于编辑
- **HTML**: 完整样式，便于阅读

## 技术实现

### 核心技术栈
- **Python 3.x**
- **Requests**: HTTP请求处理
- **BeautifulSoup4**: HTML解析
- **正则表达式**: 文本处理

### 关键特性
- 智能重试机制
- 请求频率控制
- 错误处理和日志
- 文件安全命名

## 使用示例

### 基本使用
```python
from src.spider.lummstudio_spider import LummStudioSpider

spider = LummStudioSpider()
result = spider.crawl()

print(f"爬取完成！共获取 {result['total_articles']} 篇文章")
```

### 自定义配置
```python
spider = LummStudioSpider()
spider.session.headers.update({
    'User-Agent': 'Your Custom User Agent'
})
result = spider.crawl()
```

## 注意事项

1. **网络连接**: 确保网络连接稳定
2. **访问频率**: 程序已内置延迟，避免过于频繁的请求
3. **存储空间**: 51篇文章大约需要几MB存储空间
4. **更新频率**: 建议定期运行以获取最新文章

## 版权声明

- 本工具仅用于学习和研究目的
- 所有文章内容版权归原作者所有
- 原始网站: [路漫漫 - LummStudio](https://www.lummstudio.com)
- 文章作者: 哥飞

## 更新日志

### v1.0.0 (2025-09-03)
- ✅ 初始版本发布
- ✅ 支持完整文章爬取
- ✅ 多格式输出功能
- ✅ 美观的HTML界面
- ✅ 搜索和索引功能

## 联系方式

如有问题或建议，请通过以下方式联系：
- 项目地址: 本地项目
- 技术支持: CodeBuddy AI Assistant

---

**Happy Learning! 📚✨**