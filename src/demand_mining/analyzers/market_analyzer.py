#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
市场分析器
用于分析关键词的市场数据和商业价值
"""

from .base_analyzer import BaseAnalyzer
from typing import Dict, Any, List
import pandas as pd

class MarketAnalyzer(BaseAnalyzer):
    """市场分析器类"""
    
    def __init__(self):
        """初始化市场分析器"""
        super().__init__()
        
    def analyze(self, data, **kwargs):
        """
        实现基础分析器的抽象方法
        
        Args:
            data: 关键词数据
            **kwargs: 其他参数
            
        Returns:
            分析结果
        """
        return self.analyze_market_data(data)
    
    def analyze_market_data(self, keywords: List[str]) -> Dict[str, Any]:
        """
        分析关键词市场数据
        
        Args:
            keywords: 关键词列表
            
        Returns:
            市场分析结果
        """
        results = {}
        
        for keyword in keywords:
            results[keyword] = {
                'search_volume': self._estimate_search_volume(keyword),
                'competition': self._estimate_competition(keyword),
                'cpc': self._estimate_cpc(keyword),
                'trend': self._analyze_trend(keyword),
                'commercial_intent': self._analyze_commercial_intent(keyword)
            }
        
        return results
    
    def _estimate_search_volume(self, keyword: str) -> int:
        """估算搜索量"""
        keyword_lower = keyword.lower()
        base_volume = 1500

        # AI、模型或热门品牌相关的关键词通常搜索量更高
        if any(token in keyword_lower for token in ['ai', 'gpt', 'bypass', 'undetectable']):
            base_volume *= 2.2

        # 工具类关键词搜索量偏高
        tool_keywords = ['generator', 'converter', 'editor', 'maker', 'assistant', 'humanizer']
        if any(tool in keyword_lower for tool in tool_keywords):
            base_volume *= 1.4

        # 含有定价/方案/服务等词通常关注度更高
        monetization_terms = ['price', 'pricing', 'plan', 'plans', 'premium', 'login', 'account', 'service', 'subscription']
        if any(term in keyword_lower for term in monetization_terms):
            base_volume *= 1.2

        # 长尾关键词适度下调搜索量，不再过度惩罚
        if len(keyword_lower.split()) > 3:
            base_volume *= 0.75

        return max(int(base_volume), 200)


    def _estimate_competition(self, keyword: str) -> float:
        """估算竞争度（0-1之间）"""
        # 基础竞争度
        competition = 0.5
        
        # 热门关键词竞争度高
        hot_keywords = ['ai', 'generator', 'free', 'online']
        if any(hot in keyword.lower() for hot in hot_keywords):
            competition += 0.2
        
        # 长尾关键词竞争度低
        if len(keyword.split()) > 3:
            competition -= 0.2
        
        return max(0.1, min(0.9, competition))
    
    def _estimate_cpc(self, keyword: str) -> float:
        """估算每次点击成本"""
        # 基础CPC
        cpc = 1.0
        
        # 商业关键词CPC较高
        commercial_keywords = ['buy', 'price', 'cost', 'purchase']
        if any(comm in keyword.lower() for comm in commercial_keywords):
            cpc *= 2
        
        # AI工具类CPC中等偏高
        if 'ai' in keyword.lower():
            cpc *= 1.5
        
        return round(cpc, 2)
    
    def _analyze_trend(self, keyword: str) -> str:
        """分析关键词趋势"""
        # AI相关关键词趋势上升
        if 'ai' in keyword.lower():
            return 'rising'
        
        # 传统关键词趋势稳定
        return 'stable'
    
    def _analyze_commercial_intent(self, keyword: str) -> float:
        """分析商业意图强度（0-1之间）"""
        commercial_score = 0.3  # 基础分数
        
        # 购买意图关键词
        buy_keywords = ['buy', 'purchase', 'price', 'cost', 'cheap']
        if any(buy in keyword.lower() for buy in buy_keywords):
            commercial_score += 0.4
        
        # 工具类关键词有一定商业价值
        tool_keywords = ['generator', 'converter', 'editor', 'maker']
        if any(tool in keyword.lower() for tool in tool_keywords):
            commercial_score += 0.3
        
        return min(1.0, commercial_score)