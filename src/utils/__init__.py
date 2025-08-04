#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块 - Utilities
包含辅助函数等通用工具

注意: 配置管理已迁移到 src/config/settings.py
"""

# 导入所有工具类和函数
from .logger import Logger, default_logger, log, info, warning, error, debug, safe_print
from .file_utils import FileUtils
from .exceptions import (
    FindDemandError, ConfigError, APIError, DataError, ValidationError,
    FileOperationError, AnalysisError, handle_exceptions, ExceptionHandler
)
from .constants import (
    DEFAULT_CONFIG, GEO_CODES, TIMEFRAME_OPTIONS, INTENT_TYPES, 
    INTENT_DESCRIPTIONS, SCORE_GRADES, INTENT_KEYWORDS, RECOMMENDED_ACTIONS,
    API_CONSTANTS, FILE_CONSTANTS, VALIDATION_CONSTANTS,
    get_score_grade, get_geo_code, get_timeframe_code, get_intent_description,
    get_recommended_action, validate_weights, validate_score
)
from .validators import DataValidator, ConfigValidator, validate_analysis_params
from .mock_data_generator import MockDataGenerator, generate_mock_ads_data, generate_mock_complete_dataset

# 导出的公共接口
__all__ = [
    # 日志相关
    'Logger', 'default_logger', 'log', 'info', 'warning', 'error', 'debug', 'safe_print',
    
    # 文件操作
    'FileUtils',
    
    # 异常处理
    'FindDemandError', 'ConfigError', 'APIError', 'DataError', 'ValidationError',
    'FileOperationError', 'AnalysisError', 'handle_exceptions', 'ExceptionHandler',
    
    # 常量
    'DEFAULT_CONFIG', 'GEO_CODES', 'TIMEFRAME_OPTIONS', 'INTENT_TYPES',
    'INTENT_DESCRIPTIONS', 'SCORE_GRADES', 'INTENT_KEYWORDS', 'RECOMMENDED_ACTIONS',
    'API_CONSTANTS', 'FILE_CONSTANTS', 'VALIDATION_CONSTANTS',
    
    # 工具函数
    'get_score_grade', 'get_geo_code', 'get_timeframe_code', 'get_intent_description',
    'get_recommended_action', 'validate_weights', 'validate_score',
    
    # 验证器
    'DataValidator', 'ConfigValidator', 'validate_analysis_params',
    
    # 模拟数据生成器
    'MockDataGenerator', 'generate_mock_ads_data', 'generate_mock_complete_dataset',
]
