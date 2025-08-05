#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Trends 数据采集模块
用于采集Google Trends相关查询数据
"""

import pandas as pd
import time
from pytrends.request import TrendReq
import argparse

from src.utils import (
    FileUtils, Logger, ExceptionHandler, APIError,
    DEFAULT_CONFIG, VALIDATION_CONSTANTS
)
from src.config.settings import config
from src.utils.mock_data_generator import MockDataGenerator

class TrendsCollector:
    """Google Trends 数据采集类"""
    
    def __init__(self, hl='zh-CN', tz=360, timeout=(10, 25), retries=3, backoff_factor=1.5):
        """
        初始化 TrendsCollector
        
        参数:
            hl (str): 语言设置，默认'zh-CN'
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
    
    def fetch_rising_queries(self, keyword, geo='', timeframe='today 3-m'):
        """
        获取关键词的Rising Queries
        
        参数:
            keyword (str): 种子关键词
            geo (str): 地区代码，如'US','GB'等，默认为全球
            timeframe (str): 时间范围，默认'today 3-m'
            
        返回:
            pandas.DataFrame: Rising Queries数据
        """
        self.logger.info(f"正在获取 '{keyword}' 的Rising Queries数据 (地区: {geo or '全球'})...")
        
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
                # 构建payload
                self.pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
                
                # 获取相关查询
                related_queries = self.pytrends.related_queries()
                
                if keyword in related_queries and related_queries[keyword]:
                    rising = related_queries[keyword]['rising']
                    top = related_queries[keyword]['top']
                    
                    if rising is not None and not rising.empty:
                        self.logger.info(f"成功获取 {len(rising)} 个Rising Queries")
                        return rising
                    elif top is not None and not top.empty:
                        self.logger.info(f"未找到Rising Queries，返回 {len(top)} 个Top Queries")
                        # 为Top查询添加默认增长率0
                        top['growth'] = 0
                        return top
                    else:
                        self.logger.warning(f"未找到相关查询数据")
                        return pd.DataFrame(columns=['query', 'value', 'growth'])
                else:
                    self.logger.warning(f"未找到关键词 '{keyword}' 的相关查询数据")
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
                    return pd.DataFrame(columns=['query', 'value', 'growth'])
    
    def fetch_multiple_keywords(self, keywords, geo='', timeframe='today 3-m'):
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
                self.logger.info("等待3秒以避免API限制...")
                time.sleep(3)
        
        return results
    
    def collect_rising_queries(self, keywords, geo='', timeframe='today 3-m'):
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
    parser.add_argument('--geo', default='', help='地区代码，如US、GB等，默认为全球')
    parser.add_argument('--timeframe', default='today 3-m', help='时间范围，默认为过去3个月')
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