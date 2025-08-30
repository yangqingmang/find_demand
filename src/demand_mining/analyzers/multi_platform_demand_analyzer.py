#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台需求分析器
通过搜索Reddit、GitHub等平台来验证关键词需求和发现痛点
"""

import asyncio
import json
import os
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import requests
from urllib.parse import quote
import time
import random

logger = logging.getLogger(__name__)

class MultiPlatformDemandAnalyzer:
    """多平台需求分析器"""
    
    def __init__(self, output_dir: str = "output/reports"):
        """
        初始化多平台需求分析器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        self.platforms = {
            'reddit': self._search_reddit,
            'github': self._search_github,
            'stackoverflow': self._search_stackoverflow
        }
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 用户代理
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info("✅ 多平台需求分析器初始化完成")
    
    async def analyze_high_opportunity_keywords(
        self, 
        keywords_data: List[Dict], 
        min_opportunity_score: float = 70.0,
        max_keywords: int = 5
    ) -> Dict[str, Any]:
        """
        分析高机会关键词的多平台需求
        
        Args:
            keywords_data: 关键词数据列表
            min_opportunity_score: 最小机会分数阈值
            max_keywords: 最大分析关键词数量
            
        Returns:
            分析结果字典
        """
        logger.info(f"🔍 开始多平台需求分析，阈值: {min_opportunity_score}")
        
        # 筛选高机会关键词
        high_opportunity_keywords = []
        for kw_data in keywords_data:
            score = kw_data.get('opportunity_score', 0)
            if score >= min_opportunity_score:
                high_opportunity_keywords.append(kw_data)
        
        # 限制分析数量
        high_opportunity_keywords = high_opportunity_keywords[:max_keywords]
        
        if not high_opportunity_keywords:
            logger.warning("⚠️ 未找到符合条件的高机会关键词")
            return {
                'analyzed_keywords': 0,
                'platform_results': {},
                'summary': {
                    'total_discussions': 0,
                    'pain_points': [],
                    'opportunities': []
                }
            }
        
        logger.info(f"📊 找到 {len(high_opportunity_keywords)} 个高机会关键词")
        
        # 分析每个关键词
        results = {
            'analyzed_keywords': len(high_opportunity_keywords),
            'platform_results': {},
            'summary': {
                'total_discussions': 0,
                'pain_points': [],
                'opportunities': []
            }
        }
        
        for kw_data in high_opportunity_keywords:
            keyword = kw_data.get('keyword', '')
            logger.info(f"🔍 分析关键词: {keyword}")
            
            keyword_results = await self._analyze_keyword_across_platforms(keyword)
            results['platform_results'][keyword] = keyword_results
            
            # 更新总结
            for platform_data in keyword_results.values():
                results['summary']['total_discussions'] += platform_data.get('total_results', 0)
                results['summary']['pain_points'].extend(platform_data.get('pain_points', []))
                results['summary']['opportunities'].extend(platform_data.get('opportunities', []))
        
        # 去重和排序
        results['summary']['pain_points'] = list(set(results['summary']['pain_points']))[:10]
        results['summary']['opportunities'] = list(set(results['summary']['opportunities']))[:10]
        
        logger.info(f"✅ 多平台需求分析完成，共分析 {results['analyzed_keywords']} 个关键词")
        
        return results
    
    async def _analyze_keyword_across_platforms(self, keyword: str) -> Dict[str, Any]:
        """
        跨平台分析单个关键词
        
        Args:
            keyword: 关键词
            
        Returns:
            平台分析结果
        """
        platform_results = {}
        
        for platform_name, search_func in self.platforms.items():
            try:
                logger.info(f"  🔍 搜索 {platform_name}...")
                result = await search_func(keyword)
                platform_results[platform_name] = result
                
                # 添加延迟避免被限制
                await asyncio.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"❌ {platform_name} 搜索失败: {e}")
                platform_results[platform_name] = {
                    'total_results': 0,
                    'discussions': [],
                    'pain_points': [],
                    'opportunities': [],
                    'error': str(e)
                }
        
        return platform_results
    
    async def _search_reddit(self, keyword: str) -> Dict[str, Any]:
        """
        搜索Reddit讨论
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            Reddit搜索结果
        """
        try:
            # 使用Reddit搜索API（无需认证）
            search_url = f"https://www.reddit.com/search.json"
            params = {
                'q': keyword,
                'sort': 'relevance',
                'limit': 10,
                't': 'month'  # 最近一个月
            }
            
            response = requests.get(search_url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('data', {}).get('children', [])
                
                discussions = []
                pain_points = []
                opportunities = []
                
                for post in posts[:5]:  # 只分析前5个结果
                    post_data = post.get('data', {})
                    title = post_data.get('title', '')
                    selftext = post_data.get('selftext', '')
                    score = post_data.get('score', 0)
                    num_comments = post_data.get('num_comments', 0)
                    
                    discussion = {
                        'title': title,
                        'content': selftext[:200] + '...' if len(selftext) > 200 else selftext,
                        'score': score,
                        'comments': num_comments,
                        'url': f"https://reddit.com{post_data.get('permalink', '')}"
                    }
                    discussions.append(discussion)
                    
                    # 简单的痛点和机会识别
                    text = (title + ' ' + selftext).lower()
                    
                    # 痛点关键词
                    pain_keywords = ['problem', 'issue', 'bug', 'error', 'difficult', 'hard', 'frustrating', 'slow', 'expensive']
                    for pain_word in pain_keywords:
                        if pain_word in text and len(pain_points) < 5:
                            pain_points.append(f"用户反映{keyword}存在{pain_word}相关问题")
                    
                    # 机会关键词
                    opportunity_keywords = ['need', 'want', 'wish', 'hope', 'better', 'improve', 'feature', 'alternative']
                    for opp_word in opportunity_keywords:
                        if opp_word in text and len(opportunities) < 5:
                            opportunities.append(f"用户希望{keyword}能够{opp_word}")
                
                return {
                    'total_results': len(posts),
                    'discussions': discussions,
                    'pain_points': pain_points,
                    'opportunities': opportunities
                }
            else:
                logger.warning(f"Reddit API返回状态码: {response.status_code}")
                return self._empty_result()
                
        except Exception as e:
            logger.error(f"Reddit搜索异常: {e}")
            return self._empty_result()
    
    async def _search_github(self, keyword: str) -> Dict[str, Any]:
        """
        搜索GitHub Issues
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            GitHub搜索结果
        """
        try:
            # 使用GitHub搜索API（无需认证，但有限制）
            search_url = "https://api.github.com/search/issues"
            params = {
                'q': f"{keyword} is:issue",
                'sort': 'updated',
                'per_page': 5
            }
            
            response = requests.get(search_url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                issues = data.get('items', [])
                
                discussions = []
                pain_points = []
                opportunities = []
                
                for issue in issues:
                    title = issue.get('title', '')
                    body = issue.get('body', '') or ''
                    state = issue.get('state', '')
                    comments = issue.get('comments', 0)
                    
                    discussion = {
                        'title': title,
                        'content': body[:200] + '...' if len(body) > 200 else body,
                        'state': state,
                        'comments': comments,
                        'url': issue.get('html_url', '')
                    }
                    discussions.append(discussion)
                    
                    # 分析痛点和机会
                    text = (title + ' ' + body).lower()
                    
                    if 'bug' in text or 'error' in text:
                        pain_points.append(f"GitHub上有关于{keyword}的bug报告")
                    
                    if 'feature' in text or 'enhancement' in text:
                        opportunities.append(f"用户请求{keyword}的新功能")
                
                return {
                    'total_results': data.get('total_count', 0),
                    'discussions': discussions,
                    'pain_points': pain_points,
                    'opportunities': opportunities
                }
            else:
                logger.warning(f"GitHub API返回状态码: {response.status_code}")
                return self._empty_result()
                
        except Exception as e:
            logger.error(f"GitHub搜索异常: {e}")
            return self._empty_result()
    
    async def _search_stackoverflow(self, keyword: str) -> Dict[str, Any]:
        """
        搜索Stack Overflow问题
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            Stack Overflow搜索结果
        """
        try:
            # 使用Stack Overflow API
            search_url = "https://api.stackexchange.com/2.3/search"
            params = {
                'order': 'desc',
                'sort': 'relevance',
                'intitle': keyword,
                'site': 'stackoverflow',
                'pagesize': 5
            }
            
            response = requests.get(search_url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                questions = data.get('items', [])
                
                discussions = []
                pain_points = []
                opportunities = []
                
                for question in questions:
                    title = question.get('title', '')
                    tags = question.get('tags', [])
                    score = question.get('score', 0)
                    answer_count = question.get('answer_count', 0)
                    
                    discussion = {
                        'title': title,
                        'tags': tags,
                        'score': score,
                        'answers': answer_count,
                        'url': question.get('link', '')
                    }
                    discussions.append(discussion)
                    
                    # 分析技术痛点
                    if answer_count == 0:
                        pain_points.append(f"{keyword}相关问题缺少解决方案")
                    
                    if score > 5:
                        opportunities.append(f"{keyword}是热门技术话题")
                
                return {
                    'total_results': data.get('total', 0),
                    'discussions': discussions,
                    'pain_points': pain_points,
                    'opportunities': opportunities
                }
            else:
                logger.warning(f"Stack Overflow API返回状态码: {response.status_code}")
                return self._empty_result()
                
        except Exception as e:
            logger.error(f"Stack Overflow搜索异常: {e}")
            return self._empty_result()
    
    def _empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            'total_results': 0,
            'discussions': [],
            'pain_points': [],
            'opportunities': []
        }
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """
        保存分析结果
        
        Args:
            results: 分析结果
            
        Returns:
            输出文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON格式
        json_file = os.path.join(self.output_dir, f"demand_validation_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 保存CSV格式的总结
        csv_file = os.path.join(self.output_dir, f"demand_validation_summary_{timestamp}.csv")
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入标题
            writer.writerow(['类型', '内容', '关键词', '平台'])
            
            # 写入痛点
            for pain_point in results['summary']['pain_points']:
                writer.writerow(['痛点', pain_point, '', ''])
            
            # 写入机会
            for opportunity in results['summary']['opportunities']:
                writer.writerow(['机会', opportunity, '', ''])
            
            # 写入详细讨论
            for keyword, platform_data in results['platform_results'].items():
                for platform, data in platform_data.items():
                    for discussion in data.get('discussions', []):
                        writer.writerow([
                            '讨论',
                            discussion.get('title', ''),
                            keyword,
                            platform
                        ])
        
        logger.info(f"📁 需求验证结果已保存到: {json_file}")
        logger.info(f"📁 需求验证总结已保存到: {csv_file}")
        
        return json_file

# 异步运行示例
async def main():
    """测试函数"""
    analyzer = MultiPlatformDemandAnalyzer()
    
    # 模拟关键词数据
    test_keywords = [
        {
            'keyword': 'AI code generator',
            'opportunity_score': 85.5,
            'intent': {'intent_description': 'Commercial'}
        }
    ]
    
    results = await analyzer.analyze_high_opportunity_keywords(test_keywords)
    analyzer.save_results(results)

if __name__ == "__main__":
    asyncio.run(main())