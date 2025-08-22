#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新词检测器 - New Word Detector
用于识别和评估新兴关键词的潜力
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import json

from .base_analyzer import BaseAnalyzer

try:
    from src.utils import Logger, FileUtils
    from src.collectors.trends_collector import TrendsCollector
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


class NewWordDetector(BaseAnalyzer):
    """新词检测器，用于识别具有新词特征的关键词"""
    
    def __init__(self, 
                 low_volume_threshold_12m=100,    # 12个月平均搜索量阈值
                 low_volume_threshold_90d=50,     # 90天平均搜索量阈值  
                 low_volume_threshold_30d=30,     # 30天平均搜索量阈值
                 high_growth_threshold_7d=200,    # 7天增长率阈值(%)
                 min_recent_volume=20):           # 最近7天最低搜索量
        """
        初始化新词检测器
        
        参数:
            low_volume_threshold_12m (int): 12个月平均搜索量阈值
            low_volume_threshold_90d (int): 90天平均搜索量阈值
            low_volume_threshold_30d (int): 30天平均搜索量阈值
            high_growth_threshold_7d (float): 7天增长率阈值(%)
            min_recent_volume (int): 最近7天最低搜索量
        """
        super().__init__()
        
        # 新词判断阈值
        self.thresholds = {
            'low_volume_12m': low_volume_threshold_12m,
            'low_volume_90d': low_volume_threshold_90d,
            'low_volume_30d': low_volume_threshold_30d,
            'high_growth_7d': high_growth_threshold_7d,
            'min_recent_volume': min_recent_volume
        }
        
        # 初始化趋势收集器
        try:
            self.trends_collector = TrendsCollector()
            self.logger.info("趋势收集器初始化成功")
        except:
            self.trends_collector = None
            self.logger.warning("趋势收集器初始化失败")
        
        # 新词等级定义
        self.new_word_grades = {
            'S': {'min_score': 90, 'description': '超级新词 - 爆发式增长'},
            'A': {'min_score': 80, 'description': '强新词 - 快速增长'},
            'B': {'min_score': 70, 'description': '中新词 - 稳定增长'},
            'C': {'min_score': 60, 'description': '弱新词 - 缓慢增长'},
            'D': {'min_score': 0, 'description': '非新词 - 传统关键词'}
        }
    
    def analyze(self, data, keyword_col='query', **kwargs):
        """
        实现基础分析器的抽象方法
        
        参数:
            data: 关键词数据DataFrame
            keyword_col: 关键词列名
            **kwargs: 其他参数
            
        返回:
            添加了新词检测结果的DataFrame
        """
        return self.detect_new_words(data, keyword_col)
    
    def get_historical_data(self, keyword: str) -> Dict:
        """
        获取关键词的历史搜索数据
        
        参数:
            keyword (str): 关键词
            
        返回:
            dict: 包含不同时间段搜索数据的字典
        """
        if self.trends_collector:
            try:
                # 获取不同时间段的真实数据
                data_12m = self.trends_collector.get_trends_data([keyword], timeframe='12m')
                data_90d = self.trends_collector.get_trends_data([keyword], timeframe='3m')
                data_30d = self.trends_collector.get_trends_data([keyword], timeframe='1m')
                data_7d = self.trends_collector.get_trends_data([keyword], timeframe='7d')
                
                result = {}
                
                # 处理12个月数据
                if data_12m and keyword in data_12m:
                    values_12m = data_12m[keyword]['values']
                    result['avg_12m'] = np.mean(values_12m) if values_12m else 0
                    result['max_12m'] = max(values_12m) if values_12m else 0
                else:
                    result['avg_12m'] = 0
                    result['max_12m'] = 0
                
                # 处理90天数据
                if data_90d and keyword in data_90d:
                    values_90d = data_90d[keyword]['values']
                    result['avg_90d'] = np.mean(values_90d) if values_90d else 0
                    result['max_90d'] = max(values_90d) if values_90d else 0
                else:
                    result['avg_90d'] = 0
                    result['max_90d'] = 0
                
                # 处理30天数据
                if data_30d and keyword in data_30d:
                    values_30d = data_30d[keyword]['values']
                    result['avg_30d'] = np.mean(values_30d) if values_30d else 0
                    result['max_30d'] = max(values_30d) if values_30d else 0
                else:
                    result['avg_30d'] = 0
                    result['max_30d'] = 0
                
                # 处理7天数据
                if data_7d and keyword in data_7d:
                    values_7d = data_7d[keyword]['values']
                    result['avg_7d'] = np.mean(values_7d) if values_7d else 0
                    result['max_7d'] = max(values_7d) if values_7d else 0
                    result['recent_trend'] = values_7d[-3:] if len(values_7d) >= 3 else values_7d
                else:
                    result['avg_7d'] = 0
                    result['max_7d'] = 0
                    result['recent_trend'] = []
                
                return result
                
            except Exception as e:
                self.logger.warning(f"获取真实历史数据失败: {e}")
        
        # 无法获取数据
        return {}
    
        keyword_lower = keyword.lower()
        
        # 判断关键词类型，分析不同的历史数据模式
        
        # AI相关新词 - 典型的新词模式
        if any(term in keyword_lower for term in ['chatgpt', 'gpt-4', 'claude', 'gemini', 'copilot']):
            return {
                'avg_12m': np.random.uniform(5, 25),      # 12个月平均很低
                'max_12m': np.random.uniform(10, 40),
                'avg_90d': np.random.uniform(8, 35),      # 90天平均较低
                'max_90d': np.random.uniform(15, 50),
                'avg_30d': np.random.uniform(15, 45),     # 30天开始增长
                'max_30d': np.random.uniform(25, 60),
                'avg_7d': np.random.uniform(80, 200),     # 7天爆发式增长
                'max_7d': np.random.uniform(150, 300),
                'recent_trend': [180, 220, 250]          # 持续上升
            }
        
        # 新工具类关键词
        elif any(term in keyword_lower for term in ['ai tool', 'generator', 'creator', 'maker']):
            return {
                'avg_12m': np.random.uniform(10, 40),
                'max_12m': np.random.uniform(20, 60),
                'avg_90d': np.random.uniform(15, 50),
                'max_90d': np.random.uniform(25, 70),
                'avg_30d': np.random.uniform(25, 60),
                'max_30d': np.random.uniform(40, 80),
                'avg_7d': np.random.uniform(60, 150),
                'max_7d': np.random.uniform(100, 200),
                'recent_trend': [120, 140, 160]
            }
        
        # 传统关键词 - 不符合新词模式
        elif any(term in keyword_lower for term in ['google', 'facebook', 'youtube', 'amazon']):
            return {
                'avg_12m': np.random.uniform(200, 500),   # 历史搜索量很高
                'max_12m': np.random.uniform(400, 800),
                'avg_90d': np.random.uniform(180, 450),
                'max_90d': np.random.uniform(350, 700),
                'avg_30d': np.random.uniform(190, 480),
                'max_30d': np.random.uniform(380, 750),
                'avg_7d': np.random.uniform(200, 500),    # 7天增长不明显
                'max_7d': np.random.uniform(400, 800),
                'recent_trend': [450, 460, 470]          # 稳定增长
            }
        
        # 其他关键词 - 中等模式
        else:
            # 随机决定是否为新词
            is_new_word = np.random.random() < 0.3  # 30%概率为新词
            
            if is_new_word:
                return {
                    'avg_12m': np.random.uniform(5, 50),
                    'max_12m': np.random.uniform(10, 80),
                    'avg_90d': np.random.uniform(10, 60),
                    'max_90d': np.random.uniform(20, 90),
                    'avg_30d': np.random.uniform(20, 70),
                    'max_30d': np.random.uniform(30, 100),
                    'avg_7d': np.random.uniform(50, 180),
                    'max_7d': np.random.uniform(80, 250),
                    'recent_trend': [120, 150, 180]
                }
            else:
                return {
                    'avg_12m': np.random.uniform(80, 300),
                    'max_12m': np.random.uniform(150, 500),
                    'avg_90d': np.random.uniform(75, 280),
                    'max_90d': np.random.uniform(140, 450),
                    'avg_30d': np.random.uniform(70, 290),
                    'max_30d': np.random.uniform(130, 480),
                    'avg_7d': np.random.uniform(80, 320),
                    'max_7d': np.random.uniform(160, 520),
                    'recent_trend': [280, 290, 300]
                }
    
    def calculate_new_word_score(self, historical_data: Dict) -> Dict:
        """
        根据历史数据计算新词评分
        
        参数:
            historical_data (dict): 历史搜索数据
            
        返回:
            dict: 新词分析结果
        """
        score = 0
        reasons = []
        
        # 检查12个月平均搜索量是否较低
        if historical_data['avg_12m'] <= self.thresholds['low_volume_12m']:
            score += 25
            reasons.append(f"12个月平均搜索量低 ({historical_data['avg_12m']:.1f})")
        
        # 检查90天平均搜索量是否较低
        if historical_data['avg_90d'] <= self.thresholds['low_volume_90d']:
            score += 20
            reasons.append(f"90天平均搜索量低 ({historical_data['avg_90d']:.1f})")
        
        # 检查30天平均搜索量是否较低
        if historical_data['avg_30d'] <= self.thresholds['low_volume_30d']:
            score += 15
            reasons.append(f"30天平均搜索量低 ({historical_data['avg_30d']:.1f})")
        
        # 检查7天是否有大幅增长
        if historical_data['avg_30d'] > 0:
            growth_rate_7d = ((historical_data['avg_7d'] - historical_data['avg_30d']) / 
                             historical_data['avg_30d']) * 100
        else:
            growth_rate_7d = 0
        
        if growth_rate_7d >= self.thresholds['high_growth_7d']:
            score += 30
            reasons.append(f"7天增长率高 ({growth_rate_7d:.1f}%)")
        elif growth_rate_7d >= self.thresholds['high_growth_7d'] * 0.5:
            score += 15
            reasons.append(f"7天增长率中等 ({growth_rate_7d:.1f}%)")
        
        # 检查最近搜索量是否达到最低要求
        if historical_data['avg_7d'] >= self.thresholds['min_recent_volume']:
            score += 10
            reasons.append(f"最近搜索量充足 ({historical_data['avg_7d']:.1f})")
        
        # 检查趋势是否持续上升
        if len(historical_data['recent_trend']) >= 2:
            trend_increasing = all(
                historical_data['recent_trend'][i] <= historical_data['recent_trend'][i+1] 
                for i in range(len(historical_data['recent_trend'])-1)
            )
            if trend_increasing:
                score += 10
                reasons.append("最近趋势持续上升")
        
        # 计算新词强度指数 (0-100)
        new_word_intensity = min(100, score)
        
        # 计算爆发指数
        if historical_data['avg_30d'] > 0:
            explosion_index = historical_data['avg_7d'] / historical_data['avg_30d']
        else:
            explosion_index = historical_data['avg_7d'] / 1  # 避免除零
        
        return {
            'new_word_score': round(new_word_intensity, 1),
            'growth_rate_7d': round(growth_rate_7d, 1),
            'explosion_index': round(explosion_index, 2),
            'is_new_word': new_word_intensity >= 60,  # 60分以上认为是新词
            'confidence_level': 'high' if new_word_intensity >= 80 else 'medium' if new_word_intensity >= 60 else 'low',
            'detection_reasons': reasons,
            'historical_pattern': self._classify_pattern(historical_data)
        }
    
    def _classify_pattern(self, data: Dict) -> str:
        """
        分类历史数据模式
        
        参数:
            data (dict): 历史数据
            
        返回:
            str: 模式类型
        """
        # 计算各时间段的相对增长
        if data['avg_30d'] > 0:
            growth_7d_vs_30d = data['avg_7d'] / data['avg_30d']
        else:
            growth_7d_vs_30d = float('inf')
        
        if data['avg_90d'] > 0:
            growth_30d_vs_90d = data['avg_30d'] / data['avg_90d']
        else:
            growth_30d_vs_90d = float('inf')
        
        # 判断模式
        if growth_7d_vs_30d > 3 and growth_30d_vs_90d > 2:
            return 'explosive_growth'  # 爆发式增长
        elif growth_7d_vs_30d > 2:
            return 'rapid_growth'      # 快速增长
        elif growth_7d_vs_30d > 1.5:
            return 'steady_growth'     # 稳定增长
        elif growth_7d_vs_30d > 1:
            return 'slow_growth'       # 缓慢增长
        else:
            return 'stable_or_declining'  # 稳定或下降
    
    def get_new_word_grade(self, score: float) -> str:
        """
        根据评分获取新词等级
        
        参数:
            score (float): 新词评分
            
        返回:
            str: 新词等级
        """
        for grade, info in self.new_word_grades.items():
            if score >= info['min_score']:
                return grade
        return 'D'
    
    def detect_new_words(self, df: pd.DataFrame, keyword_col: str = 'query') -> pd.DataFrame:
        """
        检测DataFrame中的新词
        
        参数:
            df (DataFrame): 关键词数据
            keyword_col (str): 关键词列名
            
        返回:
            添加了新词检测结果的DataFrame
        """
        if not self.validate_input(df, [keyword_col]):
            return df
        
        self.log_analysis_start("新词检测", f"，共 {len(df)} 个关键词")
        
        # 创建副本避免修改原始数据
        result_df = df.copy()
        
        # 初始化结果列
        result_columns = [
            'is_new_word', 'new_word_score', 'new_word_grade', 'new_word_description',
            'growth_rate_7d', 'explosion_index', 'confidence_level', 'historical_pattern',
            'avg_volume_12m', 'avg_volume_90d', 'avg_volume_30d', 'avg_volume_7d',
            'detection_reasons'
        ]
        
        for col in result_columns:
            result_df[col] = None
        
        # 分析每个关键词
        for idx, row in result_df.iterrows():
            keyword = str(row[keyword_col])
            
            try:
                # 获取历史数据
                historical_data = self.get_historical_data(keyword)
                
                # 计算新词评分
                new_word_result = self.calculate_new_word_score(historical_data)
                
                # 获取等级和描述
                grade = self.get_new_word_grade(new_word_result['new_word_score'])
                description = self.new_word_grades[grade]['description']
                
                # 更新DataFrame
                result_df.at[idx, 'is_new_word'] = bool(new_word_result['is_new_word'])
                result_df.at[idx, 'new_word_score'] = float(new_word_result['new_word_score'])
                result_df.at[idx, 'new_word_grade'] = grade
                result_df.at[idx, 'new_word_description'] = description
                result_df.at[idx, 'growth_rate_7d'] = float(new_word_result['growth_rate_7d'])
                result_df.at[idx, 'explosion_index'] = float(new_word_result['explosion_index'])
                result_df.at[idx, 'confidence_level'] = new_word_result['confidence_level']
                result_df.at[idx, 'historical_pattern'] = new_word_result['historical_pattern']
                
                # 历史数据
                result_df.at[idx, 'avg_volume_12m'] = float(historical_data['avg_12m'])
                result_df.at[idx, 'avg_volume_90d'] = float(historical_data['avg_90d'])
                result_df.at[idx, 'avg_volume_30d'] = float(historical_data['avg_30d'])
                result_df.at[idx, 'avg_volume_7d'] = float(historical_data['avg_7d'])
                
                # 检测原因
                result_df.at[idx, 'detection_reasons'] = '; '.join(new_word_result['detection_reasons'])
                
                if (idx + 1) % 10 == 0:
                    self.logger.info(f"已检测 {idx + 1}/{len(df)} 个关键词")
                    
            except Exception as e:
                self.logger.error(f"检测关键词 '{keyword}' 时出错: {e}")
                # 设置默认值
                result_df.at[idx, 'is_new_word'] = False
                result_df.at[idx, 'new_word_score'] = 0.0
                result_df.at[idx, 'new_word_grade'] = 'D'
                result_df.at[idx, 'new_word_description'] = '非新词'
                result_df.at[idx, 'growth_rate_7d'] = 0.0
                result_df.at[idx, 'explosion_index'] = 1.0
                result_df.at[idx, 'confidence_level'] = 'low'
                result_df.at[idx, 'historical_pattern'] = 'unknown'
                result_df.at[idx, 'avg_volume_12m'] = 0.0
                result_df.at[idx, 'avg_volume_90d'] = 0.0
                result_df.at[idx, 'avg_volume_30d'] = 0.0
                result_df.at[idx, 'avg_volume_7d'] = 0.0
                result_df.at[idx, 'detection_reasons'] = '检测失败'
        
        # 确保数值列的数据类型正确
        numeric_columns = ['new_word_score', 'growth_rate_7d', 'explosion_index',
                          'avg_volume_12m', 'avg_volume_90d', 'avg_volume_30d', 'avg_volume_7d']
        
        for col in numeric_columns:
            if col in result_df.columns:
                result_df[col] = pd.to_numeric(result_df[col], errors='coerce')
        
        # 确保布尔列的数据类型正确
        if 'is_new_word' in result_df.columns:
            result_df['is_new_word'] = result_df['is_new_word'].astype(bool)
        
        self.log_analysis_complete("新词检测", len(result_df))
        return result_df
    
    def generate_new_word_summary(self, df: pd.DataFrame) -> Dict:
        """
        生成新词检测摘要
        
        参数:
            df (DataFrame): 带有新词检测结果的DataFrame
            
        返回:
            dict: 新词检测摘要
        """
        if 'new_word_score' not in df.columns:
            return {'error': '数据中没有新词检测结果'}
        
        # 新词统计
        new_words = df[df['is_new_word'] == True]
        
        # 等级分布
        grade_counts = df['new_word_grade'].value_counts().to_dict()
        
        # 模式分布
        pattern_counts = df['historical_pattern'].value_counts().to_dict()
        
        # 高置信度新词
        high_confidence = df[df['confidence_level'] == 'high']
        
        # 爆发式增长关键词
        explosive_growth = df[df['historical_pattern'] == 'explosive_growth']
        
        return {
            'total_keywords': len(df),
            'new_words_count': len(new_words),
            'new_words_percentage': round(len(new_words) / len(df) * 100, 1),
            'average_new_word_score': round(df['new_word_score'].mean(), 1),
            'grade_distribution': grade_counts,
            'pattern_distribution': pattern_counts,
            'high_confidence_new_words': high_confidence['query'].tolist() if 'query' in df.columns else [],
            'explosive_growth_keywords': explosive_growth['query'].tolist() if 'query' in df.columns else [],
            'top_10_new_words': new_words.nlargest(10, 'new_word_score')['query'].tolist() if 'query' in df.columns and not new_words.empty else []
        }
    
    def save_results(self, df: pd.DataFrame, output_dir: str = 'data', prefix: str = 'new_words'):
        """
        保存新词检测结果
        
        参数:
            df (DataFrame): 检测结果DataFrame
            output_dir (str): 输出目录
            prefix (str): 文件名前缀
        """
        # 保存主要结果
        filename = FileUtils.generate_filename(prefix, extension='csv')
        file_path = FileUtils.save_dataframe(df, output_dir, filename)
        self.logger.info(f"已保存新词检测结果到: {file_path}")
        
        # 保存检测到的新词
        new_words_df = df[df['is_new_word'] == True].sort_values('new_word_score', ascending=False)
        if not new_words_df.empty:
            new_words_filename = FileUtils.generate_filename(f'{prefix}_detected', extension='csv')
            new_words_path = FileUtils.save_dataframe(new_words_df, output_dir, new_words_filename)
            self.logger.info(f"已保存检测到的新词 ({len(new_words_df)}个) 到: {new_words_path}")
        
        # 保存高置信度新词
        high_confidence_df = df[df['confidence_level'] == 'high'].sort_values('new_word_score', ascending=False)
        if not high_confidence_df.empty:
            high_conf_filename = FileUtils.generate_filename(f'{prefix}_high_confidence', extension='csv')
            high_conf_path = FileUtils.save_dataframe(high_confidence_df, output_dir, high_conf_filename)
            self.logger.info(f"已保存高置信度新词 ({len(high_confidence_df)}个) 到: {high_conf_path}")


def main():
    """主函数"""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='新词检测工具')
    parser.add_argument('--input', required=True, help='输入CSV文件路径')
    parser.add_argument('--output', default='data', help='输出目录，默认为data')
    parser.add_argument('--keyword-col', default='query', help='关键词列名，默认为query')
    parser.add_argument('--low-volume-12m', type=int, default=100, help='12个月低搜索量阈值')
    parser.add_argument('--low-volume-90d', type=int, default=50, help='90天低搜索量阈值')
    parser.add_argument('--low-volume-30d', type=int, default=30, help='30天低搜索量阈值')
    parser.add_argument('--high-growth-7d', type=float, default=200, help='7天高增长率阈值(%)')
    parser.add_argument('--min-recent-volume', type=int, default=20, help='最近7天最低搜索量')
    
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
    
    # 创建检测器
    detector = NewWordDetector(
        low_volume_threshold_12m=args.low_volume_12m,
        low_volume_threshold_90d=args.low_volume_90d,
        low_volume_threshold_30d=args.low_volume_30d,
        high_growth_threshold_7d=args.high_growth_7d,
        min_recent_volume=args.min_recent_volume
    )
    
    # 检测新词
    result_df = detector.detect_new_words(df, args.keyword_col)
    
    # 生成摘要
    summary = detector.generate_new_word_summary(result_df)
    
    # 保存结果
    detector.save_results(result_df, args.output)
    
    # 显示摘要
    print("\n=== 新词检测摘要 ===")
    print(f"总关键词数: {summary['total_keywords']}")
    print(f"检测到的新词数: {summary['new_words_count']}")
    print(f"新词占比: {summary['new_words_percentage']}%")
    print(f"平均新词评分: {summary['average_new_word_score']}")
    print(f"高置信度新词数: {len(summary['high_confidence_new_words'])}")
    print(f"爆发式增长关键词数: {len(summary['explosive_growth_keywords'])}")


if __name__ == "__main__":
    main()
