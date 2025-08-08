#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
部署配置设置向导
"""

import os
import sys
import json
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.deployment.deployment_manager import DeploymentManager


def main():
    """部署配置设置主函数"""
    print("🚀 网站部署配置向导")
    print("=" * 50)
    
    print("\n这个向导将帮助您设置网站部署配置")
    print("支持的部署服务: Cloudflare Pages, Vercel")
    
    # 1. 选择配置文件路径
    config_path = input("\n📁 请输入配置文件保存路径 (默认: deployment_config.json): ").strip()
    if not config_path:
        config_path = "deployment_config.json"
    
    # 2. 选择默认部署服务
    print("\n🌐 选择默认部署服务:")
    print("1. Vercel (推荐)")
    print("2. Cloudflare Pages")
    
    while True:
        choice = input("请选择 (1-2): ").strip()
        if choice == "1":
            default_deployer = "vercel"
            break
        elif choice == "2":
            default_deployer = "cloudflare"
            break
        else:
            print("❌ 无效选择，请输入 1 或 2")
    
    # 3. 配置部署服务
    config = {
        "default_deployer": default_deployer,
        "deployers": {},
        "deployment_settings": {
            "auto_cleanup": True,
            "max_retries": 3,
            "timeout": 300
        }
    }
    
    # 配置Vercel
    if setup_vercel():
        config["deployers"]["vercel"] = configure_vercel()
    
    # 配置Cloudflare
    if setup_cloudflare():
        config["deployers"]["cloudflare"] = configure_cloudflare()
    
    # 4. 保存配置
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 配置已保存到: {config_path}")
        
        # 5. 验证配置
        print("\n🔍 验证配置...")
        manager = DeploymentManager(config_path)
        
        for deployer_name in config["deployers"].keys():
            is_valid, error_msg = manager.validate_deployer_config(deployer_name)
            if is_valid:
                print(f"✅ {deployer_name}: 配置有效")
            else:
                print(f"⚠️ {deployer_name}: {error_msg}")
        
        # 6. 显示使用说明
        show_usage_instructions(config_path)
        
        return 0
        
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")
        return 1


def setup_vercel() -> bool:
    """询问是否配置Vercel"""
    print("\n" + "=" * 30)
    print("🔧 Vercel 配置")
    print("=" * 30)
    
    setup = input("是否配置 Vercel? (y/n): ").strip().lower()
    return setup in ['y', 'yes', '是']


def configure_vercel() -> Dict[str, Any]:
    """配置Vercel"""
    print("\n📋 请提供以下信息:")
    print("💡 获取API Token: https://vercel.com/account/tokens")
    
    api_token = input("Vercel API Token: ").strip()
    team_id = input("Team ID (可选，个人账户请留空): ").strip()
    project_name = input("默认项目名称: ").strip()
    custom_domain = input("自定义域名 (可选): ").strip()
    
    config = {
        "api_token": api_token,
        "project_name": project_name or "my-website"
    }
    
    if team_id:
        config["team_id"] = team_id
    
    if custom_domain:
        config["custom_domain"] = custom_domain
    
    return config


def setup_cloudflare() -> bool:
    """询问是否配置Cloudflare"""
    print("\n" + "=" * 30)
    print("🔧 Cloudflare Pages 配置")
    print("=" * 30)
    
    setup = input("是否配置 Cloudflare Pages? (y/n): ").strip().lower()
    return setup in ['y', 'yes', '是']


def configure_cloudflare() -> Dict[str, Any]:
    """配置Cloudflare"""
    print("\n📋 请提供以下信息:")
    print("💡 获取API Token: https://dash.cloudflare.com/profile/api-tokens")
    print("💡 获取Account ID: Cloudflare Dashboard 右侧边栏")
    
    api_token = input("Cloudflare API Token: ").strip()
    account_id = input("Account ID: ").strip()
    project_name = input("默认项目名称: ").strip()
    custom_domain = input("自定义域名 (可选): ").strip()
    
    config = {
        "api_token": api_token,
        "account_id": account_id,
        "project_name": project_name or "my-website"
    }
    
    if custom_domain:
        config["custom_domain"] = custom_domain
    
    return config


def show_usage_instructions(config_path: str):
    """显示使用说明"""
    print("\n" + "=" * 50)
    print("📖 使用说明")
    print("=" * 50)
    
    print(f"\n1. 建站并部署:")
    print(f"   python -m src.website_builder.intent_based_website_builder \\")
    print(f"     --input data/keywords.csv \\")
    print(f"     --output output/my_website \\")
    print(f"     --deploy \\")
    print(f"     --deployer vercel \\")
    print(f"     --deployment-config {config_path}")
    
    print(f"\n2. 单独部署:")
    print(f"   python -m src.deployment.cli deploy /path/to/website \\")
    print(f"     --deployer vercel \\")
    print(f"     --config {config_path}")
    
    print(f"\n3. 查看部署历史:")
    print(f"   python -m src.deployment.cli history --config {config_path}")
    
    print(f"\n4. 验证配置:")
    print(f"   python -m src.deployment.cli config validate --config {config_path}")
    
    print("\n💡 提示:")
    print("   - 确保API Token有足够的权限")
    print("   - 项目名称只能包含字母、数字和连字符")
    print("   - 自定义域名需要在DNS中正确配置")


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 运行过程中发生错误: {e}")
        sys.exit(1)