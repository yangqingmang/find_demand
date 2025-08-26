#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SERP 分析工具 - SERP Analyzer
用于分析搜索引擎结果页面特征
"""

import requests
import time
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import hashlib

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from config.config_manager import get_config
    config = get_config()
except ImportError:
    # 如果配置管理器不可用，使用默认配置
    class DefaultConfig:
        GOOGLE_API_KEY = ""
        GOOGLE_CSE_ID = ""
        SERP_API_KEY = ""
        SERP_REQUEST_DELAY = 1
        SERP_MAX_RETRIES = 3
        SERP_CACHE_ENABLED = True
        SERP_CACHE_DURATION = 3600
        
        def validate(self):
            if not self.GOOGLE_API_KEY or not self.GOOGLE_CSE_ID:
                print("警告: Google API配置未设置，SERP分析功能将受限")
            if not self.SERP_API_KEY:
                print("警告: SERP API Key 未设置，SERP分析功能将受限")
    
    config = DefaultConfig()

class SerpAnalyzer:
    """SERP分析类，用于分析搜索引擎结果页面"""
    
    def __init__(self):
        """初始化SERP分析器"""
        # 验证配置
        if hasattr(config, 'validate'):
            config.validate()
        
        # API配置
        self.api_key = config.GOOGLE_API_KEY
        self.serp_api_key = getattr(config, 'SERP_API_KEY', '')
        self.cse_id = config.GOOGLE_CSE_ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.serp_api_url = "https://serpapi.com/search"
        
        # 请求配置
        self.request_delay = getattr(config, 'SERP_REQUEST_DELAY', 1)
        self.max_retries = getattr(config, 'SERP_MAX_RETRIES', 3)
        
        # 缓存配置
        self.cache_enabled = getattr(config, 'SERP_CACHE_ENABLED', True)
        self.cache_duration = getattr(config, 'SERP_CACHE_DURATION', 3600)
        self.cache_dir = "data/serp_cache"
        
        # 创建缓存目录
        if self.cache_enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def analyze_keyword_serp(self, keyword: str) -> Dict:
        """
        分析单个关键词的SERP特征和意图
        
        参数:
            keyword (str): 关键词
            
        返回:
            Dict: 分析结果
        """
        result = {
            'keyword': keyword,
            'serp_features': {},
            'intent': 'I',
            'confidence': 0.5,
            'secondary_intent': None,
            'analysis_time': datetime.now().isoformat()
        }
        
        try:
            # 如果有 SERP API key，使用 SERP API
            if self.serp_api_key:
                search_result = self._search_with_serpapi(keyword)
            else:
                # 否则使用 Google Custom Search API
                search_result = self._search_with_google_api(keyword)
            
            if search_result:
                # 提取SERP特征
                features = self._extract_serp_features(search_result)
                result['serp_features'] = features
                
                # 分析意图
                intent, confidence, secondary = self._analyze_serp_intent(features)
                result['intent'] = intent
                result['confidence'] = confidence
                result['secondary_intent'] = secondary
                
        except Exception as e:
            print(f"SERP分析失败 {keyword}: {e}")
        
        return result
    
    def _search_with_serpapi(self, query: str) -> Optional[Dict]:
        """使用 SERP API 搜索"""
        params = {
            'api_key': self.serp_api_key,
            'engine': 'google',
            'q': query,
            'num': 10
        }
        
        try:
            response = requests.get(self.serp_api_url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"SERP API 搜索失败: {e}")
            return None
    
    def _search_with_google_api(self, query: str) -> Optional[Dict]:
        """使用 Google Custom Search API 搜索"""
        params = {
            'key': self.api_key,
            'cx': self.cse_id,
            'q': query,
            'num': 10
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Google API 搜索失败: {e}")
            return None
    
    def _extract_serp_features(self, search_result: Dict) -> Dict:
        """从搜索结果中提取SERP特征"""
        features = {
            'total_results': 0,
            'has_ads': False,
            'has_shopping': False,
            'has_images': False,
            'has_videos': False,
            'has_news': False,
            'has_knowledge_panel': False,
            'has_featured_snippet': False,
            'top_domains': []
        }
        
        # 根据不同的API响应格式提取特征
        if 'organic_results' in search_result:
            # SERP API 格式
            organic_results = search_result.get('organic_results', [])
            features['total_results'] = len(organic_results)
            features['has_ads'] = bool(search_result.get('ads'))
            features['has_shopping'] = bool(search_result.get('shopping_results'))
            features['has_images'] = bool(search_result.get('images_results'))
            features['has_videos'] = bool(search_result.get('video_results'))
            features['has_news'] = bool(search_result.get('news_results'))
            features['has_knowledge_panel'] = bool(search_result.get('knowledge_graph'))
            features['has_featured_snippet'] = bool(search_result.get('answer_box'))
            
            # 提取顶级域名
            domains = []
            for result in organic_results[:5]:
                if 'link' in result:
                    domain = urlparse(result['link']).netloc
                    domains.append(domain)
            features['top_domains'] = domains
            
        elif 'items' in search_result:
            # Google Custom Search API 格式
            items = search_result.get('items', [])
            search_info = search_result.get('searchInformation', {})
            
            features['total_results'] = int(search_info.get('totalResults', 0))
            
            # 提取顶级域名
            domains = []
            for item in items[:5]:
                if 'link' in item:
                    domain = urlparse(item['link']).netloc
                    domains.append(domain)
            features['top_domains'] = domains
        
        return features
    
    def _analyze_serp_intent(self, features: Dict) -> Tuple[str, float, Optional[str]]:
        """基于SERP特征分析搜索意图"""
        intent_scores = {
            'I': 0.0,  # 信息型
            'C': 0.0,  # 商业型
            'E': 0.0,  # 交易型
            'N': 0.0,  # 导航型
            'B': 0.0,  # 行为型
            'L': 0.0   # 本地型
        }
        
        # 基于SERP特征的评分规则
        if features.get('has_shopping'):
            intent_scores['E'] += 0.3
            intent_scores['C'] += 0.2
        
        if features.get('has_ads'):
            intent_scores['C'] += 0.2
            intent_scores['E'] += 0.1
        
        if features.get('has_knowledge_panel'):
            intent_scores['I'] += 0.3
            intent_scores['N'] += 0.2
        
        if features.get('has_featured_snippet'):
            intent_scores['I'] += 0.2
        
        if features.get('has_news'):
            intent_scores['I'] += 0.2
        
        if features.get('has_videos'):
            intent_scores['I'] += 0.1
            intent_scores['B'] += 0.1
        
        # 基于域名分析
        top_domains = features.get('top_domains', [])
        for domain in top_domains:
            if any(ecom in domain for ecom in ['amazon', 'ebay', 'shop', 'store']):
                intent_scores['E'] += 0.1
            elif any(info in domain for info in ['wikipedia', 'wiki', 'edu']):
                intent_scores['I'] += 0.1
            elif any(brand in domain for brand in ['google', 'facebook', 'twitter']):
                intent_scores['N'] += 0.1
        
        # 确定主要意图
        main_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[main_intent]
        
        # 确定次要意图
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        secondary_intent = sorted_intents[1][0] if len(sorted_intents) > 1 and sorted_intents[1][1] > 0.1 else None
        
        return main_intent, min(confidence, 1.0), secondary_intent

if __name__ == "__main__":
    # 测试 SERP 分析器
    analyzer = SerpAnalyzer()
    
    test_keywords = ["python tutorial", "buy iphone", "openai"]
    
    for keyword in test_keywords:
        print(f"\n分析关键词: {keyword}")
        result = analyzer.analyze_keyword_serp(keyword)
        print(f"意图: {result['intent']}")
        print(f"置信度: {result['confidence']:.2f}")
        print(f"SERP特征: {result['serp_features']}")