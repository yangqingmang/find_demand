#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
关键词提取工具 - 增强版
从各种数据源提取和扩展关键词，集成Google自动完成API、相关搜索词挖掘和语义相似词发现
"""

import re
import requests
import json
import time
import random
from typing import List, Dict, Set, Any, Optional
from collections import Counter
import pandas as pd
from urllib.parse import quote_plus
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KeywordExtractor:
    """增强版关键词提取器"""
    
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
        # 初始化Google Trends收集器用于相关搜索
        self.trends_collector = None
        try:
            from src.collectors.custom_trends_collector import CustomTrendsCollector
            self.trends_collector = CustomTrendsCollector()
            logger.info("✅ Google Trends收集器初始化成功")
        except ImportError as e:
            logger.warning(f"⚠️ Google Trends收集器初始化失败: {e}")
        
        # AI工具类别词汇库
        self.ai_tool_categories = {
            'image': ['generator', 'creator', 'maker', 'editor', 'enhancer', 'upscaler'],
            'text': ['writer', 'generator', 'editor', 'translator', 'summarizer', 'paraphraser'],
            'video': ['generator', 'editor', 'creator', 'enhancer', 'converter'],
            'audio': ['generator', 'editor', 'transcriber', 'converter', 'enhancer'],
            'code': ['generator', 'assistant', 'reviewer', 'optimizer', 'debugger'],
            'design': ['generator', 'creator', 'assistant', 'optimizer', 'enhancer']
        }
        
        # 长尾词扩展修饰词库（优化为低竞争、高意图的词汇）
        self.long_tail_modifiers = [
            'how to use', 'step by step guide', 'tutorial for beginners',
            'free alternative to', 'open source version of', 'simple way to create',
            'easy method for', 'complete guide to', 'beginner friendly',
            'without coding', 'for small business', 'budget friendly',
            'quick tutorial on', 'detailed review of', 'comparison between',
            'pros and cons of', 'getting started with', 'tips for using',
            'common mistakes with', 'troubleshooting guide for'
        ]
        
        # 保留原有修饰词作为备用（标记为高竞争）
        self.high_competition_modifiers = [
            'best', 'top', 'review', 'vs', 'comparison'
        ]
        
        # 中等竞争修饰词
        self.medium_competition_modifiers = [
            'free', 'online', 'guide', 'tutorial', 'alternative', 'tool',
            'software', 'app', 'platform', 'service', 'solution', 'api',
            'open source', 'simple', 'easy'
        ]
    
    def get_google_autocomplete_suggestions(self, keyword: str, language: str = 'en', 
                                          country: str = 'us', max_suggestions: int = 10) -> List[str]:
        """
        获取Google自动完成建议
        
        Args:
            keyword: 种子关键词
            language: 语言代码
            country: 国家代码
            max_suggestions: 最大建议数量
            
        Returns:
            自动完成建议列表
        """
        suggestions = []
        
        try:
            # Google自动完成API URL
            url = "http://suggestqueries.google.com/complete/search"
            
            params = {
                'client': 'firefox',
                'q': keyword,
                'hl': language,
                'gl': country
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # 解析JSON响应
                data = response.json()
                if len(data) > 1 and isinstance(data[1], list):
                    suggestions = data[1][:max_suggestions]
                    
            # 过滤和清理建议
            filtered_suggestions = []
            for suggestion in suggestions:
                if isinstance(suggestion, str) and len(suggestion) > len(keyword):
                    # 移除原关键词，只保留扩展部分
                    if suggestion.lower().startswith(keyword.lower()):
                        filtered_suggestions.append(suggestion)
            
            logger.info(f"✅ 获取到 {len(filtered_suggestions)} 个Google自动完成建议: {keyword}")
            return filtered_suggestions[:max_suggestions]
            
        except Exception as e:
            logger.warning(f"⚠️ Google自动完成获取失败 {keyword}: {e}")
            return []
    
    def get_related_search_terms(self, keyword: str, max_terms: int = 10) -> List[str]:
        """
        获取相关搜索词（通过Google Trends）
        
        Args:
            keyword: 种子关键词
            max_terms: 最大相关词数量
            
        Returns:
            相关搜索词列表
        """
        related_terms = []
        
        try:
            if self.trends_collector:
                # 使用Google Trends收集器获取相关搜索
                trends_data = self.trends_collector.collect_trends([keyword])
                
                if trends_data and 'related_queries' in trends_data:
                    for query_data in trends_data['related_queries']:
                        if 'query' in query_data:
                            related_terms.append(query_data['query'])
                
                logger.info(f"✅ 通过Trends获取到 {len(related_terms)} 个相关搜索词: {keyword}")
            else:
                # 备用方案：基于关键词生成相关词
                related_terms = self._generate_related_terms_fallback(keyword, max_terms)
                logger.info(f"✅ 使用备用方案生成 {len(related_terms)} 个相关词: {keyword}")
            
            return related_terms[:max_terms]
            
        except Exception as e:
            logger.warning(f"⚠️ 相关搜索词获取失败 {keyword}: {e}")
            return self._generate_related_terms_fallback(keyword, max_terms)
    
    def _generate_related_terms_fallback(self, keyword: str, max_terms: int = 10) -> List[str]:
        """备用相关词生成方案"""
        related_terms = []
        keyword_lower = keyword.lower()
        
        # 基于AI工具类别生成相关词
        for category, tools in self.ai_tool_categories.items():
            if category in keyword_lower or any(tool in keyword_lower for tool in tools):
                for tool in tools:
                    if tool not in keyword_lower:
                        related_terms.append(f"{keyword} {tool}")
                        related_terms.append(f"{tool} {keyword}")
        
        # 优先使用长尾修饰词生成相关词
        for modifier in self.long_tail_modifiers[:max_terms//2]:
            if modifier not in keyword_lower:
                related_terms.append(f"{modifier} {keyword}")
        
        # 补充中等竞争修饰词
        for modifier in self.medium_competition_modifiers[:max_terms//3]:
            if modifier not in keyword_lower:
                related_terms.append(f"{modifier} {keyword}")
        
        return list(set(related_terms))[:max_terms]
    
    def expand_seed_keywords(self, seed_keywords: List[str], max_per_seed: int = 20) -> Dict[str, List[str]]:
        """
        扩展种子关键词（语义相似词发现）
        
        Args:
            seed_keywords: 种子关键词列表
            max_per_seed: 每个种子词最大扩展数量
            
        Returns:
            按种子词分组的扩展关键词字典
        """
        expanded_keywords = {}
        
        for seed in seed_keywords:
            expanded = set()
            seed_lower = seed.lower()
            
            # 1. 基于AI工具类别扩展
            for category, tools in self.ai_tool_categories.items():
                if category in seed_lower or any(tool in seed_lower for tool in tools):
                    for tool in tools:
                        if tool not in seed_lower:
                            expanded.add(f"{seed} {tool}")
                            expanded.add(f"{tool} for {seed}")
            
            # 2. 优先基于长尾修饰词扩展
            for modifier in self.long_tail_modifiers:
                if modifier not in seed_lower:
                    expanded.add(f"{modifier} {seed}")
                    # 特殊处理教程类修饰词
                    if 'tutorial' in modifier or 'guide' in modifier:
                        expanded.add(f"{modifier} {seed} for beginners")
            
            # 3. 补充中等竞争修饰词
            for modifier in self.medium_competition_modifiers[:5]:  # 限制数量
                if modifier not in seed_lower:
                    expanded.add(f"{modifier} {seed}")
            
            # 4. 基于词汇变形扩展
            if 'generator' in seed_lower:
                expanded.add(seed.replace('generator', 'creator'))
                expanded.add(seed.replace('generator', 'maker'))
            elif 'creator' in seed_lower:
                expanded.add(seed.replace('creator', 'generator'))
                expanded.add(seed.replace('creator', 'maker'))
            
            # 过滤和限制数量（优先长尾词）
            filtered_expanded = []
            for kw in expanded:
                if self._is_long_tail_keyword(kw):
                    filtered_expanded.append(kw)
            
            # 如果长尾词不够，补充中等长度的关键词
            if len(filtered_expanded) < max_per_seed:
                for kw in expanded:
                    if not self._is_long_tail_keyword(kw) and len(kw) > 10 and len(kw) < 100:
                        filtered_expanded.append(kw)
                        if len(filtered_expanded) >= max_per_seed:
                            break
            
            expanded_keywords[seed] = filtered_expanded[:max_per_seed]
            logger.info(f"✅ 语义扩展 {seed}: {len(expanded_keywords[seed])} 个关键词")
        
        return expanded_keywords
    
    def _is_long_tail_keyword(self, keyword: str) -> bool:
        """
        判断是否为长尾关键词
        
        Args:
            keyword: 关键词
            
        Returns:
            是否为长尾关键词
        """
        words = keyword.split()
        # 长尾词标准：3个以上词汇且总长度15个字符以上
        return len(words) >= 3 and len(keyword) >= 15
    
    def calculate_long_tail_score(self, keyword: str) -> float:
        """
        计算长尾词评分（长尾词获得更高分数）
        
        Args:
            keyword: 关键词
            
        Returns:
            评分倍数
        """
        word_count = len(keyword.split())
        keyword_lower = keyword.lower()
        
        base_score = 1.0
        
        # 基于词数的评分加权
        if word_count >= 5:
            base_score *= 2.5  # 5+词汇获得最高加权
        elif word_count >= 4:
            base_score *= 2.0  # 4词汇获得高加权
        elif word_count >= 3:
            base_score *= 1.5  # 3词汇获得中等加权
        
        # 基于意图明确性的加权
        high_intent_phrases = ['how to', 'step by step', 'tutorial', 'guide', 'without']
        if any(phrase in keyword_lower for phrase in high_intent_phrases):
            base_score *= 1.3
        
        # 基于竞争度的调整
        if any(comp in keyword_lower for comp in self.high_competition_modifiers):
            base_score *= 0.7  # 高竞争词降低评分
        elif any(comp in keyword_lower for comp in self.medium_competition_modifiers):
            base_score *= 0.9  # 中等竞争词略微降低评分
        
        return base_score
    
    def analyze_keyword_difficulty(self, keyword: str) -> str:
        """
        分析关键词难度
        
        Args:
            keyword: 关键词
            
        Returns:
            难度等级 (Low/Medium/High)
        """
        keyword_lower = keyword.lower()
        word_count = len(keyword.split())
        
        # 基于词数判断基础难度
        if word_count >= 4:
            base_difficulty = 'Low'
        elif word_count >= 2:
            base_difficulty = 'Medium'
        else:
            base_difficulty = 'High'
        
        # 基于竞争词调整难度
        high_competition_words = ['best', 'top', 'review', 'vs', 'comparison']
        medium_competition_words = ['free', 'online', 'tool', 'software']
        
        if any(word in keyword_lower for word in high_competition_words):
            if base_difficulty == 'Low':
                return 'Medium'
            elif base_difficulty == 'Medium':
                return 'High'
        elif any(word in keyword_lower for word in medium_competition_words):
            if base_difficulty == 'Low':
                return 'Low'
            elif base_difficulty == 'Medium':
                return 'Medium'
        
        return base_difficulty
    
    def extract_from_text(self, text: str, min_length: int = 3, max_length: int = 50) -> List[str]:
        """
        从文本中提取关键词
        
        Args:
            text: 输入文本
            min_length: 最小关键词长度
            max_length: 最大关键词长度
            
        Returns:
            提取的关键词列表
        """
        # 清理文本
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # 过滤停用词
        filtered_words = [word for word in words if word not in self.stop_words and len(word) >= min_length]
        
        # 生成n-gram关键词
        keywords = set()
        
        # 单词
        for word in filtered_words:
            if min_length <= len(word) <= max_length:
                keywords.add(word)
        
        # 二元组
        for i in range(len(filtered_words) - 1):
            bigram = f"{filtered_words[i]} {filtered_words[i+1]}"
            if min_length <= len(bigram) <= max_length:
                keywords.add(bigram)
        
        # 三元组
        for i in range(len(filtered_words) - 2):
            trigram = f"{filtered_words[i]} {filtered_words[i+1]} {filtered_words[i+2]}"
            if min_length <= len(trigram) <= max_length:
                keywords.add(trigram)
        
        return list(keywords)


def main():
    """测试关键词提取器"""
    extractor = KeywordExtractor()
    
    print("🚀 关键词提取器测试")
    print("=" * 50)
    
    # 测试关键词
    test_keywords = ['ai image generator', 'chatgpt alternative']
    
    for keyword in test_keywords:
        print(f"\n🔍 测试关键词: {keyword}")
        
        # Google自动完成测试
        autocomplete = extractor.get_google_autocomplete_suggestions(keyword, max_suggestions=5)
        print(f"  自动完成建议 ({len(autocomplete)}): {autocomplete[:3]}")
        
        # 相关搜索词测试
        related = extractor.get_related_search_terms(keyword, max_terms=5)
        print(f"  相关搜索词 ({len(related)}): {related[:3]}")
        
        # 语义扩展测试
        expanded = extractor.expand_seed_keywords([keyword], max_per_seed=5)
        if keyword in expanded:
            print(f"  语义扩展 ({len(expanded[keyword])}): {expanded[keyword][:3]}")
        
        # 难度分析
        difficulty = extractor.analyze_keyword_difficulty(keyword)
        print(f"  关键词难度: {difficulty}")
    
    print(f"\n✅ 关键词提取器测试完成!")


if __name__ == '__main__':
    main()