#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SERP数据结构化解析器 - SERP Parser
用于解析搜索结果页面元素，提取竞争对手信息，生成竞争难度评分

实现待办: 1.2 SERP数据结构化
- 解析搜索结果页面元素
- 提取竞争对手信息
- 生成竞争难度评分
"""

import re
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass, asdict
import requests
from bs4 import BeautifulSoup


@dataclass
class SerpElement:
    """SERP页面元素数据结构"""
    element_type: str  # organic, ad, shopping, image, video, news, featured_snippet, knowledge_panel
    position: int
    title: str
    url: str
    domain: str
    snippet: str
    additional_data: Dict[str, Any]


@dataclass
class CompetitorInfo:
    """竞争对手信息数据结构"""
    domain: str
    url: str
    title: str
    position: int
    competitor_type: str  # domain, subdomain, inner_page
    domain_authority: int
    page_authority: int
    content_type: str  # homepage, category, product, article, tool
    brand_strength: str  # strong, medium, weak, unknown
    seo_signals: Dict[str, Any]


@dataclass
class SerpStructure:
    """SERP结构数据"""
    keyword: str
    total_results: int
    organic_results: List[SerpElement]
    paid_results: List[SerpElement]
    special_features: List[SerpElement]
    competition_metrics: Dict[str, float]
    difficulty_score: float
    opportunity_score: float
    analysis_timestamp: str


class SerpParser:
    """SERP数据结构化解析器"""
    
    def __init__(self):
        """初始化SERP解析器"""
        # 域名权重数据库
        self.domain_authority_db = {
            # 搜索引擎和大型平台
            'google.com': 100, 'youtube.com': 100, 'facebook.com': 96,
            'wikipedia.org': 95, 'twitter.com': 94, 'instagram.com': 93,
            'linkedin.com': 92, 'reddit.com': 91, 'amazon.com': 96,
            'microsoft.com': 95, 'apple.com': 94, 'github.com': 85,
            'stackoverflow.com': 87, 'medium.com': 82, 'quora.com': 80,
            
            # AI工具相关高权重域名
            'openai.com': 90, 'huggingface.co': 85, 'anthropic.com': 88,
            'midjourney.com': 82, 'stability.ai': 80, 'replicate.com': 78,
            'runwayml.com': 75, 'jasper.ai': 72, 'copy.ai': 70,
            
            # 设计工具域名
            'canva.com': 85, 'figma.com': 82, 'adobe.com': 90,
            'sketch.com': 75, 'invisionapp.com': 72,
            
            # 开发工具域名
            'vercel.com': 80, 'netlify.com': 78, 'heroku.com': 82,
            'digitalocean.com': 85, 'aws.amazon.com': 95
        }
        
        # 内容类型识别模式
        self.content_patterns = {
            'homepage': [r'^/$', r'^/index', r'^/home'],
            'category': [r'/category/', r'/categories/', r'/tag/', r'/tags/'],
            'product': [r'/product/', r'/item/', r'/p/', r'/buy/'],
            'article': [r'/article/', r'/post/', r'/blog/', r'/news/'],
            'tool': [r'/tool/', r'/generator/', r'/converter/', r'/editor/'],
            'pricing': [r'/pricing', r'/plans', r'/subscribe'],
            'about': [r'/about', r'/company', r'/team'],
            'contact': [r'/contact', r'/support', r'/help']
        }
        
        # SEO信号权重
        self.seo_weights = {
            'title_keyword_match': 0.25,
            'url_keyword_match': 0.15,
            'domain_authority': 0.30,
            'page_depth': 0.10,
            'content_relevance': 0.20
        }
    
    def parse_serp_structure(self, search_data: Dict, keyword: str) -> SerpStructure:
        """
        解析SERP结构数据
        
        Args:
            search_data: 搜索API返回的原始数据
            keyword: 搜索关键词
            
        Returns:
            SerpStructure: 结构化的SERP数据
        """
        try:
            # 解析有机结果
            organic_results = self._parse_organic_results(search_data)
            
            # 解析付费结果
            paid_results = self._parse_paid_results(search_data)
            
            # 解析特殊功能
            special_features = self._parse_special_features(search_data)
            
            # 计算竞争指标
            competition_metrics = self._calculate_competition_metrics(
                organic_results, paid_results, special_features
            )
            
            # 计算难度评分
            difficulty_score = self._calculate_difficulty_score(
                organic_results, competition_metrics
            )
            
            # 计算机会评分
            opportunity_score = self._calculate_opportunity_score(
                organic_results, competition_metrics, difficulty_score
            )
            
            # 获取总结果数
            total_results = self._extract_total_results(search_data)
            
            return SerpStructure(
                keyword=keyword,
                total_results=total_results,
                organic_results=organic_results,
                paid_results=paid_results,
                special_features=special_features,
                competition_metrics=competition_metrics,
                difficulty_score=difficulty_score,
                opportunity_score=opportunity_score,
                analysis_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            print(f"SERP结构解析失败: {e}")
            return self._create_empty_structure(keyword)
    
    def extract_competitor_info(self, organic_results: List[SerpElement]) -> List[CompetitorInfo]:
        """
        提取竞争对手详细信息
        
        Args:
            organic_results: 有机搜索结果列表
            
        Returns:
            List[CompetitorInfo]: 竞争对手信息列表
        """
        competitors = []
        
        for result in organic_results[:10]:  # 分析前10个结果
            try:
                competitor = self._analyze_competitor(result)
                if competitor:
                    competitors.append(competitor)
            except Exception as e:
                print(f"分析竞争对手失败 {result.url}: {e}")
                continue
        
        return competitors
    
    def _parse_organic_results(self, search_data: Dict) -> List[SerpElement]:
        """解析有机搜索结果"""
        organic_results = []
        
        # 处理SERP API格式
        if 'organic_results' in search_data:
            results = search_data['organic_results']
            for i, result in enumerate(results):
                element = self._create_serp_element(
                    element_type='organic',
                    position=i + 1,
                    result_data=result
                )
                if element:
                    organic_results.append(element)
        
        # 处理Google Custom Search API格式
        elif 'items' in search_data:
            results = search_data['items']
            for i, result in enumerate(results):
                element = self._create_serp_element(
                    element_type='organic',
                    position=i + 1,
                    result_data=result
                )
                if element:
                    organic_results.append(element)
        
        return organic_results
    
    def _parse_paid_results(self, search_data: Dict) -> List[SerpElement]:
        """解析付费广告结果"""
        paid_results = []
        
        # 处理广告结果
        ads = search_data.get('ads', [])
        for i, ad in enumerate(ads):
            element = self._create_serp_element(
                element_type='ad',
                position=i + 1,
                result_data=ad
            )
            if element:
                paid_results.append(element)
        
        # 处理购物广告
        shopping_results = search_data.get('shopping_results', [])
        for i, shopping in enumerate(shopping_results):
            element = self._create_serp_element(
                element_type='shopping',
                position=i + 1,
                result_data=shopping
            )
            if element:
                paid_results.append(element)
        
        return paid_results
    
    def _parse_special_features(self, search_data: Dict) -> List[SerpElement]:
        """解析特殊SERP功能"""
        special_features = []
        
        # 精选摘要
        if 'answer_box' in search_data:
            element = self._create_serp_element(
                element_type='featured_snippet',
                position=0,
                result_data=search_data['answer_box']
            )
            if element:
                special_features.append(element)
        
        # 知识面板
        if 'knowledge_graph' in search_data:
            element = self._create_serp_element(
                element_type='knowledge_panel',
                position=0,
                result_data=search_data['knowledge_graph']
            )
            if element:
                special_features.append(element)
        
        # 图片结果
        image_results = search_data.get('images_results', [])
        if image_results:
            element = SerpElement(
                element_type='images',
                position=0,
                title='图片结果',
                url='',
                domain='',
                snippet=f'包含{len(image_results)}个图片结果',
                additional_data={'count': len(image_results)}
            )
            special_features.append(element)
        
        # 视频结果
        video_results = search_data.get('video_results', [])
        if video_results:
            element = SerpElement(
                element_type='videos',
                position=0,
                title='视频结果',
                url='',
                domain='',
                snippet=f'包含{len(video_results)}个视频结果',
                additional_data={'count': len(video_results)}
            )
            special_features.append(element)
        
        # 新闻结果
        news_results = search_data.get('news_results', [])
        if news_results:
            element = SerpElement(
                element_type='news',
                position=0,
                title='新闻结果',
                url='',
                domain='',
                snippet=f'包含{len(news_results)}个新闻结果',
                additional_data={'count': len(news_results)}
            )
            special_features.append(element)
        
        return special_features
    
    def _create_serp_element(self, element_type: str, position: int, result_data: Dict) -> Optional[SerpElement]:
        """创建SERP元素对象"""
        try:
            # 提取基础信息
            title = result_data.get('title', '')
            url = result_data.get('link', result_data.get('url', ''))
            snippet = result_data.get('snippet', result_data.get('description', ''))
            
            if not url:
                return None
            
            # 解析域名
            domain = urlparse(url).netloc.lower()
            
            # 提取额外数据
            additional_data = {}
            
            # 根据元素类型提取特定数据
            if element_type == 'shopping':
                additional_data.update({
                    'price': result_data.get('price'),
                    'rating': result_data.get('rating'),
                    'reviews': result_data.get('reviews'),
                    'merchant': result_data.get('merchant')
                })
            elif element_type == 'ad':
                additional_data.update({
                    'ad_position': result_data.get('position'),
                    'display_url': result_data.get('displayed_link')
                })
            elif element_type == 'featured_snippet':
                additional_data.update({
                    'snippet_type': result_data.get('type'),
                    'source_url': result_data.get('link')
                })
            
            return SerpElement(
                element_type=element_type,
                position=position,
                title=title,
                url=url,
                domain=domain,
                snippet=snippet,
                additional_data=additional_data
            )
            
        except Exception as e:
            print(f"创建SERP元素失败: {e}")
            return None
    
    def _analyze_competitor(self, result: SerpElement) -> Optional[CompetitorInfo]:
        """分析单个竞争对手"""
        try:
            # 识别竞争对手类型
            competitor_type = self._identify_competitor_type(result.url)
            
            # 获取域名权重
            domain_authority = self._get_domain_authority(result.domain)
            
            # 估算页面权重
            page_authority = self._estimate_page_authority(result)
            
            # 识别内容类型
            content_type = self._identify_content_type(result.url)
            
            # 评估品牌强度
            brand_strength = self._evaluate_brand_strength(result.domain, domain_authority)
            
            # 分析SEO信号
            seo_signals = self._analyze_seo_signals(result)
            
            return CompetitorInfo(
                domain=result.domain,
                url=result.url,
                title=result.title,
                position=result.position,
                competitor_type=competitor_type,
                domain_authority=domain_authority,
                page_authority=page_authority,
                content_type=content_type,
                brand_strength=brand_strength,
                seo_signals=seo_signals
            )
            
        except Exception as e:
            print(f"分析竞争对手失败: {e}")
            return None
    
    def _identify_competitor_type(self, url: str) -> str:
        """识别竞争对手类型"""
        parsed_url = urlparse(url)
        domain_parts = parsed_url.netloc.split('.')
        
        # 检查子域名
        if len(domain_parts) > 2:
            subdomain = domain_parts[0]
            if subdomain not in ['www', 'm']:
                return 'subdomain'
        
        # 检查URL路径深度
        path = parsed_url.path.strip('/')
        if not path:
            return 'domain'
        
        path_segments = [seg for seg in path.split('/') if seg]
        if len(path_segments) <= 1:
            return 'domain'
        else:
            return 'inner_page'
    
    def _get_domain_authority(self, domain: str) -> int:
        """获取域名权重"""
        # 检查内置数据库
        if domain in self.domain_authority_db:
            return self.domain_authority_db[domain]
        
        # 基于域名特征估算
        score = 30  # 基础分数
        
        # TLD加分
        if domain.endswith('.edu'):
            score += 25
        elif domain.endswith('.gov'):
            score += 30
        elif domain.endswith('.org'):
            score += 15
        elif domain.endswith('.com'):
            score += 5
        
        # 域名长度影响
        domain_name = domain.split('.')[0]
        if len(domain_name) < 8:
            score += 10
        elif len(domain_name) > 15:
            score -= 5
        
        # 特殊模式识别
        patterns = {
            'wiki': 20, 'news': 15, 'blog': 10, 'shop': 5,
            'store': 5, 'tool': 8, 'app': 8, 'ai': 12
        }
        
        for pattern, bonus in patterns.items():
            if pattern in domain:
                score += bonus
                break
        
        return min(max(score, 1), 100)
    
    def _estimate_page_authority(self, result: SerpElement) -> int:
        """估算页面权重"""
        domain_authority = self._get_domain_authority(result.domain)
        page_authority = domain_authority
        
        # URL深度影响
        parsed_url = urlparse(result.url)
        path_depth = len([seg for seg in parsed_url.path.strip('/').split('/') if seg])
        
        if path_depth == 0:
            page_authority += 15  # 首页
        elif path_depth == 1:
            page_authority += 5   # 一级页面
        elif path_depth > 3:
            page_authority -= 10  # 深层页面
        
        # 标题优化程度
        if result.title:
            title_len = len(result.title)
            if 30 <= title_len <= 60:
                page_authority += 8
            elif title_len > 80:
                page_authority -= 5
        
        # URL结构优化
        if '-' in parsed_url.path or '_' in parsed_url.path:
            page_authority += 3
        
        return min(max(page_authority, 1), 100)
    
    def _identify_content_type(self, url: str) -> str:
        """识别内容类型"""
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        for content_type, patterns in self.content_patterns.items():
            for pattern in patterns:
                if re.search(pattern, path):
                    return content_type
        
        return 'unknown'
    
    def _evaluate_brand_strength(self, domain: str, domain_authority: int) -> str:
        """评估品牌强度"""
        if domain_authority >= 80:
            return 'strong'
        elif domain_authority >= 60:
            return 'medium'
        elif domain_authority >= 40:
            return 'weak'
        else:
            return 'unknown'
    
    def _analyze_seo_signals(self, result: SerpElement) -> Dict[str, Any]:
        """分析SEO信号"""
        signals = {
            'title_length': len(result.title) if result.title else 0,
            'has_https': result.url.startswith('https://'),
            'url_length': len(result.url),
            'snippet_length': len(result.snippet) if result.snippet else 0,
            'domain_age_estimate': self._estimate_domain_age(result.domain),
            'seo_score': 0.0
        }
        
        # 计算SEO评分
        seo_score = 0.0
        
        # 标题长度优化
        title_len = signals['title_length']
        if 30 <= title_len <= 60:
            seo_score += 0.2
        elif title_len > 0:
            seo_score += 0.1
        
        # HTTPS加分
        if signals['has_https']:
            seo_score += 0.1
        
        # URL长度
        if signals['url_length'] < 100:
            seo_score += 0.1
        
        # 摘要长度
        snippet_len = signals['snippet_length']
        if 120 <= snippet_len <= 160:
            seo_score += 0.15
        elif snippet_len > 0:
            seo_score += 0.05
        
        signals['seo_score'] = min(seo_score, 1.0)
        
        return signals
    
    def _estimate_domain_age(self, domain: str) -> str:
        """估算域名年龄"""
        # 基于域名权重和知名度估算
        if domain in self.domain_authority_db:
            authority = self.domain_authority_db[domain]
            if authority >= 90:
                return 'very_old'  # 10年以上
            elif authority >= 70:
                return 'old'       # 5-10年
            elif authority >= 50:
                return 'medium'    # 2-5年
            else:
                return 'new'       # 2年以下
        
        return 'unknown'
    
    def _calculate_competition_metrics(self, organic_results: List[SerpElement], 
                                     paid_results: List[SerpElement], 
                                     special_features: List[SerpElement]) -> Dict[str, float]:
        """计算竞争指标"""
        metrics = {
            'organic_density': 0.0,
            'paid_density': 0.0,
            'feature_density': 0.0,
            'domain_diversity': 0.0,
            'authority_concentration': 0.0,
            'commercial_intent': 0.0
        }
        
        total_elements = len(organic_results) + len(paid_results) + len(special_features)
        
        if total_elements > 0:
            metrics['organic_density'] = len(organic_results) / total_elements
            metrics['paid_density'] = len(paid_results) / total_elements
            metrics['feature_density'] = len(special_features) / total_elements
        
        # 域名多样性
        if organic_results:
            unique_domains = len(set(result.domain for result in organic_results))
            metrics['domain_diversity'] = unique_domains / len(organic_results)
        
        # 权重集中度
        if organic_results:
            authorities = [self._get_domain_authority(result.domain) for result in organic_results[:5]]
            avg_authority = sum(authorities) / len(authorities)
            metrics['authority_concentration'] = avg_authority / 100
        
        # 商业意图强度
        commercial_indicators = len(paid_results) + len([f for f in special_features if f.element_type == 'shopping'])
        metrics['commercial_intent'] = min(commercial_indicators / 5, 1.0)
        
        return metrics
    
    def _calculate_difficulty_score(self, organic_results: List[SerpElement], 
                                  competition_metrics: Dict[str, float]) -> float:
        """计算竞争难度评分"""
        if not organic_results:
            return 0.0
        
        difficulty = 0.0
        
        # 权重分布
        weights = {
            'authority_concentration': 0.35,  # 权威域名集中度
            'paid_density': 0.20,           # 付费广告密度
            'feature_density': 0.15,        # 特殊功能密度
            'domain_diversity': 0.15,       # 域名多样性（反向）
            'top_competitor_strength': 0.15  # 顶级竞争对手强度
        }
        
        # 权威域名集中度
        difficulty += competition_metrics.get('authority_concentration', 0) * weights['authority_concentration']
        
        # 付费广告密度
        difficulty += competition_metrics.get('paid_density', 0) * weights['paid_density']
        
        # 特殊功能密度
        difficulty += competition_metrics.get('feature_density', 0) * weights['feature_density']
        
        # 域名多样性（低多样性=高难度）
        diversity = competition_metrics.get('domain_diversity', 1.0)
        difficulty += (1.0 - diversity) * weights['domain_diversity']
        
        # 顶级竞争对手强度
        if organic_results:
            top_competitor = organic_results[0]
            top_authority = self._get_domain_authority(top_competitor.domain)
            difficulty += (top_authority / 100) * weights['top_competitor_strength']
        
        return min(difficulty, 1.0)
    
    def _calculate_opportunity_score(self, organic_results: List[SerpElement], 
                                   competition_metrics: Dict[str, float], 
                                   difficulty_score: float) -> float:
        """计算机会评分"""
        if not organic_results:
            return 0.0
        
        opportunity = 1.0 - difficulty_score  # 基础机会分数
        
        # 机会调整因子
        adjustments = 0.0
        
        # 弱竞争对手存在
        weak_competitors = 0
        for result in organic_results[:5]:
            authority = self._get_domain_authority(result.domain)
            if authority < 50:
                weak_competitors += 1
        
        if weak_competitors >= 2:
            adjustments += 0.2
        elif weak_competitors >= 1:
            adjustments += 0.1
        
        # 内页竞争多
        inner_page_competitors = 0
        for result in organic_results[:5]:
            if self._identify_competitor_type(result.url) == 'inner_page':
                inner_page_competitors += 1
        
        if inner_page_competitors >= 3:
            adjustments += 0.15
        elif inner_page_competitors >= 2:
            adjustments += 0.1
        
        # 商业意图适中（不太高不太低）
        commercial_intent = competition_metrics.get('commercial_intent', 0)
        if 0.2 <= commercial_intent <= 0.6:
            adjustments += 0.1
        
        opportunity = min(opportunity + adjustments, 1.0)
        return max(opportunity, 0.0)
    
    def _extract_total_results(self, search_data: Dict) -> int:
        """提取总结果数"""
        # SERP API格式
        if 'search_information' in search_data:
            return search_data['search_information'].get('total_results', 0)
        
        # Google Custom Search API格式
        if 'searchInformation' in search_data:
            return int(search_data['searchInformation'].get('totalResults', 0))
        
        return 0
    
    def _create_empty_structure(self, keyword: str) -> SerpStructure:
        """创建空的SERP结构"""
        return SerpStructure(
            keyword=keyword,
            total_results=0,
            organic_results=[],
            paid_results=[],
            special_features=[],
            competition_metrics={},
            difficulty_score=0.0,
            opportunity_score=0.0,
            analysis_timestamp=datetime.now().isoformat()
        )
    
    def export_to_dict(self, serp_structure: SerpStructure) -> Dict:
        """导出为字典格式"""
        return asdict(serp_structure)
    
    def export_to_json(self, serp_structure: SerpStructure, indent: int = 2) -> str:
        """导出为JSON格式"""
        return json.dumps(self.export_to_dict(serp_structure), 
                         ensure_ascii=False, indent=indent)


# 使用示例和测试
if __name__ == "__main__":
    # 创建解析器实例
    parser = SerpParser()
    
    # 模拟搜索数据
    mock_search_data = {
        "organic_results": [
            {
                "title": "Best AI Image Generator Tools 2024",
                "link": "https://example.com/ai-image-generators",
                "snippet": "Discover the top AI image generation tools..."
            },
            {
                "title": "Free AI Image Generator - Create Images Online",
                "link": "https://aitools.com/image-generator",
                "snippet": "Generate stunning images with our free AI tool..."
            }
        ],
        "ads": [
            {
                "title": "Professional AI Image Generator",
                "link": "https://premium-ai.com/generator",
                "snippet": "Create professional images with AI..."
            }
        ],
        "search_information": {
            "total_results": 1250000
        }
    }
    
    # 解析SERP结构
    keyword = "ai image generator"
    serp_structure = parser.parse_serp_structure(mock_search_data, keyword)
    
    # 输出结果
    print("SERP数据结构化解析结果:")
    print(f"关键词: {serp_structure.keyword}")
    print(f"总结果数: {serp_structure.total_results}")
    print(f"有机结果数: {len(serp_structure.organic_results)}")
    print(f"付费结果数: {len(serp_structure.paid_results)}")
    print(f"竞争难度: {serp_structure.difficulty_score:.2f}")
    print(f"机会评分: {serp_structure.opportunity_score:.2f}")
    
    # 提取竞争对手信息
    competitors = parser.extract_competitor_info(serp_structure.organic_results)
    print(f"\n竞争对手分析 ({len(competitors)}个):")
    for comp in competitors:
        print(f"- {comp.domain} (位置{comp.position}, DA:{comp.domain_authority}, 类型:{comp.competitor_type})")