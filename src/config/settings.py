#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
用于管理API密钥和系统配置
支持多种配置方式：环境变量、.env文件、系统环境变量
"""

import os
from dotenv import load_dotenv

class Config:
    """配置类 - 支持多种配置源"""
    
    def __init__(self):
        """初始化配置，按优先级加载"""
        # 1. 尝试加载 .env 文件
        env_paths = [
            'config/.env',
            '.env',
            os.path.expanduser('~/.find_demand/.env')  # 用户主目录配置
        ]
        
        for env_path in env_paths:
            if os.path.exists(env_path):
                load_dotenv(env_path)
                print(f"已加载配置文件: {env_path}")
                break
        else:
            print("未找到 .env 配置文件，将使用系统环境变量")
    
    @property
    def GOOGLE_API_KEY(self):
        """Google API密钥 - 支持多种获取方式"""
        return (
            os.getenv('GOOGLE_API_KEY') or
            os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY') or
            self._get_from_config_file('GOOGLE_API_KEY')
        )
    
    @property
    def GOOGLE_CSE_ID(self):
        """Google自定义搜索引擎ID"""
        return (
            os.getenv('GOOGLE_CSE_ID') or
            os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID') or
            self._get_from_config_file('GOOGLE_CSE_ID')
        )
    
    @property
    def SERP_CACHE_ENABLED(self):
        """SERP缓存是否启用"""
        return os.getenv('SERP_CACHE_ENABLED', 'true').lower() == 'true'
    
    @property
    def SERP_CACHE_DURATION(self):
        """SERP缓存持续时间（秒）"""
        return int(os.getenv('SERP_CACHE_DURATION', '3600'))
    
    @property
    def SERP_REQUEST_DELAY(self):
        """SERP请求延迟（秒）"""
        return float(os.getenv('SERP_REQUEST_DELAY', '1'))
    
    @property
    def SERP_MAX_RETRIES(self):
        """SERP请求最大重试次数"""
        return int(os.getenv('SERP_MAX_RETRIES', '3'))
    
    def _get_from_config_file(self, key):
        """从配置文件中获取值（备用方法）"""
        config_file = os.path.expanduser('~/.find_demand/config.txt')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        if line.startswith(f'{key}='):
                            return line.split('=', 1)[1].strip()
            except Exception:
                pass
        return None
    
    @property
    def GOOGLE_ADS_DEVELOPER_TOKEN(self):
        """Google Ads Developer Token"""
        return os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN')

    @property
    def GOOGLE_ADS_CLIENT_ID(self):
        """Google Ads Client ID"""
        return os.getenv('GOOGLE_ADS_CLIENT_ID')

    @property
    def GOOGLE_ADS_CLIENT_SECRET(self):
        """Google Ads Client Secret"""
        return os.getenv('GOOGLE_ADS_CLIENT_SECRET')

    @property
    def GOOGLE_ADS_REFRESH_TOKEN(self):
        """Google Ads Refresh Token"""
        return os.getenv('GOOGLE_ADS_REFRESH_TOKEN')

    @property
    def GOOGLE_ADS_CUSTOMER_ID(self):
        """Google Ads Customer ID"""
        return os.getenv('GOOGLE_ADS_CUSTOMER_ID')

    @property
    def GOOGLE_ADS_API_VERSION(self):
        """Google Ads API Version"""
        return os.getenv('GOOGLE_ADS_API_VERSION', 'v15')

    def validate(self, require_ads_api=False):
        """验证配置是否完整"""
        missing = []
        
        # 基础配置验证
        if not self.GOOGLE_API_KEY:
            missing.append('GOOGLE_API_KEY')
        if not self.GOOGLE_CSE_ID:
            missing.append('GOOGLE_CSE_ID')
        
        # Google Ads API 配置验证（可选）
        if require_ads_api:
            if not self.GOOGLE_ADS_DEVELOPER_TOKEN:
                missing.append('GOOGLE_ADS_DEVELOPER_TOKEN')
            if not self.GOOGLE_ADS_CLIENT_ID:
                missing.append('GOOGLE_ADS_CLIENT_ID')
            if not self.GOOGLE_ADS_CLIENT_SECRET:
                missing.append('GOOGLE_ADS_CLIENT_SECRET')
            if not self.GOOGLE_ADS_REFRESH_TOKEN:
                missing.append('GOOGLE_ADS_REFRESH_TOKEN')
            if not self.GOOGLE_ADS_CUSTOMER_ID:
                missing.append('GOOGLE_ADS_CUSTOMER_ID')
            
        if missing:
            error_msg = f"缺少必要的配置项: {', '.join(missing)}\n"
            error_msg += "请参考以下配置方法之一：\n"
            error_msg += "1. 复制 config/.env.template 为 config/.env 并填入API密钥\n"
            error_msg += "2. 设置系统环境变量\n"
            error_msg += "3. 创建 ~/.find_demand/.env 文件\n"
            if require_ads_api:
                error_msg += "4. 运行 python setup_config.py 配置 Google Ads API"
            raise ValueError(error_msg)
        
        return True
    
    def get_google_search_params(self):
        """获取 Google 搜索参数"""
        return {
            'key': self.GOOGLE_API_KEY,
            'cx': self.GOOGLE_CSE_ID
        }
    
    def show_config_status(self):
        """显示配置状态"""
        print("=== 配置状态 ===")
        print(f"Google API Key: {'✓ 已配置' if self.GOOGLE_API_KEY else '✗ 未配置'}")
        print(f"Google CSE ID: {'✓ 已配置' if self.GOOGLE_CSE_ID else '✗ 未配置'}")
        print(f"SERP缓存: {'启用' if self.SERP_CACHE_ENABLED else '禁用'}")
        print(f"缓存时长: {self.SERP_CACHE_DURATION}秒")
        print(f"请求延迟: {self.SERP_REQUEST_DELAY}秒")

# 创建全局配置实例
config = Config()
