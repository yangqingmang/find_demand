#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新加密配置脚本
"""

from crypto_manager import ConfigCrypto
import os

def reencrypt_config():
    """重新加密配置"""
    print("=== 重新加密配置工具 ===")
    
    # 需要加密的配置项
    config_items = {
        'SERPAPI_KEY': '',
        'SERP_API_ENABLED': 'true',
        'PRODUCTHUNT_API_TOKEN': ''
    }
    
    print("\n请输入以下配置的真实值（留空跳过）:")
    
    # 收集用户输入
    for key in config_items.keys():
        if key == 'SERP_API_ENABLED':
            # 这个通常是true/false
            value = input(f"{key} (true/false) [默认: true]: ").strip()
            config_items[key] = value if value else 'true'
        else:
            # API密钥等敏感信息
            value = input(f"{key}: ").strip()
            if value:
                config_items[key] = value
            else:
                print(f"  跳过 {key}")
                del config_items[key]
    
    # 过滤掉空值
    final_config = {k: v for k, v in config_items.items() if v}
    
    if not final_config:
        print("❌ 没有配置需要加密")
        return
    
    print(f"\n将要加密的配置项: {list(final_config.keys())}")
    
    # 确认
    confirm = input("确认加密这些配置? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', '是']:
        print("取消加密")
        return
    
    try:
        # 初始化加密器
        crypto = ConfigCrypto()
        
        # 加密配置
        encrypted_content = crypto.encrypt_config(final_config)
        
        # 备份原文件
        if os.path.exists('.env.encrypted'):
            os.rename('.env.encrypted', '.env.encrypted.backup')
            print("✓ 原配置文件已备份为 .env.encrypted.backup")
        
        # 保存新的加密配置
        with open('.env.encrypted', 'w', encoding='utf-8') as f:
            f.write(encrypted_content)
        
        print("✅ 配置重新加密成功!")
        print("📁 新的加密配置已保存到 .env.encrypted")
        
        # 测试解密
        print("\n🧪 测试解密...")
        decrypted = crypto.decrypt_config(encrypted_content)
        print(f"✓ 解密测试成功，配置项: {list(decrypted.keys())}")
        
    except Exception as e:
        print(f"❌ 加密失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reencrypt_config()