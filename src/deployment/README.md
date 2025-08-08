# 网站一键部署工具

这是一个支持多种云服务器的网站一键部署工具，目前支持 Cloudflare Pages 和 Vercel，并且可以方便地扩展支持更多服务。

## 功能特性

- 🚀 **多平台支持**: 支持 Cloudflare Pages 和 Vercel
- 🔧 **配置化管理**: 通过配置文件管理多个部署服务
- 📦 **自动文件处理**: 自动处理和优化部署文件
- 🌐 **自定义域名**: 支持设置自定义域名
- 📊 **部署历史**: 记录和查看部署历史
- 🔍 **状态监控**: 实时监控部署状态
- 🛠️ **易于扩展**: 基于插件架构，易于添加新的部署服务

## 支持的部署服务

### Cloudflare Pages
- ✅ 静态网站托管
- ✅ 自定义域名
- ✅ HTTPS 支持
- ✅ CDN 加速
- ✅ Edge Functions
- ✅ 分析统计
- ✅ 预览部署
- ✅ Git 集成

### Vercel
- ✅ 静态网站托管
- ✅ 自定义域名
- ✅ HTTPS 支持
- ✅ CDN 加速
- ✅ Serverless Functions
- ✅ Edge Functions
- ✅ 分析统计
- ✅ 预览部署
- ✅ Git 集成
- ✅ 自动 HTTPS

## 安装和配置

### 1. 生成配置文件模板

```bash
python -m src.deployment.cli config template deployment_config.json
```

### 2. 编辑配置文件

编辑生成的 `deployment_config.json` 文件，填入您的 API 密钥和项目信息：

```json
{
  "default_deployer": "vercel",
  "deployers": {
    "cloudflare": {
      "api_token": "your_cloudflare_api_token",
      "account_id": "your_cloudflare_account_id",
      "project_name": "my-website",
      "custom_domain": "example.com"
    },
    "vercel": {
      "api_token": "your_vercel_api_token",
      "team_id": "your_team_id_optional",
      "project_name": "my-website",
      "custom_domain": "example.com"
    }
  },
  "deployment_settings": {
    "auto_cleanup": true,
    "max_retries": 3,
    "timeout": 300
  }
}
```

### 3. 获取 API 密钥

#### Cloudflare Pages
1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 进入 "My Profile" > "API Tokens"
3. 创建自定义令牌，权限包括：
   - Zone:Zone:Read
   - Account:Cloudflare Pages:Edit

#### Vercel
1. 登录 [Vercel Dashboard](https://vercel.com/dashboard)
2. 进入 "Settings" > "Tokens"
3. 创建新的 API Token

### 4. 验证配置

```bash
python -m src.deployment.cli config validate --config deployment_config.json
```

## 使用方法

### 基本部署

```bash
# 使用默认部署服务
python -m src.deployment.cli deploy /path/to/your/website --config deployment_config.json

# 指定部署服务
python -m src.deployment.cli deploy /path/to/your/website --deployer vercel --config deployment_config.json

# 指定项目名称和自定义域名
python -m src.deployment.cli deploy /path/to/your/website \
  --deployer cloudflare \
  --project-name my-awesome-site \
  --custom-domain mysite.com \
  --config deployment_config.json
```

### 查看支持的部署服务

```bash
python -m src.deployment.cli list
```

### 查看部署历史

```bash
# 查看所有部署历史
python -m src.deployment.cli history --config deployment_config.json

# 查看特定服务的部署历史
python -m src.deployment.cli history --deployer vercel --config deployment_config.json

# 查看部署统计信息
python -m src.deployment.cli history --stats --config deployment_config.json
```

## 编程接口

### 基本使用

```python
from src.deployment.deployment_manager import DeploymentManager

# 初始化部署管理器
manager = DeploymentManager('deployment_config.json')

# 部署网站
success, url, info = manager.deploy_website(
    source_dir='/path/to/website',
    deployer_name='vercel',
    custom_config={
        'project_name': 'my-site',
        'custom_domain': 'mysite.com'
    }
)

if success:
    print(f"部署成功！访问地址: {url}")
else:
    print(f"部署失败: {url}")
```

### 高级使用

```python
# 验证配置
is_valid, error = manager.validate_deployer_config('cloudflare')

# 获取部署历史
history = manager.get_deployment_history()

# 获取统计信息
stats = manager.get_deployment_stats()

# 更新配置
manager.update_deployer_config('vercel', {
    'api_token': 'new_token',
    'project_name': 'new_project'
})
manager.save_config()
```

## 扩展新的部署服务

### 1. 创建新的部署器类

```python
from src.deployment.base_deployer import BaseDeployer

class NewServiceDeployer(BaseDeployer):
    def validate_config(self):
        # 验证配置
        pass
    
    def prepare_files(self, source_dir, temp_dir):
        # 准备文件
        pass
    
    def deploy(self, temp_dir):
        # 执行部署
        pass
    
    def get_deployment_status(self):
        # 获取部署状态
        pass
```

### 2. 注册新的部署器

在 `deployment_manager.py` 中添加：

```python
from .new_service_deployer import NewServiceDeployer

class DeploymentManager:
    SUPPORTED_DEPLOYERS = {
        'cloudflare': CloudflareDeployer,
        'vercel': VercelDeployer,
        'new_service': NewServiceDeployer,  # 添加新服务
    }
```

## 与建站脚本集成

### 在建站脚本中添加部署功能

```python
from src.deployment.deployment_manager import DeploymentManager

class IntentBasedWebsiteBuilder:
    def __init__(self, ...):
        # 现有初始化代码
        self.deployment_manager = DeploymentManager()
    
    def deploy_website(self, deployer_name='vercel', custom_config=None):
        """部署生成的网站"""
        # 确保网站已生成
        if not self.website_structure:
            print("请先生成网站结构")
            return False
        
        # 生成HTML文件（这里需要实现HTML生成逻辑）
        html_output_dir = self.generate_html_files()
        
        # 部署网站
        success, url, info = self.deployment_manager.deploy_website(
            source_dir=html_output_dir,
            deployer_name=deployer_name,
            custom_config=custom_config
        )
        
        if success:
            print(f"网站部署成功！访问地址: {url}")
            return True
        else:
            print(f"网站部署失败: {url}")
            return False
```

### 命令行集成

```bash
# 生成网站并部署
python -m src.website_builder.intent_based_website_builder \
  --input keywords.csv \
  --output website_output \
  --deploy \
  --deployer vercel \
  --deployment-config deployment_config.json
```

## 故障排除

### 常见问题

1. **API Token 无效**
   - 检查 Token 是否正确
   - 确认 Token 权限是否足够
   - 验证 Account ID 是否正确

2. **文件上传失败**
   - 检查文件大小是否超过限制
   - 确认网络连接是否正常
   - 查看部署日志获取详细错误信息

3. **自定义域名设置失败**
   - 确认域名 DNS 设置是否正确
   - 检查域名是否已被其他项目使用
   - 等待 DNS 传播完成

### 调试模式

设置环境变量启用详细日志：

```bash
export DEPLOYMENT_DEBUG=1
python -m src.deployment.cli deploy /path/to/website --config config.json
```

## 贡献指南

欢迎贡献新的部署服务支持！请遵循以下步骤：

1. Fork 项目
2. 创建新的部署器类，继承 `BaseDeployer`
3. 实现所有抽象方法
4. 添加相应的测试
5. 更新文档
6. 提交 Pull Request

## 许可证

MIT License