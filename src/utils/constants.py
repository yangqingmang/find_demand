#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目常量定义模块
定义项目中使用的各种常量和配置
"""

from typing import Dict, Any

# 默认配置
DEFAULT_CONFIG: Dict[str, Any] = {
    # 分析参数
    'timeframe': 'today 3-m',      # 默认时间范围
    'geo': '',                     # 默认地区（全球）
    'min_score': 10,               # 最低评分过滤
    'output_dir': 'data',          # 输出目录
    
    # 评分权重
    'volume_weight': 0.4,          # 搜索量权重
    'growth_weight': 0.4,          # 增长率权重
    'kd_weight': 0.2,              # 关键词难度权重
    
    # 高分关键词阈值
    'high_score_threshold': 70,
    
    # API配置
    'request_timeout': 30,         # 请求超时时间（秒）
    'retry_attempts': 3,           # 重试次数
    'retry_delay': 2,              # 重试延迟（秒）
    
    # 输出配置
    'save_intermediate_results': True,  # 是否保存中间结果
    'generate_charts': False,           # 是否生成图表
    'export_formats': ['csv', 'json'],  # 导出格式
}

# 地区代码映射
GEO_CODES: Dict[str, str] = {
    '全球': '',
    '美国': 'US',
    '英国': 'GB',
    '加拿大': 'CA',
    '澳大利亚': 'AU',
    '德国': 'DE',
    '法国': 'FR',
    '日本': 'JP',
    '韩国': 'KR',
    '中国': 'CN',
    '印度': 'IN',
    '巴西': 'BR',
    '墨西哥': 'MX',
    '南非': 'ZA',
    '俄罗斯': 'RU',
    '意大利': 'IT',
    '西班牙': 'ES',
}

# 时间范围选项
TIMEFRAME_OPTIONS: Dict[str, str] = {
    '过去1个月': 'today 1-m',
    '过去3个月': 'today 3-m',
    '过去6个月': 'today 6-m',
    '过去12个月': 'today 12-m',
    '过去2年': 'today 2-y',
    '过去5年': 'today 5-y',
}

# 搜索意图类型
INTENT_TYPES: Dict[str, str] = {
    'I': '信息型',     # Informational
    'N': '导航型',     # Navigational
    'C': '商业型',     # Commercial
    'E': '交易型',     # Transactional
    'B': '行为型'      # Behavioral
}

# 搜索意图详细描述
INTENT_DESCRIPTIONS: Dict[str, str] = {
    'I': '信息型 (Informational) - 用户寻求信息和知识',
    'N': '导航型 (Navigational) - 用户寻找特定网站或页面',
    'C': '商业型 (Commercial) - 用户进行产品或服务调研',
    'E': '交易型 (Transactional) - 用户准备购买或执行操作',
    'B': '行为型 (Behavioral) - 用户寻求解决问题或故障排除'
}

# 评分等级
SCORE_GRADES: Dict[str, Dict[str, Any]] = {
    'S': {'min': 90, 'color': '⭐', 'desc': '卓越'},
    'A': {'min': 80, 'color': '🟢', 'desc': '优秀'},
    'B': {'min': 60, 'color': '🟡', 'desc': '良好'},
    'C': {'min': 40, 'color': '🟠', 'desc': '一般'},
    'D': {'min': 20, 'color': '🔴', 'desc': '较差'},
    'F': {'min': 0, 'color': '⚫', 'desc': '很差'}
}

# 意图关键词词典
INTENT_KEYWORDS: Dict[str, list] = {
    'I': [
        'what', 'how', 'why', 'when', 'where', 'who', 'which', 
        'guide', 'tutorial', 'learn', 'example', 'explain', 'meaning',
        '什么', '如何', '为什么', '怎么', '教程', '学习', '示例', '解释', '意思'
    ],
    'N': [
        'login', 'signin', 'download', 'official', 'website', 'app', 'install',
        'account', 'dashboard', 'home', 'page', 'site', 'portal',
        '登录', '下载', '官网', '官方', '应用', '安装', '账号', '主页'
    ],
    'C': [
        'best', 'top', 'review', 'compare', 'vs', 'versus', 'alternative',
        'comparison', 'difference', 'better', 'pricing', 'features', 'pros', 'cons',
        '最佳', '评测', '对比', '比较', '替代', '区别', '价格', '功能', '优点', '缺点'
    ],
    'E': [
        'buy', 'purchase', 'order', 'coupon', 'discount', 'deal', 'price',
        'cheap', 'free', 'trial', 'subscription', 'template', 'download',
        '购买', '订购', '优惠', '折扣', '价格', '便宜', '免费', '试用', '订阅', '模板'
    ],
    'B': [
        'error', 'fix', 'issue', 'problem', 'bug', 'not working', 'help',
        'support', 'troubleshoot', 'update', 'upgrade', 'integration', 'api',
        '错误', '修复', '问题', '故障', '不工作', '帮助', '支持', '故障排除', '更新', '升级', '集成'
    ]
}

# 推荐行动映射
RECOMMENDED_ACTIONS: Dict[str, str] = {
    'I': '创建教程、指南或信息图表',
    'N': '优化登录/下载页面，提高加载速度',
    'C': '创建对比页面或评测内容',
    'E': '优化购买流程，添加促销信息',
    'B': '提供故障排除指南或支持文档'
}

# API相关常量
API_CONSTANTS = {
    'GOOGLE_SEARCH_BASE_URL': 'https://www.googleapis.com/customsearch/v1',
    'DEFAULT_SEARCH_RESULTS': 10,
    'MAX_SEARCH_RESULTS': 10,  # Google API限制
    'DEFAULT_REQUEST_DELAY': 1.0,  # 秒
    'DEFAULT_CACHE_DURATION': 3600,  # 秒
}

# 文件相关常量
FILE_CONSTANTS = {
    'DEFAULT_ENCODING': 'utf-8-sig',
    'BACKUP_DIR': 'backups',
    'CACHE_DIR': 'cache',
    'LOG_DIR': 'logs',
    'SUPPORTED_FORMATS': ['csv', 'json', 'xlsx'],
}

# 数据验证常量
VALIDATION_CONSTANTS = {
    'MIN_SCORE_RANGE': (0, 100),
    'WEIGHT_SUM_TOLERANCE': 0.01,
    'MIN_KEYWORD_LENGTH': 1,
    'MAX_KEYWORD_LENGTH': 100,
    'MAX_KEYWORDS_BATCH': 50,
}


def get_score_grade(score: float) -> tuple:
    """
    根据分数获取等级信息
    
    参数:
        score (float): 分数
        
    返回:
        tuple: (等级, 等级信息字典)
    """
    for grade, info in SCORE_GRADES.items():
        if score >= info['min']:
            return grade, info
    return 'F', SCORE_GRADES['F']


def get_geo_code(geo_name: str) -> str:
    """
    根据地区名称获取地区代码
    
    参数:
        geo_name (str): 地区名称
        
    返回:
        str: 地区代码，未找到时返回空字符串
    """
    return GEO_CODES.get(geo_name, '')


def get_timeframe_code(timeframe_name: str) -> str:
    """
    根据时间范围名称获取代码
    
    参数:
        timeframe_name (str): 时间范围名称
        
    返回:
        str: 时间范围代码，未找到时返回默认值
    """
    return TIMEFRAME_OPTIONS.get(timeframe_name, DEFAULT_CONFIG['timeframe'])


def get_intent_description(intent_code: str) -> str:
    """
    根据意图代码获取描述
    
    参数:
        intent_code (str): 意图代码
        
    返回:
        str: 意图描述
    """
    return INTENT_DESCRIPTIONS.get(intent_code, f'未知意图: {intent_code}')


def get_recommended_action(intent_code: str) -> str:
    """
    根据意图代码获取推荐行动
    
    参数:
        intent_code (str): 意图代码
        
    返回:
        str: 推荐行动
    """
    return RECOMMENDED_ACTIONS.get(intent_code, '创建综合内容')


def validate_weights(volume_weight: float, growth_weight: float, kd_weight: float) -> bool:
    """
    验证权重配置是否合理
    
    参数:
        volume_weight (float): 搜索量权重
        growth_weight (float): 增长率权重
        kd_weight (float): 关键词难度权重
        
    返回:
        bool: 权重配置是否合理
    """
    total_weight = volume_weight + growth_weight + kd_weight
    tolerance = VALIDATION_CONSTANTS['WEIGHT_SUM_TOLERANCE']
    return abs(total_weight - 1.0) <= tolerance


def validate_score(score: float) -> bool:
    """
    验证分数是否在有效范围内
    
    参数:
        score (float): 分数
        
    返回:
        bool: 分数是否有效
    """
    min_score, max_score = VALIDATION_CONSTANTS['MIN_SCORE_RANGE']
    return min_score <= score <= max_score