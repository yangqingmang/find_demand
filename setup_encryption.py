#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加密系统一键设置脚本
"""

import os
import sys
import subprocess
from pathlib import Path


def print_step(step_num: int, description: str):
    """打印步骤信息"""
    print(f"\n{'='*50}")
    print(f"步骤 {step_num}: {description}")
    print('='*50)


def check_python_version():
    """检查 Python 版本"""
    if sys.version_info < (3, 7):
        print("❌ 需要 Python 3.7 或更高版本")
        return False
    print(f"✓ Python 版本: {sys.version}")
    return True


def install_dependencies():
    """安装依赖"""
    try:
        print("正在安装 cryptography 包...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "cryptography>=3.4.8"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✓ 依赖安装成功")
        return True
    except subprocess.CalledProcessError:
        print("❌ 依赖安装失败")
        print("请手动运行: pip install cryptography")
        return False


def initialize_crypto_system():
    """初始化加密系统"""
    try:
        # 导入并初始化
        sys.path.insert(0, 'config')
        from crypto_manager import init_crypto_system
        
        crypto = init_crypto_system()
        print("✓ 加密系统初始化成功")
        return True
    except Exception as e:
        print(f"❌ 加密系统初始化失败: {e}")
        return False


def migrate_existing_config():
    """迁移现有配置"""
    env_file = Path('config/.env')
    
    if not env_file.exists():
        print("未找到现有配置文件，跳过迁移")
        return True
    
    try:
        sys.path.insert(0, 'config')
        from migrate_config import ConfigMigrator
        
        migrator = ConfigMigrator()
        
        print("找到现有配置文件，开始自动迁移...")
        success = migrator.migrate_from_env_file(str(env_file))
        
        if success:
            print("✓ 配置迁移成功")
            return True
        else:
            print("❌ 配置迁移失败")
            return False
            
    except Exception as e:
        print(f"❌ 配置迁移出错: {e}")
        return False


def verify_setup():
    """验证设置"""
    try:
        sys.path.insert(0, 'config')
        from config_manager import get_config_manager
        
        manager = get_config_manager()
        config = manager.load_config()
        
        print("✓ 配置加载测试成功")
        
        # 显示配置状态
        status = manager.get_config_status()
        print("\n配置状态:")
        for name, state in status.items():
            print(f"  {name}: {state}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False


def show_next_steps():
    """显示后续步骤"""
    print(f"\n{'='*50}")
    print("🎉 配置加密系统设置完成！")
    print('='*50)
    
    print("\n📋 后续步骤:")
    print("1. 检查并填写配置:")
    print("   - 编辑 config/.env.encrypted（如果需要修改敏感配置）")
    print("   - 编辑 config/.env.public（如果需要修改公开配置）")
    
    print("\n2. 测试配置:")
    print("   python config/config_manager.py")
    
    print("\n3. 在代码中使用:")
    print("   from config.config_manager import get_config")
    print("   config = get_config()")
    
    print("\n4. 团队协作:")
    print("   - 将 config/private.key 安全分享给团队成员")
    print("   - 确保 private.key 不被提交到版本控制")
    
    print("\n📖 详细文档:")
    print("   docs/配置加密系统使用指南.md")


def main():
    """主函数"""
    print("🔐 配置加密系统一键设置")
    print("此脚本将帮助您快速设置配置加密系统")
    
    # 步骤1: 检查环境
    print_step(1, "检查 Python 环境")
    if not check_python_version():
        sys.exit(1)
    
    # 步骤2: 安装依赖
    print_step(2, "安装依赖包")
    if not install_dependencies():
        sys.exit(1)
    
    # 步骤3: 初始化加密系统
    print_step(3, "初始化加密系统")
    if not initialize_crypto_system():
        sys.exit(1)
    
    # 步骤4: 迁移现有配置
    print_step(4, "迁移现有配置")
    if not migrate_existing_config():
        print("⚠️  配置迁移失败，但可以继续")
    
    # 步骤5: 验证设置
    print_step(5, "验证设置")
    if not verify_setup():
        print("⚠️  验证失败，请检查配置")
    
    # 显示后续步骤
    show_next_steps()


if __name__ == "__main__":
    main()