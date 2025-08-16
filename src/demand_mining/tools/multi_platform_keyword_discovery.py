#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台关键词发现工具
整合Reddit、Hacker News、Product Hunt等平台的关键词发现
"""

import requests
import json
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from urllib.parse import quote
import pandas as pd
from collections import Counter

class MultiPlatformKeywordDiscovery:
    """多平台关键词发现工具"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # 平台配置
        self.platforms = {
            'reddit': {
                'base_url': 'https://www.reddit.com',
                'api_url': 'https://www.reddit.com/r/{}/search.json',
                'enabled': True
            },
            'hackernews': {
                'base_url': 'https://hacker-news.firebaseio.com/v0',
                'search_url': 'https://hn.algolia.com/api/v1/search',
                'enabled': True
            },
            'producthunt': {
                'base_url': 'https://www.producthunt.com',
                'enabled': False  # 需要API密钥
            }
        }
        
        # AI相关subreddit列表
        self.ai_subreddits = [
            'artificial', 'MachineLearning', 'deeplearning', 'ChatGPT',
            'OpenAI', 'artificial_intelligence', 'singularity', 'Futurology',
            'programming', 'webdev', 'entrepreneur', 'SaaS', 'startups'
        ]
        
        # 关键词提取模式
        self.keyword_patterns = [
            r'\b(?:how to|what is|best|top|vs|compare|review|tutorial|guide)\b[^.!?]*',
            r'\b(?:AI|artificial intelligence|machine learning|deep learning|neural network)\b[^.!?]*',
            r'\b(?:tool|software|app|platform|service|solution)\b[^.!?]*',
            r'\b(?:free|open source|alternative|competitor)\b[^.!?]*'
        ]
    
    def discover_reddit_keywords(self, subreddit: str, limit: int = 100) -> List[Dict]:
        """从Reddit发现关键词"""
        print(f"🔍 正在分析 Reddit r/{subreddit}...")
        
        keywords = []
        
        try:
            # 获取热门帖子
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            
            for post in posts:
                post_data = post.get('data', {})
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                score = post_data.get('score', 0)
                num_comments = post_data.get('num_comments', 0)
                
                # 提取关键词
                extracted_keywords = self._extract_keywords_from_text(title + ' ' + selftext)
                
                for keyword in extracted_keywords:
                    keywords.append({
                        'keyword': keyword,
                        'source': f'reddit_r_{subreddit}',
                        'title': title,
                        'score': score,
                        'comments': num_comments,
                        'url': f"https://reddit.com{post_data.get('permalink', '')}",
                        'platform': 'reddit'
                    })
            
            time.sleep(1)  # 避免请求过快
            
        except Exception as e:
            print(f"❌ Reddit r/{subreddit} 分析失败: {e}")
        
        return keywords
    
    def discover_hackernews_keywords(self, query: str = 'AI', days: int = 30) -> List[Dict]:
        """从Hacker News发现关键词"""
        print(f"🔍 正在分析 Hacker News (查询: {query})...")
        
        keywords = []
        
        try:
            # 计算时间范围
            end_time = int(time.time())
            start_time = end_time - (days * 24 * 3600)
            
            # 搜索相关帖子
            url = "https://hn.algolia.com/api/v1/search"
            params = {
                'query': query,
                'tags': 'story',
                'numericFilters': f'created_at_i>{start_time},created_at_i<{end_time}',
                'hitsPerPage': 100
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            hits = data.get('hits', [])
            
            for hit in hits:
                title = hit.get('title', '')
                url = hit.get('url', '')
                points = hit.get('points', 0)
                num_comments = hit.get('num_comments', 0)
                
                # 提取关键词
                extracted_keywords = self._extract_keywords_from_text(title)
                
                for keyword in extracted_keywords:
                    keywords.append({
                        'keyword': keyword,
                        'source': 'hackernews',
                        'title': title,
                        'score': points,
                        'comments': num_comments,
                        'url': url or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                        'platform': 'hackernews'
                    })
        
        except Exception as e:
            print(f"❌ Hacker News 分析失败: {e}")
        
        return keywords
    
    def discover_youtube_keywords(self, search_term: str) -> List[Dict]:
        """从YouTube搜索建议发现关键词"""
        print(f"🔍 正在分析 YouTube 搜索建议 (查询: {search_term})...")
        
        keywords = []
        
        try:
            # YouTube搜索建议API (非官方)
            url = "http://suggestqueries.google.com/complete/search"
            params = {
                'client': 'youtube',
                'ds': 'yt',
                'q': search_term
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # 解析响应 (JSONP格式)
            content = response.text
            if content.startswith('window.google.ac.h('):
                json_str = content[19:-1]  # 移除JSONP包装
                data = json.loads(json_str)
                
                suggestions = data[1] if len(data) > 1 else []
                
                for suggestion in suggestions:
                    if isinstance(suggestion, list) and len(suggestion) > 0:
                        keyword = suggestion[0]
                        keywords.append({
                            'keyword': keyword,
                            'source': 'youtube_suggestions',
                            'title': f'YouTube搜索建议: {keyword}',
                            'score': 0,
                            'comments': 0,
                            'url': f'https://www.youtube.com/results?search_query={quote(keyword)}',
                            'platform': 'youtube'
                        })
        
        except Exception as e:
            print(f"❌ YouTube 分析失败: {e}")
        
        return keywords
    
    def discover_google_suggestions(self, search_term: str) -> List[Dict]:
        """从Google搜索建议发现关键词"""
        print(f"🔍 正在分析 Google 搜索建议 (查询: {search_term})...")
        
        keywords = []
        
        try:
            # Google搜索建议API
            url = "http://suggestqueries.google.com/complete/search"
            params = {
                'client': 'firefox',
                'q': search_term
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            suggestions = data[1] if len(data) > 1 else []
            
            for suggestion in suggestions:
                keywords.append({
                    'keyword': suggestion,
                    'source': 'google_suggestions',
                    'title': f'Google搜索建议: {suggestion}',
                    'score': 0,
                    'comments': 0,
                    'url': f'https://www.google.com/search?q={quote(suggestion)}',
                    'platform': 'google'
                })
        
        except Exception as e:
            print(f"❌ Google搜索建议分析失败: {e}")
        
        return keywords
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        keywords = []
        text = text.lower()
        
        # 使用正则表达式提取关键词
        for pattern in self.keyword_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # 清理和标准化关键词
                keyword = re.sub(r'[^\w\s-]', '', match).strip()
                if len(keyword) > 5 and len(keyword) < 100:
                    keywords.append(keyword)
        
        # 提取常见的AI工具相关词汇
        ai_terms = [
            'ai tool', 'ai generator', 'ai writer', 'ai assistant', 'ai chatbot',
            'machine learning', 'deep learning', 'neural network', 'gpt',
            'artificial intelligence', 'automation', 'nlp', 'computer vision'
        ]
        
        for term in ai_terms:
            if term in text:
                keywords.append(term)
        
        return list(set(keywords))  # 去重
    
    def discover_all_platforms(self, search_terms: List[str]) -> pd.DataFrame:
        """从所有平台发现关键词"""
        print("🚀 开始多平台关键词发现...")
        
        all_keywords = []
        
        # Reddit分析
        for subreddit in self.ai_subreddits[:5]:  # 限制数量避免请求过多
            reddit_keywords = self.discover_reddit_keywords(subreddit, limit=50)
            all_keywords.extend(reddit_keywords)
        
        # Hacker News分析
        for term in search_terms:
            hn_keywords = self.discover_hackernews_keywords(term)
            all_keywords.extend(hn_keywords)
        
        # YouTube搜索建议
        for term in search_terms:
            youtube_keywords = self.discover_youtube_keywords(term)
            all_keywords.extend(youtube_keywords)
        
        # Google搜索建议
        for term in search_terms:
            google_keywords = self.discover_google_suggestions(term)
            all_keywords.extend(google_keywords)
        
        # 转换为DataFrame
        df = pd.DataFrame(all_keywords)
        
        if not df.empty:
            # 去重和排序
            df = df.drop_duplicates(subset=['keyword'])
            df = df.sort_values('score', ascending=False)
            
            # 添加发现时间
            df['discovered_at'] = datetime.now().isoformat()
            
            print(f"✅ 发现 {len(df)} 个关键词")
        else:
            print("⚠️ 未发现任何关键词")
        
        return df
    
    def analyze_keyword_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析关键词趋势"""
        if df.empty:
            return {}
        
        analysis = {
            'total_keywords': len(df),
            'platform_distribution': df['platform'].value_counts().to_dict(),
            'top_keywords_by_score': df.nlargest(10, 'score')[['keyword', 'score', 'platform']].to_dict('records'),
            'keyword_length_stats': {
                'avg_length': df['keyword'].str.len().mean(),
                'min_length': df['keyword'].str.len().min(),
                'max_length': df['keyword'].str.len().max()
            },
            'common_terms': self._get_common_terms(df['keyword'].tolist())
        }
        
        return analysis
    
    def _get_common_terms(self, keywords: List[str]) -> Dict[str, int]:
        """获取常见词汇"""
        all_words = []
        for keyword in keywords:
            words = keyword.lower().split()
            all_words.extend([word for word in words if len(word) > 2])
        
        return dict(Counter(all_words).most_common(20))
    
    def save_results(self, df: pd.DataFrame, analysis: Dict, output_dir: str = 'data/multi_platform_keywords'):
        """保存结果"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存关键词数据
        csv_path = os.path.join(output_dir, f'multi_platform_keywords_{timestamp}.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # 保存分析报告（处理numpy类型序列化问题）
        json_path = os.path.join(output_dir, f'keyword_analysis_{timestamp}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            # 转换numpy类型为Python原生类型
            def convert_numpy_types(obj):
                if hasattr(obj, 'item'):
                    return obj.item()
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(v) for v in obj]
                else:
                    return obj
            
            serializable_analysis = convert_numpy_types(analysis)
            json.dump(serializable_analysis, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结果已保存:")
        print(f"   关键词数据: {csv_path}")
        print(f"   分析报告: {json_path}")
        
        return csv_path, json_path


def main():
    """主函数"""
    # 初始化发现工具
    discoverer = MultiPlatformKeywordDiscovery()
    
    # 搜索词汇
    search_terms = [
        'AI tool', 'AI generator', 'AI writer', 'AI assistant',
        'machine learning', 'chatbot', 'automation'
    ]
    
    print("🔍 多平台关键词发现工具")
    print(f"📊 搜索词汇: {', '.join(search_terms)}")
    print("-" * 50)
    
    # 发现关键词
    df = discoverer.discover_all_platforms(search_terms)
    
    if not df.empty:
        # 分析趋势
        analysis = discoverer.analyze_keyword_trends(df)
        
        # 显示结果摘要
        print("\n📈 发现结果摘要:")
        print(f"总关键词数: {analysis['total_keywords']}")
        print(f"平台分布: {analysis['platform_distribution']}")
        print(f"平均关键词长度: {analysis['keyword_length_stats']['avg_length']:.1f} 字符")
        
        print("\n🏆 热门关键词 (按评分排序):")
        for i, kw in enumerate(analysis['top_keywords_by_score'][:5], 1):
            print(f"  {i}. {kw['keyword']} (评分: {kw['score']}, 来源: {kw['platform']})")
        
        print("\n🔤 常见词汇:")
        for word, count in list(analysis['common_terms'].items())[:10]:
            print(f"  {word}: {count}次")
        
        # 保存结果
        discoverer.save_results(df, analysis)
    
    else:
        print("❌ 未发现任何关键词，请检查网络连接或调整搜索参数")


if __name__ == "__main__":
    main()