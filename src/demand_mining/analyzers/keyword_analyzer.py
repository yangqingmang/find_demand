#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
关键词分析器
用于分析关键词的基本特征和属性
"""

from .base_analyzer import BaseAnalyzer
from typing import Dict, Any, List
import re

class KeywordAnalyzer(BaseAnalyzer):
    """关键词分析器类"""
    
    def __init__(self):
        """初始化关键词分析器"""
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
        if isinstance(data, list):
            return self.analyze_keywords(data)
        elif hasattr(data, 'iterrows'):  # DataFrame
            keywords = data['query'].tolist() if 'query' in data.columns else data.iloc[:, 0].tolist()
            return self.analyze_keywords(keywords)
        else:
            return {}
    
    def analyze_keywords(self, keywords: List[str]) -> Dict[str, Any]:
        """
        分析关键词列表
        
        Args:
            keywords: 关键词列表
            
        Returns:
            分析结果字典
        """
        results = {}
        
        for keyword in keywords:
            results[keyword] = {
                'length': len(keyword),
                'word_count': len(keyword.split()),
                'language': self._detect_language(keyword),
                'keyword_type': self._classify_keyword_type(keyword),
                'difficulty_estimate': self._estimate_difficulty(keyword),
                'features': self._extract_features(keyword)
            }
        
        return results
    
    def _detect_language(self, keyword: str) -> str:
        """检测关键词语言"""
        # 简单的语言检测
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', keyword)
        if chinese_chars:
            return 'zh'
        else:
            return 'en'
    
    def _classify_keyword_type(self, keyword: str) -> str:
        """分类关键词类型"""
        keyword_lower = keyword.lower()
        
        # 问题类型
        question_words = ['what', 'how', 'why', 'when', 'where', 'who']
        if any(q in keyword_lower for q in question_words):
            return 'question'
        
        # 工具类型
        tool_words = ['generator', 'converter', 'editor', 'maker', 'creator']
        if any(tool in keyword_lower for tool in tool_words):
            return 'tool'
        
        # 信息类型
        info_words = ['guide', 'tutorial', 'tips', 'learn']
        if any(info in keyword_lower for info in info_words):
            return 'informational'
        
        # 商业类型
        commercial_words = ['buy', 'price', 'cost', 'cheap', 'best']
        if any(comm in keyword_lower for comm in commercial_words):
            return 'commercial'
        
        return 'general'
    
    def _estimate_difficulty(self, keyword: str) -> str:
        """估算关键词难度"""
        # 基于关键词特征估算难度
        word_count = len(keyword.split())
        
        # 长尾关键词通常难度较低
        if word_count >= 4:
            return 'easy'
        elif word_count == 3:
            return 'medium'
        else:
            # 短关键词通常难度较高
            return 'hard'
    
    def _extract_features(self, keyword: str) -> List[str]:
        """提取关键词特征"""
        features = []
        keyword_lower = keyword.lower()
        
        # AI相关
        if 'ai' in keyword_lower:
            features.append('ai_related')
        
        # 免费相关
        if 'free' in keyword_lower:
            features.append('free')
        
        # 在线相关
        if 'online' in keyword_lower:
            features.append('online')
        
        # 工具相关
        tool_indicators = ['generator', 'converter', 'editor', 'maker', 'tool']
        if any(tool in keyword_lower for tool in tool_indicators):
            features.append('tool_related')
        
        # 品牌相关
        brand_indicators = ['google', 'microsoft', 'adobe', 'openai']
        if any(brand in keyword_lower for brand in brand_indicators):
            features.append('brand_related')
        
        return features