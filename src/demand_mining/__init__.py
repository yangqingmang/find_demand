#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
需求挖掘模块 - 重构版
提供统一的需求挖掘和关键词分析功能
"""

from .unified_main import UnifiedDemandMiningManager
from .managers import KeywordManager, DiscoveryManager, TrendManager

__version__ = "2.0.0"
__author__ = "CodeBuddy"

# 导出主要类
__all__ = [
    'UnifiedDemandMiningManager',
    'KeywordManager',
    'DiscoveryManager', 
    'TrendManager'
]

# 提供简化的导入接口
DemandMiningManager = UnifiedDemandMiningManager