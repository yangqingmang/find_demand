#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加密命令行工具
用于手动加密和解密配置文件
"""

import os
import sys
import json
import argparse
from typing import Dict, Any
from crypto_manager import ConfigCrypto, init_crypto_system


def encrypt_config_file(input_file: str, output_file: str = None):
    """加密配置文件"""
    if not os.path.exists(input_file):
        print(f"❌ 输入文件不存在: {input_file}")
        return False
    
    if output_file is None:
        output_file = input_file + '.encrypted'
    
    try:
        # 初始化加密系统
        crypto = init_crypto_system()
        
        # 读取配置文件
        print(f"正在读取配置文件: {input_file}")
        config_data = {}
        
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    config_data[key.strip()] = value.strip()
        
        if not config_data:
            print("❌ 配置文件为空或格式错误")
            return False
        
        print(f"找到 {len(config_data)} 个配置项")
        
        # 加密配置
        print("正在加密配置...")
        encrypted_data = crypto.encrypt_config(config_data)
        
        # 保存加密文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(encrypted_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 配置已加密保存到: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ 加密失败: {e}")
        return False


def decrypt_config_file(input_file: str, output_file: str = None):
    """解密配置文件"""
    if not os.path.exists(input_file):
        print(f"❌ 输入文件不存在: {input_file}")
        return False
    
    if output_file is None:
        output_file = input_file.replace('.encrypted', '.decrypted')
    
    try:
        # 初始化加密系统
        crypto = ConfigCrypto()
        
        # 读取加密文件
        print(f"正在读取加密文件: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            encrypted_data = json.load(f)
        
        # 解密配置
        print("正在解密配置...")
        config_data = crypto.decrypt_config(encrypted_data)
        
        # 保存解密文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 解密后的配置文件\n")
            f.write("# 请勿提交到版本控制系统\n\n")
            
            for key, value in config_data.items():
                f.write(f"{key}={value}\n")
        
        print(f"✓ 配置已解密保存到: {output_file}")
        print(f"找到 {len(config_data)} 个配置项")
        return True
        
    except Exception as e:
        print(f"❌ 解密失败: {e}")
        return False


def show_config_info(config_file: str):
    """显示配置文件信息"""
    if not os.path.exists(config_file):
        print(f"❌ 配置文件不存在: {config_file}")
        return
    
    try:
        if config_file.endswith('.encrypted'):
            # 加密文件
            with open(config_file, 'r', encoding='utf-8') as f:
                encrypted_data = json.load(f)
            
            print(f"=== 加密配置文件信息 ===")
            print(f"文件: {config_file}")
            print(f"加密算法: {encrypted_data.get('algorithm', '未知')}")
            print(f"文件大小: {os.path.getsize(config_file)} 字节")
            
            # 尝试解密并显示配置项数量
            try:
                crypto = ConfigCrypto()
                config_data = crypto.decrypt_config(encrypted_data)
                print(f"配置项数量: {len(config_data)}")
                print("配置项列表:")
                for key in config_data.keys():
                    print(f"  - {key}")
            except Exception as e:
                print(f"无法解密查看详细信息: {e}")
        
        else:
            # 普通配置文件
            config_data = {}
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config_data[key.strip()] = value.strip()
            
            print(f"=== 配置文件信息 ===")
            print(f"文件: {config_file}")
            print(f"文件大小: {os.path.getsize(config_file)} 字节")
            print(f"配置项数量: {len(config_data)}")
            print("配置项列表:")
            for key, value in config_data.items():
                # 隐藏敏感信息
                if any(sensitive in key.upper() for sensitive in ['KEY', 'SECRET', 'TOKEN', 'PASSWORD']):
                    display_value = value[:10] + "..." if len(value) > 10 else "***"
                else:
                    display_value = value
                print(f"  - {key}: {display_value}")
    
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='配置文件加密工具')
    parser.add_argument('action', choices=['encrypt', 'decrypt', 'info'], 
                       help='操作类型: encrypt(加密), decrypt(解密), info(查看信息)')
    parser.add_argument('input', help='输入文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径')
    
    args = parser.parse_args()
    
    if args.action == 'encrypt':
        success = encrypt_config_file(args.input, args.output)
        sys.exit(0 if success else 1)
    
    elif args.action == 'decrypt':
        success = decrypt_config_file(args.input, args.output)
        sys.exit(0 if success else 1)
    
    elif args.action == 'info':
        show_config_info(args.input)


if __name__ == "__main__":
    main()