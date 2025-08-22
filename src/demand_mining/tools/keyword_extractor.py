#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
关键词提取工具
从各种数据源提取和扩展关键词
"""

import re
import requests
from typing import List, Dict, Set, Any
from collections import Counter
import pandas as pd

class KeywordExtractor:
    """关键词提取器"""
    
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
    
    def extract_from_text(self, text: str, min_length: int = 2, max_length: int = 4) -> List[str]:
        """从文本中提取关键词"""
        # 清理文本
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # 过滤停用词
        words = [w for w in words if w not in self.stop_words and len(w) > 1]
        
        keywords = set()
        
        # 提取单词和短语
        for i in range(len(words)):
            for j in range(min_length, min(max_length + 1, len(words) - i + 1)):
                phrase = ' '.join(words[i:i+j])
                if len(phrase) > 3:  # 最小长度
                    keywords.add(phrase)
        
        return list(keywords)
    
    def extract_from_url_list(self, urls: List[str]) -> Dict[str, List[str]]:
        """从URL列表提取关键词"""
        results = {}
        
        for url in urls:
            try:
                # 简单的URL内容提取（实际应用中可以使用更复杂的爬虫）
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    keywords = self.extract_from_text(response.text)
                    results[url] = keywords[:50]  # 限制数量
                else:
                    results[url] = []
            except Exception as e:
                print(f"提取URL失败 {url}: {e}")
                results[url] = []
        
        return results
    
    def expand_seed_keywords(self, seed_keywords: List[str]) -> List[str]:
        """扩展种子关键词"""
        expanded = set(seed_keywords)
        
        # 添加常见的修饰词
        modifiers = [
            'best', 'top', 'free', 'online', 'how to', 'what is', 'guide', 
            'tutorial', 'review', 'comparison', 'vs', 'alternative', 'tool',
            'software', 'app', 'platform', 'service', 'solution'
        ]
        
        for keyword in seed_keywords:
            for modifier in modifiers:
                expanded.add(f"{modifier} {keyword}")
                expanded.add(f"{keyword} {modifier}")
        
        return list(expanded)
    
    def extract_trending_keywords(self, category: str = 'technology') -> List[str]:
        """提取趋势关键词"""
        # 这里应该集成Google Trends API或其他趋势数据源
        # 返回数据
        trending_keywords = {
            'technology': [
                'artificial intelligence', 'machine learning', 'chatgpt', 'ai tools',
                'automation', 'blockchain', 'cryptocurrency', 'web3', 'metaverse',
                'cloud computing', 'cybersecurity', 'data science', 'python programming'
            ],
            'business': [
                'digital marketing', 'seo tools', 'social media marketing', 'email marketing',
                'content marketing', 'lead generation', 'crm software', 'project management',
                'remote work', 'productivity tools', 'business automation'
            ],
            'health': [
                'mental health', 'fitness apps', 'nutrition tracking', 'meditation',
                'wellness', 'healthcare technology', 'telemedicine', 'health monitoring'
            ]
        }
        
        return trending_keywords.get(category, [])
    
    def analyze_keyword_difficulty(self, keywords: List[str]) -> Dict[str, Dict[str, Any]]:
        """分析关键词难度"""
        results = {}
        
        for keyword in keywords:
            # 难度分析
            word_count = len(keyword.split())
            base_difficulty = min(word_count * 10, 80)
            
            # 根据关键词特征调整难度
            if any(word in keyword.lower() for word in ['best', 'top', 'review']):
                difficulty = min(base_difficulty + 20, 95)
            elif any(word in keyword.lower() for word in ['how to', 'tutorial', 'guide']):
                difficulty = max(base_difficulty - 10, 10)
            else:
                difficulty = base_difficulty
            
            results[keyword] = {
                'difficulty': difficulty,
                'search_volume': max(1000 - difficulty * 10, 100),  # 搜索量
                'competition': difficulty / 100,
                'opportunity_score': max(100 - difficulty, 10)
            }
        
        return results

def main():
    """测试关键词提取器"""
    extractor = KeywordExtractor()
    
    # 测试文本提取
    sample_text = """
    Artificial intelligence and machine learning are transforming how we work.
    The best AI tools include ChatGPT, Claude, and various automation platforms.
    These technologies help with content creation, data analysis, and productivity.
    """
    
    print("🔍 从文本提取关键词:")
    keywords = extractor.extract_from_text(sample_text)
    for kw in keywords[:10]:
        print(f"  - {kw}")
    
    # 测试种子关键词扩展
    print("\n🌱 扩展种子关键词:")
    seed_keywords = ['ai tools', 'chatgpt']
    expanded = extractor.expand_seed_keywords(seed_keywords)
    for kw in expanded[:10]:
        print(f"  - {kw}")
    
    # 测试趋势关键词
    print("\n📈 技术类趋势关键词:")
    trending = extractor.extract_trending_keywords('technology')
    for kw in trending[:10]:
        print(f"  - {kw}")
    
    # 测试难度分析
    print("\n📊 关键词难度分析:")
    test_keywords = ['ai tools', 'best chatgpt alternatives', 'how to use ai']
    difficulty_analysis = extractor.analyze_keyword_difficulty(test_keywords)
    
    for kw, data in difficulty_analysis.items():
        print(f"  {kw}:")
        print(f"    难度: {data['difficulty']}")
        print(f"    搜索量: {data['search_volume']}")
        print(f"    机会分数: {data['opportunity_score']}")

if __name__ == '__main__':
    main()