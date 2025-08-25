#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Google Trends 数据采集模块"""

import pandas as pd
import time
import requests
import json
import urllib.parse
from pytrends.request import TrendReq
import argparse
from src.utils import FileUtils, Logger
from src.utils.constants import GOOGLE_TRENDS_CONFIG
from config.config_manager import get_config

config = get_config()

class TrendsCollector:
    """Google Trends 数据采集类"""
    
    API_CONFIG = {
        'base_urls': {
            'explore': 'https://trends.google.com/trends/api/explore',
            'related_searches': 'https://trends.google.com/trends/api/widgetdata/relatedsearches'
        },
        'default_params': {
            'hl': GOOGLE_TRENDS_CONFIG['default_language'],
            'tz': GOOGLE_TRENDS_CONFIG['default_timezone'],
            'geo': GOOGLE_TRENDS_CONFIG['default_geo'],
            'timeframe': GOOGLE_TRENDS_CONFIG['default_timeframe'],
            'category': 0,
            'property': ''
        },
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://trends.google.com/'
        },
        'rate_limits': GOOGLE_TRENDS_CONFIG['rate_limits']
    }
    
    def __init__(self, hl=None, tz=None, timeout=(20, 30), retries=3, backoff_factor=1.5):
        self.hl = hl or self.API_CONFIG['default_params']['hl']
        self.tz = tz or self.API_CONFIG['default_params']['tz']
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.logger = Logger()
        
        self.pytrends = TrendReq(hl=self.hl, tz=self.tz, timeout=self.timeout)
        self.session = requests.Session()
        self._init_session()
        
        pd.set_option('future.no_silent_downcasting', True)
    
    def _init_session(self):
        """初始化Session"""
        try:
            response = self.session.get('https://trends.google.com/', 
                                      headers={'User-Agent': self.API_CONFIG['headers']['User-Agent']}, 
                                      timeout=30)
            if response.status_code == 200:
                self.logger.info(f"Session初始化成功")
        except Exception as e:
            self.logger.warning(f"Session初始化失败: {e}")

    def _make_api_request(self, request_type, keyword=None, geo=None, timeframe=None, 
                         widget_token=None, widget_request=None):
        """统一API请求方法"""
        time.sleep(1)
        
        geo = geo or self.API_CONFIG['default_params']['geo']
        timeframe = timeframe or self.API_CONFIG['default_params']['timeframe']
        
        try:
            if request_type == 'explore':
                url = self.API_CONFIG['base_urls']['explore']
                req_data = {
                    "comparisonItem": [{
                        "keyword": keyword,
                        "geo": geo,
                        "time": timeframe,
                        "category": 0,
                        "property": ""
                    }]
                }
                params = {
                    "hl": self.hl,
                    "tz": self.tz,
                    "req": json.dumps(req_data)
                }
            else:  # related_searches
                url = self.API_CONFIG['base_urls']['related_searches']
                params = {
                    'hl': self.hl,
                    'tz': self.tz,
                    'req': json.dumps(widget_request),
                    'token': widget_token
                }
            
            full_url = f"{url}?{urllib.parse.urlencode(params)}"
            response = self.session.get(full_url, headers=self.API_CONFIG['headers'], timeout=self.timeout)
            
            if response.status_code == 200:
                content = response.text
                if content.startswith(")]}',"):
                    content = content[5:]
                elif content.startswith(")]}"):
                    content = content[4:]
                return json.loads(content)
            elif response.status_code == 429:
                self.logger.error("API请求过于频繁，等待5秒")
                time.sleep(5)
                return None
            else:
                self.logger.error(f"API请求失败: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"请求异常: {e}")
            return None
    
    def _parse_related_queries(self, data):
        """解析相关查询数据"""
        queries = []
        try:
            if 'default' in data and 'rankedList' in data['default']:
                for ranked_list in data['default']['rankedList']:
                    for item in ranked_list.get('rankedKeyword', []):
                        query = item.get('query', '')
                        value = item.get('value', 0)
                        formatted_value = item.get('formattedValue', '0')
                        
                        growth = formatted_value if '%' in str(formatted_value) else f"{value}%"
                        queries.append({
                            'query': query,
                            'value': value,
                            'growth': growth
                        })
            
            return pd.DataFrame(queries) if queries else pd.DataFrame(columns=['query', 'value', 'growth'])
        except Exception as e:
            self.logger.error(f"解析数据出错: {e}")
            return pd.DataFrame(columns=['query', 'value', 'growth'])
    
    def _fetch_trending_via_api(self, geo=None, timeframe=None):
        """通过API获取热门关键词"""
        all_data = []
        
        try:
            explore_response = self._make_api_request('explore', keyword="", geo=geo, timeframe=timeframe)
            
            if explore_response and 'widgets' in explore_response:
                for widget in explore_response['widgets']:
                    if widget.get('id') == 'RELATED_QUERIES' and widget.get('type') == 'fe_related_searches':
                        token = widget.get('token')
                        widget_request = widget.get('request')
                        
                        if token and widget_request:
                            related_response = self._make_api_request('related_searches', 
                                                                    widget_token=token, 
                                                                    widget_request=widget_request)
                            if related_response:
                                df = self._parse_related_queries(related_response)
                                if not df.empty:
                                    df['source'] = 'api'
                                    all_data.append(df)
        except Exception as e:
            self.logger.error(f"API获取热门关键词出错: {e}")
        
        if not all_data:
            return pd.DataFrame(columns=['query', 'value', 'growth'])
        
        combined_df = pd.concat(all_data, ignore_index=True)
        if 'query' in combined_df.columns:
            combined_df = combined_df.drop_duplicates(subset=['query'], keep='first')
            if 'value' in combined_df.columns:
                combined_df = combined_df.sort_values('value', ascending=False)
        
        return combined_df
    
    def get_trending_searches(self, geo=None):
        """获取热门搜索"""
        geo = geo or self.API_CONFIG['default_params']['geo']
        
        try:
            trending_searches = self.pytrends.trending_searches(pn=geo)
            
            if trending_searches is not None and not trending_searches.empty:
                trending_searches.columns = ['query']
                trending_searches['value'] = range(100, 100 - len(trending_searches), -1)
                trending_searches['growth'] = 'Trending'
                return trending_searches
            else:
                return pd.DataFrame(columns=['query', 'value', 'growth'])
        except Exception as e:
            self.logger.error(f"获取热门搜索出错: {e}")
            return pd.DataFrame(columns=['query', 'value', 'growth'])
    
    def fetch_rising_queries(self, keyword=None, geo=None, timeframe=None):
        """获取Rising Queries"""
        geo = geo or self.API_CONFIG['default_params']['geo']
        timeframe = timeframe or self.API_CONFIG['default_params']['timeframe']
        
        if not keyword or not keyword.strip():
            return self._fetch_trending_via_api(geo=geo, timeframe=timeframe)
        
        time.sleep(1)
        
        for attempt in range(self.retries):
            try:
                self.pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
                related_queries = self.pytrends.related_queries()
                
                if keyword in related_queries and related_queries[keyword]:
                    rising = related_queries[keyword]['rising']
                    top = related_queries[keyword]['top']
                    
                    if rising is not None and not rising.empty:
                        return rising
                    elif top is not None and not top.empty:
                        top['growth'] = 0
                        return top
                
                return pd.DataFrame(columns=['query', 'value', 'growth'])
                    
            except Exception as e:
                if attempt < self.retries - 1:
                    wait_time = self.backoff_factor * (2 ** attempt)
                    self.logger.warning(f"获取数据出错，等待{wait_time:.1f}秒重试: {e}")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"多次尝试失败: {e}")
                    return pd.DataFrame(columns=['query', 'value', 'growth'])
        return None

    def fetch_multiple_keywords(self, keywords, geo=None, timeframe=None):
        """批量获取关键词数据"""
        results = {}
        batch_delay = self.API_CONFIG['rate_limits']['batch_delay']
        
        for i, keyword in enumerate(keywords):
            df = self.fetch_rising_queries(keyword, geo, timeframe)
            if not df.empty:
                df['seed_keyword'] = keyword
                results[keyword] = df
            
            if i < len(keywords) - 1:
                time.sleep(batch_delay)
        
        return results
    
    def collect_rising_queries(self, keywords, geo=None, timeframe=None):
        """统一接口"""
        results = self.fetch_multiple_keywords(keywords, geo, timeframe)
        
        if results:
            all_df = pd.concat(results.values(), ignore_index=True)
            
            if 'value' in all_df.columns:
                all_df = all_df.rename(columns={'value': 'volume'})
            
            if 'growth' in all_df.columns:
                def parse_growth(growth_val):
                    if pd.isna(growth_val) or growth_val == 0:
                        return 0
                    if isinstance(growth_val, str):
                        return float(growth_val.replace('%', '').replace('+', ''))
                    return float(growth_val)
                
                all_df['growth_rate'] = all_df['growth'].apply(parse_growth)
            else:
                all_df['growth_rate'] = 0
            
            return all_df
        else:
            return pd.DataFrame(columns=['query', 'volume', 'growth_rate', 'seed_keyword'])
    
    def get_keyword_trends(self, keywords, geo=None, timeframe=None):
        """获取关键词趋势数据"""
        geo = geo or self.API_CONFIG['default_params']['geo']
        timeframe = timeframe or self.API_CONFIG['default_params']['timeframe']
        
        if isinstance(keywords, list):
            keyword = keywords[0] if keywords else None
        else:
            keyword = keywords
        
        if not keyword or not keyword.strip():
            try:
                df = self.fetch_rising_queries(None, geo=geo, timeframe=timeframe)
                return {
                    'keyword': 'trending_keywords_via_api',
                    'related_queries': df.to_dict('records') if not df.empty else [],
                    'total_queries': len(df),
                    'avg_volume': float(df['value'].mean()) if not df.empty and 'value' in df.columns else 0.0,
                    'status': 'success' if not df.empty else 'no_data',
                    'data_type': 'trending_keywords_via_api'
                }
            except Exception as e:
                return {
                    'keyword': 'trending_keywords_via_api',
                    'related_queries': [],
                    'total_queries': 0,
                    'avg_volume': 0.0,
                    'status': 'error',
                    'error': str(e),
                    'data_type': 'trending_keywords_via_api'
                }
        
        try:
            df = self.fetch_rising_queries(keyword, geo, timeframe)
            
            if not df.empty:
                return {
                    'keyword': keyword,
                    'related_queries': df.to_dict('records'),
                    'total_queries': len(df),
                    'avg_volume': float(df['value'].mean()) if 'value' in df.columns else 0.0,
                    'status': 'success'
                }
            else:
                return {
                    'keyword': keyword,
                    'related_queries': [],
                    'total_queries': 0,
                    'avg_volume': 0.0,
                    'status': 'no_data'
                }
        except Exception as e:
            return {
                'keyword': keyword,
                'related_queries': [],
                'total_queries': 0,
                'avg_volume': 0.0,
                'status': 'error',
                'error': str(e)
            }
    
    def save_results(self, results, output_dir='data'):
        """保存结果"""
        all_df = pd.concat(results.values(), ignore_index=True) if results else pd.DataFrame()
        
        if not all_df.empty:
            all_filename = FileUtils.generate_filename('trends_all', extension='csv')
            all_file = FileUtils.save_dataframe(all_df, output_dir, all_filename)
            self.logger.info(f"已保存所有结果到: {all_file}")
            
            for keyword, df in results.items():
                safe_keyword = FileUtils.clean_filename(keyword)
                individual_filename = FileUtils.generate_filename(f'trends_{safe_keyword}', extension='csv')
                file_path = FileUtils.save_dataframe(df, output_dir, individual_filename)
                self.logger.info(f"已保存 '{keyword}' 的结果到: {file_path}")
        else:
            self.logger.warning("没有数据可保存")

