#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于搜索意图的网站自动建设工具 - 工具函数
"""

import os
import json
import pandas as pd
from typing import Dict, List, Tuple, Set, Optional, Any, Union

def ensure_dir(directory: str) -> None:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory: 目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

def load_data_file(file_path: str) -> Optional[pd.DataFrame]:
    """
    加载数据文件（CSV或JSON）
    
    Args:
        file_path: 文件路径
    
    Returns:
        DataFrame对象，如果加载失败则返回None
    """
    try:
        # 根据文件扩展名决定加载方式
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.csv':
            # 加载CSV文件
            return pd.read_csv(file_path)
        elif ext == '.json':
            # 加载JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 转换为DataFrame
            if isinstance(data, list):
                return pd.DataFrame(data)
            else:
                return pd.DataFrame([data])
        else:
            print(f"错误: 不支持的文件格式: {ext}")
            return None
            
    except Exception as e:
        print(f"加载数据文件失败: {e}")
        return None

def save_json_file(data: Any, file_path: str) -> bool:
    """
    保存数据到JSON文件
    
    Args:
        data: 要保存的数据
        file_path: 文件路径
    
    Returns:
        是否成功保存
    """
    try:
        # 确保目录存在
        ensure_dir(os.path.dirname(file_path))
        
        # 保存到JSON文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        print(f"保存JSON文件失败: {e}")
        return False

def get_intent_description(intent: str, intent_descriptions: Dict[str, str]) -> str:
    """
    获取意图的描述
    
    Args:
        intent: 意图代码
        intent_descriptions: 意图描述字典
    
    Returns:
        意图描述
    """
    return intent_descriptions.get(intent, intent)

def generate_url_slug(text: str) -> str:
    """
    生成URL友好的slug
    
    Args:
        text: 原始文本
    
    Returns:
        URL友好的slug
    """
    # 转换为小写
    slug = text.lower()
    
    # 替换空格为连字符
    slug = slug.replace(' ', '-')
    
    # 移除特殊字符
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    
    # 移除多余的连字符
    while '--' in slug:
        slug = slug.replace('--', '-')
    
    # 移除开头和结尾的连字符
    slug = slug.strip('-')
    
    return slug

def format_date(date_str: str, input_format: str = '%Y-%m-%d', output_format: str = '%Y年%m月%d日') -> str:
    """
    格式化日期字符串
    
    Args:
        date_str: 日期字符串
        input_format: 输入格式
        output_format: 输出格式
    
    Returns:
        格式化后的日期字符串
    """
    from datetime import datetime
    
    try:
        date_obj = datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except Exception:
        return date_str

def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀
    
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def count_words(text: str) -> int:
    """
    计算文本中的单词数
    
    Args:
        text: 文本
    
    Returns:
        单词数
    """
    # 简单的单词计数方法，适用于中英文混合文本
    # 对于中文，每个字符算一个单词
    # 对于英文，按空格分隔计算单词数
    
    # 移除多余的空白字符
    text = ' '.join(text.split())
    
    # 计算中文字符数
    chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    
    # 计算英文单词数
    english_text = ''.join(c for c in text if not '\u4e00' <= c <= '\u9fff')
    english_count = len(english_text.split())
    
    return chinese_count + english_count

def get_file_extension(file_path: str) -> str:
    """
    获取文件扩展名
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件扩展名（包含点号）
    """
    return os.path.splitext(file_path)[1]

def is_valid_file_type(file_path: str, allowed_extensions: List[str]) -> bool:
    """
    检查文件类型是否有效
    
    Args:
        file_path: 文件路径
        allowed_extensions: 允许的扩展名列表
    
    Returns:
        文件类型是否有效
    """
    ext = get_file_extension(file_path).lower()
    return ext in allowed_extensions