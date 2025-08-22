#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件工具模块
提供文件操作相关的工具函数
"""

import os
import re
import csv
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

def ensure_directory_exists(directory_path: str) -> str:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory_path: 目录路径
        
    Returns:
        创建或确认存在的目录路径
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)
    return directory_path

def clean_filename(filename: str) -> str:
    """
    清理文件名，移除不允许的字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    # 替换不允许的字符为下划线
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def generate_filename(base_name: str, extension: str = 'json') -> str:
    """
    生成带时间戳的文件名
    
    Args:
        base_name: 基础文件名
        extension: 文件扩展名（不含点）
        
    Returns:
        生成的文件名
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{clean_filename(base_name)}_{timestamp}.{extension}"

def save_dataframe(df: pd.DataFrame, output_dir: str, filename: str) -> str:
    """
    保存DataFrame到CSV文件
    
    Args:
        df: 要保存的DataFrame
        output_dir: 输出目录
        filename: 文件名
        
    Returns:
        保存的文件路径
    """
    ensure_directory_exists(output_dir)
    file_path = os.path.join(output_dir, filename)
    
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    return file_path

def load_json(file_path: str) -> Dict:
    """
    加载JSON文件
    
    Args:
        file_path: JSON文件路径
        
    Returns:
        加载的JSON数据
    """
    if not os.path.exists(file_path):
        return {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data: Dict, file_path: str) -> str:
    """
    保存数据到JSON文件
    
    Args:
        data: 要保存的数据
        file_path: 文件路径
        
    Returns:
        保存的文件路径
    """
    ensure_directory_exists(os.path.dirname(file_path))
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return file_path

def save_results_with_timestamp(results: Dict, output_dir: str, file_prefix: str) -> str:
    """
    保存结果到带时间戳的JSON文件
    
    Args:
        results: 要保存的结果数据
        output_dir: 输出目录
        file_prefix: 文件名前缀
        
    Returns:
        保存的文件路径
    """
    ensure_directory_exists(output_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = os.path.join(output_dir, f'{file_prefix}_{timestamp}.json')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return file_path