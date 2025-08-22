# API配置待办事项清单

本文档列出了项目所需的所有API配置，包括申请地址、配置方法和加密说明。

## 📋 配置优先级

### 🔴 必需配置（立即申请）

#### ✅ 1. Google Custom Search API
- **用途**: SERP分析、搜索结果获取、竞争对手分析
- **免费额度**: 每天100次查询
- **申请地址**: 
  - Google Cloud Console: https://console.cloud.google.com/
  - Custom Search Engine: https://cse.google.com/cse/
- **详细申请指南**: [Google_Custom_Search_API_申请指南.md](./docs/Google_Custom_Search_API_申请指南.md)

**申请步骤**:
- [ ] 1. 访问 Google Cloud Console
- [ ] 2. 创建新项目或选择现有项目
- [ ] 3. 启用 Custom Search API
- [ ] 4. 创建 API 凭据（API密钥）
- [ ] 5. 创建自定义搜索引擎
- [ ] 6. 获取搜索引擎ID

**需要的配置项**:
```bash
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_custom_search_engine_id_here
```

**配置位置**:
- 方式1: `config/.env` 文件
- 方式2: 系统环境变量
- 方式3: `~/.find_demand/.env` 文件

**加密配置**:
```bash
# 使用加密配置工具
python setup_encryption.py
# 选择加密存储，密钥将自动加密保存到 config/.env.encrypted
```

---

#### ⭐ 2. Google Ads API
- **用途**: 获取精确的搜索量、竞争度、CPC数据
- **申请地址**: https://developers.google.com/google-ads/api/
- **详细申请指南**: [Google_Ads_API_集成指南.md](./docs/Google_Ads_API_集成指南.md)

**申请步骤**:
- [ ] 1. 申请 Google Ads 开发者令牌
- [ ] 2. 创建 OAuth2 客户端ID和密钥
- [ ] 3. 获取刷新令牌
- [ ] 4. 获取客户ID

**需要的配置项**:
```bash
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token_here
GOOGLE_ADS_CLIENT_ID=your_client_id_here
GOOGLE_ADS_CLIENT_SECRET=your_client_secret_here
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token_here
GOOGLE_ADS_CUSTOMER_ID=your_customer_id_here
GOOGLE_ADS_API_VERSION=v15
```

**配置位置**: 同上

**加密配置**: 同上（这些密钥会自动加密）

---

### 🟡 可选配置（根据需要申请）

#### 🚀 3. 网站部署API

##### Vercel API
- **用途**: 自动部署生成的网站到Vercel平台
- **申请地址**: https://vercel.com/account/tokens
- **免费额度**: 个人账户免费

**申请步骤**:
- [ ] 1. 登录 Vercel Dashboard
- [ ] 2. 进入 Settings > Tokens
- [ ] 3. 创建新的 API Token
- [ ] 4. 复制并保存令牌

**需要的配置项**:
```bash
VERCEL_API_TOKEN=your_vercel_token_here
VERCEL_TEAM_ID=your_team_id_here  # 可选，团队账户需要
```

**配置位置**: `deployment_config.json` 或环境变量

**配置示例**:
```json
{
  "deployers": {
    "vercel": {
      "api_token": "your_vercel_token_here",
      "team_id": "your_team_id_optional",
      "project_name": "my-website",
      "custom_domain": "example.com"
    }
  }
}
```

##### Cloudflare API
- **用途**: 自动部署生成的网站到Cloudflare Pages
- **申请地址**: https://dash.cloudflare.com/profile/api-tokens
- **免费额度**: 免费计划可用

**申请步骤**:
- [ ] 1. 登录 Cloudflare Dashboard
- [ ] 2. 进入 My Profile > API Tokens
- [ ] 3. 创建自定义令牌
- [ ] 4. 设置权限：Zone:Zone:Read, Account:Cloudflare Pages:Edit
- [ ] 5. 获取 Account ID（Dashboard右侧边栏）

**需要的配置项**:
```bash
CLOUDFLARE_API_TOKEN=your_cloudflare_token_here
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
```

**配置位置**: `deployment_config.json` 或环境变量

---

#### 📊 4. 第三方SERP API（可选）

##### SerpApi
- **用途**: 替代Google Custom Search API，获取更丰富的SERP数据
- **申请地址**: https://serpapi.com/
- **免费额度**: 每月100次查询

**申请步骤**:
- [ ] 1. 注册 SerpApi 账户
- [ ] 2. 获取 API Key
- [ ] 3. 选择合适的定价计划

**需要的配置项**:
```bash
SERP_API_KEY=your_serpapi_key_here
```

##### DataForSEO API
- **用途**: 专业的SEO数据API
- **申请地址**: https://dataforseo.com/
- **免费额度**: 有限的免费试用

**申请步骤**:
- [ ] 1. 注册 DataForSEO 账户
- [ ] 2. 获取 API 凭据
- [ ] 3. 选择合适的服务包

---

#### 🔍 5. Ahrefs API（高级功能）
- **用途**: 获取专业的SEO数据、关键词难度、竞争分析
- **申请地址**: https://ahrefs.com/api
- **费用**: 付费服务

**申请步骤**:
- [ ] 1. 拥有 Ahrefs 付费订阅
- [ ] 2. 申请 API 访问权限
- [ ] 3. 获取 API Token

**需要的配置项**:
```bash
AHREFS_API_KEY=your_ahrefs_token_here
```

---

#### 🔧 6. Google Trends API 真实地址解析
- **用途**: 通过浏览器开发者工具解析Google Trends的真实API调用地址和参数格式
- **优先级**: 中等
- **预计时间**: 2-3小时
- **状态**: 待完成

**任务步骤**:
- [ ] 1. 打开浏览器开发者工具（F12）
- [ ] 2. 访问 Google Trends 网站 (https://trends.google.com)
- [ ] 3. 在 Network 标签页中监控网络请求
- [ ] 4. 搜索关键词并观察相关查询的加载过程
- [ ] 5. 分析 API 请求的完整 URL 结构
- [ ] 6. 记录请求头、参数格式和响应结构
- [ ] 7. 测试不同关键词和地区的请求格式
- [ ] 8. 验证响应数据的解析方法
- [ ] 9. 更新代码中的 API 调用逻辑
- [ ] 10. 编写详细的 API 文档

**重点关注**:
- 请求 URL 的完整格式
- 必需的请求头和参数
- 响应数据的前缀处理（如 `)]}'` 字符）
- 不同类型数据的获取方式（相关查询、热门话题等）
- 频率限制和错误处理

**预期产出**:
- Google Trends API 完整调用文档
- 优化后的 trends_collector.py 代码
- API 测试脚本和示例

---

## 🛠️ 配置方法

### 方法1: 使用配置工具（推荐）

```bash
# 基础配置
python setup_config.py

# 加密配置
python setup_encryption.py

# 部署配置
python src/deployment/setup_deployment.py
```

### 方法2: 手动配置环境变量

**macOS/Linux**:
```bash
# 临时设置
export GOOGLE_API_KEY="your_api_key"
export GOOGLE_CSE_ID="your_cse_id"

# 永久设置（添加到 ~/.zshrc 或 ~/.bashrc）
echo 'export GOOGLE_API_KEY="your_api_key"' >> ~/.zshrc
echo 'export GOOGLE_CSE_ID="your_cse_id"' >> ~/.zshrc
source ~/.zshrc
```

**Windows PowerShell**:
```powershell
# 临时设置
$env:GOOGLE_API_KEY="your_api_key"
$env:GOOGLE_CSE_ID="your_cse_id"

# 永久设置
[Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "your_api_key", "User")
[Environment]::SetEnvironmentVariable("GOOGLE_CSE_ID", "your_cse_id", "User")
```

### 方法3: 创建配置文件

**创建 `config/.env` 文件**:
```bash
# Google APIs
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_custom_search_engine_id_here

# Google Ads API
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token_here
GOOGLE_ADS_CLIENT_ID=your_client_id_here
GOOGLE_ADS_CLIENT_SECRET=your_client_secret_here
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token_here
GOOGLE_ADS_CUSTOMER_ID=your_customer_id_here
GOOGLE_ADS_API_VERSION=v15

# SERP配置
SERP_CACHE_ENABLED=true
SERP_CACHE_DURATION=3600
SERP_REQUEST_DELAY=1
SERP_MAX_RETRIES=3

# 第三方APIs（可选）
SERP_API_KEY=your_serpapi_key_here
AHREFS_API_KEY=your_ahrefs_key_here

# 部署APIs（可选）
VERCEL_API_TOKEN=your_vercel_token_here
CLOUDFLARE_API_TOKEN=your_cloudflare_token_here
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
```

---

## 🔐 安全配置

### 加密存储（推荐）

1. **安装加密依赖**:
   ```bash
   python install_crypto_deps.py
   ```

2. **设置加密配置**:
   ```bash
   python setup_encryption.py
   ```

3. **加密现有配置**:
   ```bash
   python config/encrypt_config.py
   ```

### 配置文件安全

- ✅ `config/.env` 已在 `.gitignore` 中，不会提交到版本控制
- ✅ 加密配置存储在 `config/.env.encrypted`
- ✅ 公开配置存储在 `config/.env.public`
- ✅ 支持用户级配置 `~/.find_demand/.env`

### 权限设置

```bash
# 设置配置文件权限（仅所有者可读写）
chmod 600 config/.env
chmod 600 ~/.find_demand/.env
```

---

## ✅ 配置验证

### 测试配置

```bash
# 测试 Google APIs
python test_serp_config.py

# 测试 Google Ads API
python test_ads_integration.py

# 测试部署配置
python src/deployment/test_deployment.py

# 查看配置状态
python -c "from src.config.settings import config; config.show_status()"
```

---

## 📚 相关文档

- [API密钥安全管理指南](./docs/API密钥安全管理指南.md)
- [配置加密系统使用指南](./docs/配置加密系统使用指南.md)
- [Google Custom Search API 申请指南](./docs/Google_Custom_Search_API_申请指南.md)
- [Google Ads API 集成指南](./docs/Google_Ads_API_集成指南.md)
- [网站一键部署工具](./src/deployment/README.md)

---

## 🆘 故障排除

### 常见问题

**1. 配置文件找不到**
```
错误：未找到 .env 配置文件
解决：运行 python setup_config.py 重新配置
```

**2. API密钥无效**
```
错误：401 Unauthorized
解决：检查API密钥是否正确，是否已启用相应的API服务
```

**3. 环境变量未生效**
```
错误：缺少必要的配置项
解决：重启终端或重新加载环境变量
```

**4. 加密配置问题**
```
错误：解密失败
解决：检查加密密钥是否正确，重新运行 setup_encryption.py
```

### 配置优先级

系统按以下优先级加载配置：
1. 系统环境变量（最高优先级）
2. 项目目录 `config/.env`
3. 用户目录 `~/.find_demand/.env`
4. 加密配置 `config/.env.encrypted`
5. 默认值（最低优先级）

---

## 📝 配置完成检查清单

### 必需配置
- [ ] Google Custom Search API Key
- [ ] Google Custom Search Engine ID
- [ ] Google Ads API 完整配置（5个配置项）

### 可选配置
- [ ] Vercel API Token（如需自动部署）
- [ ] Cloudflare API Token（如需自动部署）
- [ ] SERP API Key（如需更丰富的SERP数据）
- [ ] Ahrefs API Key（如需专业SEO数据）

### 安全配置
- [ ] 配置文件权限设置
- [ ] 敏感信息加密存储
- [ ] .gitignore 配置正确

### 测试验证
- [ ] 运行配置测试脚本
- [ ] 验证API连接正常
- [ ] 确认功能正常工作

---

**完成时间预估**: 2-4小时（包括申请等待时间）

**更新日期**: 2025年1月27日
**版本**: 1.0