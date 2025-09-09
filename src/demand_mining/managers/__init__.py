#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
需求挖掘管理器模块
"""

from .base_manager import BaseManager
from .keyword_manager import KeywordManager
from .discovery_manager import DiscoveryManager
from .trend_manager import TrendManager
from .task_manager import TaskManager

__all__ = [
    'BaseManager',
    'KeywordManager', 
    'DiscoveryManager',
    'TrendManager',
    'TaskManager'
]