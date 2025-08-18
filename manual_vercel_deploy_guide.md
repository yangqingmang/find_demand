# Vercel 手动部署指南

## 🚀 快速部署步骤

### 1. 安装 Vercel CLI
```bash
# 方法1：全局安装
npm install -g vercel

# 方法2：使用 npx（推荐）
npx vercel --version
```

### 2. 登录 Vercel
```bash
# 使用 CLI 登录
npx vercel login

# 或者设置 API Token
# 获取 Token: https://vercel.com/account/tokens
export VERCEL_TOKEN=your_token_here
```

### 3. 准备部署文件
确保 `generated_website` 目录包含以下文件：
- ✅ index.html
- ✅ styles.css
- ✅ script.js
- ✅ 其他静态资源

### 4. 创建 vercel.json 配置
在 `generated_website` 目录下创建 `vercel.json`：
```json
{
  "version": 2,
  "public": true,
  "cleanUrls": true,
  "trailingSlash": false,
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        }
      ]
    }
  ]
}
```

### 5. 执行部署
```bash
# 进入网站目录
cd generated_website

# 部署到生产环境
npx vercel --prod --yes --name find-demand-website

# 或者先部署到预览环境测试
npx vercel --yes --name find-demand-website
```

## 🔧 常见问题解决

### 问题1：CLI 未找到
```bash
# 检查 Node.js 是否安装
node --version
npm --version

# 安装 Vercel CLI
npm install -g vercel
```

### 问题2：认证失败
```bash
# 重新登录
npx vercel logout
npx vercel login

# 或使用 API Token
npx vercel --token your_token_here --prod
```

### 问题3：部署失败
```bash
# 查看详细日志
npx vercel --debug

# 清除缓存
npx vercel --force
```

## 📋 部署检查清单

- [ ] Node.js 已安装 (v14+)
- [ ] Vercel CLI 可用
- [ ] 已登录 Vercel 账户
- [ ] 网站文件完整
- [ ] vercel.json 配置正确
- [ ] 网络连接正常

## 🌐 部署后验证

1. **检查部署状态**
   ```bash
   npx vercel ls
   ```

2. **访问网站**
   - 部署成功后会显示 URL
   - 格式：`https://find-demand-website-xxx.vercel.app`

3. **设置自定义域名**（可选）
   ```bash
   npx vercel domains add your-domain.com find-demand-website
   ```

## 💡 优化建议

1. **使用环境变量**
   ```bash
   # 设置项目名称
   export VERCEL_PROJECT_NAME=find-demand-website
   
   # 设置组织ID（如果有团队）
   export VERCEL_ORG_ID=your_org_id
   ```

2. **自动化部署**
   - 连接 Git 仓库实现自动部署
   - 使用 GitHub Actions 集成

3. **性能优化**
   - 启用 CDN 缓存
   - 压缩静态资源
   - 使用 Vercel Analytics

## 🚨 故障排除

如果遇到问题，请检查：

1. **网络连接**：确保可以访问 vercel.com
2. **权限问题**：检查 API Token 权限
3. **文件大小**：单个文件不超过 100MB
4. **文件数量**：项目文件不超过 10,000 个

## 📞 获取帮助

- Vercel 官方文档：https://vercel.com/docs
- CLI 帮助：`npx vercel --help`
- 社区支持：https://github.com/vercel/vercel/discussions