#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台关键词发现工具
整合Reddit、Hacker News、Product Hunt等平台的关键词发现
"""

import requests
import json
import time
import random
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import quote
import pandas as pd
from collections import Counter
import sys
import os

# 添加config目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config'))
from config.config_manager import get_config
from src.pipeline.cleaning.cleaner import standardize_term, is_valid_term, CleaningConfig

class MultiPlatformKeywordDiscovery:
    """多平台关键词发现工具"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        self.request_timeout = 10
        self.max_retries = 3
        self.retry_backoff = (1, 3)
        
        # 加载配置
        self.config = get_config()
        
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
                'base_url': 'https://api.producthunt.com/v2/api/graphql',
                'enabled': bool(self.config.PRODUCTHUNT_API_TOKEN)
            }
        }
        
        # 设置ProductHunt认证头
        if self.config.PRODUCTHUNT_API_TOKEN:
            self.ph_headers = {
                'Authorization': f'Bearer {self.config.PRODUCTHUNT_API_TOKEN}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

        # 请求控制参数
        self._retry_enabled = True

        # AI相关subreddit列表
        self.ai_subreddits = [
            'artificial', 'MachineLearning', 'deeplearning', 'ChatGPT',
            'OpenAI', 'artificial_intelligence', 'singularity', 'Futurology',
            'programming', 'webdev', 'entrepreneur', 'SaaS', 'startups'
        ]
        
        # 关键词提取模式（用于论坛/新闻原始文本）
        self.keyword_patterns = [
            r'\b(?:ai|artificial intelligence|machine learning|deep learning|neural network)\b',
            r'\b(?:tool|software|app|platform|service|solution)\b'
        ]

        self.brand_phrases = {
            'chatgpt', 'openai', 'gpt', 'gpt-4', 'gpt4', 'gpt5', 'claude',
            'midjourney', 'deepseek', 'hix bypass', 'undetectable ai', 'turnitin',
            'copilot'
        }
        self.brand_tokens = {token for phrase in self.brand_phrases for token in phrase.split()}
        self.brand_tokens.update({'chatgpt', 'openai', 'gpt', 'claude', 'midjourney', 'deepseek', 'hix', 'bypass', 'turnitin', 'copilot'})
        self.brand_modifier_tokens = {
            'login', 'logins', 'signup', 'sign', 'account', 'app', 'apps',
            'download', 'downloads', 'premium', 'price', 'prices', 'pricing',
            'cost', 'costs', 'free', 'trial', 'promo', 'discount', 'code',
            'codes', 'coupon', 'review', 'reviews', 'vs', 'versus', 'alternative',
            'alternatives', 'compare', 'comparison', 'checker', 'detector',
            'essay', 'humanizer', 'turnitin', 'unlimited', 'pro', 'plus', 'plan',
            'plans', 'tier', 'tiers', 'lifetime', 'prompt', 'prompts', 'price',
            'pricing'
        }
        self.generic_head_terms = {
            'service', 'services', 'software', 'platform', 'platforms', 'solution',
            'solutions', 'application', 'applications', 'tool', 'tools',
            'machine learning', 'artificial intelligence', 'automation', 'ai',
            'technology', 'technologies', 'gpt'
        }
        self.generic_lead_tokens = {'ai', 'machine', 'software', 'platform', 'service', 'tool', 'technology', 'data'}
        self.generic_tail_tokens = {
            'tool', 'tools', 'software', 'platform', 'platforms', 'service',
            'services', 'application', 'applications', 'app', 'apps', 'solution',
            'solutions', 'system', 'systems', 'suite'
        }
        self.long_tail_tokens = {
            'workflow', 'workflows', 'strategy', 'strategies', 'ideas', 'guide',
            'guides', 'tutorial', 'tutorials', 'template', 'templates', 'checklist',
            'automation', 'process', 'processes', 'plan', 'plans', 'blueprint',
            'blueprints', 'examples', 'case', 'cases', 'study', 'studies', 'use',
            'uses', 'stack', 'stacks', 'integration', 'integrations', 'niche',
            'niches', 'system', 'systems', 'playbook', 'playbooks', 'framework',
            'frameworks', 'marketing', 'seo', 'content', 'workflow', 'roadmap',
            'roadmaps', 'setup', 'automation', 'builders', 'for', 'beginners',
            'advanced', 'agency', 'agencies', 'students', 'writers', 'designers',
            'developers', 'founders', 'startups', 'teams', 'checklists'
        }
        self.question_prefixes = (
            'how to', 'how do', 'how can', 'what is', 'what are', 'why', 'should i',
            'can i', 'is there', 'best way', 'ways to'
        )
        self.max_brand_variations = 5
        self._cleaning_config = CleaningConfig()

    def _request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """对外部请求增加超时与重试机制"""
        kwargs.setdefault('timeout', self.request_timeout)
        attempt = 0
        while True:
            attempt += 1
            try:
                request_func = getattr(self.session, method)
                response = request_func(url, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                if not self._retry_enabled or attempt >= self.max_retries:
                    raise
                sleep_for = random.uniform(*self.retry_backoff)
                time.sleep(sleep_for)

    def discover_reddit_keywords(self, subreddit: str, limit: int = 100) -> List[Dict]:
        """从Reddit发现关键词"""
        print(f"🔍 正在分析 Reddit r/{subreddit}...")
        
        keywords = []
        
        try:
            # 获取热门帖子
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
            response = self._request_with_retry('get', url)

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
            
            response = self._request_with_retry('get', url, params=params)

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
            
            response = self._request_with_retry('get', url, params=params)

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
            
            response = self._request_with_retry('get', url, params=params)

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
    
    def discover_producthunt_keywords(self, search_term: str = "AI", days: int = 30) -> List[Dict]:
        """从ProductHunt发现关键词"""
        print(f"🔍 正在分析 ProductHunt (查询: {search_term})...")
        
        keywords = []
        
        if not self.config.PRODUCTHUNT_API_TOKEN:
            print("⚠️ ProductHunt API Token未配置，跳过ProductHunt分析")
            return keywords
        
        try:
            # ProductHunt GraphQL查询
            query = """
            query($search: String!, $first: Int!) {
              posts(search: $search, first: $first, order: VOTES) {
                edges {
                  node {
                    id
                    name
                    tagline
                    description
                    votesCount
                    commentsCount
                    url
                    topics {
                      edges {
                        node {
                          name
                        }
                      }
                    }
                  }
                }
              }
            }
            """
            
            variables = {
                "search": search_term,
                "first": 50
            }
            
            response = self._request_with_retry(
                'post',
                self.platforms['producthunt']['base_url'],
                headers=self.ph_headers,
                json={
                    'query': query,
                    'variables': variables
                }
            )

            data = response.json()
            
            if 'data' in data and 'posts' in data['data']:
                posts = data['data']['posts']['edges']
                
                for post in posts:
                    node = post['node']
                    name = node.get('name', '')
                    tagline = node.get('tagline', '')
                    description = node.get('description', '')
                    votes = node.get('votesCount', 0)
                    comments = node.get('commentsCount', 0)
                    url = node.get('url', '')
                    
                    # 从产品名称、标语和描述中提取关键词
                    text_content = f"{name} {tagline} {description}"
                    extracted_keywords = self._extract_keywords_from_text(text_content)
                    
                    # 添加主题标签作为关键词
                    topics = node.get('topics', {}).get('edges', [])
                    for topic in topics:
                        topic_name = topic.get('node', {}).get('name', '')
                        if topic_name:
                            extracted_keywords.append(topic_name.lower())
                    
                    for keyword in extracted_keywords:
                        keywords.append({
                            'keyword': keyword,
                            'source': 'producthunt',
                            'title': name,
                            'score': votes,
                            'comments': comments,
                            'url': url,
                            'platform': 'producthunt'
                        })
        
        except Exception as e:
            print(f"❌ ProductHunt 分析失败: {e}")
        
        return keywords
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """从文本中提取关键词（论坛/新闻名词短语抽取 + 模式词）"""
        keywords = []
        text = text.lower()
        try:
            import nltk
            from nltk import pos_tag, word_tokenize, RegexpParser
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
            try:
                nltk.data.find('taggers/averaged_perceptron_tagger')
            except LookupError:
                nltk.download('averaged_perceptron_tagger', quiet=True)
            tokens = word_tokenize(text)
            tagged = pos_tag(tokens)
            grammar = r"NP: {<JJ>*<NN|NNS|NNP|NNPS>+}"
            cp = RegexpParser(grammar)
            tree = cp.parse(tagged)
            nps = []
            for subtree in tree.subtrees(filter=lambda t: t.label() == 'NP'):
                phrase = ' '.join(w for w, t in subtree.leaves())
                nps.append(phrase)
            for np in nps:
                np_clean = re.sub(r'[^a-z0-9\s-]', ' ', np).strip()
                if 3 <= len(np_clean) <= 40 and 1 <= len(np_clean.split()) <= 3:
                    keywords.append(np_clean)
        except Exception:
            pass
        for pattern in self.keyword_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                keyword = re.sub(r'[^a-z0-9\s-]', ' ', match).strip()
                if 3 <= len(keyword) <= 40 and 1 <= len(keyword.split()) <= 3:
                    keywords.append(keyword)
        base = [
            'ai tool', 'ai generator', 'ai writer', 'ai assistant', 'ai chatbot',
            'machine learning', 'deep learning', 'neural network', 'gpt',
            'artificial intelligence', 'automation', 'nlp', 'computer vision'
        ]
        for term in base:
            if term in text and 3 <= len(term) <= 40:
                keywords.append(term)
        return list(set(keywords))
    
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
    
    def _calculate_long_tail_score(self, keyword: str) -> float:
        """
        计算长尾词评分加权
        
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
            base_score *= 3.0  # 5+词汇获得最高加权
        elif word_count >= 4:
            base_score *= 2.5  # 4词汇获得高加权
        elif word_count >= 3:
            base_score *= 2.0  # 3词汇获得中等加权
        
        # 基于意图明确性的加权
        high_intent_phrases = ['how to', 'step by step', 'tutorial', 'guide', 'without', 'for beginners']
        if any(phrase in keyword_lower for phrase in high_intent_phrases):
            base_score *= 1.5
        
        # 基于竞争度的调整
        high_competition_words = ['best', 'top', 'review', 'vs', 'comparison']
        if any(comp in keyword_lower for comp in high_competition_words):
            base_score *= 0.6  # 高竞争词降低评分

        return base_score

    def _is_brand_heavy(self, keyword: str) -> bool:
        """过滤品牌词及其常见附属词"""
        if not keyword:
            return False

        keyword_lower = keyword.lower()
        tokens = [t for t in re.split(r"[^a-z0-9]+", keyword_lower) if t]
        if not tokens:
            return False

        brand_present = any(phrase in keyword_lower for phrase in self.brand_phrases)
        if not brand_present:
            brand_present = any(token in self.brand_tokens for token in tokens)
        if not brand_present:
            return False

        non_brand_tokens = [t for t in tokens if t not in self.brand_tokens]
        if not non_brand_tokens:
            return True

        if all(token in self.brand_modifier_tokens for token in non_brand_tokens):
            return True

        if len(non_brand_tokens) == 1 and non_brand_tokens[0] in self.brand_modifier_tokens:
            return True

        return False

    def _is_underspecified_keyword(self, keyword: str) -> bool:
        """过滤缺乏限定词的泛词"""
        if not keyword:
            return True

        keyword_lower = keyword.lower()
        if keyword_lower in self.generic_head_terms:
            return True

        tokens = [t for t in re.split(r"[^a-z0-9]+", keyword_lower) if t]
        if not tokens:
            return True

        if len(tokens) == 1:
            token = tokens[0]
            return token in self.generic_head_terms or len(token) <= 3

        if len(tokens) == 2:
            joined = " ".join(tokens)
            if joined in self.generic_head_terms:
                return True
            if tokens[0] in self.generic_head_terms and tokens[1] in self.generic_head_terms:
                return True
            if tokens[0] in self.generic_lead_tokens and tokens[1] in self.generic_tail_tokens:
                return True
            if tokens[1] in self.generic_lead_tokens and tokens[0] in self.generic_tail_tokens:
                return True
            if not any(token in self.long_tail_tokens for token in tokens):
                return False

        if any(keyword_lower.startswith(prefix) for prefix in self.question_prefixes):
            return False

        if len(tokens) >= 3:
            informative_tokens = [t for t in tokens if t in self.long_tail_tokens]
            return len(informative_tokens) == 0

        return False

    def _identify_brand(self, keyword: str) -> Optional[str]:
        """识别关键词所属品牌"""
        if not keyword:
            return None

        keyword_lower = keyword.lower()
        for phrase in self.brand_phrases:
            if phrase in keyword_lower:
                return phrase

        tokens = [t for t in re.split(r"[^a-z0-9]+", keyword_lower) if t]
        for token in tokens:
            if token in self.brand_tokens:
                return token
        return None

    def _limit_brand_keywords(self, df: pd.DataFrame) -> pd.DataFrame:
        """限制单一品牌的关键词数量"""
        if df.empty or 'keyword' not in df.columns:
            return df

        keep_indices = []
        brand_counts: Dict[str, int] = {}

        for idx, keyword in df['keyword'].items():
            brand = self._identify_brand(str(keyword))
            if not brand:
                keep_indices.append(idx)
                continue

            count = brand_counts.get(brand, 0)
            if count < self.max_brand_variations:
                keep_indices.append(idx)
                brand_counts[brand] = count + 1

        return df.loc[keep_indices].reset_index(drop=True)
    
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
        # Google搜索建议
        for term in search_terms:
            google_keywords = self.discover_google_suggestions(term)
            all_keywords.extend(google_keywords)
        
        # ProductHunt分析
        if self.platforms['producthunt']['enabled']:
            for term in search_terms:
                ph_keywords = self.discover_producthunt_keywords(term)
                all_keywords.extend(ph_keywords)
        
        # 转换为DataFrame
        df = pd.DataFrame(all_keywords)
        
        if 'keyword' not in df.columns:
            print("⚠️ 结果缺少关键词字段")
            return df

        if not df.empty:
            try:
                df['keyword'] = df['keyword'].astype(str)
                df['normalized_keyword'] = df['keyword'].apply(standardize_term)
                df = df[df['normalized_keyword'].apply(lambda term: is_valid_term(term, self._cleaning_config))]
                df = df.drop_duplicates(subset='normalized_keyword')
                df['keyword'] = df['normalized_keyword']
                df = df.drop(columns=['normalized_keyword'])
            except Exception as exc:
                print(f"⚠️ 关键词清洗失败: {exc}")
                df['keyword'] = df['keyword'].astype(str)

            if df.empty:
                print("⚠️ 清洗后无有效关键词")
            else:
                if 'platform' not in df.columns:
                    df['platform'] = 'unknown'
                else:
                    df['platform'] = df['platform'].fillna('unknown')

                before_brand = len(df)
                df = df[~df['keyword'].apply(self._is_brand_heavy)].reset_index(drop=True)
                if len(df) < before_brand:
                    print(f"⚠️ 移除了 {before_brand - len(df)} 个品牌泛词")

                before_generic = len(df)
                df = df[~df['keyword'].apply(self._is_underspecified_keyword)].reset_index(drop=True)
                if len(df) < before_generic:
                    print(f"⚠️ 移除了 {before_generic - len(df)} 个泛化头部词")

                df = self._limit_brand_keywords(df)

                if df.empty:
                    print("⚠️ 过滤后无有效关键词")
                else:
                    try:
                        from datasketch import MinHash, MinHashLSH
                        from sklearn.cluster import AgglomerativeClustering
                        from sentence_transformers import SentenceTransformer
                        import numpy as np

                        texts = df['keyword'].tolist()

                        def shingles(s, k=3):
                            s = s.replace(' ', '_')
                            return {s[i:i+k] for i in range(max(len(s) - k + 1, 1))}

                        mhashes = []
                        for t in texts:
                            mh = MinHash(num_perm=64)
                            for sh in shingles(t):
                                mh.update(sh.encode('utf-8'))
                            mhashes.append(mh)
                        lsh = MinHashLSH(threshold=0.85, num_perm=64)
                        for idx, mh in enumerate(mhashes):
                            lsh.insert(str(idx), mh)
                        keep_idx = []
                        seen = set()
                        for i, mh in enumerate(mhashes):
                            if i in seen:
                                continue
                            near = lsh.query(mh)
                            grp = sorted(int(x) for x in near)
                            for j in grp:
                                seen.add(j)
                            keep_idx.append(grp[0])
                        df = df.iloc[keep_idx].reset_index(drop=True)

                        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                        emb = model.encode(df['keyword'].tolist(), normalize_embeddings=True)
                        if len(df) >= 5:
                            clustering = AgglomerativeClustering(
                                n_clusters=None,
                                distance_threshold=0.18,
                                affinity='cosine',
                                linkage='average'
                            )
                            labels = clustering.fit_predict(emb)
                            df['cluster_id'] = labels
                            reps = []
                            for c in sorted(set(labels)):
                                idxs = np.where(labels == c)[0]
                                sub = emb[idxs]
                                center = sub.mean(axis=0, keepdims=True)
                                sims = (sub @ center.T).ravel()
                                rep = idxs[int(np.argmax(sims))]
                                reps.append(rep)
                            df = df.iloc[sorted(set(reps))].reset_index(drop=True)
                        else:
                            df['cluster_id'] = 0
                    except Exception:
                        pass

                    df['score'] = 0 if 'score' not in df.columns else df['score']
                    df['long_tail_score'] = df['keyword'].apply(self._calculate_long_tail_score)
                    df['weighted_score'] = df['score'] * df['long_tail_score']
                    df = df.sort_values('weighted_score', ascending=False)
                    df['discovered_at'] = datetime.now().isoformat()
                    print(f"✅ 发现 {len(df)} 个关键词")
        else:
            print("⚠️ 未发现任何关键词")

        return df
    
    def analyze_keyword_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析关键词趋势"""
        if df.empty:
            return {}
        
        platform_distribution = df['platform'].value_counts().to_dict() if 'platform' in df.columns else {}

        score_df = df.copy()
        if 'score' not in score_df.columns:
            score_df['score'] = 0.0
        if 'platform' not in score_df.columns:
            score_df['platform'] = 'unknown'

        top_keywords = score_df.nlargest(10, 'score')[['keyword', 'score', 'platform']].to_dict('records')

        analysis = {
            'total_keywords': len(df),
            'platform_distribution': platform_distribution,
            'top_keywords_by_score': top_keywords,
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


def run_discovery(input_keywords=None, limit=10, output_dir=None, verbose=True):
    """
    运行多平台关键词发现
    
    参数:
        input_keywords: 输入关键词列表，如果为None则使用默认关键词
        limit: 限制使用的关键词数量
        output_dir: 输出目录，如果为None则使用默认目录
        verbose: 是否打印详细信息
    
    返回:
        tuple: (关键词DataFrame, 分析结果字典, 输出CSV路径, 输出JSON路径)
    """
    # 初始化发现工具
    discoverer = MultiPlatformKeywordDiscovery()
    
    # 获取初始关键词
    if input_keywords is None or len(input_keywords) == 0:
        # 使用默认关键词
        search_terms = [
            'AI tool', 'AI generator', 'AI writer', 'AI assistant',
            'machine learning', 'chatbot', 'automation'
        ]
        if verbose:
            print(f"ℹ️ 使用默认关键词: {', '.join(search_terms)}")
    else:
        search_terms = input_keywords
        if verbose:
            print(f"✅ 使用提供的 {len(search_terms)} 个关键词")
    
    # 限制关键词数量
    if limit and len(search_terms) > limit:
        search_terms = search_terms[:limit]
        if verbose:
            print(f"ℹ️ 限制使用前 {limit} 个关键词")
    
    if verbose:
        print("🔍 多平台关键词发现工具")
        print(f"📊 搜索词汇: {', '.join(search_terms)}")
        print("-" * 50)
    
    # 发现关键词
    df = discoverer.discover_all_platforms(search_terms)
    
    if not df.empty:
        # 分析趋势
        analysis = discoverer.analyze_keyword_trends(df)
        
        if verbose:
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
        csv_path, json_path = discoverer.save_results(df, analysis, output_dir=output_dir)
        
        return df, analysis, csv_path, json_path
    else:
        if verbose:
            print("❌ 未发现任何关键词，请检查网络连接或调整搜索参数")
        return pd.DataFrame(), {}, None, None


def main():
    """命令行入口函数"""
    import argparse
    
    # 命令行参数解析
    parser = argparse.ArgumentParser(description="多平台关键词发现工具")
    parser.add_argument("--input", "-i", help="输入关键词文件路径 (CSV格式，包含keyword列)")
    parser.add_argument("--keywords", "-k", help="直接指定关键词，用逗号分隔")
    parser.add_argument("--use-root-words", "-r", action="store_true", help="使用词根趋势数据")
    parser.add_argument("--limit", "-l", type=int, default=10, help="每个来源使用的关键词数量限制")
    parser.add_argument("--output-dir", "-o", help="输出目录")
    args = parser.parse_args()
    
    # 获取初始关键词
    search_terms = []
    
    if args.input:
        # 从CSV文件读取关键词
        try:
            import pandas as pd
            df_input = pd.read_csv(args.input)
            if 'keyword' in df_input.columns:
                search_terms = df_input['keyword'].tolist()
                print(f"✅ 从文件 {args.input} 读取了 {len(search_terms)} 个关键词")
            else:
                print("❌ 输入文件必须包含'keyword'列")
                return
        except Exception as e:
            print(f"❌ 读取输入文件失败: {e}")
            return
    
    elif args.keywords:
        # 直接使用指定的关键词
        search_terms = [k.strip() for k in args.keywords.split(',')]
        print(f"✅ 使用指定的 {len(search_terms)} 个关键词")
    
    elif args.use_root_words:
        # 使用词根相关关键词
        try:
            # 尝试从词根趋势数据目录读取
            root_words_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'root_word_trends')
            if os.path.exists(root_words_dir):
                # 查找最新的词根趋势文件
                files = [f for f in os.listdir(root_words_dir) if f.endswith('.csv')]
                if files:
                    # 按修改时间排序，获取最新文件
                    latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(root_words_dir, f)))
                    file_path = os.path.join(root_words_dir, latest_file)
                    
                    # 读取词根趋势数据
                    import pandas as pd
                    df_roots = pd.read_csv(file_path)
                    if 'keyword' in df_roots.columns:
                        # 获取关键词
                        search_terms = df_roots['keyword'].head(args.limit).tolist()
                        print(f"✅ 从词根趋势文件 {latest_file} 读取了 {len(search_terms)} 个关键词")
                    else:
                        raise ValueError("词根趋势文件缺少'keyword'列")
                else:
                    raise FileNotFoundError("未找到词根趋势CSV文件")
            else:
                raise FileNotFoundError(f"词根趋势目录不存在: {root_words_dir}")
                
        except Exception as e:
            print(f"❌ 读取词根趋势数据失败: {e}")
            # 使用默认关键词作为备选
            search_terms = [
                'AI tool', 'AI generator', 'AI writer', 'AI assistant',
                'machine learning', 'chatbot', 'automation'
            ]
            print(f"⚠️ 使用默认关键词: {', '.join(search_terms)}")
    
    # 运行发现过程
    run_discovery(
        input_keywords=search_terms,
        limit=args.limit,
        output_dir=args.output_dir,
        verbose=True
    )


if __name__ == "__main__":
    main()
    
# 示例用法:
# 1. 命令行使用:
#    - 使用默认关键词: python multi_platform_keyword_discovery.py
#    - 指定关键词: python multi_platform_keyword_discovery.py --keywords "AI tools,machine learning,data science"
#    - 从文件读取: python multi_platform_keyword_discovery.py --input path/to/keywords.csv
#    - 使用词根: python multi_platform_keyword_discovery.py --use-root-words --limit 20
#
# 2. 作为模块导入:
#    from demand_mining.tools.multi_platform_keyword_discovery import run_discovery
#    
#    # 使用主流程中获取的关键词
#    keywords = ["ai writing", "machine learning", "data science"]
#    df, analysis, csv_path, json_path = run_discovery(
#        input_keywords=keywords,
#        limit=10,
#        output_dir="output/multi_platform_keywords",
#        verbose=True
#    )
#    
#    # 使用结果进行后续处理
#    top_keywords = df.head(20)
