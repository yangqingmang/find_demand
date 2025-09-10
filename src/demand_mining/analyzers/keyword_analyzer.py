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
        elif isinstance(data, dict):
            # 处理字典类型数据
            if 'query' in data:
                keywords = [data['query']] if isinstance(data['query'], str) else data['query']
            elif 'keyword' in data:
                keywords = [data['keyword']] if isinstance(data['keyword'], str) else data['keyword']
            else:
                # 尝试获取第一个值作为关键词
                keywords = list(data.values())[:1] if data else []
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
            # 基础分析
            basic_analysis = {'length': len(keyword), 'word_count': len(keyword.split()),
                              'language': self._detect_language(keyword),
                              'keyword_type': self._classify_keyword_type(keyword),
                              'difficulty_estimate': self._estimate_difficulty(keyword),
                              'features': self._extract_features(keyword),
                              'long_tail_score': self._calculate_long_tail_score(keyword),
                              'is_long_tail': len(keyword.split()) >= 3 and len(keyword) >= 15}
            
            # 添加长尾词评分

            results[keyword] = basic_analysis
        
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
        """估算关键词难度（优化长尾词评估）"""
        word_count = len(keyword.split())
        keyword_lower = keyword.lower()
        
        # 基于词数的基础难度
        if word_count >= 5:
            base_difficulty = 'very_easy'
        elif word_count >= 4:
            base_difficulty = 'easy'
        elif word_count == 3:
            base_difficulty = 'medium'
        else:
            base_difficulty = 'hard'
        
        # 基于竞争词汇调整难度
        high_competition_words = ['best', 'top', 'review', 'vs', 'comparison']
        medium_competition_words = ['free', 'online', 'tool', 'software']
        low_competition_words = ['tutorial', 'guide', 'how to', 'step by step', 'beginner']
        
        if any(word in keyword_lower for word in high_competition_words):
            # 高竞争词提升难度
            if base_difficulty == 'very_easy':
                return 'easy'
            elif base_difficulty == 'easy':
                return 'medium'
            elif base_difficulty == 'medium':
                return 'hard'
            else:
                return 'very_hard'
        elif any(word in keyword_lower for word in low_competition_words):
            # 低竞争词降低难度
            if base_difficulty == 'hard':
                return 'medium'
            elif base_difficulty == 'medium':
                return 'easy'
            else:
                return base_difficulty
        
        return base_difficulty
    
    def _extract_features(self, keyword: str) -> List[str]:
        """提取关键词特征（增强长尾词识别）"""
        features = []
        keyword_lower = keyword.lower()
        word_count = len(keyword.split())
        
        # 长尾词特征
        if word_count >= 5:
            features.append('very_long_tail')
        elif word_count >= 4:
            features.append('long_tail')
        elif word_count >= 3:
            features.append('medium_tail')
        else:
            features.append('short_tail')
        
        # 意图明确性特征
        high_intent_phrases = ['how to', 'step by step', 'tutorial', 'guide', 'without']
        if any(phrase in keyword_lower for phrase in high_intent_phrases):
            features.append('high_intent')
        
        # 竞争度特征
        high_competition_words = ['best', 'top', 'review', 'vs', 'comparison']
        if any(word in keyword_lower for word in high_competition_words):
            features.append('high_competition')
        
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
    
    def _calculate_long_tail_score(self, keyword: str) -> float:
        """
        计算长尾词评分
        
        Args:
            keyword: 关键词
            
        Returns:
            长尾词评分
        """
        word_count = len(keyword.split())
        keyword_lower = keyword.lower()
        
        base_score = 1.0
        
        # 基于词数的评分加权
        if word_count >= 5:
            base_score *= 3.0
        elif word_count >= 4:
            base_score *= 2.5
        elif word_count >= 3:
            base_score *= 2.0
        
        # 基于意图明确性的加权
        high_intent_phrases = ['how to', 'step by step', 'tutorial', 'guide', 'without']
        if any(phrase in keyword_lower for phrase in high_intent_phrases):
            base_score *= 1.5
        
        # 基于竞争度的调整
        high_competition_words = ['best', 'top', 'review', 'vs', 'comparison']
        if any(comp in keyword_lower for comp in high_competition_words):
            base_score *= 0.7
        
        return round(base_score, 2)