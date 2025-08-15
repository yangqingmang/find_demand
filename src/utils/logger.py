#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志工具模块
提供统一的日志记录功能
"""

import os
import logging
from datetime import datetime
from typing import Optional

def setup_logger(name: str = None, level: str = "INFO") -> logging.Logger:
    """
    设置并返回一个日志记录器
    
    Args:
        name: 日志记录器名称，默认为None（使用root logger）
        level: 日志级别，默认为INFO
        
    Returns:
        配置好的日志记录器
    """
    # 转换日志级别字符串为logging常量
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    log_level = level_map.get(level.upper(), logging.INFO)
    
    # 获取或创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 如果已经有处理器，不再添加
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(console_handler)
    
    return logger

class Logger:
    """简化版日志记录器类，兼容现有代码"""
    
    def __init__(self, name: str = None):
        self.logger = setup_logger(name)
    
    def info(self, message: str):
        """记录信息级别日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """记录警告级别日志"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录错误级别日志"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """记录调试级别日志"""
        self.logger.debug(message)