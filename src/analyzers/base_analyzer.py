#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础分析器类 - 提供通用的分析器功能
"""

import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from src.utils import FileUtils, Logger


class BaseAnalyzer(ABC):
    """基础分析器抽象类，提供通用功能"""
    
    def __init__(self):
        """初始化基础分析器"""
        self.logger = Logger()
    
    @abstractmethod
    def analyze(self, data, **kwargs):
        """
        抽象分析方法，子类必须实现
        
        参数:
            data: 要分析的数据
            **kwargs: 其他参数
            
        返回:
            分析结果
        """
        pass
    
    def save_results(self, df: pd.DataFrame, output_dir: str = 'data', 
                    prefix: str = 'analysis', summary: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        统一的结果保存方法
        
        参数:
            df: 要保存的DataFrame
            output_dir: 输出目录
            prefix: 文件名前缀
            summary: 可选的摘要数据
            
        返回:
            保存的文件路径字典
        """
        saved_files = {}
        
        if df.empty:
            self.logger.warning("没有数据可保存")
            return saved_files
        
        try:
            # 保存主要结果
            main_filename = FileUtils.generate_filename(prefix, extension='csv')
            main_path = FileUtils.save_dataframe(df, output_dir, main_filename)
            saved_files['main_results'] = main_path
            self.logger.info(f"已保存主要结果到: {main_path}")
            
            # 保存摘要（如果提供）
            if summary:
                summary_filename = FileUtils.generate_filename(f'{prefix}_summary', extension='json')
                summary_path = FileUtils.save_json(summary, output_dir, summary_filename)
                saved_files['summary'] = summary_path
                self.logger.info(f"已保存摘要到: {summary_path}")
            
            return saved_files
            
        except Exception as e:
            self.logger.error(f"保存结果失败: {e}")
            return saved_files
    
    def validate_input(self, data, required_columns: list = None) -> bool:
        """
        验证输入数据
        
        参数:
            data: 要验证的数据
            required_columns: 必需的列名列表
            
        返回:
            验证是否通过
        """
        if data is None:
            self.logger.error("输入数据为空")
            return False
        
        if isinstance(data, pd.DataFrame):
            if data.empty:
                self.logger.warning("输入DataFrame为空")
                return False
            
            if required_columns:
                missing_columns = [col for col in required_columns if col not in data.columns]
                if missing_columns:
                    self.logger.error(f"缺少必需的列: {missing_columns}")
                    return False
        
        return True
    
    def log_analysis_start(self, analysis_type: str, data_info: str = ""):
        """记录分析开始"""
        self.logger.info(f"开始{analysis_type}分析{data_info}")
    
    def log_analysis_complete(self, analysis_type: str, result_count: int = 0):
        """记录分析完成"""
        if result_count > 0:
            self.logger.info(f"{analysis_type}分析完成，处理了 {result_count} 条记录")
        else:
            self.logger.info(f"{analysis_type}分析完成")