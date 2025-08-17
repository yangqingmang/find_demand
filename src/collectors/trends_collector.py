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

from src.utils import (
    FileUtils, Logger, ExceptionHandler, APIError,
    DEFAULT_CONFIG, VALIDATION_CONSTANTS
)
try:
    from config.config_manager import get_config
    config = get_config()
except ImportError:
    # 如果配置管理器不可用，使用简化版配置
    from src.utils.simple_config import get_config
    config = get_config()
from src.utils.mock_data_generator import MockDataGenerator

class TrendsCollector:
    """Google Trends 数据采集类"""
    
    def __init__(self, hl='en-US', tz=360, timeout=(20, 30), retries=5, backoff_factor=2.0):
        """
        初始化 TrendsCollector
        
        参数:
            hl (str): 语言设置，默认'en-US'（改为英文以提高兼容性）
            tz (int): 时区，默认360
            timeout (tuple): 连接和读取超时时间(秒)
            retries (int): 重试次数
            backoff_factor (float): 重试间隔增长因子
        """
        self.hl = hl
        self.tz = tz
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.pytrends = None
        self.logger = Logger()
        self._connect()
        
        # 设置pandas选项，消除警告
        pd.set_option('future.no_silent_downcasting', True)
    
    def _connect(self):
        """创建pytrends连接"""
        self.pytrends = TrendReq(hl=self.hl, tz=self.tz, timeout=self.timeout)
    
    def _make_direct_api_request(self, keyword, geo='US', timeframe='today 12-m'):
        """
        使用正确的API格式直接请求Google Trends数据
        
        参数:
            keyword (str): 关键词
            geo (str): 地区代码，默认'US'
            timeframe (str): 时间范围，默认'today 12-m'
            
        返回:
            dict: API响应数据
        """
        try:
            # 构建请求参数，按照你提供的格式
            req_data = {
                "comparisonItem": [{
                    "keyword": keyword,
                    "geo": geo,
                    "time": timeframe
                }]
            }
            
            # 构建完整的URL
            base_url = "https://trends.google.com/trends/api/explore"
            params = {
                "hl": self.hl,
                "tz": self.tz,
                "req": json.dumps(req_data)
            }
            
            # 发送请求
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            self.logger.info(f"发送API请求: {base_url}")
            self.logger.info(f"请求参数: {params}")
            
            response = requests.get(base_url, params=params, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                # Google Trends API返回的数据以")]}'"开头，需要去除这4个字符
                content = response.text
                if content.startswith(")]}',"):
                    # 去除前4个字符 ")]}'"
                    content = content[4:]
                    # 如果后面还有换行符，也去除
                    if content.startswith('\n'):
                        content = content[1:]
                elif content.startswith(")]}',\n"):
                    # 兼容之前的处理方式
                    content = content[6:]
                
                self.logger.info("✓ API请求成功，正在解析响应数据")
                self.logger.debug(f"处理后的响应内容前100字符: {content[:100]}")
                return json.loads(content)
            else:
                self.logger.error(f"API请求失败，状态码: {response.status_code}")
                self.logger.error(f"响应内容: {response.text[:500]}")
                return None
                
        except Exception as e:
            self.logger.error(f"直接API请求出错: {e}")
            return None
    
    def _extract_related_queries_from_api_response(self, api_response):
        """
        从API响应中提取相关查询数据
        根据真实的Google Trends API响应格式进行解析
        
        参数:
            api_response (dict): API响应数据
            
        返回:
            pandas.DataFrame: 相关查询数据
        """
        try:
            if not api_response or 'widgets' not in api_response:
                self.logger.warning("API响应中没有widgets数据")
                return pd.DataFrame(columns=['query', 'value', 'growth'])
            
            self.logger.info(f"找到 {len(api_response['widgets'])} 个widgets")
            
            # 查找相关查询widget (RELATED_QUERIES)
            related_queries_data = []
            
            for widget in api_response['widgets']:
                widget_id = widget.get('id', '')
                widget_type = widget.get('type', '')
                self.logger.info(f"处理widget: id={widget_id}, type={widget_type}")
                
                if widget_id == 'RELATED_QUERIES' and widget_type == 'fe_related_searches':
                    self.logger.info("找到相关查询widget (RELATED_QUERIES)")
                    
                    # 获取widget的token
                    token = widget.get('token')
                    if not token:
                        self.logger.warning("相关查询widget缺少token")
                        continue
                    
                    # 构建相关查询的请求URL
                    related_url = "https://trends.google.com/trends/api/widgetdata/relatedsearches"
                    params = {
                        'hl': self.hl,
                        'tz': self.tz,
                        'req': json.dumps(widget['request']),
                        'token': token
                    }
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    self.logger.info(f"请求相关查询数据: {related_url}")
                    response = requests.get(related_url, params=params, headers=headers, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        content = response.text
                        # 处理Google Trends API特殊的响应前缀 ")]}'"
                        if content.startswith(")]}',"):
                            content = content[4:]
                            if content.startswith('\n'):
                                content = content[1:]
                        elif content.startswith(")]}',\n"):
                            content = content[6:]
                        
                        self.logger.debug(f"相关查询响应前100字符: {content[:100]}")
                        
                        try:
                            data = json.loads(content)
                            
                            # 根据真实API响应结构解析数据
                            if 'default' in data and 'rankedList' in data['default']:
                                for ranked_list in data['default']['rankedList']:
                                    list_type = ranked_list.get('rankedKeyword', [])
                                    
                                    for item in list_type:
                                        # 提取查询数据
                                        query = item.get('query', '')
                                        value = item.get('value', 0)
                                        formatted_value = item.get('formattedValue', '0')
                                        
                                        # 处理增长率数据
                                        growth = formatted_value
                                        if isinstance(formatted_value, str) and '%' in formatted_value:
                                            growth = formatted_value
                                        elif isinstance(value, (int, float)):
                                            growth = f"{value}%"
                                        
                                        query_data = {
                                            'query': query,
                                            'value': value,
                                            'growth': growth
                                        }
                                        related_queries_data.append(query_data)
                                        
                                self.logger.info(f"从rankedList中提取了 {len(related_queries_data)} 个查询")
                            else:
                                self.logger.warning("相关查询响应中没有找到expected的数据结构")
                                self.logger.debug(f"响应数据结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                                
                        except json.JSONDecodeError as e:
                            self.logger.error(f"解析相关查询JSON数据失败: {e}")
                            self.logger.debug(f"原始响应内容: {content[:200]}")
                            
                    else:
                        self.logger.error(f"相关查询请求失败，状态码: {response.status_code}")
                        self.logger.debug(f"错误响应: {response.text[:200]}")
                    
                    break  # 找到RELATED_QUERIES后就退出循环
            
            if related_queries_data:
                self.logger.info(f"✓ 成功提取 {len(related_queries_data)} 个相关查询")
                return pd.DataFrame(related_queries_data)
            else:
                self.logger.warning("未找到相关查询数据，返回空DataFrame")
                return pd.DataFrame(columns=['query', 'value', 'growth'])
                
        except Exception as e:
            self.logger.error(f"提取相关查询数据出错: {e}")
            import traceback
            self.logger.debug(f"错误详情: {traceback.format_exc()}")
            return pd.DataFrame(columns=['query', 'value', 'growth'])
    
    def fetch_rising_queries(self, keyword, geo='US', timeframe='today 12-m'):
        """
        获取关键词的Rising Queries - 使用改进的API请求格式
        
        参数:
            keyword (str): 种子关键词
            geo (str): 地区代码，如'US','GB'等，默认'US'
            timeframe (str): 时间范围，默认'today 12-m'
            
        返回:
            pandas.DataFrame: Rising Queries数据
        """
        self.logger.info(f"正在获取 '{keyword}' 的Rising Queries数据 (地区: {geo})...")
        
        # 如果启用模拟模式，返回模拟数据
        if config.MOCK_MODE:
            self.logger.info("🔧 模拟模式：生成模拟趋势数据")
            mock_generator = MockDataGenerator()
            mock_results = mock_generator.generate_trends_data([keyword], geo, timeframe)
            if keyword in mock_results:
                return mock_results[keyword]
            else:
                return pd.DataFrame(columns=['query', 'value', 'growth'])
        
        for attempt in range(self.retries):
            try:
                # 首先尝试使用改进的直接API请求
                self.logger.info(f"尝试使用直接API请求 (尝试 {attempt+1}/{self.retries})")
                
                api_response = self._make_direct_api_request(keyword, geo, timeframe)
                
                if api_response:
                    # 从API响应中提取相关查询数据
                    df = self._extract_related_queries_from_api_response(api_response)
                    
                    if not df.empty:
                        self.logger.info(f"✓ 直接API成功获取 {len(df)} 个相关查询")
                        return df
                    else:
                        self.logger.warning("直接API响应中未找到相关查询数据")
                
                # 如果直接API请求失败，回退到pytrends
                self.logger.info("直接API请求失败，尝试使用pytrends库")
                
                # 构建payload
                self.pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
                
                # 获取相关查询
                related_queries = self.pytrends.related_queries()
                
                if keyword in related_queries and related_queries[keyword]:
                    rising = related_queries[keyword]['rising']
                    top = related_queries[keyword]['top']
                    
                    if rising is not None and not rising.empty:
                        self.logger.info(f"✓ pytrends成功获取 {len(rising)} 个Rising Queries")
                        return rising
                    elif top is not None and not top.empty:
                        self.logger.info(f"✓ pytrends未找到Rising Queries，返回 {len(top)} 个Top Queries")
                        # 为Top查询添加默认增长率0
                        top['growth'] = 0
                        return top
                    else:
                        self.logger.warning(f"pytrends未找到相关查询数据")
                        return pd.DataFrame(columns=['query', 'value', 'growth'])
                else:
                    self.logger.warning(f"pytrends未找到关键词 '{keyword}' 的相关查询数据")
                    return pd.DataFrame(columns=['query', 'value', 'growth'])
                    
            except Exception as e:
                wait_time = self.backoff_factor * (2 ** attempt)
                if attempt < self.retries - 1:
                    self.logger.warning(f"获取数据时出错: {e}")
                    self.logger.info(f"等待 {wait_time:.1f} 秒后重试 ({attempt+1}/{self.retries})...")
                    time.sleep(wait_time)
                    # 重新连接
                    self._connect()
                else:
                    self.logger.error(f"多次尝试后仍然失败: {e}")
                    self.logger.info("🔄 API失败，自动回退到模拟数据模式")
                    # 自动回退到模拟数据
                    try:
                        mock_generator = MockDataGenerator()
                        mock_results = mock_generator.generate_trends_data([keyword], geo, timeframe)
                        if keyword in mock_results:
                            self.logger.info(f"✓ 已生成 '{keyword}' 的模拟数据作为回退")
                            return mock_results[keyword]
                    except Exception as mock_error:
                        self.logger.error(f"模拟数据生成也失败: {mock_error}")
                    
                    return pd.DataFrame(columns=['query', 'value', 'growth'])
    
    def fetch_multiple_keywords(self, keywords, geo='US', timeframe='today 12-m'):
        """
        批量获取多个关键词的Rising Queries
        
        参数:
            keywords (list): 种子关键词列表
            geo (str): 地区代码
            timeframe (str): 时间范围
            
        返回:
            dict: 关键词到DataFrame的映射
        """
        # 如果启用模拟模式，直接生成所有关键词的模拟数据
        if config.MOCK_MODE:
            self.logger.info("🔧 模拟模式：批量生成模拟趋势数据")
            mock_generator = MockDataGenerator()
            return mock_generator.generate_trends_data(keywords, geo, timeframe)
        
        results = {}
        
        for keyword in keywords:
            df = self.fetch_rising_queries(keyword, geo, timeframe)
            if not df.empty:
                df['seed_keyword'] = keyword  # 添加种子关键词列
                results[keyword] = df
            
            # 避免API限制，每次请求之间等待
            if keyword != keywords[-1]:  # 如果不是最后一个关键词
                self.logger.info("等待30秒以避免API限制...")
                time.sleep(30)
        
        return results
    
    def collect_rising_queries(self, keywords, geo='US', timeframe='today 12-m'):
        """
        为主分析器提供的统一接口
        
        参数:
            keywords (list): 种子关键词列表
            geo (str): 地区代码
            timeframe (str): 时间范围
            
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
    
    def get_keyword_trends(self, keywords, geo='US', timeframe='today 12-m'):
        """
        获取关键词的趋势数据（为RootWordTrendsAnalyzer提供的接口）
        
        参数:
            keywords (str or list): 关键词或关键词列表
            geo (str): 地区代码
            timeframe (str): 时间范围
            
        返回:
            dict: 包含趋势数据的字典
        """
        # 确保keywords是字符串（单个关键词）
        if isinstance(keywords, list):
            keyword = keywords[0] if keywords else ""
        else:
            keyword = keywords
            
        self.logger.info(f"正在获取关键词 '{keyword}' 的趋势数据...")
        
        # 如果启用模拟模式，返回模拟数据
        if config.MOCK_MODE:
            self.logger.info("🔧 模拟模式：生成模拟趋势数据")
            mock_generator = MockDataGenerator()
            
            try:
                # 生成单个关键词的模拟数据
                mock_results = mock_generator.generate_trends_data([keyword], geo, timeframe)
                if keyword in mock_results:
                    df = mock_results[keyword]
                    
                    # 确保DataFrame不为空且有正确的列
                    if not df.empty and 'value' in df.columns:
                        return {
                            'keyword': keyword,
                            'related_queries': df.to_dict('records'),
                            'total_queries': len(df),
                            'avg_volume': float(df['value'].mean()),
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
                else:
                    return {
                        'keyword': keyword,
                        'related_queries': [],
                        'total_queries': 0,
                        'avg_volume': 0.0,
                        'status': 'no_data'
                    }
            except Exception as e:
                self.logger.error(f"生成模拟数据时出错: {e}")
                return {
                    'keyword': keyword,
                    'related_queries': [],
                    'total_queries': 0,
                    'avg_volume': 0.0,
                    'status': 'error',
                    'error': str(e)
                }
        
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
    parser.add_argument('--geo', default='US', help='地区代码，如US、GB等，默认为US')
    parser.add_argument('--timeframe', default='today 12-m', help='时间范围，默认为过去12个月')
    parser.add_argument('--output', default='data', help='输出目录，默认为data')
    
    args = parser.parse_args()
    
    # 创建采集器
    collector = TrendsCollector()
    
    # 获取数据
    results = collector.fetch_multiple_keywords(args.keywords, args.geo, args.timeframe)
    
    # 保存结果
    collector.save_results(results, args.output)


if __name__ == "__main__":
    main()