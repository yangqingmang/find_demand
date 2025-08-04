#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一日志工具模块
提供项目统一的日志记录功能
"""

import sys
import re
import os
from datetime import datetime
from typing import Optional


class Logger:
    """统一日志记录器"""
    
    def __init__(self, log_file: Optional[str] = None, enable_console: bool = True):
        """
        初始化日志记录器
        
        参数:
            log_file (str, optional): 日志文件路径
            enable_console (bool): 是否输出到控制台
        """
        self.log_file = log_file
        self.enable_console = enable_console
        
        # 如果指定了日志文件，确保目录存在
        if self.log_file:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def log(self, message: str, level: str = "INFO", print_to_console: Optional[bool] = None):
        """
        记录日志
        
        参数:
            message (str): 日志消息
            level (str): 日志级别
            print_to_console (bool, optional): 是否打印到控制台，None时使用默认设置
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"
        
        # 决定是否输出到控制台
        should_print = print_to_console if print_to_console is not None else self.enable_console
        
        if should_print:
            self.safe_print(log_message)
        
        # 写入日志文件
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_message + '\n')
            except Exception as e:
                print(f"写入日志文件失败: {e}")
    
    def info(self, message: str):
        """记录信息级别日志"""
        self.log(message, "INFO")
    
    def warning(self, message: str):
        """记录警告级别日志"""
        self.log(message, "WARNING")
    
    def error(self, message: str):
        """记录错误级别日志"""
        self.log(message, "ERROR")
    
    def debug(self, message: str):
        """记录调试级别日志"""
        self.log(message, "DEBUG")
    
    def safe_print(self, text: str):
        """
        安全的打印函数，处理编码问题
        
        参数:
            text (str): 要打印的文本
        """
        try:
            print(text)
        except UnicodeEncodeError:
            # 如果出现编码错误，移除emoji和特殊字符
            clean_text = re.sub(r'[^\u4e00-\u9fff\u0020-\u007f]', '', text)
            print(clean_text)
    
    def setup_console_encoding(self):
        """设置控制台编码以正确显示中文"""
        if sys.platform.startswith('win'):
            try:
                # Windows系统设置
                import locale
                import codecs
                
                # 设置标准输出编码
                if hasattr(sys.stdout, 'reconfigure'):
                    sys.stdout.reconfigure(encoding='utf-8')
                if hasattr(sys.stderr, 'reconfigure'):
                    sys.stderr.reconfigure(encoding='utf-8')
                
                # 设置控制台代码页为UTF-8
                os.system('chcp 65001 >nul 2>&1')
                
            except Exception:
                # 如果设置失败，使用备用方案
                pass


# 创建全局日志实例
default_logger = Logger()

# 便捷函数
def log(message: str, level: str = "INFO"):
    """便捷的日志记录函数"""
    default_logger.log(message, level)

def info(message: str):
    """记录信息"""
    default_logger.info(message)

def warning(message: str):
    """记录警告"""
    default_logger.warning(message)

def error(message: str):
    """记录错误"""
    default_logger.error(message)

def debug(message: str):
    """记录调试信息"""
    default_logger.debug(message)

def safe_print(text: str):
    """安全打印"""
    default_logger.safe_print(text)