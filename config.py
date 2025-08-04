#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场需求分析工具 - 配置文件
"""

# 默认配置
DEFAULT_CONFIG = {
    # 分析参数
    'timeframe': 'today 3-m',  # 默认时间范围
    'geo': '',  # 默认地区（全球）
    'min_score': 10,  # 最低评分过滤
    'output_dir': 'data',  # 输出目录
    
    # 评分权重
    'volume_weight': 0.4,  # 搜索量权重
    'growth_weight': 0.4,  # 增长率权重
    'kd_weight': 0.2,  # 关键词难度权重
    
    # 高分关键词阈值
    'high_score_threshold': 70,
    
    # API配置
    'request_timeout': 30,  # 请求超时时间（秒）
    'retry_attempts': 3,  # 重试次数
    'retry_delay': 2,  # 重试延迟（秒）
    
    # 输出配置
    'save_intermediate_results': True,  # 是否保存中间结果
    'generate_charts': False,  # 是否生成图表（需要matplotlib）
    'export_formats': ['csv', 'json'],  # 导出格式
}

# 地区代码映射
GEO_CODES = {
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
}

# 时间范围选项
TIMEFRAME_OPTIONS = {
    '过去1个月': 'today 1-m',
    '过去3个月': 'today 3-m',
    '过去12个月': 'today 12-m',
    '过去5年': 'today 5-y',
}

# 搜索意图类型
INTENT_TYPES = {
    'I': '信息型 (Informational)',
    'N': '导航型 (Navigational)', 
    'C': '商业型 (Commercial)',
    'E': '交易型 (Transactional)',
    'B': '行为型 (Behavioral)'
}

# 评分等级
SCORE_GRADES = {
    'A': {'min': 80, 'color': '🟢', 'desc': '优秀'},
    'B': {'min': 60, 'color': '🟡', 'desc': '良好'},
    'C': {'min': 40, 'color': '🟠', 'desc': '一般'},
    'D': {'min': 20, 'color': '🔴', 'desc': '较差'},
    'F': {'min': 0, 'color': '⚫', 'desc': '很差'}
}

def get_score_grade(score):
    """根据分数获取等级"""
    for grade, info in SCORE_GRADES.items():
        if score >= info['min']:
            return grade, info
    return 'F', SCORE_GRADES['F']

def get_geo_code(geo_name):
    """根据地区名称获取代码"""
    return GEO_CODES.get(geo_name, geo_name)

def get_timeframe_code(timeframe_name):
    """根据时间范围名称获取代码"""
    return TIMEFRAME_OPTIONS.get(timeframe_name, timeframe_name)