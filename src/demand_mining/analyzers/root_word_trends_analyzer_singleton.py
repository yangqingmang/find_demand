#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
词根趋势分析器单例模式
避免创建多个RootWordTrendsAnalyzer实例导致的429错误
"""

import threading
from typing import Optional

# 全局变量存储单例实例
_root_word_trends_analyzer_instance: Optional['RootWordTrendsAnalyzer'] = None
_lock = threading.Lock()

def get_root_word_trends_analyzer(output_dir: str = "data/root_word_trends") -> 'RootWordTrendsAnalyzer':
    """
    获取词根趋势分析器单例实例
    
    Args:
        output_dir: 输出目录
        
    Returns:
        RootWordTrendsAnalyzer: 词根趋势分析器实例
    """
    global _root_word_trends_analyzer_instance
    
    if _root_word_trends_analyzer_instance is None:
        with _lock:
            # 双重检查锁定模式
            if _root_word_trends_analyzer_instance is None:
                from ..root_word_trends_analyzer import RootWordTrendsAnalyzer
                _root_word_trends_analyzer_instance = RootWordTrendsAnalyzer(output_dir)
    
    return _root_word_trends_analyzer_instance

def reset_root_word_trends_analyzer():
    """
    重置词根趋势分析器实例（主要用于测试）
    """
    global _root_word_trends_analyzer_instance
    
    with _lock:
        if _root_word_trends_analyzer_instance is not None:
            # 如果有清理方法，在这里调用
            if hasattr(_root_word_trends_analyzer_instance, 'close'):
                _root_word_trends_analyzer_instance.close()
        _root_word_trends_analyzer_instance = None