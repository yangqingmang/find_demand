#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟数据生成器
用于生成测试和演示用的模拟数据
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from .logger import Logger


class MockDataGenerator:
    """模拟数据生成器类"""
    
    def __init__(self, seed: int = 42):
        """
        初始化模拟数据生成器
        
        参数:
            seed (int): 随机种子，确保结果可重复
        """
        self.seed = seed
        self.logger = Logger()
        np.random.seed(seed)
    
    def generate_ads_data(self, df: pd.DataFrame, keyword_col: str = 'query') -> pd.DataFrame:
        """
        生成模拟的Google Ads数据
        
        参数:
            df (pd.DataFrame): 关键词数据
            keyword_col (str): 关键词列名
            
        返回:
            pd.DataFrame: 添加了模拟Ads数据的DataFrame
        """
        self.logger.info("生成模拟Google Ads数据...")
        
        result_df = df.copy()
        
        if keyword_col in result_df.columns:
            np.random.seed(self.seed)  # 重置随机种子以获得可重复的结果
            n_rows = len(result_df)
            
            # 模拟月搜索量 (100-10000)
            result_df['monthly_searches'] = np.random.randint(100, 10000, size=n_rows)
            
            # 模拟竞争度 (0-1)
            result_df['competition'] = np.random.random(size=n_rows)
            
            # 模拟CPC (0.1-5.0)
            result_df['cpc'] = np.random.uniform(0.1, 5.0, size=n_rows).round(2)
            
            # 模拟关键词难度 (1-100)
            result_df['keyword_difficulty'] = np.random.randint(1, 100, size=n_rows)
            
            # 模拟搜索趋势 (-50% 到 +200%)
            result_df['trend_change'] = np.random.uniform(-50, 200, size=n_rows).round(1)
            
            self.logger.info(f"已添加模拟的Ads数据到 {n_rows} 个关键词")
        else:
            self.logger.warning(f"未找到关键词列 '{keyword_col}'")
        
        return result_df
    
    def generate_serp_features(self, df: pd.DataFrame, keyword_col: str = 'query') -> pd.DataFrame:
        """
        生成模拟的SERP特征数据
        
        参数:
            df (pd.DataFrame): 关键词数据
            keyword_col (str): 关键词列名
            
        返回:
            pd.DataFrame: 添加了模拟SERP特征的DataFrame
        """
        self.logger.info("生成模拟SERP特征数据...")
        
        result_df = df.copy()
        
        if keyword_col in result_df.columns:
            np.random.seed(self.seed)
            n_rows = len(result_df)
            
            # 模拟搜索结果数量
            result_df['total_results'] = np.random.randint(1000, 10000000, size=n_rows)
            
            # 模拟SERP特征（布尔值）
            result_df['has_featured_snippet'] = np.random.choice([True, False], size=n_rows, p=[0.3, 0.7])
            result_df['has_paa'] = np.random.choice([True, False], size=n_rows, p=[0.4, 0.6])
            result_df['has_shopping'] = np.random.choice([True, False], size=n_rows, p=[0.2, 0.8])
            result_df['has_video'] = np.random.choice([True, False], size=n_rows, p=[0.25, 0.75])
            result_df['has_images'] = np.random.choice([True, False], size=n_rows, p=[0.35, 0.65])
            result_df['has_news'] = np.random.choice([True, False], size=n_rows, p=[0.15, 0.85])
            result_df['has_local'] = np.random.choice([True, False], size=n_rows, p=[0.1, 0.9])
            
            # 模拟广告数量
            result_df['ads_count'] = np.random.randint(0, 8, size=n_rows)
            
            self.logger.info(f"已添加模拟的SERP特征到 {n_rows} 个关键词")
        else:
            self.logger.warning(f"未找到关键词列 '{keyword_col}'")
        
        return result_df
    
    def generate_trends_data(self, keywords: list, geo: str = '', timeframe: str = 'today 3-m') -> Dict[str, pd.DataFrame]:
        """
        生成模拟的Google Trends数据
        
        参数:
            keywords (list): 关键词列表
            geo (str): 地区代码
            timeframe (str): 时间范围
            
        返回:
            Dict[str, pd.DataFrame]: 关键词到DataFrame的映射
        """
        self.logger.info(f"生成模拟Google Trends数据，关键词: {keywords}")
        
        results = {}
        np.random.seed(self.seed)
        
        for keyword in keywords:
            # 生成相关查询数据
            n_queries = np.random.randint(10, 50)  # 每个关键词生成10-50个相关查询
            
            # 生成相关查询名称
            query_suffixes = [
                'tutorial', 'guide', 'tips', 'best', 'free', 'online', 'tool', 'software',
                'review', 'comparison', 'alternative', 'price', 'cost', 'download',
                '教程', '指南', '技巧', '最佳', '免费', '在线', '工具', '软件'
            ]
            
            queries = []
            for i in range(n_queries):
                if np.random.random() > 0.5:
                    # 添加后缀
                    suffix = np.random.choice(query_suffixes)
                    query = f"{keyword} {suffix}"
                else:
                    # 添加前缀
                    prefix = np.random.choice(['best', 'free', 'top', 'how to', '如何', '最佳'])
                    query = f"{prefix} {keyword}"
                queries.append(query)
            
            # 生成搜索量数据
            values = np.random.randint(10, 1000, size=n_queries)
            
            # 生成增长率数据（可能为空）
            if np.random.random() > 0.3:  # 70%的概率有增长率数据
                growth_rates = np.random.uniform(-50, 500, size=n_queries).round(0).astype(int)
                growth = [f"{rate}%" if rate >= 0 else f"{rate}%" for rate in growth_rates]
            else:
                growth = [0] * n_queries
            
            # 创建DataFrame
            df = pd.DataFrame({
                'query': queries,
                'value': values,
                'growth': growth,
                'seed_keyword': keyword
            })
            
            results[keyword] = df
        
        self.logger.info(f"已生成 {len(results)} 个关键词的模拟Trends数据")
        return results
    
    def generate_intent_data(self, df: pd.DataFrame, keyword_col: str = 'query') -> pd.DataFrame:
        """
        生成模拟的搜索意图数据
        
        参数:
            df (pd.DataFrame): 关键词数据
            keyword_col (str): 关键词列名
            
        返回:
            pd.DataFrame: 添加了模拟意图数据的DataFrame
        """
        from .constants import INTENT_TYPES, RECOMMENDED_ACTIONS
        
        self.logger.info("生成模拟搜索意图数据...")
        
        result_df = df.copy()
        
        if keyword_col in result_df.columns:
            np.random.seed(self.seed)
            n_rows = len(result_df)
            
            # 随机分配意图类型
            intent_codes = list(INTENT_TYPES.keys())
            intents = np.random.choice(intent_codes, size=n_rows)
            
            # 生成置信度
            confidences = np.random.uniform(0.6, 0.95, size=n_rows).round(2)
            
            # 添加意图相关列
            result_df['intent'] = intents
            result_df['intent_confidence'] = confidences
            result_df['intent_description'] = [INTENT_TYPES[intent] for intent in intents]
            result_df['recommended_action'] = [RECOMMENDED_ACTIONS[intent] for intent in intents]
            
            # 随机添加次要意图（30%的概率）
            secondary_intents = []
            for i in range(n_rows):
                if np.random.random() < 0.3:
                    # 选择与主要意图不同的次要意图
                    available_intents = [code for code in intent_codes if code != intents[i]]
                    secondary_intents.append(np.random.choice(available_intents))
                else:
                    secondary_intents.append('')
            
            result_df['secondary_intent'] = secondary_intents
            
            self.logger.info(f"已添加模拟的意图数据到 {n_rows} 个关键词")
        else:
            self.logger.warning(f"未找到关键词列 '{keyword_col}'")
        
        return result_df
    
    def generate_complete_dataset(self, keywords: list, geo: str = '', 
                                timeframe: str = 'today 3-m') -> pd.DataFrame:
        """
        生成完整的模拟数据集
        
        参数:
            keywords (list): 关键词列表
            geo (str): 地区代码
            timeframe (str): 时间范围
            
        返回:
            pd.DataFrame: 完整的模拟数据集
        """
        self.logger.info("生成完整的模拟数据集...")
        
        # 生成Trends数据
        trends_results = self.generate_trends_data(keywords, geo, timeframe)
        
        # 合并所有Trends数据
        all_df = pd.concat(trends_results.values(), ignore_index=True)
        
        # 添加各种模拟数据
        all_df = self.generate_ads_data(all_df)
        all_df = self.generate_serp_features(all_df)
        all_df = self.generate_intent_data(all_df)
        
        # 生成综合评分（基于多个因素）
        np.random.seed(self.seed)
        base_scores = np.random.uniform(20, 95, size=len(all_df))
        
        # 根据搜索量调整分数
        volume_factor = (all_df['value'] - all_df['value'].min()) / (all_df['value'].max() - all_df['value'].min())
        
        # 根据竞争度调整分数（竞争度越低分数越高）
        competition_factor = 1 - all_df['competition']
        
        # 计算最终分数
        final_scores = (base_scores * 0.6 + volume_factor * 100 * 0.3 + competition_factor * 100 * 0.1)
        all_df['score'] = np.clip(final_scores, 0, 100).round().astype(int)
        
        # 添加评分等级
        all_df['grade'] = pd.cut(
            all_df['score'],
            bins=[0, 30, 50, 70, 100],
            labels=['D', 'C', 'B', 'A']
        )
        
        self.logger.info(f"已生成包含 {len(all_df)} 条记录的完整模拟数据集")
        return all_df


# 便捷函数
def generate_mock_ads_data(df: pd.DataFrame, keyword_col: str = 'query', seed: int = 42) -> pd.DataFrame:
    """生成模拟Ads数据的便捷函数"""
    generator = MockDataGenerator(seed)
    return generator.generate_ads_data(df, keyword_col)


def generate_mock_complete_dataset(keywords: list, geo: str = '', 
                                 timeframe: str = 'today 3-m', seed: int = 42) -> pd.DataFrame:
    """生成完整模拟数据集的便捷函数"""
    generator = MockDataGenerator(seed)
    return generator.generate_complete_dataset(keywords, geo, timeframe)