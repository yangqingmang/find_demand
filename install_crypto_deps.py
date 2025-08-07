#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装配置加密所需的依赖包
"""

import subprocess
import sys


def install_cryptography():
    """安装 cryptography 包"""
    try:
        print("正在安装 cryptography 包...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "cryptography>=3.4.8"
        ])
        print("✓ cryptography 包安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装失败: {e}")
        return False


def test_import():
    """测试导入"""
    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.ciphers import Cipher
        print("✓ cryptography 包导入测试成功")
        return True
    except ImportError as e:
        print(f"❌ 导入测试失败: {e}")
        return False


def main():
    """主函数"""
    print("=== 配置加密系统依赖安装 ===")
    
    # 安装依赖
    if install_cryptography():
        # 测试导入
        if test_import():
            print("\n✅ 所有依赖安装完成！")
            print("\n下一步:")
            print("1. 初始化加密系统: python config/crypto_manager.py")
            print("2. 迁移现有配置: python config/migrate_config.py")
            print("3. 测试配置加载: python config/config_manager.py")
        else:
            print("\n❌ 依赖安装可能有问题，请检查错误信息")
    else:
        print("\n❌ 依赖安装失败")
        print("请尝试手动安装: pip install cryptography")


if __name__ == "__main__":
    main()