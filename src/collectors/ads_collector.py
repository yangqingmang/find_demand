#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Ads 数据采集器
用于获取关键词的搜索量、CPC、竞争度等数据
"""

import pandas as pd
import time
from typing import List, Dict, Optional

try:
    from google.ads.googleads.client import GoogleAdsClient
    from google.ads.googleads.errors import GoogleAdsException
    GOOGLE_ADS_AVAILABLE = True
except ImportError:
    GOOGLE_ADS_AVAILABLE = False
    print("警告: google-ads 包未安装，Google Ads 功能将不可用")
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from utils import Logger
    logger = Logger()
    logger.warning("google-ads 包未安装，Google Ads 功能将不可用")
    logger.info("安装命令: pip install google-ads==22.1.0")

from config.config_manager import get_config
config = get_config()
from ..utils.logger import Logger
from ..utils.exceptions import handle_api_errors
from ..utils.file_utils import FileUtils

class AdsCollector:
    """Google Ads 数据采集器"""
    
    def __init__(self):
        """初始化采集器"""
        self.logger = Logger('logs/ads_collector.log')
        
        if not GOOGLE_ADS_AVAILABLE:
            raise ImportError("Google Ads API 包未安装，请运行: pip install google-ads==22.1.0")
        
        # 验证配置
        self._validate_config()
        
        # 初始化 Google Ads 客户端
        self.client = self._init_client()
        self.customer_id = config.GOOGLE_ADS_CUSTOMER_ID
        
    def _validate_config(self):
        """验证 Google Ads API 配置"""
        missing = []
        
        if not hasattr(config, 'GOOGLE_ADS_DEVELOPER_TOKEN') or not config.GOOGLE_ADS_DEVELOPER_TOKEN:
            missing.append('GOOGLE_ADS_DEVELOPER_TOKEN')
        if not hasattr(config, 'GOOGLE_ADS_CLIENT_ID') or not config.GOOGLE_ADS_CLIENT_ID:
            missing.append('GOOGLE_ADS_CLIENT_ID')
        if not hasattr(config, 'GOOGLE_ADS_CLIENT_SECRET') or not config.GOOGLE_ADS_CLIENT_SECRET:
            missing.append('GOOGLE_ADS_CLIENT_SECRET')
        if not hasattr(config, 'GOOGLE_ADS_REFRESH_TOKEN') or not config.GOOGLE_ADS_REFRESH_TOKEN:
            missing.append('GOOGLE_ADS_REFRESH_TOKEN')
        if not hasattr(config, 'GOOGLE_ADS_CUSTOMER_ID') or not config.GOOGLE_ADS_CUSTOMER_ID:
            missing.append('GOOGLE_ADS_CUSTOMER_ID')
            
        if missing:
            error_msg = f"缺少 Google Ads API 配置项: {', '.join(missing)}\n"
            error_msg += "请运行 python setup_config.py 配置 Google Ads API"
            raise ValueError(error_msg)
    
    def _init_client(self) -> GoogleAdsClient:
        """初始化 Google Ads 客户端"""
        try:
            # 创建配置字典
            google_ads_config = {
                'developer_token': config.GOOGLE_ADS_DEVELOPER_TOKEN,
                'client_id': config.GOOGLE_ADS_CLIENT_ID,
                'client_secret': config.GOOGLE_ADS_CLIENT_SECRET,
                'refresh_token': config.GOOGLE_ADS_REFRESH_TOKEN,
                'use_proto_plus': True
            }
            
            client = GoogleAdsClient.load_from_dict(google_ads_config)
            self.logger.info("Google Ads 客户端初始化成功")
            return client
            
        except Exception as e:
            self.logger.error(f"Google Ads 客户端初始化失败: {e}")
            raise
    
    @handle_api_errors
    def get_keyword_ideas(self, keywords: List[str], geo_target: str = None) -> pd.DataFrame:
        """
        获取关键词创意和搜索量数据
        
        参数:
            keywords: 种子关键词列表
            geo_target: 地理位置目标
            
        返回:
            包含关键词数据的DataFrame
        """
        self.logger.info(f"开始获取关键词创意: {keywords}")
        
        keyword_plan_idea_service = self.client.get_service("KeywordPlanIdeaService")
        
        # 构建请求
        request = self.client.get_type("GenerateKeywordIdeasRequest")
        request.customer_id = self.customer_id
        
        # 设置关键词种子
        request.keyword_seed.keywords.extend(keywords)
        
        # 设置地理位置
        if geo_target:
            geo_target_constant = self._get_geo_target_constant(geo_target)
            if geo_target_constant:
                request.geo_target_constants.append(geo_target_constant)
        
        # 设置语言（中文）
        request.language = self._get_language_constant("zh")
        
        # 设置关键词规划网络
        request.keyword_plan_network = self.client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
        
        try:
            # 发送请求
            keyword_ideas = keyword_plan_idea_service.generate_keyword_ideas(request=request)
            
            # 解析结果
            results = []
            for idea in keyword_ideas:
                keyword_data = {
                    'keyword': idea.text,
                    'avg_monthly_searches': self._get_monthly_searches(idea.keyword_idea_metrics),
                    'competition': self._get_competition_level(idea.keyword_idea_metrics),
                    'competition_index': self._get_competition_index(idea.keyword_idea_metrics),
                    'low_top_of_page_bid_micros': self._get_bid_micros(idea.keyword_idea_metrics, 'low'),
                    'high_top_of_page_bid_micros': self._get_bid_micros(idea.keyword_idea_metrics, 'high'),
                    'avg_cpc': self._calculate_avg_cpc(idea.keyword_idea_metrics)
                }
                results.append(keyword_data)
            
            df = pd.DataFrame(results)
            self.logger.info(f"成功获取 {len(df)} 个关键词的数据")
            return df
            
        except GoogleAdsException as ex:
            self.logger.error(f"Google Ads API 请求失败: {ex}")
            raise
    
    def _get_geo_target_constant(self, geo_code: str) -> Optional[str]:
        """获取地理位置常量"""
        # 地区代码映射
        geo_mapping = {
            'US': '2840',  # 美国
            'GB': '2826',  # 英国
            'CN': '2156',  # 中国
            'DE': '2276',  # 德国
            'JP': '2392',  # 日本
            'KR': '2410',  # 韩国
            'CA': '2124',  # 加拿大
            'AU': '2036',  # 澳大利亚
            'FR': '2250',  # 法国
            'IT': '2380',  # 意大利
        }
        
        if geo_code in geo_mapping:
            return f"geoTargetConstants/{geo_mapping[geo_code]}"
        
        return None
    
    def _get_language_constant(self, language_code: str) -> str:
        """获取语言常量"""
        language_mapping = {
            'zh': 'languageConstants/1018',  # 中文
            'en': 'languageConstants/1000',  # 英文
            'ja': 'languageConstants/1005',  # 日文
            'ko': 'languageConstants/1012',  # 韩文
            'de': 'languageConstants/1001',  # 德文
            'fr': 'languageConstants/1002',  # 法文
        }
        
        return language_mapping.get(language_code, 'languageConstants/1000')
    
    def _get_monthly_searches(self, metrics) -> int:
        """获取月搜索量"""
        if metrics and hasattr(metrics, 'avg_monthly_searches'):
            return metrics.avg_monthly_searches
        return 0
    
    def _get_competition_level(self, metrics) -> str:
        """获取竞争程度"""
        if metrics and hasattr(metrics, 'competition'):
            competition_enum = self.client.enums.KeywordPlanCompetitionEnum
            if metrics.competition == competition_enum.LOW:
                return 'LOW'
            elif metrics.competition == competition_enum.MEDIUM:
                return 'MEDIUM'
            elif metrics.competition == competition_enum.HIGH:
                return 'HIGH'
        return 'UNKNOWN'
    
    def _get_competition_index(self, metrics) -> float:
        """获取竞争指数"""
        if metrics and hasattr(metrics, 'competition_index'):
            return metrics.competition_index
        return 0.0
    
    def _get_bid_micros(self, metrics, bid_type: str) -> int:
        """获取出价（微单位）"""
        if not metrics:
            return 0
            
        if bid_type == 'low' and hasattr(metrics, 'low_top_of_page_bid_micros'):
            return metrics.low_top_of_page_bid_micros
        elif bid_type == 'high' and hasattr(metrics, 'high_top_of_page_bid_micros'):
            return metrics.high_top_of_page_bid_micros
        
        return 0
    
    def _calculate_avg_cpc(self, metrics) -> float:
        """计算平均CPC（美元）"""
        if not metrics:
            return 0.0
            
        low_bid = self._get_bid_micros(metrics, 'low')
        high_bid = self._get_bid_micros(metrics, 'high')
        
        if low_bid > 0 and high_bid > 0:
            # 转换微单位到美元（1美元 = 1,000,000微单位）
            avg_cpc = (low_bid + high_bid) / 2 / 1_000_000
            return round(avg_cpc, 2)
        
        return 0.0
    
    def batch_collect(self, keyword_groups: List[List[str]], geo_target: str = None) -> pd.DataFrame:
        """
        批量采集关键词数据
        
        参数:
            keyword_groups: 关键词组列表
            geo_target: 地理位置目标
            
        返回:
            合并后的DataFrame
        """
        all_results = []
        
        for i, keywords in enumerate(keyword_groups, 1):
            self.logger.info(f"处理关键词组 {i}/{len(keyword_groups)}: {keywords}")
            
            try:
                df = self.get_keyword_ideas(keywords, geo_target)
                all_results.append(df)
                
                # API限制：避免请求过于频繁
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"关键词组 {i} 处理失败: {e}")
                continue
        
        if all_results:
            combined_df = pd.concat(all_results, ignore_index=True)
            # 去重
            combined_df = combined_df.drop_duplicates(subset=['keyword'])
            self.logger.info(f"批量采集完成，共获取 {len(combined_df)} 个关键词")
            return combined_df
        
        return pd.DataFrame()
    
    def save_results(self, df: pd.DataFrame, output_dir: str = 'data') -> str:
        """保存结果到文件"""
        if df.empty:
            self.logger.warning("没有数据需要保存")
            return ""
        
        filename = FileUtils.generate_filename('ads_data', 'keywords', 'csv')
        filepath = FileUtils.save_dataframe(df, output_dir, filename)
        
        self.logger.info(f"Google Ads 数据已保存到: {filepath}")
        return filepath