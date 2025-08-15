#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块初始化文件
提供常用工具和常量
"""

from .logger import setup_logger, Logger
from .file_utils import ensure_directory_exists
from .exceptions import APIError, ExceptionHandler

# 默认配置
DEFAULT_CONFIG = {
    'timeout': 30,
    'retries': 3,
    'cache_duration': 3600
}

# 验证常量
VALIDATION_CONSTANTS = {
    'min_keyword_length': 2,
    'max_keyword_length': 100
}

# 意图类型常量
INTENT_TYPES = {
    'informational': '信息型',
    'navigational': '导航型',
    'transactional': '交易型',
    'commercial': '商业型',
    'local': '本地型',
    'brand': '品牌型',
    'educational': '教育型',
    'entertainment': '娱乐型'
}

# 搜索意图映射
SEARCH_INTENT_MAPPING = {
    'what': 'informational',
    'how': 'informational',
    'why': 'informational',
    'when': 'informational',
    'where': 'local',
    'buy': 'transactional',
    'purchase': 'transactional',
    'price': 'commercial',
    'cost': 'commercial',
    'review': 'commercial',
    'best': 'commercial',
    'top': 'commercial',
    'compare': 'commercial',
    'vs': 'commercial',
    'near me': 'local',
    'login': 'navigational',
    'download': 'navigational',
    'tutorial': 'educational',
    'guide': 'educational',
    'learn': 'educational'
}

# 意图关键词映射
INTENT_KEYWORDS = {
    'informational': [
        'what', 'how', 'why', 'when', 'where', 'who', 'which',
        'explain', 'definition', 'meaning', 'guide', 'tutorial',
        'learn', 'understand', 'know', 'information', 'about'
    ],
    'navigational': [
        'login', 'sign in', 'homepage', 'website', 'official',
        'download', 'app', 'portal', 'dashboard', 'account'
    ],
    'transactional': [
        'buy', 'purchase', 'order', 'shop', 'cart', 'checkout',
        'payment', 'subscribe', 'register', 'signup', 'book'
    ],
    'commercial': [
        'price', 'cost', 'cheap', 'expensive', 'discount', 'deal',
        'review', 'compare', 'best', 'top', 'vs', 'alternative',
        'recommendation', 'rating', 'evaluation'
    ],
    'local': [
        'near me', 'nearby', 'location', 'address', 'directions',
        'hours', 'open', 'close', 'contact', 'phone', 'local'
    ],
    'brand': [
        'brand name', 'company', 'official', 'authentic', 'genuine',
        'original', 'trademark', 'logo', 'corporate'
    ],
    'educational': [
        'tutorial', 'course', 'lesson', 'training', 'education',
        'learn', 'study', 'teach', 'instruction', 'guide',
        'example', 'demo', 'practice'
    ],
    'entertainment': [
        'fun', 'game', 'play', 'entertainment', 'funny', 'joke',
        'video', 'music', 'movie', 'show', 'stream'
    ]
}

# 推荐行动映射
RECOMMENDED_ACTIONS = {
    'informational': {
        'content_type': 'educational_content',
        'seo_strategy': 'long_tail_keywords',
        'content_format': ['blog_posts', 'guides', 'tutorials', 'faqs'],
        'optimization': 'answer_questions'
    },
    'navigational': {
        'content_type': 'brand_content',
        'seo_strategy': 'brand_keywords',
        'content_format': ['landing_pages', 'homepage', 'about_page'],
        'optimization': 'brand_visibility'
    },
    'transactional': {
        'content_type': 'product_content',
        'seo_strategy': 'conversion_keywords',
        'content_format': ['product_pages', 'checkout_pages', 'pricing'],
        'optimization': 'conversion_rate'
    },
    'commercial': {
        'content_type': 'comparison_content',
        'seo_strategy': 'commercial_keywords',
        'content_format': ['reviews', 'comparisons', 'buying_guides'],
        'optimization': 'purchase_intent'
    },
    'local': {
        'content_type': 'local_content',
        'seo_strategy': 'local_seo',
        'content_format': ['location_pages', 'contact_info', 'directions'],
        'optimization': 'local_visibility'
    },
    'brand': {
        'content_type': 'brand_content',
        'seo_strategy': 'brand_protection',
        'content_format': ['official_pages', 'brand_story', 'testimonials'],
        'optimization': 'brand_authority'
    },
    'educational': {
        'content_type': 'learning_content',
        'seo_strategy': 'educational_keywords',
        'content_format': ['courses', 'tutorials', 'workshops', 'webinars'],
        'optimization': 'knowledge_sharing'
    },
    'entertainment': {
        'content_type': 'engaging_content',
        'seo_strategy': 'viral_keywords',
        'content_format': ['videos', 'games', 'interactive_content'],
        'optimization': 'engagement_rate'
    }
}

# 意图描述映射
INTENT_DESCRIPTIONS = {
    'I': '信息型搜索',
    'N': '导航型搜索',
    'T': '交易型搜索',
    'C': '商业型搜索',
    'L': '本地型搜索',
    'B': '品牌型搜索',
    'E': '教育型搜索',
    'EN': '娱乐型搜索'
}

# 数据错误异常类
class DataError(Exception):
    """数据相关的错误异常"""
    pass

# 推荐行动获取函数
def get_recommended_action(intent):
    """
    根据意图获取推荐行动
    
    参数:
        intent (str): 意图代码
        
    返回:
        str: 推荐行动描述
    """
    intent_mapping = {
        'I': 'informational',
        'N': 'navigational', 
        'T': 'transactional',
        'C': 'commercial',
        'L': 'local',
        'B': 'brand',
        'E': 'educational',
        'EN': 'entertainment'
    }
    
    full_intent = intent_mapping.get(intent, 'informational')
    action = RECOMMENDED_ACTIONS.get(full_intent, {})
    
    if action:
        return f"内容类型: {action.get('content_type', '未知')}, SEO策略: {action.get('seo_strategy', '未知')}"
    else:
        return "创建相关内容以满足用户需求"

# 文件工具类（兼容性）
class FileUtils:
    @staticmethod
    def generate_filename(base_name, extension='json'):
        from .file_utils import generate_filename
        return generate_filename(base_name, extension)
    
    @staticmethod
    def clean_filename(filename):
        from .file_utils import clean_filename
        return clean_filename(filename)
    
    @staticmethod
    def save_dataframe(df, output_dir, filename):
        from .file_utils import save_dataframe
        return save_dataframe(df, output_dir, filename)

# 导出所有工具类
__all__ = [
    'setup_logger',
    'Logger',
    'ensure_directory_exists',
    'APIError',
    'ExceptionHandler',
    'FileUtils',
    'DEFAULT_CONFIG',
    'VALIDATION_CONSTANTS',
    'INTENT_TYPES',
    'SEARCH_INTENT_MAPPING',
    'INTENT_KEYWORDS',
    'RECOMMENDED_ACTIONS',
    'INTENT_DESCRIPTIONS',
    'DataError',
    'get_recommended_action'
]
