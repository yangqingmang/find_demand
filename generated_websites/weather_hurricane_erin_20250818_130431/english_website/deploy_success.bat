@echo off
echo ========================================
echo Hurricane Website Vercel 部署脚本
echo ========================================
echo.

echo 1. 切换到项目目录...
cd /d "%~dp0"
echo 当前目录: %CD%

echo.
echo 2. 检查必要文件...
if not exist "index.html" (
    echo 错误: 找不到 index.html 文件
    pause
    exit /b 1
)

if not exist "vercel.json" (
    echo 错误: 找不到 vercel.json 配置文件
    pause
    exit /b 1
)

echo ✅ index.html 存在
echo ✅ vercel.json 存在

echo.
echo 3. 开始 Vercel 部署...
echo 注意: 请在交互提示中选择以下配置:
echo   - Scope: yangqingmangs-projects
echo   - Link to existing project: No (创建新项目)
echo   - Project name: 使用默认或输入新名称
echo.

vercel --prod

echo.
echo 4. 部署完成!
echo 请检查终端输出中的部署 URL
echo.
pause