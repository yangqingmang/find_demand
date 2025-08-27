#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势收集器单例模式
避免创建多个TrendsCollector实例导致的429错误
"""

import threading
from typing import Optional
from .custom_trends_collector import CustomTrendsCollector

# 全局变量存储单例实例
_trends_collector_instance: Optional[CustomTrendsCollector] = None
_lock = threading.Lock()

def get_trends_collector() -> CustomTrendsCollector:
    """
    获取趋势收集器单例实例
    
    返回:
        CustomTrendsCollector: 趋势收集器实例
    """
    global _trends_collector_instance
    
    if _trends_collector_instance is None:
        with _lock:
            # 双重检查锁定模式
            if _trends_collector_instance is None:
                _trends_collector_instance = CustomTrendsCollector()
    
    return _trends_collector_instance

def reset_trends_collector():
    """
    重置趋势收集器实例（主要用于测试）
    """
    global _trends_collector_instance
    
    with _lock:
        if _trends_collector_instance is not None:
            # 如果有清理方法，在这里调用
            if hasattr(_trends_collector_instance, 'close'):
                _trends_collector_instance.close()
        _trends_collector_instance = None