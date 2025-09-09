#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理配置加载器

功能:
- 加载代理配置文件
- 支持环境特定配置
- 集成加密配置管理
- 提供配置验证

作者: AI Assistant
创建时间: 2025-01-27
"""

import os
import yaml
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProxyConfig:
    """代理配置数据类"""
    enabled: bool = True
    max_requests_per_minute: int = 10
    request_delay_min: float = 1.0
    request_delay_max: float = 3.0
    max_retries: int = 3
    timeout: int = 10
    proxies: List[Dict[str, Any]] = None
    user_agent_rotation: bool = True
    domain_specific: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.proxies is None:
            self.proxies = []
        if self.domain_specific is None:
            self.domain_specific = {}


class ProxyConfigLoader:
    """代理配置加载器"""
    
    def __init__(self, config_dir: str = None):
        """
        初始化配置加载器
        
        Args:
            config_dir: 配置文件目录，默认为当前目录
        """
        self.config_dir = config_dir or os.path.dirname(__file__)
        self.config_file = os.path.join(self.config_dir, 'proxy_config.yaml')
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self._config_cache = None
    
    def load_config(self, force_reload: bool = False) -> ProxyConfig:
        """
        加载代理配置
        
        Args:
            force_reload: 是否强制重新加载
            
        Returns:
            ProxyConfig对象
        """
        if self._config_cache is None or force_reload:
            self._config_cache = self._load_config_from_file()
        return self._config_cache
    
    def _load_config_from_file(self) -> ProxyConfig:
        """
        从文件加载配置
        
        Returns:
            ProxyConfig对象
        """
        try:
            # 加载YAML配置文件
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 获取基础配置
            base_config = config_data.get('proxy_settings', {})
            
            # 获取环境特定配置
            env_config = config_data.get('environments', {}).get(self.environment, {})
            env_proxy_config = env_config.get('proxy_settings', {})
            
            # 合并配置
            merged_config = self._merge_configs(base_config, env_proxy_config)
            
            # 加载代理列表
            proxies = self._load_proxy_list(merged_config)
            
            # 创建配置对象
            proxy_config = ProxyConfig(
                enabled=merged_config.get('enabled', True),
                max_requests_per_minute=merged_config.get('rate_limiting', {}).get('max_requests_per_minute', 10),
                request_delay_min=merged_config.get('rate_limiting', {}).get('request_delay', {}).get('min', 1.0),
                request_delay_max=merged_config.get('rate_limiting', {}).get('request_delay', {}).get('max', 3.0),
                max_retries=merged_config.get('retry_settings', {}).get('max_retries', 3),
                timeout=merged_config.get('retry_settings', {}).get('timeout', 10),
                proxies=proxies,
                user_agent_rotation=merged_config.get('user_agent', {}).get('rotation', True),
                domain_specific=merged_config.get('domain_specific', {})
            )
            
            logger.info(f"✅ 代理配置加载成功，环境: {self.environment}")
            return proxy_config
            
        except FileNotFoundError:
            logger.warning(f"⚠️ 代理配置文件不存在: {self.config_file}，使用默认配置")
            return ProxyConfig()
        except Exception as e:
            logger.error(f"❌ 加载代理配置失败: {e}，使用默认配置")
            return ProxyConfig()
    
    def _merge_configs(self, base_config: Dict[str, Any], env_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并基础配置和环境配置
        
        Args:
            base_config: 基础配置
            env_config: 环境配置
            
        Returns:
            合并后的配置
        """
        merged = base_config.copy()
        
        def deep_merge(target: Dict, source: Dict):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    deep_merge(target[key], value)
                else:
                    target[key] = value
        
        deep_merge(merged, env_config)
        return merged
    
    def _load_proxy_list(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        加载代理列表
        
        Args:
            config: 配置字典
            
        Returns:
            代理列表
        """
        proxy_pool = config.get('proxy_pool', {})
        proxies = proxy_pool.get('proxies', [])
        
        # 如果代理列表为空，尝试从环境变量或加密配置加载
        if not proxies:
            proxies = self._load_proxies_from_env()
        
        # 验证代理配置
        validated_proxies = []
        for proxy in proxies:
            if self._validate_proxy_config(proxy):
                validated_proxies.append(proxy)
            else:
                logger.warning(f"⚠️ 无效的代理配置: {proxy}")
        
        logger.info(f"✅ 加载了 {len(validated_proxies)} 个有效代理")
        return validated_proxies
    
    def _load_proxies_from_env(self) -> List[Dict[str, Any]]:
        """
        从环境变量加载代理列表
        
        Returns:
            代理列表
        """
        proxy_list_env = os.getenv('PROXY_LIST', '')
        if not proxy_list_env:
            return []
        
        try:
            # 尝试解析JSON格式的代理列表
            if proxy_list_env.startswith('['):
                return json.loads(proxy_list_env)
            
            # 尝试从文件加载
            if os.path.isfile(proxy_list_env):
                with open(proxy_list_env, 'r', encoding='utf-8') as f:
                    if proxy_list_env.endswith('.json'):
                        return json.load(f)
                    elif proxy_list_env.endswith('.yaml') or proxy_list_env.endswith('.yml'):
                        data = yaml.safe_load(f)
                        return data.get('proxies', [])
            
            # 简单格式：host:port,host:port
            proxies = []
            for proxy_str in proxy_list_env.split(','):
                proxy_str = proxy_str.strip()
                if ':' in proxy_str:
                    host, port = proxy_str.split(':', 1)
                    proxies.append({
                        'host': host.strip(),
                        'port': int(port.strip()),
                        'protocol': 'http'
                    })
            return proxies
            
        except Exception as e:
            logger.error(f"❌ 解析环境变量代理列表失败: {e}")
            return []
    
    def _validate_proxy_config(self, proxy: Dict[str, Any]) -> bool:
        """
        验证代理配置
        
        Args:
            proxy: 代理配置字典
            
        Returns:
            配置是否有效
        """
        required_fields = ['host', 'port']
        for field in required_fields:
            if field not in proxy:
                return False
        
        # 验证端口号
        try:
            port = int(proxy['port'])
            if not (1 <= port <= 65535):
                return False
        except (ValueError, TypeError):
            return False
        
        # 验证协议
        protocol = proxy.get('protocol', 'http')
        if protocol not in ['http', 'https', 'socks4', 'socks5']:
            return False
        
        return True
    
    def get_domain_config(self, domain: str) -> Dict[str, Any]:
        """
        获取特定域名的配置
        
        Args:
            domain: 域名
            
        Returns:
            域名特定配置
        """
        config = self.load_config()
        return config.domain_specific.get(domain, {})
    
    def is_proxy_enabled_for_domain(self, domain: str) -> bool:
        """
        检查特定域名是否启用代理
        
        Args:
            domain: 域名
            
        Returns:
            是否启用代理
        """
        config = self.load_config()
        if not config.enabled:
            return False
        
        domain_config = self.get_domain_config(domain)
        return domain_config.get('use_proxy', True)
    
    def get_rate_limit_for_domain(self, domain: str) -> Dict[str, Any]:
        """
        获取特定域名的频率限制配置
        
        Args:
            domain: 域名
            
        Returns:
            频率限制配置
        """
        config = self.load_config()
        domain_config = self.get_domain_config(domain)
        
        return {
            'max_requests_per_minute': domain_config.get('max_requests_per_minute', config.max_requests_per_minute),
            'request_delay_min': domain_config.get('request_delay', {}).get('min', config.request_delay_min),
            'request_delay_max': domain_config.get('request_delay', {}).get('max', config.request_delay_max)
        }
    
    def reload_config(self) -> ProxyConfig:
        """
        重新加载配置
        
        Returns:
            ProxyConfig对象
        """
        return self.load_config(force_reload=True)
    
    def validate_config(self) -> Dict[str, Any]:
        """
        验证配置完整性
        
        Returns:
            验证结果
        """
        try:
            config = self.load_config()
            
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'info': {
                    'proxy_count': len(config.proxies),
                    'enabled': config.enabled,
                    'environment': self.environment
                }
            }
            
            # 检查代理数量
            if config.enabled and len(config.proxies) == 0:
                validation_result['warnings'].append('代理已启用但没有配置代理服务器')
            
            # 检查配置合理性
            if config.max_requests_per_minute <= 0:
                validation_result['errors'].append('max_requests_per_minute必须大于0')
                validation_result['valid'] = False
            
            if config.request_delay_min < 0 or config.request_delay_max < config.request_delay_min:
                validation_result['errors'].append('请求延迟配置无效')
                validation_result['valid'] = False
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f'配置验证失败: {e}'],
                'warnings': [],
                'info': {}
            }


# 全局配置加载器实例
_proxy_config_loader = None


def get_proxy_config_loader() -> ProxyConfigLoader:
    """获取全局代理配置加载器实例"""
    global _proxy_config_loader
    if _proxy_config_loader is None:
        _proxy_config_loader = ProxyConfigLoader()
    return _proxy_config_loader


def get_proxy_config() -> ProxyConfig:
    """获取代理配置"""
    return get_proxy_config_loader().load_config()


def reload_proxy_config() -> ProxyConfig:
    """重新加载代理配置"""
    return get_proxy_config_loader().reload_config()


if __name__ == "__main__":
    # 测试配置加载
    loader = ProxyConfigLoader()
    config = loader.load_config()
    
    print(f"代理启用: {config.enabled}")
    print(f"代理数量: {len(config.proxies)}")
    print(f"最大请求频率: {config.max_requests_per_minute}/分钟")
    print(f"请求延迟: {config.request_delay_min}-{config.request_delay_max}秒")
    
    # 验证配置
    validation = loader.validate_config()
    print(f"\n配置验证: {'通过' if validation['valid'] else '失败'}")
    if validation['errors']:
        print(f"错误: {validation['errors']}")
    if validation['warnings']:
        print(f"警告: {validation['warnings']}")