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
    
    import logging
    logger = logging.getLogger(__name__)
    
    if _trends_collector_instance is None:
        with _lock:
            # 双重检查锁定模式
            if _trends_collector_instance is None:
                _trends_collector_instance = CustomTrendsCollector()
            else:
                logger.info("🔄 使用已存在的CustomTrendsCollector实例（双重检查）")
    else:
        logger.info("♻️ 复用现有的CustomTrendsCollector实例")
    
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