#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势收集器单例模式
避免创建多个TrendsCollector实例导致的429错误
"""

from typing import Optional
from .trends_collector import TrendsCollector

# 全局变量存储单例实例
_trends_collector_instance: Optional[TrendsCollector] = None

def get_trends_collector() -> TrendsCollector:
    """
    获取趋势收集器单例实例
    
    返回:
        TrendsCollector: 趋势收集器实例
    """
    global _trends_collector_instance
    
    import logging
    logger = logging.getLogger(__name__)
    
    if _trends_collector_instance is None:
        # 简单单例模式，无锁
        _trends_collector_instance = TrendsCollector()
        logger.info("🆕 创建新的TrendsCollector实例")
    else:
        logger.info("♻️ 复用现有的TrendsCollector实例")
    
    return _trends_collector_instance

def reset_trends_collector():
    """
    重置趋势收集器实例（主要用于测试）
    """
    global _trends_collector_instance
    
    if _trends_collector_instance is not None:
        # 如果有清理方法，在这里调用
        if hasattr(_trends_collector_instance, 'close'):
            _trends_collector_instance.close()
    _trends_collector_instance = None
