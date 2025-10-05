#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置管理器
支持加密配置的自动加载和解密
"""

import os
import json
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass
try:
    from .crypto_manager import ConfigCrypto
except ImportError:
    try:
        from crypto_manager import ConfigCrypto
    except ImportError:
        # 如果加密模块不可用，创建一个简化版本
        class ConfigCrypto:
            def encrypt_config(self, config):
                return config
            def decrypt_config(self, config):
                return config


@dataclass
class ConfigData:
    """配置数据类 - 只定义字段类型，不设置默认值"""
    # Google API 配置
    GOOGLE_API_KEY: str = ""
    GOOGLE_CSE_ID: str = ""
    
    # SERP 分析配置
    SERP_CACHE_ENABLED: bool = True
    SERP_CACHE_DURATION: int = 3600
    SERP_REQUEST_DELAY: int = 1
    SERP_MAX_RETRIES: int = 3
    
    # Google Ads API 配置
    GOOGLE_ADS_DEVELOPER_TOKEN: str = ""
    GOOGLE_ADS_CLIENT_ID: str = ""
    GOOGLE_ADS_CLIENT_SECRET: str = ""
    GOOGLE_ADS_REFRESH_TOKEN: str = ""
    GOOGLE_ADS_CUSTOMER_ID: str = ""
    GOOGLE_ADS_API_VERSION: str = "v15"
    
    # 其他 API 配置
    SERP_API_KEY: str = ""
    AHREFS_API_KEY: str = ""
    PRODUCTHUNT_API_TOKEN: str = ""
    
    # 代理配置
    PROXY_ENABLED: bool = True
    PROXY_MAX_REQUESTS_PER_MINUTE: int = 10
    PROXY_REQUEST_DELAY_MIN: float = 1.0
    PROXY_REQUEST_DELAY_MAX: float = 3.0
    PROXY_MAX_RETRIES: int = 3
    PROXY_TIMEOUT: int = 10
    PROXY_LIST: str = ""  # JSON格式的代理列表或文件路径
    
    # 部署 API 配置
    VERCEL_API_TOKEN: str = ""
    CLOUDFLARE_API_TOKEN: str = ""
    CLOUDFLARE_ACCOUNT_ID: str = ""
    
    # 应用配置 - 这些值将从配置文件中读取
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    DISCOVERY_CACHE_ENABLED: bool = True
    DISCOVERY_CACHE_TTL: int = 3600
    DISCOVERY_CACHE_DIR: str = "output/cache/discovery"
    DISCOVERY_MAX_CONCURRENCY: int = 5
    DISCOVERY_DEFAULT_RATE_INTERVAL: float = 0.35
    DISCOVERY_MAX_RETRIES: int = 3
    DISCOVERY_REQUEST_TIMEOUT: int = 12
    DISCOVERY_RETRY_BACKOFF: Tuple[float, float] = (1.0, 3.0)
    DISCOVERY_RATE_LIMITS: Optional[Dict[str, float]] = None
    DISCOVERY_EMBEDDINGS_ENABLED: bool = True
    DISCOVERY_EMBEDDINGS_MIN_KEYWORDS: int = 5
    DISCOVERY_EMBEDDINGS_MODEL: str = 'sentence-transformers/all-MiniLM-L6-v2'

    OUTPUT_DIR: str = "data/results"
    WORKFLOW_CACHE_ENABLED: bool = True
    WORKFLOW_CACHE_TTL_HOURS: float = 12.0
    WORKFLOW_CACHE_DIR: str = "output/workflow_cache"
    REDDIT_API: Dict[str, Any] = None
    SERP_API_ENABLED: bool = True
    SERP_API_MONTHLY_LIMIT: int = 250
    SERP_API_FAILURE_LIMIT: int = 5
    SERP_API_SKIP_ON_FAILURE: bool = False
    SERP_API_FAILURE_COOLDOWN_HOURS: float = 12.0
    SERP_API_FAILURE_DISABLE_DAYS: int = 1


class ConfigManager:
    """统一配置管理器"""
    
    def __init__(self):
        self.config_dir = os.path.dirname(__file__)
        self.crypto = ConfigCrypto()
        self._config_data: Optional[ConfigData] = None
        
        # 配置文件路径
        self.env_file = os.path.join(self.config_dir, '.env')
        self.encrypted_file = os.path.join(self.config_dir, '.env.encrypted')
        self.public_config_file = os.path.join(self.config_dir, '.env.public')
    
    def load_config(self, force_reload: bool = False) -> ConfigData:
        """
        加载配置数据
        
        Args:
            force_reload: 是否强制重新加载
            
        Returns:
            ConfigData: 配置数据对象
        """
        if self._config_data is not None and not force_reload:
            return self._config_data
        
        print("正在加载配置...")
        
        # 合并多个配置源
        config_dict = {}
        
        # 1. 加载公开配置（如果存在）
        public_config = self._load_public_config()
        if public_config:
            config_dict.update(public_config)
            print("✓ 已加载公开配置")
        
        # 2. 加载加密配置（如果存在）
        encrypted_config = self._load_encrypted_config()
        if encrypted_config:
            config_dict.update(encrypted_config)
            print("✓ 已加载加密配置")
        
        # 3. 加载普通 .env 文件（如果存在）
        env_config = self._load_env_file()
        if env_config:
            config_dict.update(env_config)
            print("✓ 已加载 .env 配置")
        
        # 4. 加载环境变量（优先级最高）
        env_vars = self._load_environment_variables()
        config_dict.update(env_vars)
        if env_vars:
            print(f"✓ 已加载 {len(env_vars)} 个环境变量")
        
        # 转换为 ConfigData 对象
        self._config_data = self._dict_to_config_data(config_dict)
        
        print("✓ 配置加载完成")
        return self._config_data
    
    def _load_public_config(self) -> Dict[str, Any]:
        """加载公开配置"""
        if not os.path.exists(self.public_config_file):
            return {}
        
        return self._parse_env_file(self.public_config_file)
    
    def _load_encrypted_config(self) -> Dict[str, Any]:
        """加载加密配置"""
        if not os.path.exists(self.encrypted_file):
            return {}
        
        try:
            with open(self.encrypted_file, 'r', encoding='utf-8') as f:
                encrypted_content = f.read()
            
            # 尝试解析为 JSON（兼容旧格式）
            try:
                encrypted_data = json.loads(encrypted_content)
                decrypted_config = self.crypto.decrypt_config(encrypted_data)
            except json.JSONDecodeError:
                # 新的 .env 格式
                decrypted_config = self.crypto.decrypt_config(encrypted_content)
            
            return decrypted_config
            
        except KeyboardInterrupt:
            print("⚠️  用户取消加密配置加载，跳过加密配置")
            return {}
        except Exception as e:
            print(f"⚠️  加载加密配置失败: {e}")
            print("⚠️  跳过加密配置，使用公开配置和默认值")
            return {}
    
    def _load_env_file(self) -> Dict[str, Any]:
        """加载 .env 文件"""
        if not os.path.exists(self.env_file):
            return {}
        
        return self._parse_env_file(self.env_file)
    
    def _parse_env_file(self, file_path: str) -> Dict[str, Any]:
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
                    
                    # 类型转换
                    config[key] = self._convert_value(value)
        
        return config
    
    def _load_environment_variables(self) -> Dict[str, Any]:
        """加载环境变量中的配置"""
        config = {}
        
        # 定义需要检查的环境变量
        env_keys = [
            'GOOGLE_API_KEY', 'GOOGLE_CSE_ID',
            'GOOGLE_ADS_DEVELOPER_TOKEN', 'GOOGLE_ADS_CLIENT_ID',
            'GOOGLE_ADS_CLIENT_SECRET', 'GOOGLE_ADS_REFRESH_TOKEN',
            'GOOGLE_ADS_CUSTOMER_ID', 'GOOGLE_ADS_API_VERSION',
            'SERP_API_KEY', 'SERPAPI_KEY', 'AHREFS_API_KEY',
            'PRODUCTHUNT_API_TOKEN',
            'DEBUG', 'LOG_LEVEL', 'OUTPUT_DIR',
            'DISCOVERY_CACHE_ENABLED', 'DISCOVERY_CACHE_TTL', 'DISCOVERY_CACHE_DIR',
            'DISCOVERY_MAX_CONCURRENCY', 'DISCOVERY_DEFAULT_RATE_INTERVAL',
            'DISCOVERY_MAX_RETRIES', 'DISCOVERY_REQUEST_TIMEOUT', 'DISCOVERY_RETRY_BACKOFF',
            'DISCOVERY_RATE_LIMITS',
            'DISCOVERY_EMBEDDINGS_ENABLED', 'DISCOVERY_EMBEDDINGS_MIN_KEYWORDS',
            'DISCOVERY_EMBEDDINGS_MODEL',
            'WORKFLOW_CACHE_ENABLED', 'WORKFLOW_CACHE_TTL_HOURS', 'WORKFLOW_CACHE_DIR',
            'SERP_API_MONTHLY_LIMIT'
        ]
        
        for key in env_keys:
            value = os.getenv(key)
            if value is not None:
                config[key] = self._convert_value(value)
        
        return config
    
    def _convert_value(self, value: str) -> Any:
        """转换配置值类型"""
        if not value:
            return ""
        
        # 布尔值转换
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # 数字转换
        if value.isdigit():
            return int(value)
        
        try:
            return float(value)
        except ValueError:
            pass
        
        return value
    
    def _dict_to_config_data(self, config_dict: Dict[str, Any]) -> ConfigData:
        """将字典转换为 ConfigData 对象"""
        # 获取 ConfigData 的所有字段
        config_data = ConfigData()
        
        # 字段名映射
        field_mapping = {
            'SERPAPI_KEY': 'SERP_API_KEY',  # 兼容旧的字段名
            'reddit_api': 'REDDIT_API'
        }
        
        for key, value in config_dict.items():
            # 检查是否需要映射字段名
            target_key = field_mapping.get(key, key)
            
            if hasattr(config_data, target_key):
                setattr(config_data, target_key, value)
        
        return config_data
    
    def save_encrypted_config(self, sensitive_config: Dict[str, Any]):
        """
        保存敏感配置到加密文件
        
        Args:
            sensitive_config: 需要加密的敏感配置
        """
        try:
            encrypted_content = self.crypto.encrypt_config(sensitive_config)
            
            with open(self.encrypted_file, 'w', encoding='utf-8') as f:
                f.write(encrypted_content)
            
            print(f"✓ 敏感配置已加密保存到: {self.encrypted_file}")
            
        except Exception as e:
            print(f"❌ 保存加密配置失败: {e}")
            raise
    
    def save_public_config(self, public_config: Dict[str, Any]):
        """
        保存公开配置到明文文件
        
        Args:
            public_config: 公开的非敏感配置
        """
        try:
            with open(self.public_config_file, 'w', encoding='utf-8') as f:
                f.write("# 公开配置（非敏感信息）\n")
                f.write("# 此文件可以安全提交到版本控制系统\n\n")
                
                for key, value in public_config.items():
                    f.write(f"{key}={value}\n")
            
            print(f"✓ 公开配置已保存到: {self.public_config_file}")
            
        except Exception as e:
            print(f"❌ 保存公开配置失败: {e}")
            raise
    
    def get_config(self) -> ConfigData:
        """获取配置数据（单例模式）"""
        return self.load_config()
    
    def reload_config(self) -> ConfigData:
        """重新加载配置"""
        return self.load_config(force_reload=True)
    
    def is_configured(self, *keys: str) -> bool:
        """检查指定配置是否已设置"""
        config = self.get_config()
        
        for key in keys:
            if not hasattr(config, key):
                return False
            
            value = getattr(config, key)
            if not value or (isinstance(value, str) and value.strip() == ""):
                return False
        
        return True
    
    def get_config_status(self) -> Dict[str, str]:
        """获取配置状态报告"""
        config = self.get_config()
        status = {}
        
        # 检查各个配置项
        checks = {
            'Google API Key': config.GOOGLE_API_KEY,
            'Google CSE ID': config.GOOGLE_CSE_ID,
            'Google Ads Developer Token': config.GOOGLE_ADS_DEVELOPER_TOKEN,
            'Google Ads Client ID': config.GOOGLE_ADS_CLIENT_ID,
            'Google Ads Client Secret': config.GOOGLE_ADS_CLIENT_SECRET,
            'Google Ads Refresh Token': config.GOOGLE_ADS_REFRESH_TOKEN,
            'Google Ads Customer ID': config.GOOGLE_ADS_CUSTOMER_ID,
        }
        
        for name, value in checks.items():
            if value and str(value).strip():
                status[name] = "✓ 已配置"
            else:
                status[name] = "✗ 未配置"
        
        return status


# 全局配置管理器实例
_config_manager = None

def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config() -> ConfigData:
    """快捷方式：获取配置数据"""
    return get_config_manager().get_config()


if __name__ == "__main__":
    # 测试配置管理器
    manager = ConfigManager()
    config = manager.load_config()
    
    print("\n=== 配置状态 ===")
    status = manager.get_config_status()
    for name, state in status.items():
        print(f"{name}: {state}")
    
    print(f"\n=== 当前配置 ===")
    print(f"Google API Key: {config.GOOGLE_API_KEY[:10]}..." if config.GOOGLE_API_KEY else "未配置")
    print(f"Google CSE ID: {config.GOOGLE_CSE_ID}")
    print(f"Debug 模式: {config.DEBUG}")
    print(f"日志级别: {config.LOG_LEVEL}")
