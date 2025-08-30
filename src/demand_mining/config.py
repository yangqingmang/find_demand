#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
需求挖掘配置文件
"""

import os
from typing import Dict, Any

# 基础配置
BASE_CONFIG = {
    # 分析参数
    'min_search_volume': 100,           # 最小搜索量
    'max_competition': 0.8,             # 最大竞争度
    'min_confidence': 0.7,              # 最小置信度
    'opportunity_threshold': 70,         # 机会分数阈值
    
    # 输出配置
    'output_formats': ['csv', 'json', 'md'],
    'max_results_per_report': 1000,
    'enable_charts': True,
    
    # 数据源配置
    'data_sources': {
        'google_trends': True,
        'keyword_planner': False,  # 需要API密钥
        'ahrefs': False,          # 需要API密钥
        'semrush': False,         # 需要API密钥
        'serp_api': True          # SERP API 已配置
    },
    
    # 分析深度
    'analysis_depth': 'standard',  # basic, standard, deep
    
    # 意图分析配置
    'intent_config': {
        'use_serp_analysis': True,   # 是否使用SERP分析
        'confidence_threshold': 0.6,
        'enable_secondary_intent': True,
        'intent_weights': {
            'I': 1.0,  # 信息型
            'C': 1.2,  # 商业型
            'E': 1.5,  # 交易型
            'N': 0.8,  # 导航型
            'B': 1.1,  # 行为型
            'L': 1.0   # 本地型
        }
    },
    
    # 市场分析配置
    'market_config': {
        'trend_analysis_days': 90,
        'competitor_analysis': True,
        'seasonality_detection': True,
        'price_analysis': True
    },
    
    # 报告配置
    'report_config': {
        'daily_report': True,
        'weekly_report': True,
        'monthly_report': True,
        'auto_email': False,
        'email_recipients': [],
        'include_charts': True,
        'chart_types': ['bar', 'line', 'pie']
    },
    
    # 缓存配置
    'cache_config': {
        'enable_cache': True,
        'cache_duration_hours': 24,
        'cache_directory': 'cache'
    }
}

# API配置 (需要用户自行配置)
API_CONFIG = {
    'google_ads': {
        'developer_token': os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN'),
        'client_id': os.getenv('GOOGLE_ADS_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_ADS_CLIENT_SECRET'),
        'refresh_token': os.getenv('GOOGLE_ADS_REFRESH_TOKEN'),
        'customer_id': os.getenv('GOOGLE_ADS_CUSTOMER_ID')
    },
    
    'ahrefs': {
        'api_token': os.getenv('AHREFS_API_TOKEN')
    },
    
    'semrush': {
        'api_key': os.getenv('SEMRUSH_API_KEY')
    },
    
    'serp_api': {
        'api_key': os.getenv('SERPAPI_KEY')
    }
}

# 关键词分类配置 (优化版本 - 加入垂直细分领域)
KEYWORD_CATEGORIES = {
    'ai_tools': {
        'keywords': ['ai', 'artificial intelligence', 'machine learning', 'chatgpt', 'claude'],
        'priority': 'high',
        'intent_bias': 'C',  # 偏向商业意图
        'niche_score': 85    # 垂直细分评分
    },
    
    'tutorials': {
        'keywords': ['how to', 'tutorial', 'guide', 'learn'],
        'priority': 'medium',
        'intent_bias': 'I',  # 偏向信息意图
        'niche_score': 60
    },
    
    'products': {
        'keywords': ['buy', 'price', 'cost', 'purchase', 'deal'],
        'priority': 'high',
        'intent_bias': 'E',  # 偏向交易意图
        'niche_score': 70
    },
    
    'comparisons': {
        'keywords': ['vs', 'compare', 'best', 'top', 'review'],
        'priority': 'high',
        'intent_bias': 'C',  # 偏向商业意图
        'niche_score': 75
    },
    
    # 新增垂直细分领域
    'fintech': {
        'keywords': ['blockchain', 'defi', 'crypto', 'nft', 'web3', 'dao'],
        'priority': 'high',
        'intent_bias': 'C',
        'niche_score': 90    # 高垂直细分评分
    },
    
    'healthtech': {
        'keywords': ['telemedicine', 'digital health', 'wearable', 'biotech'],
        'priority': 'high',
        'intent_bias': 'C',
        'niche_score': 88
    },
    
    'edtech': {
        'keywords': ['online learning', 'e-learning', 'mooc', 'lms'],
        'priority': 'medium',
        'intent_bias': 'I',
        'niche_score': 82
    },
    
    'saas_tools': {
        'keywords': ['crm', 'erp', 'automation', 'workflow', 'api'],
        'priority': 'high',
        'intent_bias': 'C',
        'niche_score': 85
    },
    
    'emerging_tech': {
        'keywords': ['quantum', 'ar', 'vr', 'iot', 'edge computing'],
        'priority': 'high',
        'intent_bias': 'I',
        'niche_score': 95    # 最高垂直细分评分
    }
}

# 意图描述
INTENT_DESCRIPTIONS = {
    'I': '信息获取 - 用户寻求知识、定义、教程等信息',
    'C': '商业评估 - 用户比较产品、服务，寻求推荐',
    'E': '交易购买 - 用户准备购买产品或服务',
    'N': '导航直达 - 用户寻找特定网站或页面',
    'B': '行为后续 - 用户需要解决问题或完成任务',
    'L': '本地到店 - 用户寻找本地服务或实体店'
}

# 机会评分权重 (最终优化版本 - 加入新词、垂直细分和意图深度权重)
OPPORTUNITY_WEIGHTS = {
    'search_volume': 0.20,      # 搜索量权重 (再次降低)
    'competition': 0.12,        # 竞争度权重 (降低)
    'intent_confidence': 0.12,  # 意图置信度权重 (降低)
    'trend': 0.10,             # 趋势权重 (降低)
    'new_word_bonus': 0.18,     # 新词权重 (保持高权重)
    'intent_depth': 0.12,       # 用户意图深度权重 (新增 - 重要!)
    'niche_vertical': 0.10,     # 垂直细分领域权重 (保持)
    'cpc': 0.06,               # 每次点击成本权重 (降低)
    'seasonality': 0.05        # 季节性权重 (保持)
}

def get_config() -> Dict[str, Any]:
    """获取完整配置"""
    config = BASE_CONFIG.copy()
    config['api'] = API_CONFIG
    config['categories'] = KEYWORD_CATEGORIES
    config['intent_descriptions'] = INTENT_DESCRIPTIONS
    config['opportunity_weights'] = OPPORTUNITY_WEIGHTS
    return config

def validate_config(config: Dict[str, Any]) -> bool:
    """验证配置有效性"""
    required_keys = ['min_search_volume', 'analysis_depth', 'intent_config']
    
    for key in required_keys:
        if key not in config:
            print(f"❌ 配置错误: 缺少必需的配置项 '{key}'")
            return False
    
    # 验证分析深度
    if config['analysis_depth'] not in ['basic', 'standard', 'deep']:
        print("❌ 配置错误: analysis_depth 必须是 'basic', 'standard' 或 'deep'")
        return False
    
    print("✅ 配置验证通过")
    return True

def load_user_config(config_path: str) -> Dict[str, Any]:
    """加载用户自定义配置"""
    config = get_config()
    
    if os.path.exists(config_path):
        try:
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                config.update(user_config)
                print(f"✅ 已加载用户配置: {config_path}")
        except Exception as e:
            print(f"⚠️ 加载用户配置失败: {e}")
    
    return config


class DemandMiningConfig:
    """需求挖掘配置类"""
    
    def __init__(self, config_path: str = None):
        """初始化配置"""
        if config_path:
            self.config = load_user_config(config_path)
        else:
            self.config = get_config()
    
    def get(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)
    
    def get_nested(self, *keys, default=None):
        """获取嵌套配置项"""
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    @property
    def min_search_volume(self) -> int:
        """最小搜索量"""
        return self.config.get('min_search_volume', 100)
    
    @property
    def max_competition(self) -> float:
        """最大竞争度"""
        return self.config.get('max_competition', 0.8)
    
    @property
    def opportunity_threshold(self) -> int:
        """机会分数阈值"""
        return self.config.get('opportunity_threshold', 70)
    
    @property
    def intent_config(self) -> Dict[str, Any]:
        """意图分析配置"""
        return self.config.get('intent_config', {})
    
    @property
    def opportunity_weights(self) -> Dict[str, float]:
        """机会评分权重"""
        return self.config.get('opportunity_weights', OPPORTUNITY_WEIGHTS)
    
    @property
    def intent_descriptions(self) -> Dict[str, str]:
        """意图描述"""
        return self.config.get('intent_descriptions', INTENT_DESCRIPTIONS)

if __name__ == '__main__':
    # 测试配置
    config = get_config()
    if validate_config(config):
        print("🎉 配置测试通过!")
        print(f"当前分析深度: {config['analysis_depth']}")
        print(f"支持的数据源: {list(config['data_sources'].keys())}")