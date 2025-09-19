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

# 导入SERP数据结构化解析器
try:
    from src.demand_mining.core.serp_parser import SerpParser
except ImportError:
    SerpParser = None
    print("警告: SERP数据结构化解析器不可用")

# 导入代理管理器
try:
    from src.demand_mining.core.proxy_manager import get_proxy_manager
except ImportError:
    get_proxy_manager = None
    print("警告: 代理管理器不可用，将使用直接请求")

try:
    from config.proxy_config_loader import get_proxy_config
except ImportError:
    get_proxy_config = None

class SerpAnalyzer:
    """SERP分析类，用于分析搜索引擎结果页面"""
    
    def __init__(self, use_proxy: bool = True):
        """初始化SERP分析器"""
        # 验证配置
        if hasattr(config, 'validate'):
            config.validate()
        
        # 初始化SERP数据结构化解析器
        self.serp_parser = SerpParser() if SerpParser else None
        
        # API配置
        self.api_key = config.GOOGLE_API_KEY
        self.serp_api_key = getattr(config, 'SERP_API_KEY', '')
        self.cse_id = config.GOOGLE_CSE_ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.serp_api_url = "https://serpapi.com/search"
        
        # 请求配置
        self.request_delay = getattr(config, 'SERP_REQUEST_DELAY', 1)
        self.max_retries = getattr(config, 'SERP_MAX_RETRIES', 3)
        
        # 代理配置
        self.use_proxy = use_proxy
        if self.use_proxy and get_proxy_config:
            try:
                proxy_config = get_proxy_config()
                if not proxy_config.enabled:
                    print("提示: 当前代理配置已禁用代理，SERP 分析器将使用直连模式")
                    self.use_proxy = False
            except Exception as e:
                print(f"警告: 读取代理配置失败: {e}，SERP 分析器将使用直连模式")
                self.use_proxy = False
        self.proxy_manager = None
        if self.use_proxy and get_proxy_manager:
            try:
                self.proxy_manager = get_proxy_manager()
                print("✅ SERP分析器：代理管理器已启用")
            except Exception as e:
                print(f"⚠️ SERP分析器：代理管理器初始化失败: {e}，将使用直接请求")
                self.use_proxy = False
        
        # 缓存配置
        self.cache_enabled = getattr(config, 'SERP_CACHE_ENABLED', True)
        self.cache_duration = getattr(config, 'SERP_CACHE_DURATION', 3600)
        self.cache_dir = "data/serp_cache"
        
        # 创建缓存目录
        if self.cache_enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
        
        # 域名权重数据库（用于竞争对手分析）
        self.domain_authority_db = {
            'google.com': 100, 'youtube.com': 100, 'facebook.com': 96,
            'wikipedia.org': 95, 'twitter.com': 94, 'instagram.com': 93,
            'linkedin.com': 92, 'reddit.com': 91, 'amazon.com': 96,
            'microsoft.com': 95, 'apple.com': 94, 'github.com': 85,
            'stackoverflow.com': 87, 'medium.com': 82, 'quora.com': 80
        }
    
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
            'q': query,
            'engine': 'google',
            'num': 10
        }
        
        try:
            # 如果启用代理管理器，使用代理发送请求
            if self.use_proxy and self.proxy_manager:
                try:
                    response = self.proxy_manager.make_request(
                        self.serp_api_url, 
                        method='GET', 
                        params=params, 
                        timeout=30
                    )
                    if response:
                        response.raise_for_status()
                        return response.json()
                    else:
                        print("⚠️ 代理请求失败，尝试直接请求")
                except Exception as e:
                    print(f"⚠️ 代理请求异常: {e}，尝试直接请求")
            
            # 直接请求（无代理或代理失败时的回退方案）
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
            # 如果启用代理管理器，使用代理发送请求
            if self.use_proxy and self.proxy_manager:
                try:
                    response = self.proxy_manager.make_request(
                        self.base_url, 
                        method='GET', 
                        params=params, 
                        timeout=30
                    )
                    if response:
                        response.raise_for_status()
                        return response.json()
                    else:
                        print("⚠️ 代理请求失败，尝试直接请求")
                except Exception as e:
                    print(f"⚠️ 代理请求异常: {e}，尝试直接请求")
            
            # 直接请求（无代理或代理失败时的回退方案）
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
            'top_domains': [],
            'ads_count': 0,
            'purchase_intent_hits': 0,
            'purchase_intent_ratio': 0.0,
            'purchase_intent_terms': [],
            'analyzed_results': 0,
            'ads_reference_window': 4,
        }

        purchase_terms = {'buy', 'price', 'cost', 'discount', 'deal', 'coupon', 'order', 'subscribe', 'quote', 'plan'}
        matched_terms = set()
        purchase_hits = 0
        analyzed_results = 0

        if 'organic_results' in search_result:
            organic_results = search_result.get('organic_results', [])
            features['total_results'] = len(organic_results)
            features['has_ads'] = bool(search_result.get('ads'))
            features['has_shopping'] = bool(search_result.get('shopping_results'))
            features['has_images'] = bool(search_result.get('images_results'))
            features['has_videos'] = bool(search_result.get('video_results'))
            features['has_news'] = bool(search_result.get('news_results'))
            features['has_knowledge_panel'] = bool(search_result.get('knowledge_graph'))
            features['has_featured_snippet'] = bool(search_result.get('answer_box'))

            features['ads_count'] = len(search_result.get('ads') or []) + len(search_result.get('shopping_results') or [])

            domains = []
            for result in organic_results[:5]:
                if 'link' in result:
                    domain = urlparse(result['link']).netloc
                    domains.append(domain)
            features['top_domains'] = domains

            for result in organic_results[:10]:
                text_parts = [
                    result.get('title', ''),
                    result.get('snippet', ''),
                    result.get('description', '')
                ]
                text = ' '.join(part for part in text_parts if part).strip().lower()
                if not text:
                    continue
                analyzed_results += 1
                matched = {term for term in purchase_terms if term in text}
                if matched:
                    purchase_hits += 1
                    matched_terms.update(matched)

            features['ads_reference_window'] = max(features['ads_count'], len(organic_results), 4)

        elif 'items' in search_result:
            items = search_result.get('items', [])
            search_info = search_result.get('searchInformation', {})
            features['total_results'] = int(search_info.get('totalResults', 0))
            features['ads_count'] = len(search_result.get('promotions') or [])

            domains = []
            for item in items[:5]:
                if 'link' in item:
                    domain = urlparse(item['link']).netloc
                    domains.append(domain)
            features['top_domains'] = domains

            for item in items[:10]:
                text_parts = [
                    item.get('title', ''),
                    item.get('snippet', ''),
                    item.get('htmlSnippet', '')
                ]
                text = ' '.join(part for part in text_parts if part).strip().lower()
                if not text:
                    continue
                analyzed_results += 1
                matched = {term for term in purchase_terms if term in text}
                if matched:
                    purchase_hits += 1
                    matched_terms.update(matched)

            features['ads_reference_window'] = max(features['ads_count'], len(items), 4)

        if analyzed_results:
            features['purchase_intent_ratio'] = round(purchase_hits / analyzed_results, 4)
        features['purchase_intent_hits'] = purchase_hits
        features['purchase_intent_terms'] = sorted(matched_terms)
        features['analyzed_results'] = analyzed_results

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
    
    def analyze_serp_structure(self, keyword: str) -> Dict:
        """
        分析SERP结构和竞争情况
        
        Args:
            keyword: 要分析的关键词
            
        Returns:
            Dict: SERP结构分析结果
        """
        try:
            # 获取搜索结果
            search_result = self._get_search_results(keyword)
            if not search_result:
                return self._create_empty_structure_analysis(keyword)
            
            # 分析SERP结构
            structure_info = self._extract_serp_structure(search_result)
            
            # 分析竞争对手
            competitors = self._analyze_competitors_basic(search_result)
            
            # 计算竞争难度
            difficulty_score = self._calculate_basic_difficulty(structure_info, competitors)
            
            return {
                'keyword': keyword,
                'structure': structure_info,
                'competitors': competitors,
                'difficulty_score': difficulty_score,
                'competition_level': self._get_competition_level(difficulty_score),
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"SERP结构分析失败 {keyword}: {e}")
            return self._create_empty_structure_analysis(keyword)
    
    def _get_search_results(self, keyword: str) -> Optional[Dict]:
        """获取搜索结果（带缓存）"""
        # 检查缓存
        if self.cache_enabled:
            cached_result = self._get_cached_result(keyword)
            if cached_result:
                return cached_result
        
        # 获取新的搜索结果
        if self.serp_api_key:
            result = self._search_with_serpapi(keyword)
        else:
            result = self._search_with_google_api(keyword)
        
        # 缓存结果
        if result and self.cache_enabled:
            self._cache_result(keyword, result)
        
        return result
    
    def _extract_serp_structure(self, search_result: Dict) -> Dict:
        """提取SERP结构信息"""
        structure = {
            'total_results': 0,
            'organic_count': 0,
            'ads_count': 0,
            'shopping_count': 0,
            'images_count': 0,
            'videos_count': 0,
            'news_count': 0,
            'has_featured_snippet': False,
            'has_knowledge_panel': False,
            'has_local_results': False,
            'competition_density': 0.0
        }
        
        if 'organic_results' in search_result:
            # SERP API格式
            structure['organic_count'] = len(search_result.get('organic_results', []))
            structure['ads_count'] = len(search_result.get('ads', []))
            structure['shopping_count'] = len(search_result.get('shopping_results', []))
            structure['images_count'] = len(search_result.get('images_results', []))
            structure['videos_count'] = len(search_result.get('video_results', []))
            structure['news_count'] = len(search_result.get('news_results', []))
            structure['has_featured_snippet'] = bool(search_result.get('answer_box'))
            structure['has_knowledge_panel'] = bool(search_result.get('knowledge_graph'))
            structure['has_local_results'] = bool(search_result.get('local_results'))
            
        elif 'items' in search_result:
            # Google Custom Search API格式
            items = search_result.get('items', [])
            search_info = search_result.get('searchInformation', {})
            
            structure['organic_count'] = len(items)
            structure['total_results'] = int(search_info.get('totalResults', 0))
        
        # 计算竞争密度
        total_elements = (structure['organic_count'] + structure['ads_count'] + 
                         structure['shopping_count'])
        if total_elements > 0:
            non_organic = structure['ads_count'] + structure['shopping_count']
            structure['competition_density'] = non_organic / total_elements
        
        return structure
    
    def _analyze_competitors_basic(self, search_result: Dict) -> List[Dict]:
        """基础竞争对手分析"""
        competitors = []
        
        organic_results = search_result.get('organic_results', search_result.get('items', []))
        
        for i, result in enumerate(organic_results[:10]):
            try:
                url = result.get('link', '')
                if not url:
                    continue
                
                domain = urlparse(url).netloc.lower()
                title = result.get('title', '')
                
                # 识别竞争对手类型
                competitor_type = self._identify_competitor_type(url, domain)
                
                # 获取域名权重
                domain_authority = self._get_domain_authority(domain)
                
                # 评估页面权重
                page_authority = self._estimate_page_authority_basic(domain, url, title)
                
                competitor = {
                    'position': i + 1,
                    'url': url,
                    'domain': domain,
                    'title': title,
                    'competitor_type': competitor_type,
                    'domain_authority': domain_authority,
                    'page_authority': page_authority
                }
                
                competitors.append(competitor)
                
            except Exception as e:
                print(f"分析竞争对手失败: {e}")
                continue
        
        return competitors
    
    def _identify_competitor_type(self, url: str, domain: str) -> str:
        """识别竞争对手类型"""
        parsed_url = urlparse(url)
        
        # 检查是否为子域名
        domain_parts = domain.split('.')
        if len(domain_parts) > 2:
            subdomain = domain_parts[0]
            if subdomain in ['www', 'blog', 'shop', 'store', 'news', 'support']:
                return 'subdomain'
        
        # 检查URL路径深度
        path = parsed_url.path.strip('/')
        if not path:
            return 'domain'
        
        path_segments = path.split('/')
        if len(path_segments) <= 2:
            return 'domain'
        else:
            return 'inner_page'
    
    def _get_domain_authority(self, domain: str) -> int:
        """获取域名权重"""
        # 首先检查内置数据库
        if domain in self.domain_authority_db:
            return self.domain_authority_db[domain]
        
        # 基于域名特征估算权重
        score = 30  # 基础分数
        
        # 顶级域名加分
        if domain.endswith('.edu'):
            score += 20
        elif domain.endswith('.gov'):
            score += 25
        elif domain.endswith('.org'):
            score += 10
        
        # 知名网站模式识别
        if any(pattern in domain for pattern in ['wiki', 'news', 'blog']):
            score += 15
        
        # 域名长度影响
        if len(domain) < 10:
            score += 5
        elif len(domain) > 20:
            score -= 5
        
        return min(max(score, 1), 100)
    
    def _estimate_page_authority_basic(self, domain: str, url: str, title: str) -> int:
        """基础页面权重估算"""
        domain_authority = self._get_domain_authority(domain)
        
        # 基于域名权重和URL结构估算页面权重
        page_authority = domain_authority
        
        # URL深度影响
        parsed_url = urlparse(url)
        path_depth = len(parsed_url.path.strip('/').split('/')) if parsed_url.path.strip('/') else 0
        
        if path_depth == 0:
            page_authority += 10  # 首页权重高
        elif path_depth > 3:
            page_authority -= 10  # 深层页面权重低
        
        # 标题质量影响
        if title and 30 <= len(title) <= 60:
            page_authority += 5
        
        return min(max(page_authority, 1), 100)
    
    def _calculate_basic_difficulty(self, structure: Dict, competitors: List[Dict]) -> float:
        """计算基础竞争难度"""
        if not competitors:
            return 0.0
        
        difficulty = 0.0
        
        # SERP复杂度影响 (30%)
        complexity = 0.0
        if structure.get('ads_count', 0) > 0:
            complexity += 0.2
        if structure.get('shopping_count', 0) > 0:
            complexity += 0.15
        if structure.get('has_featured_snippet'):
            complexity += 0.2
        if structure.get('has_knowledge_panel'):
            complexity += 0.15
        
        difficulty += complexity * 0.3
        
        # 顶级竞争对手权重影响 (50%)
        top_competitors = competitors[:5]
        avg_domain_authority = sum(comp['domain_authority'] for comp in top_competitors) / len(top_competitors)
        difficulty += (avg_domain_authority / 100) * 0.5
        
        # 竞争对手类型影响 (20%)
        domain_competitors = sum(1 for comp in top_competitors if comp['competitor_type'] == 'domain')
        if domain_competitors >= 3:
            difficulty += 0.2
        elif domain_competitors >= 1:
            difficulty += 0.1
        
        return min(difficulty, 1.0)
    
    def _get_competition_level(self, difficulty_score: float) -> str:
        """获取竞争级别"""
        if difficulty_score >= 0.8:
            return "极高"
        elif difficulty_score >= 0.6:
            return "高"
        elif difficulty_score >= 0.4:
            return "中等"
        elif difficulty_score >= 0.2:
            return "低"
        else:
            return "极低"
    
    def _create_empty_structure_analysis(self, keyword: str) -> Dict:
        """创建空的结构分析结果"""
        return {
            'keyword': keyword,
            'structure': {
                'total_results': 0,
                'organic_count': 0,
                'ads_count': 0,
                'competition_density': 0.0
            },
            'competitors': [],
            'difficulty_score': 0.0,
            'competition_level': "未知",
            'analysis_time': datetime.now().isoformat()
        }
    
    def _get_cached_result(self, keyword: str) -> Optional[Dict]:
        """获取缓存的搜索结果"""
        cache_key = hashlib.md5(keyword.encode()).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # 检查缓存是否过期
                cache_time = datetime.fromisoformat(cached_data.get('timestamp', ''))
                if datetime.now() - cache_time < timedelta(seconds=self.cache_duration):
                    return cached_data.get('data')
            except Exception as e:
                print(f"读取缓存失败: {e}")
        
        return None
    
    def _cache_result(self, keyword: str, result: Dict):
        """缓存搜索结果"""
        cache_key = hashlib.md5(keyword.encode()).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            cache_data = {
                'keyword': keyword,
                'timestamp': datetime.now().isoformat(),
                'data': result
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"缓存结果失败: {e}")
    
    def analyze_serp_detailed(self, keyword: str) -> Dict:
        """
        使用结构化解析器进行详细SERP分析
        
        Args:
            keyword: 要分析的关键词
            
        Returns:
            Dict: 包含基础分析和结构化分析的完整结果
        """
        result = {
            'keyword': keyword,
            'basic_analysis': self.analyze_keyword_serp(keyword),
            'structured_analysis': None,
            'competitors': []
        }
        
        try:
            if self.serp_parser:
                search_data = self._get_search_results(keyword)
                if search_data:
                    serp_structure = self.serp_parser.parse_serp_structure(search_data, keyword)
                    result['structured_analysis'] = {
                        'difficulty_score': serp_structure.difficulty_score,
                        'opportunity_score': serp_structure.opportunity_score,
                        'total_results': serp_structure.total_results,
                        'organic_count': len(serp_structure.organic_results),
                        'paid_count': len(serp_structure.paid_results),
                        'competition_metrics': serp_structure.competition_metrics
                    }
                    
                    competitors = self.serp_parser.extract_competitor_info(serp_structure.organic_results)
                    result['competitors'] = [
                        {
                            'domain': comp.domain,
                            'position': comp.position,
                            'domain_authority': comp.domain_authority,
                            'competitor_type': comp.competitor_type
                        }
                        for comp in competitors[:5]  # 只返回前5个
                    ]
        except Exception as e:
            print(f"详细SERP分析失败: {e}")
        
        return result

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