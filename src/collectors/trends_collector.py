#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Google Trends 数据采集模块"""

import pandas as pd
import time
import requests
import json
import urllib.parse
from .custom_trends_collector import CustomTrendsCollector
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
        
        # 使用单例模式获取 trends collector，不再创建独立的session
        try:
            from .trends_singleton import get_trends_collector
            self.trends_collector = get_trends_collector()
            self.logger.info("Session初始化成功")
        except Exception as e:
            self.logger.error(f"Session初始化失败: {e}")
            self.trends_collector = None
            
        pd.set_option('future.no_silent_downcasting', True)

    def get_trends_data(self, keywords, timeframe='today 12-m', geo=''):
        """
        获取关键词趋势数据
        
        Args:
            keywords: 关键词列表或单个关键词
            timeframe: 时间范围，默认过去12个月
            geo: 地理位置，默认全球
            
        Returns:
            pandas.DataFrame: 趋势数据
        """
        if not self.trends_collector:
            self.logger.error("trends_collector 未初始化")
            return pd.DataFrame()
            
        try:
            # 确保keywords是列表格式
            if isinstance(keywords, str):
                keywords = [keywords]
            
            # 打印请求参数用于调试
            self.logger.info(f"🔍 正在请求Google Trends数据:")
            self.logger.info(f"   关键词: {keywords}")
            self.logger.info(f"   时间范围: {timeframe}")
            self.logger.info(f"   地理位置: {geo}")
            
            # 构建payload
            self.trends_collector.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo, gprop='')
            
            # 获取兴趣度数据
            interest_over_time = self.trends_collector.interest_over_time()
            
            if not interest_over_time.empty:
                # 移除 'isPartial' 列
                if 'isPartial' in interest_over_time.columns:
                    interest_over_time = interest_over_time.drop('isPartial', axis=1)
                
                self.logger.info(f"✅ 成功获取到 {len(interest_over_time)} 条趋势数据")
                return interest_over_time
            else:
                self.logger.warning(f"⚠️ 未获取到关键词 {keywords} 的趋势数据")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"❌ 获取趋势数据失败: {e}")
            self.logger.error(f"   请求参数: keywords={keywords}, timeframe={timeframe}, geo={geo}")
            return pd.DataFrame()

    def _make_api_request(self, request_type, keyword=None, geo=None, timeframe=None, 
                         widget_token=None, widget_request=None):
        """统一API请求方法"""
        time.sleep(1)
        
        geo = geo or self.API_CONFIG['default_params']['geo']
        timeframe = timeframe or self.API_CONFIG['default_params']['timeframe']
        
        try:
            if request_type == 'explore':
                url = self.API_CONFIG['base_urls']['explore']
                params = {
                    'hl': self.hl,
                    'tz': self.tz,
                    'req': json.dumps({
                        'comparisonItem': [{
                            'keyword': keyword,
                            'geo': geo,
                            'time': timeframe
                        }],
                        'category': 0,
                        'property': ''
                    })
                }
            elif request_type == 'related_searches':
                url = self.API_CONFIG['base_urls']['related_searches']
                params = {
                    'hl': self.hl,
                    'tz': self.tz,
                    'req': json.dumps(widget_request),
                    'token': widget_token
                }
            
            full_url = f"{url}?{urllib.parse.urlencode(params)}"
            
            # 打印完整的请求URL用于调试
            self.logger.debug(f"🔍 正在请求URL: {full_url}")
            self.logger.debug(f"📋 请求参数: {params}")
            
            # 使用trends_collector的session进行请求
            if self.trends_collector and hasattr(self.trends_collector, 'session'):
                response = self.trends_collector.session.get(full_url, headers=self.API_CONFIG['headers'], timeout=self.timeout)
            else:
                self.logger.error("trends_collector未初始化或没有session")
                return None
            
            # 打印响应状态
            self.logger.info(f"📡 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                if content.startswith(")]}',"):
                    content = content[5:]
                elif content.startswith(")]}'"):
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
            self.logger.error(f"API请求异常: {e}")
            return None

    def fetch_rising_queries(self, keyword=None, geo=None, timeframe=None):
        """获取Rising Queries - 兼容方法"""
        if not self.trends_collector:
            self.logger.error("trends_collector 未初始化")
            return []
            
        try:
            return self.trends_collector.fetch_rising_queries(keyword, geo, timeframe)
        except Exception as e:
            self.logger.error(f"获取Rising Queries失败: {e}")
            return []

    def get_related_queries(self, keyword, geo='', timeframe='today 12-m'):
        """获取相关查询"""
        if not self.trends_collector:
            self.logger.error("trends_collector 未初始化")
            return {}
            
        try:
            # 构建payload
            self.trends_collector.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo, gprop='')
            
            # 获取相关查询
            related_queries = self.trends_collector.related_queries()
            return related_queries
        except Exception as e:
            self.logger.error(f"获取相关查询失败: {e}")
            return {}

    def get_related_topics(self, keyword, geo='', timeframe='today 12-m'):
        """获取相关主题"""
        if not self.trends_collector:
            self.logger.error("trends_collector 未初始化")
            return {}
            
        try:
            # 构建payload
            self.trends_collector.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo, gprop='')
            
            # 获取相关主题
            related_topics = self.trends_collector.related_topics()
            return related_topics
        except Exception as e:
            self.logger.error(f"获取相关主题失败: {e}")
            return {}

    def get_interest_by_region(self, keyword, geo='', timeframe='today 12-m'):
        """获取按地区分布的兴趣度"""
        if not self.trends_collector:
            self.logger.error("trends_collector 未初始化")
            return pd.DataFrame()
            
        try:
            # 构建payload
            self.trends_collector.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo, gprop='')
            
            # 获取地区兴趣度
            interest_by_region = self.trends_collector.interest_by_region()
            return interest_by_region
        except Exception as e:
            self.logger.error(f"获取地区兴趣度失败: {e}")
            return pd.DataFrame()

    def get_suggestions(self, keyword):
        """获取关键词建议"""
        if not self.trends_collector:
            self.logger.error("trends_collector 未初始化")
            return []
            
        try:
            suggestions = self.trends_collector.suggestions(keyword)
            return suggestions
        except Exception as e:
            self.logger.error(f"获取关键词建议失败: {e}")
            return []

    def trending_searches(self, pn='united_states'):
        """获取热门搜索"""
        if not self.trends_collector:
            self.logger.error("trends_collector 未初始化")
            return pd.DataFrame()
            
        try:
            trending = self.trends_collector.trending_searches(pn)
            return trending
        except Exception as e:
            self.logger.error(f"获取热门搜索失败: {e}")
            return pd.DataFrame()

    def get_historical_interest(self, keyword, start_date, end_date=None):
        """获取历史兴趣数据"""
        if not self.trends_collector:
            self.logger.error("trends_collector 未初始化")
            return pd.DataFrame()
            
        try:
            historical_data = self.trends_collector.get_historical_interest(keyword, start_date, end_date)
            return historical_data
        except Exception as e:
            self.logger.error(f"获取历史兴趣数据失败: {e}")
            return pd.DataFrame()


def main():
    """主函数 - 用于测试"""
    parser = argparse.ArgumentParser(description='Google Trends 数据采集工具')
    parser.add_argument('--keyword', '-k', type=str, required=True, help='要查询的关键词')
    parser.add_argument('--geo', '-g', type=str, default='', help='地理位置 (如: US, CN)')
    parser.add_argument('--timeframe', '-t', type=str, default='today 12-m', help='时间范围')
    parser.add_argument('--output', '-o', type=str, help='输出文件路径')
    
    args = parser.parse_args()
    
    # 创建采集器实例
    collector = TrendsCollector()
    
    print(f"🔍 正在查询关键词: {args.keyword}")
    print(f"📍 地理位置: {args.geo or '全球'}")
    print(f"⏰ 时间范围: {args.timeframe}")
    print("-" * 50)
    
    # 获取趋势数据
    trends_data = collector.get_trends_data(args.keyword, args.timeframe, args.geo)
    
    if not trends_data.empty:
        print("✅ 趋势数据获取成功!")
        print(f"📊 数据行数: {len(trends_data)}")
        print("\n📈 前5行数据:")
        print(trends_data.head())
        
        if args.output:
            trends_data.to_csv(args.output, index=False)
            print(f"💾 数据已保存到: {args.output}")
    else:
        print("❌ 未获取到趋势数据")
    
    # 获取相关查询
    print("\n🔍 获取相关查询...")
    related_queries = collector.get_related_queries(args.keyword, args.geo, args.timeframe)
    
    if related_queries:
        print("✅ 相关查询获取成功!")
        for query_type, queries in related_queries.items():
            if not queries.empty:
                print(f"\n📋 {query_type}:")
                print(queries.head())
    else:
        print("❌ 未获取到相关查询")


if __name__ == "__main__":
    main()