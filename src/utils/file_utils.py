#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件操作工具模块
提供统一的文件保存、读取等功能
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path


class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def ensure_dir(directory: str) -> str:
        """
        确保目录存在
        
        参数:
            directory (str): 目录路径
            
        返回:
            str: 目录路径
        """
        os.makedirs(directory, exist_ok=True)
        return directory
    
    @staticmethod
    def get_date_str(format_str: str = '%Y-%m-%d') -> str:
        """
        获取当前日期字符串
        
        参数:
            format_str (str): 日期格式字符串
            
        返回:
            str: 格式化的日期字符串
        """
        return datetime.now().strftime(format_str)
    
    @staticmethod
    def save_dataframe(df: pd.DataFrame, output_dir: str, filename: str, 
                      encoding: str = 'utf-8-sig', index: bool = False) -> str:
        """
        保存DataFrame到CSV文件
        
        参数:
            df (pd.DataFrame): 要保存的DataFrame
            output_dir (str): 输出目录
            filename (str): 文件名
            encoding (str): 编码格式
            index (bool): 是否保存索引
            
        返回:
            str: 保存的文件路径
        """
        FileUtils.ensure_dir(output_dir)
        file_path = os.path.join(output_dir, filename)
        df.to_csv(file_path, index=index, encoding=encoding)
        return file_path
    
    @staticmethod
    def save_json(data: Dict[str, Any], output_dir: str, filename: str, 
                  ensure_ascii: bool = False, indent: int = 2) -> str:
        """
        保存数据到JSON文件
        
        参数:
            data (dict): 要保存的数据
            output_dir (str): 输出目录
            filename (str): 文件名
            ensure_ascii (bool): 是否确保ASCII编码
            indent (int): 缩进空格数
            
        返回:
            str: 保存的文件路径
        """
        FileUtils.ensure_dir(output_dir)
        file_path = os.path.join(output_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
        return file_path
    
    @staticmethod
    def load_json(file_path: str) -> Optional[Dict[str, Any]]:
        """
        从JSON文件加载数据
        
        参数:
            file_path (str): 文件路径
            
        返回:
            dict: 加载的数据，失败时返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    @staticmethod
    def load_dataframe(file_path: str, encoding: str = 'utf-8-sig') -> Optional[pd.DataFrame]:
        """
        从CSV文件加载DataFrame
        
        参数:
            file_path (str): 文件路径
            encoding (str): 编码格式
            
        返回:
            pd.DataFrame: 加载的DataFrame，失败时返回None
        """
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except Exception:
            return None
    
    @staticmethod
    def generate_filename(prefix: str, suffix: str = '', extension: str = 'csv', 
                         include_date: bool = True) -> str:
        """
        生成标准化的文件名
        
        参数:
            prefix (str): 文件名前缀
            suffix (str): 文件名后缀
            extension (str): 文件扩展名
            include_date (bool): 是否包含日期
            
        返回:
            str: 生成的文件名
        """
        parts = [prefix]
        
        if suffix:
            parts.append(suffix)
            
        if include_date:
            parts.append(FileUtils.get_date_str())
        
        filename = '_'.join(parts)
        return f"{filename}.{extension}"
    
    @staticmethod
    def save_analysis_results(df: pd.DataFrame, summary: Dict[str, Any], 
                            output_dir: str, prefix: str) -> Dict[str, str]:
        """
        保存分析结果（DataFrame + 摘要）
        
        参数:
            df (pd.DataFrame): 分析结果DataFrame
            summary (dict): 分析摘要
            output_dir (str): 输出目录
            prefix (str): 文件名前缀
            
        返回:
            dict: 保存的文件路径映射
        """
        saved_files = {}
        
        # 保存主要结果
        csv_filename = FileUtils.generate_filename(prefix, extension='csv')
        csv_path = FileUtils.save_dataframe(df, output_dir, csv_filename)
        saved_files['main_results'] = csv_path
        
        # 保存摘要
        json_filename = FileUtils.generate_filename(prefix, 'summary', 'json')
        json_path = FileUtils.save_json(summary, output_dir, json_filename)
        saved_files['summary'] = json_path
        
        return saved_files
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """
        清理文件名，移除特殊字符
        
        参数:
            filename (str): 原始文件名
            
        返回:
            str: 清理后的文件名
        """
        # 替换特殊字符为下划线
        import re
        clean_name = re.sub(r'[^\w\-_.]', '_', filename)
        # 移除多余的下划线
        clean_name = re.sub(r'_+', '_', clean_name)
        return clean_name.strip('_')
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        获取文件大小（字节）
        
        参数:
            file_path (str): 文件路径
            
        返回:
            int: 文件大小，文件不存在时返回0
        """
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    @staticmethod
    def backup_file(file_path: str, backup_dir: str = None) -> Optional[str]:
        """
        备份文件
        
        参数:
            file_path (str): 要备份的文件路径
            backup_dir (str): 备份目录，None时使用原目录
            
        返回:
            str: 备份文件路径，失败时返回None
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            # 确定备份目录
            if backup_dir is None:
                backup_dir = os.path.dirname(file_path)
            else:
                FileUtils.ensure_dir(backup_dir)
            
            # 生成备份文件名
            base_name = os.path.basename(file_path)
            name, ext = os.path.splitext(base_name)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{name}_backup_{timestamp}{ext}"
            backup_path = os.path.join(backup_dir, backup_name)
            
            # 复制文件
            import shutil
            shutil.copy2(file_path, backup_path)
            
            return backup_path
            
        except Exception:
            return None