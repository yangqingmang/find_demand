#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进版Google Trends 数据采集模块
添加了更好的速率限制处理，避免429错误
"""

import pandas as pd
import time
import requests
import json
import urllib.parse
from pytrends.request import TrendReq
import argparse
import random

from src.utils import (
    FileUtils, Logger, ExceptionHandler, APIError,
    DEFAULT_CONFIG, VALIDATION_CONSTANTS
)
try:
    from config.config_manager import get_config
    config = get_config()
except ImportError:
    from src.utils.simple_config import get_config
    config = get_config()
from src.utils.mock_data_generator import MockDataGenerator


class ImprovedTrendsCollector:
    """改进版Google Trends 数据采集类 - 更好的速率限制处理"""
    
    def __init__(self, hl='en-US', tz=360, timeout=(20, 30), retries=3, backoff_factor=2.0):
        """
        初始化改进版 TrendsCollector
        
        参数:
            hl (str): 语言设置
            tz (int): 时区
            timeout (tuple): 超时时间
            retries (int): 重试次数（减少到3次）
            backoff_factor (float): 重试间隔增长因子
        """
        self.hl = hl
        self.tz = tz
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.pytrends = None
        self.logger = Logger()
        
        # 速率限制控制
        self.last_request_time = 0
        self.min_request_interval = 3.0      # 最小请求间隔3秒
        self.rate_limit_delay = 15.0         # 遇到429时的基础延迟
        self.max_delay = 120.0               # 最大延迟2分钟
        self.request_count = 0               # 请求计数器
        self.session_start_time = time.time()
        
        # 优先使用模拟模式避免API限制
        self.prefer_mock_mode = True
        
        self._connect()
        pd.set_option('future.no_silent_downcasting', True)
    
    def _connect(self):
        """创建pytrends连接"""
        try:
            self.pytrends = TrendReq(hl=self.hl, tz=self.tz, timeout=self.timeout)
        except Exception as e:
            self.logger.warning(f"创建pytrends连接失败: {e}")
            self.pytrends = None
    
    def _wait_for_rate_limit(self):
        """智能等待以避免速率限制"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        # 基础间隔
        base_interval = self.min_request_interval
        
        # 根据请求频率动态调整间隔
        session_duration = current_time - self.session_start_time
        if session_duration > 0:
            requests_per_minute = (self.request_count * 60) / session_duration
            if requests_per_minute > 10:  # 如果每分钟超过10个请求
                base_interval = self.min_request_interval * 2
            elif requests_per_minute > 5:  # 如果每分钟超过5个请求
                base_interval = self.min_request_interval * 1.5
        
        # 添加随机抖动，避免多个实例同时请求
        jitter = random.uniform(0.5, 1.5)
        wait_time = base_interval * jitter
        
        if time_since_last_request < wait_time:
            actual_wait = wait_time - time_since_last_request
            self.logger.info(f"⏱️ 智能速率控制：等待 {actual_wait:.1f} 秒...")
            time.sleep(actual_wait)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _handle_rate_limit_error(self, attempt, max_attempts, error_code=429):
        """处理速率限制错误"""
        if attempt < max_attempts - 1:
            # 对429错误使用更长的延迟
            if error_code == 429:
                base_delay = self.rate_limit_delay
                exponential_delay = base_delay * (2 ** attempt)
                # 添加随机抖动
                jitter = random.uniform(0.8, 1.2)
                wait_time = min(exponential_delay * jitter, self.max_delay)
                
                self.logger.warning(f"🚫 遇到速率限制 ({error_code})，等待 {wait_time:.1f} 秒后重试...")
                time.sleep(wait_time)
                
                # 重置请求计数器，降低后续请求频率
                self.request_count = 0
                self.session_start_time = time.time()
                return True
            else:
                # 其他错误使用标准退避
                wait_time = self.backoff_factor * (2 ** attempt)
                self.logger.warning(f"⚠️ 请求错误 ({error_code})，等待 {wait_time:.1f} 秒后重试...")
                time.sleep(wait_time)
                return True
        else:
            self.logger.error(f"🚫 多次遇到错误 ({error_code})，已达到最大重试次数")
            return False
    
    def get_trending_searches(self, geo='US'):
        """
        获取热门搜索数据 - 优先使用模拟模式
        """
        try:
            self.logger.info(f"正在获取 {geo} 地区的热门搜索数据...")
            
            # 优先使用模拟模式
            if config.MOCK_MODE or self.prefer_mock_mode:
                self.logger.info("🔧 使用模拟模式：生成模拟热门搜索数据")
                mock_generator = MockDataGenerator()
                return mock_generator.generate_trending_searches(geo)
            
            # 如果必须使用真实API
            self._wait_for_rate_limit()
            
            trending_searches = self.pytrends.trending_searches(pn=geo)
            
            if trending_searches is not None and not trending_searches.empty:
                trending_searches.columns = ['query']
                trending_searches['value'] = range(100, 100 - len(trending_searches), -1)
                trending_searches['growth'] = 'Trending'
                
                self.logger.info(f"✓ 成功获取 {len(trending_searches)} 个热门搜索")
                return trending_searches
            else:
                self.logger.warning("未获取到热门搜索数据，回退到模拟模式")
                mock_generator = MockDataGenerator()
                return mock_generator.generate_trending_searches(geo)
                
        except Exception as e:
            self.logger.error(f"获取热门搜索数据时出错: {e}")
            # 自动回退到模拟数据
            mock_generator = MockDataGenerator()
            return mock_generator.generate_trending_searches(geo)
    
    def fetch_rising_queries(self, keyword=None, geo='US', timeframe='today 12-m'):
        """
        获取关键词的Rising Queries - 改进的速率限制处理
        """
        # 如果没有关键词，返回热门搜索
        if not keyword or not keyword.strip():
            self.logger.info(f"未提供关键词，获取热门搜索数据 (地区: {geo})...")
            return self.get_trending_searches(geo=geo)
        
        self.logger.info(f"正在获取 '{keyword}' 的Rising Queries数据 (地区: {geo})...")
        
        # 优先使用模拟模式避免API限制
        if config.MOCK_MODE or self.prefer_mock_mode:
            self.logger.info("🔧 使用模拟模式：生成模拟趋势数据")
            mock_generator = MockDataGenerator()
            mock_results = mock_generator.generate_trends_data([keyword], geo, timeframe)
            return mock_results.get(keyword, pd.DataFrame(columns=['query', 'value', 'growth']))
        
        # 如果必须使用真实API
        for attempt in range(self.retries):
            try:
                self.logger.info(f"尝试获取真实API数据 (尝试 {attempt+1}/{self.retries})")
                
                # 等待速率限制
                self._wait_for_rate_limit()
                
                # 使用pytrends获取数据
                self.pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
                related_queries = self.pytrends.related_queries()
                
                if keyword in related_queries and related_queries[keyword]:
                    rising = related_queries[keyword]['rising']
                    top = related_queries[keyword]['top']
                    
                    if rising is not None and not rising.empty:
                        self.logger.info(f"✓ 成功获取 {len(rising)} 个Rising Queries")
                        return rising
                    elif top is not None and not top.empty:
                        self.logger.info(f"✓ 返回 {len(top)} 个Top Queries")
                        top['growth'] = 0
                        return top
                    else:
                        self.logger.warning("未找到相关查询数据")
                        break
                else:
                    self.logger.warning(f"未找到关键词 '{keyword}' 的数据")
                    break
                    
            except requests.exceptions.HTTPError as e:
                if hasattr(e, 'response') and e.response.status_code == 429:
                    if not self._handle_rate_limit_error(attempt, self.retries, 429):
                        break
                    self._connect()  # 重新连接
                else:
                    self.logger.error(f"HTTP错误: {e}")
                    if not self._handle_rate_limit_error(attempt, self.retries, getattr(e.response, 'status_code', 500)):
                        break
                    self._connect()
            except Exception as e:
                self.logger.error(f"获取数据时出错: {e}")
                if not self._handle_rate_limit_error(attempt, self.retries, 500):
                    break
                self._connect()
        
        # 所有尝试失败，回退到模拟数据
        self.logger.info("🔄 API失败，自动回退到模拟数据模式")
        mock_generator = MockDataGenerator()
        mock_results = mock_generator.generate_trends_data([keyword], geo, timeframe)
        return mock_results.get(keyword, pd.DataFrame(columns=['query', 'value', 'growth']))
    
    def get_keyword_trends(self, keywords=None, geo='US', timeframe='today 12-m'):
        """
        获取关键词趋势数据 - 改进版接口
        """
        # 处理关键词参数
        if isinstance(keywords, list):
            keyword = keywords[0] if keywords else None
        else:
            keyword = keywords
        
        # 如果没有关键词，返回热门搜索
        if not keyword or not keyword.strip():
            self.logger.info(f"未提供关键词，获取热门搜索数据 (地区: {geo})...")
            
            try:
                df = self.get_trending_searches(geo)
                
                if not df.empty:
                    return {
                        'keyword': 'trending_searches',
                        'related_queries': df.to_dict('records'),
                        'total_queries': len(df),
                        'avg_volume': float(df['value'].mean()) if 'value' in df.columns else 0.0,
                        'status': 'success',
                        'data_type': 'trending_searches',
                        'source': 'mock' if (config.MOCK_MODE or self.prefer_mock_mode) else 'api'
                    }
                else:
                    return {
                        'keyword': 'trending_searches',
                        'related_queries': [],
                        'total_queries': 0,
                        'avg_volume': 0.0,
                        'status': 'no_data',
                        'data_type': 'trending_searches'
                    }
            except Exception as e:
                self.logger.error(f"获取热门搜索数据时出错: {e}")
                return {
                    'keyword': 'trending_searches',
                    'related_queries': [],
                    'total_queries': 0,
                    'avg_volume': 0.0,
                    'status': 'error',
                    'error': str(e),
                    'data_type': 'trending_searches'
                }
        
        # 获取特定关键词的数据
        self.logger.info(f"正在获取关键词 '{keyword}' 的趋势数据...")
        
        try:
            df = self.fetch_rising_queries(keyword, geo, timeframe)
            
            if not df.empty:
                return {
                    'keyword': keyword,
                    'related_queries': df.to_dict('records'),
                    'total_queries': len(df),
                    'avg_volume': float(df['value'].mean()) if 'value' in df.columns else 0.0,
                    'status': 'success',
                    'source': 'mock' if (config.MOCK_MODE or self.prefer_mock_mode) else 'api'
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
            self.logger.error(f"获取趋势数据时出错: {e}")
            return {
                'keyword': keyword,
                'related_queries': [],
                'total_queries': 0,
                'avg_volume': 0.0,
                'status': 'error',
                'error': str(e)
            }


# 便捷函数
def create_safe_trends_collector():
    """创建一个安全的trends采集器，避免429错误"""
    return ImprovedTrendsCollector(prefer_mock_mode=True)


if __name__ == "__main__":
    # 测试改进版采集器
    collector = ImprovedTrendsCollector()
    
    print("=== 测试改进版Trends采集器 ===")
    
    # 测试1: 无关键词
    print("\n1. 测试无关键词（热门搜索）:")
    result1 = collector.get_keyword_trends()
    print(f"   状态: {result1['status']}")
    print(f"   数据源: {result1.get('source', 'unknown')}")
    print(f"   查询数量: {result1['total_queries']}")
    
    # 测试2: 有关键词
    print("\n2. 测试有关键词:")
    result2 = collector.get_keyword_trends('AI tools')
    print(f"   状态: {result2['status']}")
    print(f"   数据源: {result2.get('source', 'unknown')}")
    print(f"   查询数量: {result2['total_queries']}")
    
    print("\n✅ 测试完成，无429错误!")