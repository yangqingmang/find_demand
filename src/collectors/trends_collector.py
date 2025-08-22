#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Trends 数据采集模块
用于采集Google Trends相关查询数据
"""

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
from src.utils.mock_data_generator import MockDataGenerator

config = get_config()

class TrendsCollector:
    """Google Trends 数据采集类 - 统一API请求管理"""
    
    # 统一的API配置常量 - 使用全局配置
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
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://trends.google.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        },
        'rate_limits': GOOGLE_TRENDS_CONFIG['rate_limits']
    }
    
    def __init__(self, hl=None, tz=None, timeout=(20, 30), retries=5, backoff_factor=2.0):
        """
        初始化 TrendsCollector
        
        参数:
            hl (str): 语言设置，默认使用API_CONFIG中的值
            tz (int): 时区，默认使用API_CONFIG中的值
            timeout (tuple): 连接和读取超时时间(秒)
            retries (int): 重试次数
            backoff_factor (float): 重试间隔增长因子
        """
        # 使用传入参数或默认配置
        self.hl = hl or self.API_CONFIG['default_params']['hl']
        self.tz = tz or self.API_CONFIG['default_params']['tz']
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.pytrends = None
        self.logger = Logger()
        self._connect()
        
        # 速率限制控制
        self.last_request_time = 0
        self.min_request_interval = self.API_CONFIG['rate_limits']['min_request_interval']
        self.rate_limit_delay = self.API_CONFIG['rate_limits']['rate_limit_delay']
        
        # 设置pandas选项，消除警告
        pd.set_option('future.no_silent_downcasting', True)
    
    def _connect(self):
        """创建pytrends连接"""
        self.pytrends = TrendReq(hl=self.hl, tz=self.tz, timeout=self.timeout)

    def _make_unified_trends_request(self, request_type, keyword=None, geo=None, timeframe=None, 
                                   widget_token=None, widget_request=None):
        """
        统一的Google Trends API请求方法
        
        参数:
            request_type (str): 请求类型 ('explore' 或 'related_searches')
            keyword (str): 关键词
            geo (str): 地区代码
            timeframe (str): 时间范围
            widget_token (str): widget token (仅用于related_searches)
            widget_request (dict): widget请求数据 (仅用于related_searches)
            
        返回:
            dict: API响应数据
        """
        # 等待速率限制
        time.sleep(5)
        
        try:
            # 使用默认值填充参数
            geo = geo or self.API_CONFIG['default_params']['geo']
            timeframe = timeframe or self.API_CONFIG['default_params']['timeframe']
            
            # 根据请求类型构建URL和参数
            if request_type == 'explore':
                url = self.API_CONFIG['base_urls']['explore']
                req_data = {
                    "comparisonItem": [{
                        "keyword": keyword,
                        "geo": geo,
                        "time": timeframe,
                        "category": self.API_CONFIG['default_params']['category'],
                        "property": self.API_CONFIG['default_params']['property']
                    }]
                }
                params = {
                    "hl": self.hl,
                    "tz": self.tz,
                    "req": json.dumps(req_data)
                }
            elif request_type == 'related_searches':
                url = self.API_CONFIG['base_urls']['related_searches']
                params = {
                    'hl': self.hl,
                    'tz': self.tz,
                    'req': json.dumps(widget_request),
                    'token': widget_token
                }
            else:
                raise ValueError(f"不支持的请求类型: {request_type}")
            
            # 构建完整URL
            encoded_params = urllib.parse.urlencode(params)
            full_url = f"{url}?{encoded_params}"
            
            self.logger.info(f"🌐 发送{request_type}请求: {url}")
            self.logger.debug(f"📋 请求参数: {params}")
            self.logger.info(f"🔗 完整请求路径: {full_url}")

            
            # 发送POST请求
            response = requests.post(full_url, headers=self.API_CONFIG['headers'], timeout=self.timeout)
            
            if response.status_code == 200:
                # 处理Google Trends API特殊的响应前缀
                content = response.text
                if content.startswith(")]}',"):
                    content = content[5:]  # 去除 ")]}'"
                elif content.startswith(")]}',\n"):
                    content = content[6:]  # 去除 ")]}',\n"
                
                self.logger.info(f"✅ {request_type}请求成功")
                self.logger.debug(f"📄 响应内容前100字符: {content[:100]}")
                return json.loads(content)
            elif response.status_code == 429:
                # 专门处理429错误
                self.logger.error(f"🚫 429 Too Many Requests - API请求过于频繁")
                self.logger.info(f"⏰ 等待 5 秒后重试...")
                time.sleep(5)
                return None
            else:
                self.logger.error(f"❌ {request_type}请求失败，状态码: {response.status_code}")
                self.logger.error(f"📝 响应内容: {response.text[:500]}")
                return None
                
        except Exception as e:
            self.logger.error(f"💥 {request_type}请求出错: {e}")
            return None
    
    def _extract_related_queries_from_response(self, api_response):
        """
        从API响应中提取相关查询数据 - 使用统一的处理逻辑
        
        参数:
            api_response (dict): API响应数据
            
        返回:
            pandas.DataFrame: 相关查询数据
        """
        try:
            if not api_response:
                return pd.DataFrame(columns=['query', 'value', 'growth'])
            
            # 处理explore响应 - 查找相关查询widget
            if 'widgets' in api_response:
                self.logger.info(f"找到 {len(api_response['widgets'])} 个widgets")
                
                for widget in api_response['widgets']:
                    widget_id = widget.get('id', '')
                    widget_type = widget.get('type', '')
                    
                    if widget_id == 'RELATED_QUERIES' and widget_type == 'fe_related_searches':
                        self.logger.info("找到相关查询widget")
                        
                        token = widget.get('token')
                        if not token:
                            self.logger.warning("相关查询widget缺少token")
                            continue
                        
                        # 使用统一方法请求相关查询数据
                        related_response = self._make_unified_trends_request(
                            'related_searches',
                            widget_token=token,
                            widget_request=widget['request']
                        )
                        
                        if related_response:
                            return self._parse_related_queries_data(related_response)
                        
                        break
            
            # 处理related_searches响应
            elif 'default' in api_response:
                return self._parse_related_queries_data(api_response)
            
            return pd.DataFrame(columns=['query', 'value', 'growth'])
            
        except Exception as e:
            self.logger.error(f"提取相关查询数据出错: {e}")
            return pd.DataFrame(columns=['query', 'value', 'growth'])
    
    def _parse_related_queries_data(self, data):
        """
        解析相关查询数据的统一方法
        
        参数:
            data (dict): 相关查询响应数据
            
        返回:
            pandas.DataFrame: 解析后的查询数据
        """
        related_queries_data = []
        
        try:
            if 'default' in data and 'rankedList' in data['default']:
                for ranked_list in data['default']['rankedList']:
                    list_type = ranked_list.get('rankedKeyword', [])
                    
                    for item in list_type:
                        query = item.get('query', '')
                        value = item.get('value', 0)
                        formatted_value = item.get('formattedValue', '0')
                        
                        # 统一处理增长率数据
                        growth = formatted_value
                        if isinstance(formatted_value, str) and '%' in formatted_value:
                            growth = formatted_value
                        elif isinstance(value, (int, float)):
                            growth = f"{value}%"
                        
                        related_queries_data.append({
                            'query': query,
                            'value': value,
                            'growth': growth
                        })
                
                self.logger.info(f"解析了 {len(related_queries_data)} 个相关查询")
            
            return pd.DataFrame(related_queries_data) if related_queries_data else pd.DataFrame(columns=['query', 'value', 'growth'])
            
        except Exception as e:
            self.logger.error(f"解析相关查询数据出错: {e}")
            return pd.DataFrame(columns=['query', 'value', 'growth'])
    
    def get_trending_searches(self, geo=None):
        """
        获取热门搜索数据
        
        参数:
            geo (str): 地区代码，默认使用API_CONFIG中的值
            
        返回:
            pandas.DataFrame: 热门搜索数据
        """
        geo = geo or self.API_CONFIG['default_params']['geo']
        
        try:
            self.logger.info(f"正在获取 {geo} 地区的热门搜索数据...")

            # 使用pytrends获取热门搜索
            trending_searches = self.pytrends.trending_searches(pn=geo)
            
            if trending_searches is not None and not trending_searches.empty:
                # 重命名列以匹配预期格式
                trending_searches.columns = ['query']
                trending_searches['value'] = range(100, 100 - len(trending_searches), -1)
                trending_searches['growth'] = 'Trending'
                
                self.logger.info(f"✓ 成功获取 {len(trending_searches)} 个热门搜索")
                return trending_searches
            else:
                self.logger.warning("未获取到热门搜索数据")
                return pd.DataFrame(columns=['query', 'value', 'growth'])
                
        except Exception as e:
            self.logger.error(f"获取热门搜索数据时出错: {e}")
            return pd.DataFrame(columns=['query', 'value', 'growth'])
    
    def fetch_rising_queries(self, keyword=None, geo=None, timeframe=None):
        """
        获取关键词的Rising Queries - 只使用pytrends避免双重请求
        如果没有提供关键词，返回热门搜索数据
        
        参数:
            keyword (str, optional): 种子关键词，如果为空则返回热门搜索
            geo (str): 地区代码，默认使用API_CONFIG中的值
            timeframe (str): 时间范围，默认使用API_CONFIG中的值
            
        返回:
            pandas.DataFrame: Rising Queries数据或热门搜索数据
        """
        # 使用默认值
        geo = geo or self.API_CONFIG['default_params']['geo']
        timeframe = timeframe or self.API_CONFIG['default_params']['timeframe']
        
        # 如果没有提供关键词，返回热门搜索数据
        if not keyword or not keyword.strip():
            self.logger.info(f"未提供关键词，获取热门搜索数据 (地区: {geo})...")
            return self.get_trending_searches(geo=geo)
        
        self.logger.info(f"正在获取 '{keyword}' 的Rising Queries数据 (地区: {geo})...")

        # 等待速率限制（避免429错误）
        time.sleep(5)
        
        for attempt in range(self.retries):
            try:
                self.logger.info(f"🔍 使用pytrends获取数据 (尝试 {attempt+1}/{self.retries})")
                
                # 只使用pytrends，避免双重请求
                self.pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
                
                # 获取相关查询
                related_queries = self.pytrends.related_queries()
                
                if keyword in related_queries and related_queries[keyword]:
                    rising = related_queries[keyword]['rising']
                    top = related_queries[keyword]['top']
                    
                    if rising is not None and not rising.empty:
                        self.logger.info(f"✅ 成功获取 {len(rising)} 个Rising Queries")
                        return rising
                    elif top is not None and not top.empty:
                        self.logger.info(f"✅ 未找到Rising Queries，返回 {len(top)} 个Top Queries")
                        # 为Top查询添加默认增长率0
                        top['growth'] = 0
                        return top
                    else:
                        self.logger.warning(f"⚠️ 未找到相关查询数据")
                        return pd.DataFrame(columns=['query', 'value', 'growth'])
                else:
                    self.logger.warning(f"⚠️ 未找到关键词 '{keyword}' 的相关查询数据")
                    return pd.DataFrame(columns=['query', 'value', 'growth'])
                    
            except Exception as e:
                wait_time = self.backoff_factor * (2 ** attempt)
                if attempt < self.retries - 1:
                    self.logger.warning(f"⚠️ 获取数据时出错: {e}")
                    self.logger.info(f"⏰ 等待 {wait_time:.1f} 秒后重试 ({attempt+1}/{self.retries})...")
                    time.sleep(wait_time)
                    # 重新连接
                    self._connect()
                else:
                    self.logger.error(f"❌ 多次尝试后仍然失败: {e}")
                    return pd.DataFrame(columns=['query', 'value', 'growth'])
    
    def fetch_multiple_keywords(self, keywords, geo=None, timeframe=None):
        """
        批量获取多个关键词的Rising Queries - 使用统一的延迟配置
        
        参数:
            keywords (list): 种子关键词列表
            geo (str): 地区代码，默认使用API_CONFIG中的值
            timeframe (str): 时间范围，默认使用API_CONFIG中的值
            
        返回:
            dict: 关键词到DataFrame的映射
        """
        # 使用默认值
        geo = geo or self.API_CONFIG['default_params']['geo']
        timeframe = timeframe or self.API_CONFIG['default_params']['timeframe']

        results = {}
        
        for keyword in keywords:
            df = self.fetch_rising_queries(keyword, geo, timeframe)
            if not df.empty:
                df['seed_keyword'] = keyword  # 添加种子关键词列
                results[keyword] = df
            
            # 使用统一的批次延迟配置
            if keyword != keywords[-1]:  # 如果不是最后一个关键词
                batch_delay = self.API_CONFIG['rate_limits']['batch_delay']
                self.logger.info(f"等待{batch_delay}秒以避免API限制...")
                time.sleep(batch_delay)
        
        return results
    
    def collect_rising_queries(self, keywords, geo=None, timeframe=None):
        """
        为主分析器提供的统一接口
        
        参数:
            keywords (list): 种子关键词列表
            geo (str): 地区代码，默认使用API_CONFIG中的值
            timeframe (str): 时间范围，默认使用API_CONFIG中的值
            
        返回:
            pandas.DataFrame: 合并后的所有关键词数据
        """
        results = self.fetch_multiple_keywords(keywords, geo, timeframe)
        
        if results:
            # 合并所有结果
            all_df = pd.concat(results.values(), ignore_index=True)
            
            # 重命名列以匹配预期格式
            if 'value' in all_df.columns:
                all_df = all_df.rename(columns={'value': 'volume'})
            
            # 处理增长率数据
            if 'growth' in all_df.columns:
                # 将增长率从字符串转换为数值
                def parse_growth(growth_val):
                    if pd.isna(growth_val) or growth_val == 0:
                        return 0
                    if isinstance(growth_val, str):
                        # 移除%符号并转换为数值
                        return float(growth_val.replace('%', '').replace('+', ''))
                    return float(growth_val)
                
                all_df['growth_rate'] = all_df['growth'].apply(parse_growth)
            else:
                all_df['growth_rate'] = 0
            
            self.logger.info(f"成功收集到 {len(all_df)} 个关键词的趋势数据")
            return all_df
        else:
            self.logger.warning("未收集到任何趋势数据")
            return pd.DataFrame(columns=['query', 'volume', 'growth_rate', 'seed_keyword'])
    
    def get_keyword_trends(self, keywords, geo=None, timeframe=None):
        """
        获取关键词的趋势数据（为RootWordTrendsAnalyzer提供的接口）
        
        参数:
            keywords (str or list): 关键词或关键词列表
            geo (str): 地区代码，默认使用API_CONFIG中的值
            timeframe (str): 时间范围，默认使用API_CONFIG中的值
            
        返回:
            dict: 包含趋势数据的字典
        """
        # 使用默认值
        geo = geo or self.API_CONFIG['default_params']['geo']
        timeframe = timeframe or self.API_CONFIG['default_params']['timeframe']
        
        # 处理关键词参数
        if isinstance(keywords, list):
            keyword = keywords[0] if keywords else None
        else:
            keyword = keywords
        
        # 如果没有提供关键词，返回热门搜索数据
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
                        'data_type': 'trending_searches'
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
        
        self.logger.info(f"正在获取关键词 '{keyword}' 的趋势数据...")

        # 获取Rising Queries数据
        try:
            df = self.fetch_rising_queries(keyword, geo, timeframe)
            
            if not df.empty:
                # 计算统计信息
                total_queries = len(df)
                avg_volume = float(df['value'].mean()) if 'value' in df.columns else 0.0
                
                return {
                    'keyword': keyword,
                    'related_queries': df.to_dict('records'),
                    'total_queries': total_queries,
                    'avg_volume': avg_volume,
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
            self.logger.error(f"获取趋势数据时出错: {e}")
            return {
                'keyword': keyword,
                'related_queries': [],
                'total_queries': 0,
                'avg_volume': 0.0,
                'status': 'error',
                'error': str(e)
            }
    
    def save_results(self, results, output_dir='data'):
        """
        保存结果到CSV文件
        
        参数:
            results (dict): 关键词到DataFrame的映射
            output_dir (str): 输出目录
        """
        # 合并所有结果
        all_df = pd.concat(results.values(), ignore_index=True) if results else pd.DataFrame()
        
        if not all_df.empty:
            # 保存合并的结果
            all_filename = FileUtils.generate_filename('trends_all', extension='csv')
            all_file = FileUtils.save_dataframe(all_df, output_dir, all_filename)
            self.logger.info(f"已保存所有结果到: {all_file}")
            
            # 为每个关键词保存单独的文件
            for keyword, df in results.items():
                # 清理关键词作为文件名
                safe_keyword = FileUtils.clean_filename(keyword)
                individual_filename = FileUtils.generate_filename(f'trends_{safe_keyword}', extension='csv')
                file_path = FileUtils.save_dataframe(df, output_dir, individual_filename)
                self.logger.info(f"已保存 '{keyword}' 的结果到: {file_path}")
        else:
            self.logger.warning("没有数据可保存")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Google Trends 数据采集工具')
    parser.add_argument('--keywords', nargs='+', required=True, help='要查询的关键词列表')
    parser.add_argument('--geo', help='地区代码，如US、GB等，默认使用配置中的值')
    parser.add_argument('--timeframe', help='时间范围，默认使用配置中的值')
    parser.add_argument('--output', default='data', help='输出目录，默认为data')

    args = parser.parse_args()

    # 创建采集器
    collector = TrendsCollector()

    # 获取数据
    results = collector.fetch_multiple_keywords(
        keywords=args.keywords,
        geo=args.geo,
        timeframe=args.timeframe
    )

    # 保存结果
    collector.save_results(results, args.output)


if __name__ == "__main__":
    main()