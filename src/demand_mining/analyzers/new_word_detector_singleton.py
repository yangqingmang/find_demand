#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
新词检测器单例模式
避免创建多个NewWordDetector实例导致的并发请求问题
"""

from typing import Optional

# 全局变量存储单例实例
_new_word_detector_instance: Optional['NewWordDetector'] = None

def get_new_word_detector():
    """
    获取新词检测器单例实例
    
    返回:
        NewWordDetector: 新词检测器实例
    """
    global _new_word_detector_instance
    
    if _new_word_detector_instance is None:
        # 简单单例模式，无锁
        from .new_word_detector import NewWordDetector
        _new_word_detector_instance = NewWordDetector()
    
    return _new_word_detector_instance

def reset_new_word_detector():
    """
    重置新词检测器实例（主要用于测试）
    """
    global _new_word_detector_instance
    
    if _new_word_detector_instance is not None:
        # 如果有清理方法，在这里调用
        if hasattr(_new_word_detector_instance, 'close'):
            _new_word_detector_instance.close()
    _new_word_detector_instance = None
