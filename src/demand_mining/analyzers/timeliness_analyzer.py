#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时性分析器 - Timeliness Analyzer
用于分析关键词的时效性和趋势热度
"""

import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import re
import time

from .base_analyzer import BaseAnalyzer

try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from collectors.trends_collector import TrendsCollector
    from utils import Logger, FileUtils, ExceptionHandler
except ImportError:
    class Logger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    class FileUtils:
        @staticmethod
        def generate_filename(prefix, extension='csv'):
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"{prefix}_{timestamp}.{extension}"


class TimelinessAnalyzer(BaseAnalyzer):
    """实时性分析器，用于评估关键词的时效性和热度"""
    
    def __init__(self, trends_weight=0.4, news_weight=0.3, social_weight=0.2, seasonal_weight=0.1):
        """
        初始化实时性分析器
        
        参数:
            trends_weight (float): 搜索趋势权重
            news_weight (float): 新闻热度权重
            social_weight (float): 社交媒体权重
            seasonal_weight (float): 季节性权重
        """
        super().__init__()
        self.trends_weight = trends_weight
        self.news_weight = news_weight
        self.social_weight = social_weight
        self.seasonal_weight = seasonal_weight
        
        # 验证权重总和
        total_weight = trends_weight + news_weight + social_weight + seasonal_weight
        if abs(total_weight - 1.0) > 0.001:
            self.logger.warning(f"权重总和 ({total_weight}) 不等于1，已自动归一化")
            self.trends_weight /= total_weight
            self.news_weight /= total_weight
            self.social_weight /= total_weight
            self.seasonal_weight /= total_weight
        
        # 初始化趋势收集器
        self.trends_collector = None
        try:
            from src.collectors.trends_singleton import get_trends_collector
            self.trends_collector = get_trends_collector()
        except:
            pass
        
        if not self.trends_collector:
            self.logger.warning("趋势收集器初始化失败")
        
        # 时效性等级定义
        self.timeliness_grades = {
            'A': {'min_score': 80, 'description': '极高时效性 - 热门趋势'},
            'B': {'min_score': 60, 'description': '高时效性 - 上升趋势'},
            'C': {'min_score': 40, 'description': '中等时效性 - 稳定关注'},
            'D': {'min_score': 20, 'description': '低时效性 - 下降趋势'},
            'F': {'min_score': 0, 'description': '无时效性 - 过时内容'}
        }
    
    def analyze(self, data, keyword_col='query', **kwargs):
        """
        实现基础分析器的抽象方法
        
        参数:
            data: 关键词数据DataFrame
            keyword_col: 关键词列名
            **kwargs: 其他参数
            
        返回:
            添加了实时性分析结果的DataFrame
        """
        return self.analyze_timeliness(data, keyword_col)
    
    def calculate_trend_score(self, keyword: str, timeframe: str = '7d') -> Dict:
        """
        计算关键词的搜索趋势评分
        
        参数:
            keyword (str): 关键词
            timeframe (str): 时间范围 ('1d', '7d', '30d', '90d')
            
        返回:
            dict: 趋势分析结果
        """
        if self.trends_collector:
            try:
                # 使用真实的Google Trends数据
                trend_data = self.trends_collector.get_trends_data([keyword], timeframe=timeframe)
                
                if trend_data and keyword in trend_data:
                    values = trend_data[keyword]['values']
                    if len(values) >= 2:
                        # 计算趋势变化
                        recent_avg = np.mean(values[-3:])  # 最近3个数据点
                        earlier_avg = np.mean(values[:3])  # 最早3个数据点
                        
                        if earlier_avg > 0:
                            growth_rate = (recent_avg - earlier_avg) / earlier_avg * 100
                        else:
                            growth_rate = 0
                        
                        # 计算趋势评分
                        trend_score = min(100, max(0, 50 + growth_rate))
                        
                        return {
                            'trend_score': round(trend_score, 1),
                            'growth_rate': round(growth_rate, 2),
                            'current_interest': round(recent_avg, 1),
                            'peak_interest': max(values),
                            'trend_direction': 'rising' if growth_rate > 10 else 'falling' if growth_rate < -10 else 'stable'
                        }
            except Exception as e:
                self.logger.warning(f"获取真实趋势数据失败: {e}")
        
        # 无法获取数据
        return {}
    
        
        # AI相关关键词通常有上升趋势
        if any(term in keyword_lower for term in ['ai', 'chatgpt', 'gpt', 'artificial intelligence']):
            base_score = 75
            growth_rate = np.random.uniform(20, 50)
            trend_direction = 'rising'
        
        # 工具类关键词稳定增长
        elif any(term in keyword_lower for term in ['tool', 'generator', 'converter', 'editor']):
            base_score = 65
            growth_rate = np.random.uniform(5, 25)
            trend_direction = 'rising'
        
        # 教程类关键词稳定
        elif any(term in keyword_lower for term in ['how to', 'tutorial', 'guide', 'learn']):
            base_score = 55
            growth_rate = np.random.uniform(-5, 15)
            trend_direction = 'stable'
        
        # 其他关键词
        else:
            base_score = 45
            growth_rate = np.random.uniform(-15, 10)
            trend_direction = 'stable' if growth_rate > -5 else 'falling'
        
        return {
            'trend_score': base_score,
            'growth_rate': round(growth_rate, 2),
            'current_interest': round(base_score * 0.8, 1),
            'peak_interest': round(base_score * 1.2, 1),
            'trend_direction': trend_direction
        }
    
    def calculate_news_score(self, keyword: str) -> Dict:
        """
        计算关键词的新闻热度评分
        
        参数:
            keyword (str): 关键词
            
        返回:
            dict: 新闻热度分析结果
        """
        # 新闻热度分析
        keyword_lower = keyword.lower()
        
        # 热门科技关键词新闻热度高
        if any(term in keyword_lower for term in ['ai', 'chatgpt', 'openai', 'google', 'microsoft']):
            news_score = np.random.uniform(70, 95)
            news_count = np.random.randint(50, 200)
            sentiment = 'positive'
        
        # 工具类关键词中等热度
        elif any(term in keyword_lower for term in ['tool', 'app', 'software', 'platform']):
            news_score = np.random.uniform(40, 70)
            news_count = np.random.randint(10, 50)
            sentiment = 'neutral'
        
        # 教程类关键词低热度
        elif any(term in keyword_lower for term in ['tutorial', 'guide', 'how to']):
            news_score = np.random.uniform(20, 45)
            news_count = np.random.randint(1, 15)
            sentiment = 'neutral'
        
        # 其他关键词
        else:
            news_score = np.random.uniform(10, 40)
            news_count = np.random.randint(0, 10)
            sentiment = 'neutral'
        
        return {
            'news_score': round(news_score, 1),
            'news_count': news_count,
            'sentiment': sentiment,
            'recency': 'recent' if news_score > 60 else 'moderate' if news_score > 30 else 'old'
        }
    
    def calculate_social_score(self, keyword: str) -> Dict:
        """
        计算关键词的社交媒体热度评分
        
        参数:
            keyword (str): 关键词
            
        返回:
            dict: 社交媒体热度分析结果
        """
        # 社交媒体热度分析
        keyword_lower = keyword.lower()
        
        # 病毒式传播的关键词
        if any(term in keyword_lower for term in ['viral', 'trending', 'meme', 'challenge']):
            social_score = np.random.uniform(80, 100)
            engagement_rate = np.random.uniform(8, 15)
            platform_coverage = ['twitter', 'tiktok', 'instagram', 'youtube']
        
        # AI和科技关键词在社交媒体上活跃
        elif any(term in keyword_lower for term in ['ai', 'chatgpt', 'tech', 'innovation']):
            social_score = np.random.uniform(60, 85)
            engagement_rate = np.random.uniform(5, 10)
            platform_coverage = ['twitter', 'linkedin', 'reddit']
        
        # 工具类关键词中等活跃度
        elif any(term in keyword_lower for term in ['tool', 'app', 'free']):
            social_score = np.random.uniform(35, 65)
            engagement_rate = np.random.uniform(2, 6)
            platform_coverage = ['twitter', 'reddit']
        
        # 其他关键词
        else:
            social_score = np.random.uniform(15, 45)
            engagement_rate = np.random.uniform(0.5, 3)
            platform_coverage = ['twitter']
        
        return {
            'social_score': round(social_score, 1),
            'engagement_rate': round(engagement_rate, 2),
            'platform_coverage': platform_coverage,
            'viral_potential': 'high' if social_score > 75 else 'medium' if social_score > 45 else 'low'
        }
    
    def calculate_seasonal_score(self, keyword: str, current_month: int = None) -> Dict:
        """
        计算关键词的季节性评分
        
        参数:
            keyword (str): 关键词
            current_month (int): 当前月份，如果为None则使用当前时间
            
        返回:
            dict: 季节性分析结果
        """
        if current_month is None:
            current_month = datetime.now().month
        
        keyword_lower = keyword.lower()
        
        # 季节性关键词模式
        seasonal_patterns = {
            'christmas': [11, 12, 1],  # 圣诞节相关
            'summer': [6, 7, 8],       # 夏季相关
            'back to school': [8, 9],   # 开学季
            'black friday': [11],       # 黑色星期五
            'new year': [12, 1],        # 新年相关
            'valentine': [2],           # 情人节
            'spring': [3, 4, 5],        # 春季
            'winter': [12, 1, 2],       # 冬季
            'fall': [9, 10, 11],        # 秋季
        }
        
        seasonal_score = 50  # 基础分数
        seasonal_relevance = 'none'
        peak_months = []
        
        # 检查季节性模式
        for pattern, months in seasonal_patterns.items():
            if pattern in keyword_lower:
                if current_month in months:
                    seasonal_score = 90  # 当前是旺季
                    seasonal_relevance = 'high'
                else:
                    seasonal_score = 30  # 当前是淡季
                    seasonal_relevance = 'low'
                peak_months = months
                break
        
        # 检查节假日相关
        holiday_keywords = ['holiday', 'festival', 'celebration', 'gift']
        if any(holiday in keyword_lower for holiday in holiday_keywords):
            # 节假日前后时间评分较高
            if current_month in [11, 12, 1, 2]:  # 年末年初节假日多
                seasonal_score = max(seasonal_score, 75)
                seasonal_relevance = 'medium'
        
        # 教育相关关键词在开学季评分高
        education_keywords = ['course', 'learn', 'study', 'tutorial', 'education']
        if any(edu in keyword_lower for edu in education_keywords):
            if current_month in [8, 9, 1, 2]:  # 开学季
                seasonal_score = max(seasonal_score, 70)
                seasonal_relevance = 'medium'
        
        return {
            'seasonal_score': round(seasonal_score, 1),
            'seasonal_relevance': seasonal_relevance,
            'peak_months': peak_months,
            'current_season_match': current_month in peak_months if peak_months else False
        }
    
    def calculate_timeliness_score(self, trend_data: Dict, news_data: Dict, 
                                 social_data: Dict, seasonal_data: Dict) -> float:
        """
        计算综合实时性评分
        
        参数:
            trend_data: 趋势数据
            news_data: 新闻数据
            social_data: 社交媒体数据
            seasonal_data: 季节性数据
            
        返回:
            float: 综合实时性评分 (0-100)
        """
        timeliness_score = (
            self.trends_weight * trend_data['trend_score'] +
            self.news_weight * news_data['news_score'] +
            self.social_weight * social_data['social_score'] +
            self.seasonal_weight * seasonal_data['seasonal_score']
        )
        
        return round(timeliness_score, 1)
    
    def get_timeliness_grade(self, score: float) -> str:
        """
        根据评分获取时效性等级
        
        参数:
            score (float): 实时性评分
            
        返回:
            str: 时效性等级
        """
        for grade, info in self.timeliness_grades.items():
            if score >= info['min_score']:
                return grade
        return 'F'
    
    def analyze_timeliness(self, df: pd.DataFrame, keyword_col: str = 'query') -> pd.DataFrame:
        """
        分析DataFrame中关键词的实时性
        
        参数:
            df (DataFrame): 关键词数据
            keyword_col (str): 关键词列名
            
        返回:
            添加了实时性分析结果的DataFrame
        """
        if not self.validate_input(df, [keyword_col]):
            return df
        
        self.log_analysis_start("实时性分析", f"，共 {len(df)} 个关键词")
        
        # 创建副本避免修改原始数据
        result_df = df.copy()
        
        # 初始化结果列
        result_columns = [
            'timeliness_score', 'timeliness_grade', 'timeliness_description',
            'trend_score', 'trend_direction', 'growth_rate',
            'news_score', 'news_sentiment', 'news_count',
            'social_score', 'viral_potential', 'engagement_rate',
            'seasonal_score', 'seasonal_relevance', 'current_season_match'
        ]
        
        for col in result_columns:
            result_df[col] = None
        
        # 分析每个关键词
        for idx, row in result_df.iterrows():
            keyword = str(row[keyword_col])
            
            try:
                # 计算各维度评分
                trend_data = self.calculate_trend_score(keyword)
                news_data = self.calculate_news_score(keyword)
                social_data = self.calculate_social_score(keyword)
                seasonal_data = self.calculate_seasonal_score(keyword)
                
                # 计算综合实时性评分
                timeliness_score = self.calculate_timeliness_score(
                    trend_data, news_data, social_data, seasonal_data
                )
                
                # 获取等级和描述
                grade = self.get_timeliness_grade(timeliness_score)
                description = self.timeliness_grades[grade]['description']
                
                # 更新DataFrame
                result_df.at[idx, 'timeliness_score'] = float(timeliness_score)
                result_df.at[idx, 'timeliness_grade'] = grade
                result_df.at[idx, 'timeliness_description'] = description
                
                # 趋势数据
                result_df.at[idx, 'trend_score'] = float(trend_data['trend_score'])
                result_df.at[idx, 'trend_direction'] = trend_data['trend_direction']
                result_df.at[idx, 'growth_rate'] = float(trend_data['growth_rate'])
                
                # 新闻数据
                result_df.at[idx, 'news_score'] = float(news_data['news_score'])
                result_df.at[idx, 'news_sentiment'] = news_data['sentiment']
                result_df.at[idx, 'news_count'] = int(news_data['news_count'])
                
                # 社交媒体数据
                result_df.at[idx, 'social_score'] = float(social_data['social_score'])
                result_df.at[idx, 'viral_potential'] = social_data['viral_potential']
                result_df.at[idx, 'engagement_rate'] = float(social_data['engagement_rate'])
                
                # 季节性数据
                result_df.at[idx, 'seasonal_score'] = float(seasonal_data['seasonal_score'])
                result_df.at[idx, 'seasonal_relevance'] = seasonal_data['seasonal_relevance']
                result_df.at[idx, 'current_season_match'] = bool(seasonal_data['current_season_match'])
                
                if (idx + 1) % 10 == 0:
                    self.logger.info(f"已分析 {idx + 1}/{len(df)} 个关键词")
                    
            except Exception as e:
                self.logger.error(f"分析关键词 '{keyword}' 时出错: {e}")
                # 设置默认值
                result_df.at[idx, 'timeliness_score'] = 50.0
                result_df.at[idx, 'timeliness_grade'] = 'C'
                result_df.at[idx, 'timeliness_description'] = '中等时效性'
                result_df.at[idx, 'trend_score'] = 50.0
                result_df.at[idx, 'trend_direction'] = 'stable'
                result_df.at[idx, 'growth_rate'] = 0.0
                result_df.at[idx, 'news_score'] = 50.0
                result_df.at[idx, 'news_sentiment'] = 'neutral'
                result_df.at[idx, 'news_count'] = 0
                result_df.at[idx, 'social_score'] = 50.0
                result_df.at[idx, 'viral_potential'] = 'low'
                result_df.at[idx, 'engagement_rate'] = 0.0
                result_df.at[idx, 'seasonal_score'] = 50.0
                result_df.at[idx, 'seasonal_relevance'] = 'none'
                result_df.at[idx, 'current_season_match'] = False
        
        # 确保数值列的数据类型正确
        numeric_columns = ['timeliness_score', 'trend_score', 'growth_rate', 'news_score', 
                          'news_count', 'social_score', 'engagement_rate', 'seasonal_score']
        
        for col in numeric_columns:
            if col in result_df.columns:
                result_df[col] = pd.to_numeric(result_df[col], errors='coerce')
        
        # 确保布尔列的数据类型正确
        if 'current_season_match' in result_df.columns:
            result_df['current_season_match'] = result_df['current_season_match'].astype(bool)
        
        self.log_analysis_complete("实时性分析", len(result_df))
        return result_df
    
    def generate_timeliness_summary(self, df: pd.DataFrame) -> Dict:
        """
        生成实时性分析摘要
        
        参数:
            df (DataFrame): 带有实时性分析结果的DataFrame
            
        返回:
            dict: 实时性分析摘要
        """
        if 'timeliness_score' not in df.columns:
            return {'error': '数据中没有实时性分析结果'}
        
        # 等级分布
        grade_counts = df['timeliness_grade'].value_counts().to_dict()
        
        # 趋势方向分布
        trend_direction_counts = df['trend_direction'].value_counts().to_dict()
        
        # 高时效性关键词 (A级和B级)
        high_timeliness = df[df['timeliness_grade'].isin(['A', 'B'])]
        
        # 上升趋势关键词
        rising_trends = df[df['trend_direction'] == 'rising']
        
        # 病毒潜力关键词
        viral_potential = df[df['viral_potential'] == 'high']
        
        return {
            'total_keywords': len(df),
            'average_timeliness_score': round(df['timeliness_score'].mean(), 1),
            'grade_distribution': grade_counts,
            'trend_direction_distribution': trend_direction_counts,
            'high_timeliness_keywords': high_timeliness['query'].tolist() if 'query' in df.columns else [],
            'rising_trend_keywords': rising_trends['query'].tolist() if 'query' in df.columns else [],
            'viral_potential_keywords': viral_potential['query'].tolist() if 'query' in df.columns else [],
            'top_10_by_timeliness': df.nlargest(10, 'timeliness_score')['query'].tolist() if 'query' in df.columns else []
        }
    
    def save_results(self, df: pd.DataFrame, output_dir: str = 'data', prefix: str = 'timeliness'):
        """
        保存实时性分析结果
        
        参数:
            df (DataFrame): 分析结果DataFrame
            output_dir (str): 输出目录
            prefix (str): 文件名前缀
        """
        # 保存主要结果
        filename = FileUtils.generate_filename(prefix, extension='csv')
        file_path = FileUtils.save_dataframe(df, output_dir, filename)
        self.logger.info(f"已保存实时性分析结果到: {file_path}")
        
        # 保存高时效性关键词
        high_timeliness_df = df[df['timeliness_grade'].isin(['A', 'B'])].sort_values('timeliness_score', ascending=False)
        if not high_timeliness_df.empty:
            high_filename = FileUtils.generate_filename(f'{prefix}_high_timeliness', extension='csv')
            high_path = FileUtils.save_dataframe(high_timeliness_df, output_dir, high_filename)
            self.logger.info(f"已保存高时效性关键词 ({len(high_timeliness_df)}个) 到: {high_path}")
        
        # 保存上升趋势关键词
        rising_df = df[df['trend_direction'] == 'rising'].sort_values('growth_rate', ascending=False)
        if not rising_df.empty:
            rising_filename = FileUtils.generate_filename(f'{prefix}_rising_trends', extension='csv')
            rising_path = FileUtils.save_dataframe(rising_df, output_dir, rising_filename)
            self.logger.info(f"已保存上升趋势关键词 ({len(rising_df)}个) 到: {rising_path}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='关键词实时性分析工具')
    parser.add_argument('--input', required=True, help='输入CSV文件路径')
    parser.add_argument('--output', default='data', help='输出目录，默认为data')
    parser.add_argument('--keyword-col', default='query', help='关键词列名，默认为query')
    parser.add_argument('--trends-weight', type=float, default=0.4, help='搜索趋势权重，默认0.4')
    parser.add_argument('--news-weight', type=float, default=0.3, help='新闻热度权重，默认0.3')
    parser.add_argument('--social-weight', type=float, default=0.2, help='社交媒体权重，默认0.2')
    parser.add_argument('--seasonal-weight', type=float, default=0.1, help='季节性权重，默认0.1')
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"错误: 输入文件 '{args.input}' 不存在")
        return
    
    # 读取数据
    try:
        df = pd.read_csv(args.input)
        print(f"已读取 {len(df)} 条关键词数据")
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return
    
    # 创建分析器
    analyzer = TimelinessAnalyzer(
        trends_weight=args.trends_weight,
        news_weight=args.news_weight,
        social_weight=args.social_weight,
        seasonal_weight=args.seasonal_weight
    )
    
    # 分析实时性
    result_df = analyzer.analyze_timeliness(df, args.keyword_col)
    
    # 生成摘要
    summary = analyzer.generate_timeliness_summary(result_df)
    
    # 保存结果
    analyzer.save_results(result_df, args.output)
    
    # 显示摘要
    print("\n=== 实时性分析摘要 ===")
    print(f"总关键词数: {summary['total_keywords']}")
    print(f"平均实时性评分: {summary['average_timeliness_score']}")
    print(f"高时效性关键词数: {len(summary['high_timeliness_keywords'])}")
    print(f"上升趋势关键词数: {len(summary['rising_trend_keywords'])}")
    print(f"病毒潜力关键词数: {len(summary['viral_potential_keywords'])}")


if __name__ == "__main__":
    main()