#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置初始化脚本
帮助用户安全地设置API密钥和配置
"""

import os
import shutil
import getpass
from pathlib import Path

def create_user_config_dir():
    """创建用户配置目录"""
    config_dir = Path.home() / '.find_demand'
    config_dir.mkdir(exist_ok=True)
    return config_dir

def setup_local_config():
    """设置本地配置（推荐用于开发）"""
    print("=== 本地配置设置 ===")
    print("这种方式将配置保存在项目目录中，适合单机开发")
    print("注意：请确保 .gitignore 已正确配置，避免提交敏感信息")
    
    # 检查是否存在 .env 文件
    env_file = Path('config/.env')
    template_file = Path('config/.env.template')
    
    if env_file.exists():
        overwrite = input(f"\n配置文件 {env_file} 已存在，是否覆盖？(y/N): ").lower()
        if overwrite != 'y':
            print("取消配置")
            return
    
    if not template_file.exists():
        print(f"错误：模板文件 {template_file} 不存在")
        return
    
    # 复制模板文件
    shutil.copy(template_file, env_file)
    
    # 获取用户输入
    print("\n请输入API配置信息：")
    
    google_api_key = getpass.getpass("Google API Key: ").strip()
    google_cse_id = input("Google CSE ID: ").strip()
    
    if not google_api_key or not google_cse_id:
        print("错误：API密钥和搜索引擎ID不能为空")
        return
    
    # 更新配置文件
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace('your_google_api_key_here', google_api_key)
    content = content.replace('your_custom_search_engine_id_here', google_cse_id)
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✓ 配置已保存到 {env_file}")
    print("✓ 本地配置设置完成")

def setup_user_config():
    """设置用户级配置（推荐用于多项目共享）"""
    print("=== 用户级配置设置 ===")
    print("这种方式将配置保存在用户主目录中，可在多个项目间共享")
    print("配置文件位置：~/.find_demand/.env")
    
    config_dir = create_user_config_dir()
    env_file = config_dir / '.env'
    
    if env_file.exists():
        overwrite = input(f"\n配置文件 {env_file} 已存在，是否覆盖？(y/N): ").lower()
        if overwrite != 'y':
            print("取消配置")
            return
    
    # 获取用户输入
    print("\n请输入API配置信息：")
    
    google_api_key = getpass.getpass("Google API Key: ").strip()
    google_cse_id = input("Google CSE ID: ").strip()
    
    if not google_api_key or not google_cse_id:
        print("错误：API密钥和搜索引擎ID不能为空")
        return
    
    # 创建配置内容
    config_content = f"""# Google Custom Search API 配置
GOOGLE_API_KEY={google_api_key}
GOOGLE_CSE_ID={google_cse_id}

# SERP 分析配置
SERP_CACHE_ENABLED=true
SERP_CACHE_DURATION=3600
SERP_REQUEST_DELAY=1
SERP_MAX_RETRIES=3
"""
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    # 设置文件权限（仅用户可读写）
    os.chmod(env_file, 0o600)
    
    print(f"\n✓ 配置已保存到 {env_file}")
    print("✓ 文件权限已设置为仅用户可访问")
    print("✓ 用户级配置设置完成")

def setup_env_variables():
    """设置系统环境变量（推荐用于生产环境）"""
    print("=== 系统环境变量设置 ===")
    print("这种方式使用系统环境变量，最安全但需要手动设置")
    
    print("\n请在系统中设置以下环境变量：")
    
    google_api_key = getpass.getpass("Google API Key: ").strip()
    google_cse_id = input("Google CSE ID: ").strip()
    
    if not google_api_key or not google_cse_id:
        print("错误：API密钥和搜索引擎ID不能为空")
        return
    
    print("\n=== 环境变量设置命令 ===")
    print("\n对于 macOS/Linux (bash/zsh):")
    print(f'export GOOGLE_API_KEY="{google_api_key}"')
    print(f'export GOOGLE_CSE_ID="{google_cse_id}"')
    print("\n将以上命令添加到 ~/.bashrc 或 ~/.zshrc 文件中")
    
    print("\n对于 Windows (PowerShell):")
    print(f'$env:GOOGLE_API_KEY="{google_api_key}"')
    print(f'$env:GOOGLE_CSE_ID="{google_cse_id}"')
    print("\n或使用系统设置中的环境变量配置")
    
    print("\n✓ 环境变量信息已显示，请手动设置")

def test_configuration():
    """测试配置是否正确"""
    print("\n=== 测试配置 ===")
    
    try:
        import sys
        sys.path.append('src')
        
        from src.config.settings import config
        
        config.show_config_status()
        
        # 验证配置
        config.validate()
        print("\n✓ 配置验证通过")
        
        # 测试API连接
        print("\n正在测试API连接...")
        from src.analyzers.serp_analyzer import SerpAnalyzer
        
        analyzer = SerpAnalyzer()
        result = analyzer.search_google("测试", num_results=1)
        
        if result and 'items' in result:
            print("✓ API连接测试成功")
            return True
        else:
            print("✗ API连接测试失败")
            return False
            
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False

def main():
    """主函数"""
    print("欢迎使用 Find Demand 配置工具！")
    print("此工具将帮助您安全地配置API密钥")
    
    while True:
        print("\n=== 配置选项 ===")
        print("1. 本地配置 (推荐用于开发)")
        print("2. 用户级配置 (推荐用于多项目)")
        print("3. 系统环境变量 (推荐用于生产)")
        print("4. 测试当前配置")
        print("5. 退出")
        
        choice = input("\n请选择配置方式 (1-5): ").strip()
        
        if choice == '1':
            setup_local_config()
        elif choice == '2':
            setup_user_config()
        elif choice == '3':
            setup_env_variables()
        elif choice == '4':
            test_configuration()
        elif choice == '5':
            print("退出配置工具")
            break
        else:
            print("无效选择，请重试")
    
    print("\n=== 安全提醒 ===")
    print("1. 不要将API密钥提交到版本控制系统")
    print("2. 定期检查和轮换API密钥")
    print("3. 监控API使用量，避免超出配额")
    print("4. 在生产环境中使用环境变量")

if __name__ == "__main__":
    main()