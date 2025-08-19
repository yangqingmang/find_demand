# 🆓 免费SEO API申请指南

本指南将帮助您申请各种免费的SEO API密钥，用于关键词研究和网站分析。

## 📋 申请清单

### ✅ 必申请（完全免费）

#### 1. Google Search Console API ⭐⭐⭐⭐⭐
**功能**：获取网站搜索性能数据、关键词排名、点击率等
**免费额度**：完全免费，无限制
**申请步骤**：
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 "Google Search Console API"
4. 创建服务账号并下载JSON密钥文件
5. 在Search Console中添加服务账号为用户

```bash
# 设置环境变量
export GOOGLE_CREDENTIALS_JSON="/path/to/your/credentials.json"
```

#### 2. Google Trends API ⭐⭐⭐⭐⭐
**功能**：关键词趋势分析、热门搜索话题
**免费额度**：每天1000次请求
**申请步骤**：
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 启用 "Google Trends API"
3. 创建API密钥

```bash
# 设置环境变量
export GOOGLE_API_KEY="your_google_api_key"
```

#### 3. Bing Webmaster Tools API ⭐⭐⭐⭐
**功能**：Bing搜索数据、关键词性能
**免费额度**：完全免费
**申请步骤**：
1. 访问 [Bing Webmaster Tools](https://www.bing.com/webmasters)
2. 注册并验证网站
3. 在设置中生成API密钥

```bash
# 设置环境变量
export BING_WEBMASTER_API_KEY="your_bing_api_key"
```

### 🔄 推荐申请（有限免费额度）

#### 4. SerpApi ⭐⭐⭐
**功能**：Google SERP数据抓取
**免费额度**：每月100次搜索
**申请步骤**：
1. 访问 [SerpApi](https://serpapi.com/)
2. 注册账号
3. 获取API密钥

```bash
# 设置环境变量
export SERPAPI_KEY="your_serpapi_key"
```

#### 5. DataForSEO ⭐⭐⭐
**功能**：SERP数据、关键词分析
**免费额度**：$1信用额度（约20-50次请求）
**申请步骤**：
1. 访问 [DataForSEO](https://dataforseo.com/)
2. 注册账号
3. 获取登录凭据

```bash
# 设置环境变量
export DATAFORSEO_LOGIN="your_login"
export DATAFORSEO_PASSWORD="your_password"
```

## 🚀 快速配置脚本

创建 `.env` 文件并添加以下内容：

```bash
# 完全免费的API
GOOGLE_CREDENTIALS_JSON="/path/to/your/google-credentials.json"
GOOGLE_API_KEY="your_google_api_key"
BING_WEBMASTER_API_KEY="your_bing_api_key"

# 有限免费额度的API
SERPAPI_KEY="your_serpapi_key"
DATAFORSEO_LOGIN="your_dataforseo_login"
DATAFORSEO_PASSWORD="your_dataforseo_password"

# 付费API（可选）
SEMRUSH_API_KEY=""
AHREFS_API_KEY=""
SIMILARWEB_API_KEY=""
```

## 📊 免费工具功能对比

| 工具 | 关键词研究 | SERP分析 | 竞争分析 | 流量分析 | 免费额度 |
|------|------------|----------|----------|----------|----------|
| Google Search Console | ✅ | ✅ | ❌ | ✅ | 无限制 |
| Google Trends | ✅ | ❌ | ❌ | ❌ | 1000次/天 |
| Bing Webmaster | ✅ | ✅ | ❌ | ✅ | 无限制 |
| SerpApi | ❌ | ✅ | ✅ | ❌ | 100次/月 |
| DataForSEO | ✅ | ✅ | ✅ | ❌ | $1额度 |

## 💡 使用建议

### 🎯 **最佳免费组合**
1. **Google Search Console** - 主要数据源
2. **Google Trends** - 趋势分析
3. **Bing Webmaster** - 补充数据
4. **SerpApi** - SERP分析（节约使用）

### 📈 **使用策略**
- 优先使用无限制的免费API
- 合理分配有限额度的API调用
- 设置缓存减少重复请求
- 使用模拟数据进行开发测试

## 🔧 测试配置

配置完成后，运行以下命令测试：

```bash
cd /path/to/your/project
python -c "
from src.collectors.seo_tools_collector import IntegratedSEOCollector
collector = IntegratedSEOCollector()
result = collector.get_comprehensive_keyword_data('AI tools')
print('✅ 配置成功!' if result else '❌ 配置失败')
"
```

## 📞 获取帮助

如果在申请过程中遇到问题：
1. 查看各平台的官方文档
2. 检查API密钥格式是否正确
3. 确认环境变量设置正确
4. 验证网络连接和防火墙设置

## 🔄 定期维护

- 监控API使用量，避免超出限制
- 定期更新API密钥
- 关注各平台政策变化
- 备份重要的配置文件

---

**注意**：免费API通常有使用限制，建议合理规划使用频率，避免超出配额。对于商业项目，建议考虑升级到付费版本以获得更好的服务。