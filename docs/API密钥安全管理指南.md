# API密钥安全管理指南

本指南介绍如何安全地管理 Google Custom Search API 密钥，避免在版本控制中泄露敏感信息。

## 问题说明

当你使用 Git 管理代码时，如果直接将包含API密钥的 `.env` 文件提交到仓库，会导致：
- ✗ API密钥泄露给所有能访问仓库的人
- ✗ 安全风险，他人可能滥用你的API配额
- ✗ 违反最佳安全实践

## 解决方案

我们提供了多种安全的配置管理方案：

### 方案1：本地配置 + .gitignore（推荐用于个人开发）

**优点：**
- 简单易用
- 适合单机开发
- 配置文件在项目目录中

**设置步骤：**
1. 运行配置工具：`python setup_config.py`
2. 选择"本地配置"
3. 输入API密钥
4. `.gitignore` 会自动忽略 `.env` 文件

**文件结构：**
```
project/
├── config/
│   ├── .env          # 包含真实密钥（被git忽略）
│   └── .env.template # 模板文件（提交到git）
└── .gitignore        # 忽略敏感文件
```

### 方案2：用户级配置（推荐用于多项目）

**优点：**
- 多个项目共享配置
- 配置文件在用户主目录
- 更安全的文件权限

**设置步骤：**
1. 运行配置工具：`python setup_config.py`
2. 选择"用户级配置"
3. 配置保存在 `~/.find_demand/.env`

**配置位置：**
- macOS/Linux: `~/.find_demand/.env`
- Windows: `C:\Users\用户名\.find_demand\.env`

### 方案3：系统环境变量（推荐用于生产环境）

**优点：**
- 最安全的方式
- 适合生产环境
- 不依赖文件系统

**设置步骤：**

**macOS/Linux:**
```bash
# 临时设置（当前会话有效）
export GOOGLE_API_KEY="your_api_key"
export GOOGLE_CSE_ID="your_cse_id"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export GOOGLE_API_KEY="your_api_key"' >> ~/.zshrc
echo 'export GOOGLE_CSE_ID="your_cse_id"' >> ~/.zshrc
source ~/.zshrc
```

**Windows PowerShell:**
```powershell
# 临时设置
$env:GOOGLE_API_KEY="your_api_key"
$env:GOOGLE_CSE_ID="your_cse_id"

# 永久设置（系统级）
[Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "your_api_key", "User")
[Environment]::SetEnvironmentVariable("GOOGLE_CSE_ID", "your_cse_id", "User")
```

## 团队协作最佳实践

### 1. 配置文件管理
```
# 提交到版本控制
config/.env.template    ✓ 提交（模板文件）
.gitignore             ✓ 提交（忽略规则）
docs/配置说明.md        ✓ 提交（说明文档）

# 不提交到版本控制
config/.env            ✗ 不提交（包含真实密钥）
.env                   ✗ 不提交（任何环境变量文件）
```

### 2. 团队成员配置流程
1. 克隆仓库后，运行 `python setup_config.py`
2. 选择适合的配置方式
3. 输入自己的API密钥
4. 运行 `python test_serp_config.py` 验证配置

### 3. 不同环境的配置策略

**开发环境：**
- 使用本地配置或用户级配置
- 每个开发者使用自己的API密钥

**测试环境：**
- 使用环境变量
- 使用专门的测试API密钥

**生产环境：**
- 必须使用环境变量
- 使用生产专用API密钥
- 设置适当的访问权限

## 安全检查清单

### 提交代码前检查：
- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 没有在代码中硬编码API密钥
- [ ] 提交的是 `.env.template` 而不是 `.env`
- [ ] 运行 `git status` 确认没有敏感文件被跟踪

### 定期安全维护：
- [ ] 定期轮换API密钥
- [ ] 监控API使用量
- [ ] 检查访问日志
- [ ] 更新团队成员的访问权限

## 故障排除

### 常见问题

**1. 配置文件找不到**
```
错误：未找到 .env 配置文件
解决：运行 python setup_config.py 重新配置
```

**2. API密钥无效**
```
错误：401 Unauthorized
解决：检查API密钥是否正确，是否已启用Custom Search API
```

**3. 环境变量未生效**
```
错误：缺少必要的配置项
解决：重启终端或重新加载环境变量
```

### 配置优先级

系统按以下优先级加载配置：
1. 系统环境变量（最高优先级）
2. 项目目录 `config/.env`
3. 用户目录 `~/.find_demand/.env`
4. 默认值（最低优先级）

## 快速开始

如果你是新用户，推荐按以下步骤开始：

1. **运行配置工具**
   ```bash
   python setup_config.py
   ```

2. **选择配置方式**
   - 个人开发：选择"本地配置"
   - 多项目：选择"用户级配置"
   - 生产环境：选择"系统环境变量"

3. **测试配置**
   ```bash
   python test_serp_config.py
   ```

4. **开始使用**
   ```bash
   python src/analyzers/intent_analyzer.py --input data/keywords.csv --use-serp
   ```

## 相关文档

- [Google Custom Search API 申请指南](./Google_Custom_Search_API_申请指南.md)
- [SERP分析工具使用指南](./SERP分析工具使用指南.md)
- [开发计划](./开发计划.md)

---

*更新日期：2025年1月27日*
*版本：1.0*