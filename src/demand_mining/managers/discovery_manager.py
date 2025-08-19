#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发现管理器 - 负责多平台关键词发现功能
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from .base_manager import BaseManager


class DiscoveryManager(BaseManager):
    """多平台关键词发现管理器"""
    
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self._discoverer = None
        print("🔍 发现管理器初始化完成")
    
    @property
    def discoverer(self):
        """延迟加载多平台发现工具"""
        if self._discoverer is None:
            try:
                from src.demand_mining.tools.multi_platform_keyword_discovery import MultiPlatformKeywordDiscovery
                self._discoverer = MultiPlatformKeywordDiscovery()
            except ImportError as e:
                print(f"⚠️ 无法导入多平台发现工具: {e}")
                self._discoverer = None
        return self._discoverer
    
    def analyze(self, search_terms: List[str], output_dir: str = None) -> Dict[str, Any]:
        """
        执行多平台关键词发现
        
        Args:
            search_terms: 搜索词列表
            output_dir: 输出目录
            
        Returns:
            发现结果
        """
        print(f"🔍 开始多平台关键词发现...")
        print(f"📊 搜索词汇: {', '.join(search_terms)}")
        
        if self.discoverer is None:
            return {
                'error': '多平台发现工具不可用',
                'total_keywords': 0,
                'platform_distribution': {},
                'top_keywords_by_score': []
            }
        
        try:
            # 执行发现
            df = self.discoverer.discover_all_platforms(search_terms)
            
            if not df.empty:
                # 分析趋势
                analysis = self.discoverer.analyze_keyword_trends(df)
                
                # 保存结果
                if output_dir:
                    csv_path, json_path = self.discoverer.save_results(df, analysis, output_dir)
                    analysis['output_files'] = {
                        'csv': csv_path,
                        'json': json_path
                    }
                
                analysis['search_terms'] = search_terms
                analysis['discovery_time'] = datetime.now().isoformat()
                
                return analysis
            else:
                return {
                    'message': '未发现任何关键词',
                    'total_keywords': 0,
                    'platform_distribution': {},
                    'top_keywords_by_score': [],
                    'search_terms': search_terms,
                    'discovery_time': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ 多平台关键词发现失败: {e}")
            return {
                'error': f'发现失败: {str(e)}',
                'total_keywords': 0,
                'platform_distribution': {},
                'top_keywords_by_score': [],
                'search_terms': search_terms,
                'discovery_time': datetime.now().isoformat()
            }
    
    def discover_from_platforms(self, search_terms: List[str], 
                               platforms: List[str] = None) -> Dict[str, Any]:
        """
        从指定平台发现关键词
        
        Args:
            search_terms: 搜索词列表
            platforms: 平台列表，如果为None则使用所有平台
            
        Returns:
            发现结果
        """
        if self.discoverer is None:
            return {'error': '多平台发现工具不可用'}
        
        # 这里可以扩展为支持指定平台的发现
        # 目前使用默认的所有平台发现
        return self.analyze(search_terms)
    
    def get_supported_platforms(self) -> List[str]:
        """获取支持的平台列表"""
        if self.discoverer is None:
            return []
        
        # 返回支持的平台列表
        return [
            'Reddit',
            'Hacker News', 
            'YouTube',
            'Google Suggestions',
            'Twitter',
            'ProductHunt'
        ]
    
    def get_discovery_stats(self) -> Dict[str, Any]:
        """获取发现统计信息"""
        stats = self.get_stats()
        stats.update({
            'supported_platforms': self.get_supported_platforms(),
            'discoverer_available': self.discoverer is not None
        })
        return stats