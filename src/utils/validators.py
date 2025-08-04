#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证工具模块
提供各种数据验证功能
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
from .constants import (
    VALIDATION_CONSTANTS, GEO_CODES, TIMEFRAME_OPTIONS, 
    INTENT_TYPES, validate_weights, validate_score
)
from .exceptions import ValidationError


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_keywords(keywords: Union[str, List[str]]) -> List[str]:
        """
        验证关键词列表
        
        参数:
            keywords: 关键词或关键词列表
            
        返回:
            List[str]: 验证后的关键词列表
            
        异常:
            ValidationError: 关键词验证失败
        """
        if isinstance(keywords, str):
            keywords = [keywords]
        
        if not keywords:
            raise ValidationError("关键词列表不能为空")
        
        validated_keywords = []
        min_len = VALIDATION_CONSTANTS['MIN_KEYWORD_LENGTH']
        max_len = VALIDATION_CONSTANTS['MAX_KEYWORD_LENGTH']
        max_batch = VALIDATION_CONSTANTS['MAX_KEYWORDS_BATCH']
        
        for keyword in keywords:
            if not isinstance(keyword, str):
                raise ValidationError(f"关键词必须是字符串类型: {keyword}")
            
            keyword = keyword.strip()
            if not keyword:
                continue
                
            if len(keyword) < min_len:
                raise ValidationError(f"关键词长度不能少于{min_len}个字符: {keyword}")
            
            if len(keyword) > max_len:
                raise ValidationError(f"关键词长度不能超过{max_len}个字符: {keyword}")
            
            validated_keywords.append(keyword)
        
        if not validated_keywords:
            raise ValidationError("没有有效的关键词")
        
        if len(validated_keywords) > max_batch:
            raise ValidationError(f"关键词数量不能超过{max_batch}个")
        
        return validated_keywords
    
    @staticmethod
    def validate_geo_code(geo: str) -> str:
        """
        验证地区代码
        
        参数:
            geo (str): 地区代码或名称
            
        返回:
            str: 验证后的地区代码
            
        异常:
            ValidationError: 地区代码验证失败
        """
        if not geo:
            return ''  # 空字符串表示全球
        
        # 如果是地区名称，转换为代码
        if geo in GEO_CODES:
            return GEO_CODES[geo]
        
        # 如果是地区代码，验证是否有效
        if geo in GEO_CODES.values():
            return geo
        
        raise ValidationError(f"无效的地区代码或名称: {geo}")
    
    @staticmethod
    def validate_timeframe(timeframe: str) -> str:
        """
        验证时间范围
        
        参数:
            timeframe (str): 时间范围代码或名称
            
        返回:
            str: 验证后的时间范围代码
            
        异常:
            ValidationError: 时间范围验证失败
        """
        if not timeframe:
            raise ValidationError("时间范围不能为空")
        
        # 如果是时间范围名称，转换为代码
        if timeframe in TIMEFRAME_OPTIONS:
            return TIMEFRAME_OPTIONS[timeframe]
        
        # 如果是时间范围代码，验证是否有效
        if timeframe in TIMEFRAME_OPTIONS.values():
            return timeframe
        
        raise ValidationError(f"无效的时间范围: {timeframe}")
    
    @staticmethod
    def validate_scoring_weights(volume_weight: float, growth_weight: float, 
                               kd_weight: float) -> tuple:
        """
        验证评分权重
        
        参数:
            volume_weight (float): 搜索量权重
            growth_weight (float): 增长率权重
            kd_weight (float): 关键词难度权重
            
        返回:
            tuple: 验证后的权重元组
            
        异常:
            ValidationError: 权重验证失败
        """
        # 检查权重类型
        for weight, name in [(volume_weight, '搜索量权重'), 
                           (growth_weight, '增长率权重'), 
                           (kd_weight, '关键词难度权重')]:
            if not isinstance(weight, (int, float)):
                raise ValidationError(f"{name}必须是数值类型")
            
            if weight < 0 or weight > 1:
                raise ValidationError(f"{name}必须在0-1范围内: {weight}")
        
        # 检查权重总和
        if not validate_weights(volume_weight, growth_weight, kd_weight):
            total = volume_weight + growth_weight + kd_weight
            raise ValidationError(f"权重总和必须为1.0，当前为{total:.3f}")
        
        return volume_weight, growth_weight, kd_weight
    
    @staticmethod
    def validate_score_range(min_score: Optional[int] = None, 
                           max_score: Optional[int] = None) -> tuple:
        """
        验证分数范围
        
        参数:
            min_score (int, optional): 最低分数
            max_score (int, optional): 最高分数
            
        返回:
            tuple: (min_score, max_score)
            
        异常:
            ValidationError: 分数范围验证失败
        """
        score_min, score_max = VALIDATION_CONSTANTS['MIN_SCORE_RANGE']
        
        if min_score is not None:
            if not isinstance(min_score, int):
                raise ValidationError("最低分数必须是整数")
            
            if not validate_score(min_score):
                raise ValidationError(f"最低分数必须在{score_min}-{score_max}范围内: {min_score}")
        
        if max_score is not None:
            if not isinstance(max_score, int):
                raise ValidationError("最高分数必须是整数")
            
            if not validate_score(max_score):
                raise ValidationError(f"最高分数必须在{score_min}-{score_max}范围内: {max_score}")
        
        if min_score is not None and max_score is not None:
            if min_score > max_score:
                raise ValidationError(f"最低分数不能大于最高分数: {min_score} > {max_score}")
        
        return min_score, max_score
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, required_columns: List[str] = None) -> pd.DataFrame:
        """
        验证DataFrame
        
        参数:
            df (pd.DataFrame): 要验证的DataFrame
            required_columns (List[str]): 必需的列名列表
            
        返回:
            pd.DataFrame: 验证后的DataFrame
            
        异常:
            ValidationError: DataFrame验证失败
        """
        if not isinstance(df, pd.DataFrame):
            raise ValidationError("输入必须是pandas DataFrame")
        
        if df.empty:
            raise ValidationError("DataFrame不能为空")
        
        if required_columns:
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                raise ValidationError(f"缺少必需的列: {missing_columns}")
        
        return df
    
    @staticmethod
    def validate_intent_code(intent: str) -> str:
        """
        验证意图代码
        
        参数:
            intent (str): 意图代码
            
        返回:
            str: 验证后的意图代码
            
        异常:
            ValidationError: 意图代码验证失败
        """
        if not isinstance(intent, str):
            raise ValidationError("意图代码必须是字符串")
        
        intent = intent.upper().strip()
        
        if intent not in INTENT_TYPES:
            valid_intents = ', '.join(INTENT_TYPES.keys())
            raise ValidationError(f"无效的意图代码: {intent}，有效值: {valid_intents}")
        
        return intent
    
    @staticmethod
    def validate_file_path(file_path: str, must_exist: bool = False) -> str:
        """
        验证文件路径
        
        参数:
            file_path (str): 文件路径
            must_exist (bool): 文件是否必须存在
            
        返回:
            str: 验证后的文件路径
            
        异常:
            ValidationError: 文件路径验证失败
        """
        if not isinstance(file_path, str):
            raise ValidationError("文件路径必须是字符串")
        
        file_path = file_path.strip()
        if not file_path:
            raise ValidationError("文件路径不能为空")
        
        if must_exist:
            import os
            if not os.path.exists(file_path):
                raise ValidationError(f"文件不存在: {file_path}")
        
        return file_path
    
    @staticmethod
    def validate_output_format(formats: Union[str, List[str]]) -> List[str]:
        """
        验证输出格式
        
        参数:
            formats: 输出格式或格式列表
            
        返回:
            List[str]: 验证后的格式列表
            
        异常:
            ValidationError: 输出格式验证失败
        """
        from .constants import FILE_CONSTANTS
        
        if isinstance(formats, str):
            formats = [formats]
        
        if not formats:
            raise ValidationError("输出格式不能为空")
        
        supported_formats = FILE_CONSTANTS['SUPPORTED_FORMATS']
        validated_formats = []
        
        for fmt in formats:
            if not isinstance(fmt, str):
                raise ValidationError(f"输出格式必须是字符串: {fmt}")
            
            fmt = fmt.lower().strip()
            if fmt not in supported_formats:
                raise ValidationError(f"不支持的输出格式: {fmt}，支持的格式: {supported_formats}")
            
            if fmt not in validated_formats:
                validated_formats.append(fmt)
        
        return validated_formats


class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_analysis_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证分析配置
        
        参数:
            config (dict): 配置字典
            
        返回:
            dict: 验证后的配置
            
        异常:
            ValidationError: 配置验证失败
        """
        validated_config = config.copy()
        
        # 验证关键词
        if 'keywords' in config:
            validated_config['keywords'] = DataValidator.validate_keywords(config['keywords'])
        
        # 验证地区代码
        if 'geo' in config:
            validated_config['geo'] = DataValidator.validate_geo_code(config['geo'])
        
        # 验证时间范围
        if 'timeframe' in config:
            validated_config['timeframe'] = DataValidator.validate_timeframe(config['timeframe'])
        
        # 验证权重
        if all(key in config for key in ['volume_weight', 'growth_weight', 'kd_weight']):
            weights = DataValidator.validate_scoring_weights(
                config['volume_weight'], 
                config['growth_weight'], 
                config['kd_weight']
            )
            validated_config['volume_weight'] = weights[0]
            validated_config['growth_weight'] = weights[1]
            validated_config['kd_weight'] = weights[2]
        
        # 验证分数范围
        if 'min_score' in config:
            min_score, _ = DataValidator.validate_score_range(config['min_score'])
            validated_config['min_score'] = min_score
        
        # 验证输出格式
        if 'export_formats' in config:
            validated_config['export_formats'] = DataValidator.validate_output_format(
                config['export_formats']
            )
        
        return validated_config
    
    @staticmethod
    def validate_api_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证API配置
        
        参数:
            config (dict): API配置字典
            
        返回:
            dict: 验证后的配置
            
        异常:
            ValidationError: API配置验证失败
        """
        validated_config = config.copy()
        
        # 验证API密钥
        if 'api_key' in config:
            api_key = config['api_key']
            if not isinstance(api_key, str) or not api_key.strip():
                raise ValidationError("API密钥不能为空")
            validated_config['api_key'] = api_key.strip()
        
        # 验证超时时间
        if 'timeout' in config:
            timeout = config['timeout']
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                raise ValidationError("超时时间必须是正数")
            validated_config['timeout'] = timeout
        
        # 验证重试次数
        if 'retries' in config:
            retries = config['retries']
            if not isinstance(retries, int) or retries < 0:
                raise ValidationError("重试次数必须是非负整数")
            validated_config['retries'] = retries
        
        return validated_config


# 便捷验证函数
def validate_analysis_params(keywords: Union[str, List[str]], geo: str = '', 
                           timeframe: str = 'today 3-m', **kwargs) -> Dict[str, Any]:
    """
    验证分析参数的便捷函数
    
    参数:
        keywords: 关键词
        geo: 地区代码
        timeframe: 时间范围
        **kwargs: 其他参数
        
    返回:
        dict: 验证后的参数字典
    """
    params = {
        'keywords': keywords,
        'geo': geo,
        'timeframe': timeframe,
        **kwargs
    }
    
    return ConfigValidator.validate_analysis_config(params)