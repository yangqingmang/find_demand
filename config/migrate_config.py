#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置迁移工具
将现有的 .env 配置迁移到加密系统
"""

import os
import json
from typing import Dict, Set
try:
    from .crypto_manager import init_crypto_system
    from .config_manager import ConfigManager
except ImportError:
    from crypto_manager import init_crypto_system
    from config_manager import ConfigManager


class ConfigMigrator:
    """配置迁移器"""
    
    def __init__(self):
        self.config_dir = os.path.dirname(__file__)
        self.crypto = init_crypto_system()
        self.manager = ConfigManager()
        
        # 定义敏感配置键（需要加密）
        self.sensitive_keys: Set[str] = {
            'GOOGLE_API_KEY',
            'GOOGLE_CSE_ID',
            'GOOGLE_ADS_DEVELOPER_TOKEN',
            'GOOGLE_ADS_CLIENT_ID',
            'GOOGLE_ADS_CLIENT_SECRET',
            'GOOGLE_ADS_REFRESH_TOKEN',
            'GOOGLE_ADS_CUSTOMER_ID',
            'SERP_API_KEY',
            'AHREFS_API_KEY',
            'VERCEL_API_TOKEN',
            'CLOUDFLARE_API_TOKEN',
            'CLOUDFLARE_ACCOUNT_ID'
        }
        
        # 定义公开配置键（不需要加密）
        self.public_keys: Set[str] = {
            'SERP_CACHE_ENABLED',
            'SERP_CACHE_DURATION',
            'SERP_REQUEST_DELAY',
            'SERP_MAX_RETRIES',
            'GOOGLE_ADS_API_VERSION',
            'DEBUG',
            'LOG_LEVEL',
            'OUTPUT_DIR'
        }
    
    def migrate_from_env_file(self, env_file_path: str = None) -> bool:
        """
        从 .env 文件迁移配置
        
        Args:
            env_file_path: .env 文件路径，默认为 config/.env
            
        Returns:
            bool: 迁移是否成功
        """
        if env_file_path is None:
            env_file_path = os.path.join(self.config_dir, '.env')
        
        if not os.path.exists(env_file_path):
            print(f"❌ 找不到配置文件: {env_file_path}")
            return False
        
        print(f"正在从 {env_file_path} 迁移配置...")
        
        # 解析现有配置
        config_data = self._parse_env_file(env_file_path)
        
        if not config_data:
            print("❌ 配置文件为空或格式错误")
            return False
        
        # 分离敏感和公开配置
        sensitive_config = {}
        public_config = {}
        unknown_config = {}
        
        for key, value in config_data.items():
            if key in self.sensitive_keys:
                sensitive_config[key] = value
            elif key in self.public_keys:
                public_config[key] = value
            else:
                unknown_config[key] = value
        
        # 显示迁移计划
        print(f"\n=== 迁移计划 ===")
        print(f"敏感配置（将加密）: {len(sensitive_config)} 项")
        for key in sensitive_config.keys():
            print(f"  - {key}")
        
        print(f"\n公开配置（保持明文）: {len(public_config)} 项")
        for key in public_config.keys():
            print(f"  - {key}")
        
        if unknown_config:
            print(f"\n未知配置（需要手动处理）: {len(unknown_config)} 项")
            for key in unknown_config.keys():
                print(f"  - {key}")
        
        # 确认迁移
        confirm = input("\n是否继续迁移？(y/N): ").lower().strip()
        if confirm != 'y':
            print("迁移已取消")
            return False
        
        try:
            # 保存敏感配置（加密）
            if sensitive_config:
                self.manager.save_encrypted_config(sensitive_config)
                print(f"✓ 已加密保存 {len(sensitive_config)} 个敏感配置")
            
            # 保存公开配置
            if public_config:
                self.manager.save_public_config(public_config)
                print(f"✓ 已保存 {len(public_config)} 个公开配置")
            
            # 备份原始文件
            backup_path = f"{env_file_path}.backup"
            os.rename(env_file_path, backup_path)
            print(f"✓ 原始配置已备份到: {backup_path}")
            
            # 处理未知配置
            if unknown_config:
                unknown_file = os.path.join(self.config_dir, '.env.unknown')
                with open(unknown_file, 'w', encoding='utf-8') as f:
                    f.write("# 未知配置项，请手动处理\n")
                    for key, value in unknown_config.items():
                        f.write(f"{key}={value}\n")
                print(f"⚠️  未知配置已保存到: {unknown_file}")
            
            print("\n✅ 配置迁移完成！")
            print("\n下一步:")
            print("1. 验证配置: python config/config_manager.py")
            print("2. 测试应用: python main.py")
            print("3. 删除备份文件（确认无误后）")
            
            return True
            
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            return False
    
    def _parse_env_file(self, file_path: str) -> Dict[str, str]:
        """解析 .env 格式文件"""
        config = {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                
                # 解析键值对
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 移除引号
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    config[key] = value
        
        return config
    
    def create_sample_configs(self):
        """创建示例配置文件"""
        print("正在创建示例配置文件...")
        
        # 示例敏感配置
        sample_sensitive = {
            "GOOGLE_API_KEY": "your_google_api_key_here",
            "GOOGLE_CSE_ID": "your_custom_search_engine_id_here",
            "GOOGLE_ADS_DEVELOPER_TOKEN": "your_developer_token_here",
            "GOOGLE_ADS_CLIENT_ID": "your_client_id_here",
            "GOOGLE_ADS_CLIENT_SECRET": "your_client_secret_here",
            "GOOGLE_ADS_REFRESH_TOKEN": "your_refresh_token_here",
            "GOOGLE_ADS_CUSTOMER_ID": "your_customer_id_here"
        }
        
        # 示例公开配置
        sample_public = {
            "SERP_CACHE_ENABLED": "true",
            "SERP_CACHE_DURATION": "3600",
            "SERP_REQUEST_DELAY": "1",
            "SERP_MAX_RETRIES": "3",
            "GOOGLE_ADS_API_VERSION": "v15",
            "DEBUG": "false",
            "LOG_LEVEL": "INFO",
            "OUTPUT_DIR": "data/results"
        }
        
        try:
            # 保存示例配置
            self.manager.save_encrypted_config(sample_sensitive)
            self.manager.save_public_config(sample_public)
            
            print("✓ 示例配置文件已创建")
            print("请编辑配置文件并填入真实的API密钥")
            
        except Exception as e:
            print(f"❌ 创建示例配置失败: {e}")
    
    def verify_migration(self) -> bool:
        """验证迁移结果"""
        print("正在验证迁移结果...")
        
        try:
            # 尝试加载配置
            config = self.manager.load_config()
            
            # 检查关键配置
            checks = [
                ('Google API Key', config.GOOGLE_API_KEY),
                ('Google CSE ID', config.GOOGLE_CSE_ID),
                ('SERP Cache Enabled', config.SERP_CACHE_ENABLED),
                ('Debug Mode', config.DEBUG)
            ]
            
            print("\n=== 配置验证结果 ===")
            all_ok = True
            
            for name, value in checks:
                if value:
                    print(f"✓ {name}: 已配置")
                else:
                    print(f"⚠️  {name}: 未配置")
                    all_ok = False
            
            if all_ok:
                print("\n✅ 所有配置验证通过！")
            else:
                print("\n⚠️  部分配置缺失，请检查配置文件")
            
            return all_ok
            
        except Exception as e:
            print(f"❌ 配置验证失败: {e}")
            return False


def main():
    """主函数"""
    print("=== 配置迁移工具 ===")
    print("此工具将帮助您将现有配置迁移到加密系统")
    
    migrator = ConfigMigrator()
    
    # 检查是否存在现有配置
    env_file = os.path.join(migrator.config_dir, '.env')
    
    if os.path.exists(env_file):
        print(f"\n找到现有配置文件: {env_file}")
        
        choice = input("选择操作:\n1. 迁移现有配置\n2. 创建示例配置\n3. 验证配置\n请输入选择 (1-3): ").strip()
        
        if choice == '1':
            success = migrator.migrate_from_env_file()
            if success:
                migrator.verify_migration()
        elif choice == '2':
            migrator.create_sample_configs()
        elif choice == '3':
            migrator.verify_migration()
        else:
            print("无效选择")
    else:
        print(f"\n未找到现有配置文件: {env_file}")
        
        choice = input("是否创建示例配置？(y/N): ").lower().strip()
        if choice == 'y':
            migrator.create_sample_configs()


if __name__ == "__main__":
    main()
