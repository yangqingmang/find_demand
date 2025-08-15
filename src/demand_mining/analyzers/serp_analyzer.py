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
        SERP_REQUEST_DELAY = 1
        SERP_MAX_RETRIES = 3
        SERP_CACHE_ENABLED = True
        SERP_CACHE_DURATION = 3600
        
        def validate(self):
            if not self.GOOGLE_API_KEY or not self.GOOGLE_CSE_ID:
                print("警告: Google API配置未设置，SERP分析功能将受限")
    
    config = DefaultConfig()

class SerpAnalyzer:
    """SERP分析类，用于分析搜索引擎结果页面"""
    
    def __init__(self):
        """初始化SERP分析器"""
        # 验证配置
        config.validate()
        
        # API配置
        self.api_key = config.GOOGLE_API_KEY
        self.cse_id = config.GOOGLE_CSE_ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        # 请求配置
        self.request_delay = config.SERP_REQUEST_DELAY
        self.max_retries = config.SERP_MAX_RETRIES
        
        # 缓存配置
        self.cache_enabled = config.SERP_CACHE_ENABLED
        self.cache_duration = config.SERP_CACHE_DURATION
        self.cache_dir = "data/serp_cache"
        
        # 创建缓存目录
        if self.cache_enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_key(self, query: str, **params) -> str:
        """生成缓存键"""
        cache_data = f"{query}_{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """从缓存加载数据"""
        if not self.cache_enabled:
            return None
            
        cache_path = self._get_cache_path(cache_key)
        
        if not os.path.exists(cache_path):
            return None
            
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # 检查缓存是否过期
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time > timedelta(seconds=self.cache_duration):
                os.remove(cache_path)
                return None
                
            return cache_data['data']
            
        except Exception as e:
            print(f"读取缓存失败: {e}")
            return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        """保存数据到缓存"""
        if not self.cache_enabled:
            return
            
        cache_path = self._get_cache_path(cache_key)
        
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def search_google(self, query: str, num_results: int = 10, **kwargs) -> Optional[Dict]:
        """
        使用 Google Custom Search API 搜索
        
        参数:
            query (str): 搜索查询
            num_results (int): 结果数量
            **kwargs: 其他搜索参数
            
        返回:
            Dict: 搜索结果数据
        """
        # 检查缓存
        cache_key = self._get_cache_key(query, num=num_results, **kwargs)
        cached_result = self._load_from_cache(cache_key)
        
        if cached_result:
            print(f"从缓存加载搜索结果: {query}")
            return cached_result
        
        # 构建请求参数
        params = {
            'key': self.api_key,
            'cx': self.cse_id,
            'q': query,
            'num': min(num_results, 10),  # API限制每次最多10个结果
            **kwargs
        }
        
        # 发送请求
        for attempt in range(self.max_retries):
            try:
                print(f"搜索查询: {query} (尝试 {attempt + 1}/{self.max_retries})")
                
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                
                # 保存到缓存
                self._save_to_cache(cache_key, result)
                
                # 请求延迟
                if self.request_delay > 0:
                    time.sleep(self.request_delay)
                
                return result
                
            except requests.exceptions.RequestException as e:
                print(f"请求失败 (尝试 {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    print(f"搜索失败: {query}")
                    return None
    
    def extract_serp_features(self, search_result: Dict) -> Dict:
        """
        从搜索结果中提取SERP特征
        
        参数:
            search_result (Dict): Google搜索API返回的结果
            
        返回:
            Dict: SERP特征数据
        """
        if not search_result or 'items' not in search_result:
            return self._get_empty_features()
        
        items = search_result.get('items', [])
        search_info = search_result.get('searchInformation', {})
        
        # 基础特征
        features = {
            'total_results': int(search_info.get('totalResults', 0)),
            'search_time': float(search_info.get('searchTime', 0)),
            'organic_count': len(items),
            'ads_count': 0,  # Google Custom Search API 不直接提供广告信息
            'competitor_urls': [],
            'title_keywords': [],
            'snippet_keywords': []
        }
        
        # 分析搜索结果特征
        has_video = False
        has_images = False
        has_shopping = False
        has_news = False
        
        for item in items:
            # 提取URL
            url = item.get('link', '')
            if url:
                features['competitor_urls'].append(url)
            
            # 提取标题关键词
            title = item.get('title', '').lower()
            features['title_keywords'].extend(self._extract_keywords(title))
            
            # 提取摘要关键词
            snippet = item.get('snippet', '').lower()
            features['snippet_keywords'].extend(self._extract_keywords(snippet))
            
            # 检测内容类型
            if 'youtube.com' in url or 'video' in title:
                has_video = True
            if 'image' in item.get('kind', '') or 'images' in url:
                has_images = True
            if 'shopping' in url or 'buy' in title or 'price' in snippet:
                has_shopping = True
            if 'news' in url or item.get('kind', '') == 'news':
                has_news = True
        
        # 设置布尔特征
        features.update({
            'has_video': has_video,
            'has_images': has_images,
            'has_shopping': has_shopping,
            'has_news': has_news,
            'has_paa': self._detect_paa(search_result),
            'has_featured_snippet': self._detect_featured_snippet(search_result),
            'has_local': self._detect_local_results(search_result)
        })
        
        # 去重关键词
        features['title_keywords'] = list(set(features['title_keywords']))
        features['snippet_keywords'] = list(set(features['snippet_keywords']))
        
        return features
    
    def _get_empty_features(self) -> Dict:
        """返回空的特征字典"""
        return {
            'total_results': 0,
            'search_time': 0,
            'organic_count': 0,
            'ads_count': 0,
            'has_paa': False,
            'has_featured_snippet': False,
            'has_shopping': False,
            'has_video': False,
            'has_images': False,
            'has_news': False,
            'has_local': False,
            'competitor_urls': [],
            'title_keywords': [],
            'snippet_keywords': []
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        # 简单的关键词提取，可以后续优化
        words = re.findall(r'\b[a-zA-Z\u4e00-\u9fff]{2,}\b', text)
        return [word.lower() for word in words if len(word) > 2]
    
    def _detect_paa(self, search_result: Dict) -> bool:
        """检测是否有People Also Ask"""
        # Google Custom Search API 可能不直接提供PAA信息
        # 这里使用启发式方法检测
        items = search_result.get('items', [])
        
        for item in items:
            snippet = item.get('snippet', '').lower()
            if any(phrase in snippet for phrase in ['people also ask', 'related questions', '相关问题']):
                return True
        
        return False
    
    def _detect_featured_snippet(self, search_result: Dict) -> bool:
        """检测是否有特色片段"""
        items = search_result.get('items', [])
        
        if items:
            # 第一个结果的摘要较长可能是特色片段
            first_snippet = items[0].get('snippet', '')
            if len(first_snippet) > 200:
                return True
        
        return False
    
    def _detect_local_results(self, search_result: Dict) -> bool:
        """检测是否有本地结果"""
        items = search_result.get('items', [])
        
        for item in items:
            url = item.get('link', '').lower()
            title = item.get('title', '').lower()
            
            if any(keyword in url or keyword in title 
                   for keyword in ['maps.google', 'local', 'near me', '附近']):
                return True
        
        return False
    
    def analyze_serp_intent(self, features: Dict) -> Tuple[str, float, Optional[str]]:
        """
        基于SERP特征分析搜索意图
        
        参数:
            features (Dict): SERP特征数据
            
        返回:
            Tuple: (主要意图, 置信度, 次要意图)
        """
        scores = {'I': 0, 'N': 0, 'C': 0, 'E': 0, 'B': 0}
        
        # 基于SERP特征的评分规则
        
        # 交易意图 (E)
        if features['has_shopping']:
            scores['E'] += 3
        if any(kw in features['title_keywords'] for kw in ['buy', 'purchase', 'order', 'price']):
            scores['E'] += 2
        if any(kw in features['title_keywords'] for kw in ['购买', '订购', '价格']):
            scores['E'] += 2
        
        # 商业意图 (C)
        if any(kw in features['title_keywords'] for kw in ['best', 'top', 'review', 'vs', 'compare']):
            scores['C'] += 3
        if any(kw in features['title_keywords'] for kw in ['最佳', '评测', '对比', '比较']):
            scores['C'] += 3
        
        # 信息意图 (I)
        if features['has_featured_snippet']:
            scores['I'] += 2
        if features['has_paa']:
            scores['I'] += 2
        if features['has_video']:
            scores['I'] += 1
        if any(kw in features['title_keywords'] for kw in ['how', 'what', 'why', 'guide', 'tutorial']):
            scores['I'] += 2
        if any(kw in features['title_keywords'] for kw in ['如何', '什么', '为什么', '教程']):
            scores['I'] += 2
        
        # 导航意图 (N)
        if features['has_local']:
            scores['N'] += 2
        if any(kw in features['title_keywords'] for kw in ['login', 'signin', 'official', 'website']):
            scores['N'] += 3
        if any(kw in features['title_keywords'] for kw in ['登录', '官网', '官方']):
            scores['N'] += 3
        
        # 行为意图 (B)
        if any(kw in features['title_keywords'] for kw in ['error', 'fix', 'problem', 'help', 'support']):
            scores['B'] += 3
        if any(kw in features['title_keywords'] for kw in ['错误', '修复', '问题', '帮助']):
            scores['B'] += 3
        
        # 如果没有明确信号，默认为信息意图
        if sum(scores.values()) == 0:
            return ('I', 0.5, None)
        
        # 找出主要意图和次要意图
        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_intent, primary_score = sorted_intents[0]
        
        # 计算置信度
        total_score = sum(scores.values())
        confidence = 0.6 + 0.4 * (primary_score / total_score) if total_score > 0 else 0.5
        confidence = min(confidence, 1.0)
        
        # 次要意图
        secondary_intent = sorted_intents[1][0] if len(sorted_intents) > 1 and sorted_intents[1][1] > 0 else None
        
        return (primary_intent, round(confidence, 2), secondary_intent)
    
    def analyze_keyword_serp(self, keyword: str) -> Dict:
        """
        分析单个关键词的SERP特征和意图
        
        参数:
            keyword (str): 关键词
            
        返回:
            Dict: 分析结果
        """
        # 搜索关键词
        search_result = self.search_google(keyword)
        
        if not search_result:
            return {
                'keyword': keyword,
                'error': '搜索失败',
                'features': self._get_empty_features(),
                'intent': 'I',
                'confidence': 0.5,
                'secondary_intent': None
            }
        
        # 提取SERP特征
        features = self.extract_serp_features(search_result)
        
        # 分析意图
        intent, confidence, secondary = self.analyze_serp_intent(features)
        
        return {
            'keyword': keyword,
            'features': features,
            'intent': intent,
            'confidence': confidence,
            'secondary_intent': secondary,
            'search_results_count': features['total_results'],
            'top_competitors': features['competitor_urls'][:5]
        }
    
    def analyze_keywords(self, keywords: List[str]) -> List[Dict]:
        """
        分析关键词列表（兼容性方法）
        
        参数:
            keywords (List[str]): 关键词列表
            
        返回:
            List[Dict]: 分析结果列表
        """
        return self.batch_analyze(keywords)
    
    def batch_analyze(self, keywords: List[str]) -> List[Dict]:
        """
        批量分析关键词SERP特征
        
        参数:
            keywords (List[str]): 关键词列表
            
        返回:
            List[Dict]: 分析结果列表
        """
        results = []
        
        for i, keyword in enumerate(keywords, 1):
            print(f"分析关键词 {i}/{len(keywords)}: {keyword}")
            
            result = self.analyze_keyword_serp(keyword)
            results.append(result)
            
            # 进度显示
            if i % 10 == 0:
                print(f"已完成 {i}/{len(keywords)} 个关键词的分析")
        
        return results
