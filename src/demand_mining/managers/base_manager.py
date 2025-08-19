#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础管理器 - 所有管理器的基类
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod


class BaseManager(ABC):
    """基础管理器抽象类"""
    
    def __init__(self, config_path: str = None):
        """初始化基础管理器"""
        self.config = self._load_config(config_path)
        self.output_dir = "src/demand_mining/reports"
        self._ensure_output_dirs()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            'min_search_volume': 100,
            'max_competition': 0.8,
            'min_confidence': 0.7,
            'output_formats': ['csv', 'json'],
            'data_sources': ['google_trends', 'keyword_planner'],
            'analysis_depth': 'standard'
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _ensure_output_dirs(self):
        """确保输出目录存在"""
        dirs = [
            self.output_dir,
            os.path.join(self.output_dir, 'daily_reports'),
            os.path.join(self.output_dir, 'weekly_reports'),
            os.path.join(self.output_dir, 'monthly_reports'),
            os.path.join(self.output_dir, 'keyword_analysis'),
            os.path.join(self.output_dir, 'intent_analysis'),
            os.path.join(self.output_dir, 'market_analysis')
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def save_results(self, results: Dict[str, Any], output_dir: str = None, 
                    filename_prefix: str = None) -> str:
        """保存分析结果"""
        if not output_dir:
            output_dir = self.output_dir
        
        if not filename_prefix:
            filename_prefix = self.__class__.__name__.lower().replace('manager', '')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存JSON格式
        json_path = os.path.join(output_dir, f'{filename_prefix}_{timestamp}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return json_path
    
    @abstractmethod
    def analyze(self, *args, **kwargs) -> Dict[str, Any]:
        """抽象分析方法，子类必须实现"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息"""
        return {
            'manager_type': self.__class__.__name__,
            'config': self.config,
            'output_dir': self.output_dir
        }