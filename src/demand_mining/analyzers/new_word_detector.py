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
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from collectors.trends_singleton import get_trends_collector
    from utils import Logger, FileUtils
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
        
        # 初始化趋势收集器 - 使用单例模式避免重复创建会话
        self.trends_collector = None
        try:
            from src.collectors.trends_singleton import get_trends_collector
            self.trends_collector = get_trends_collector()
        except ImportError:
            pass
        
        if self.trends_collector:
            self.logger.info("趋势收集器初始化成功")
        else:
            self.logger.warning("趋势收集器初始化失败")
        
        # 添加请求缓存避免重复请求
        self._trends_cache = {}
        
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
        # 检查缓存
        cache_key = f"trends_{keyword}"
        if cache_key in self._trends_cache:
            return self._trends_cache[cache_key]
        
        if self.trends_collector:
            try:
                # 添加延迟避免429错误 - 新词检测器请求间隔控制
                import time
                time.sleep(2)  # 新词检测器专用延迟
                
                # 只获取12个月数据，从中提取其他时间段的数据
                data_12m = self.trends_collector.get_trends_data([keyword], timeframe='today 12-m')
                
                # 如果12个月数据获取失败，尝试获取3个月数据
                if data_12m.empty:
                    # 添加额外延迟避免连续请求
                    time.sleep(1)
                    data_12m = self.trends_collector.get_trends_data([keyword], timeframe='today 3-m')
                    
                    # 如果3个月数据也失败，返回默认值并缓存
                    if data_12m.empty:
                        self.logger.warning(f"无法获取关键词 '{keyword}' 的趋势数据，使用默认值")
                        default_result = {
                            'avg_12m': 0.0, 'max_12m': 0.0,
                            'avg_90d': 0.0, 'max_90d': 0.0,
                            'avg_30d': 0.0, 'max_30d': 0.0,
                            'avg_7d': 0.0, 'max_7d': 0.0,
                            'recent_trend': []
                        }
                        self._trends_cache[cache_key] = default_result
                        return default_result
                
                # 从12个月数据中计算其他时间段
                data_90d = data_12m.tail(90) if len(data_12m) >= 90 else data_12m
                data_30d = data_12m.tail(30) if len(data_12m) >= 30 else data_12m
                data_7d = data_12m.tail(7) if len(data_12m) >= 7 else data_12m
                
                result = {}
                
                # 处理12个月数据
                if not data_12m.empty and keyword in data_12m.columns:
                    values_12m = data_12m[keyword].values
                    result['avg_12m'] = float(np.mean(values_12m)) if len(values_12m) > 0 else 0.0
                    result['max_12m'] = float(np.max(values_12m)) if len(values_12m) > 0 else 0.0
                else:
                    result['avg_12m'] = 0.0
                    result['max_12m'] = 0.0
                
                # 处理90天数据
                if not data_90d.empty and keyword in data_90d.columns:
                    values_90d = data_90d[keyword].values
                    result['avg_90d'] = float(np.mean(values_90d)) if len(values_90d) > 0 else 0.0
                    result['max_90d'] = float(np.max(values_90d)) if len(values_90d) > 0 else 0.0
                else:
                    result['avg_90d'] = 0.0
                    result['max_90d'] = 0.0
                
                # 处理30天数据
                if not data_30d.empty and keyword in data_30d.columns:
                    values_30d = data_30d[keyword].values
                    result['avg_30d'] = float(np.mean(values_30d)) if len(values_30d) > 0 else 0.0
                    result['max_30d'] = float(np.max(values_30d)) if len(values_30d) > 0 else 0.0
                else:
                    result['avg_30d'] = 0.0
                    result['max_30d'] = 0.0
                
                # 处理7天数据
                if not data_7d.empty and keyword in data_7d.columns:
                    values_7d = data_7d[keyword].values
                    result['avg_7d'] = float(np.mean(values_7d)) if len(values_7d) > 0 else 0.0
                    result['max_7d'] = float(np.max(values_7d)) if len(values_7d) > 0 else 0.0
                    result['recent_trend'] = values_7d[-3:].tolist() if len(values_7d) >= 3 else values_7d.tolist()
                else:
                    result['avg_7d'] = 0.0
                    result['max_7d'] = 0.0
                    result['recent_trend'] = []
                
                # 缓存结果
                self._trends_cache[cache_key] = result
                return result
                
            except Exception as e:
                self.logger.warning(f"获取真实历史数据失败: {e}")
        
        # 无法获取数据时返回空结果
        return {
            'avg_12m': 0.0,
            'max_12m': 0.0,
            'avg_90d': 0.0,
            'max_90d': 0.0,
            'avg_30d': 0.0,
            'max_30d': 0.0,
            'avg_7d': 0.0,
            'max_7d': 0.0,
            'recent_trend': []
        }
    
    def calculate_new_word_score(self, historical_data: Dict) -> float:
        """
        计算新词得分
        
        参数:
            historical_data (dict): 历史搜索数据
            
        返回:
            float: 新词得分 (0-100)
        """
        score = 0.0
        
        # 获取数据
        avg_12m = historical_data.get('avg_12m', 0)
        avg_90d = historical_data.get('avg_90d', 0)
        avg_30d = historical_data.get('avg_30d', 0)
        avg_7d = historical_data.get('avg_7d', 0)
        
        # 1. 历史搜索量低 (40分)
        if avg_12m <= self.thresholds['low_volume_12m']:
            score += 15
        if avg_90d <= self.thresholds['low_volume_90d']:
            score += 15
        if avg_30d <= self.thresholds['low_volume_30d']:
            score += 10
        
        # 2. 近期增长率高 (40分)
        if avg_30d > 0 and avg_7d > avg_30d:
            growth_rate = ((avg_7d - avg_30d) / avg_30d) * 100
            if growth_rate >= self.thresholds['high_growth_7d']:
                score += 40
            elif growth_rate >= self.thresholds['high_growth_7d'] * 0.5:
                score += 25
            elif growth_rate >= self.thresholds['high_growth_7d'] * 0.25:
                score += 15
        
        # 3. 最近搜索量达标 (20分)
        if avg_7d >= self.thresholds['min_recent_volume']:
            score += 20
        elif avg_7d >= self.thresholds['min_recent_volume'] * 0.5:
            score += 10
        
        return min(score, 100.0)
    
    def get_new_word_grade(self, score: float) -> str:
        """
        根据得分获取新词等级
        
        参数:
            score (float): 新词得分
            
        返回:
            str: 新词等级 (S/A/B/C/D)
        """
        for grade, info in self.new_word_grades.items():
            if score >= info['min_score']:
                return grade
        return 'D'
    
    def detect_new_words(self, data: pd.DataFrame, keyword_col: str = 'query') -> pd.DataFrame:
        """
        检测新词
        
        参数:
            data (pd.DataFrame): 包含关键词的数据
            keyword_col (str): 关键词列名
            
        返回:
            pd.DataFrame: 添加了新词检测结果的数据
        """
        if data.empty or keyword_col not in data.columns:
            return data
        
        results = []
        
        # 批量处理关键词，每批最多3个，避免429错误
        keywords = data[keyword_col].tolist()
        batch_size = 3
        
        for i in range(0, len(keywords), batch_size):
            batch_keywords = keywords[i:i + batch_size]
            batch_indices = data.index[i:i + batch_size]
            
            for j, keyword in enumerate(batch_keywords):
                idx = batch_indices[j]
                row = data.loc[idx]
                
                # 获取历史数据
                historical_data = self.get_historical_data(keyword)
                
                # 计算新词得分
                score = self.calculate_new_word_score(historical_data)
                
                # 获取新词等级
                grade = self.get_new_word_grade(score)
                
                # 添加结果
            result = {
                'keyword': keyword,
                'new_word_score': score,
                'new_word_grade': grade,
                'is_new_word': score >= 60,  # 添加is_new_word字段
                'confidence_level': 'high' if score >= 80 else 'medium' if score >= 60 else 'low',  # 添加confidence_level字段
                'grade_description': self.new_word_grades[grade]['description'],
                'avg_12m': historical_data.get('avg_12m', 0),
                'avg_90d': historical_data.get('avg_90d', 0),
                'avg_30d': historical_data.get('avg_30d', 0),
                'avg_7d': historical_data.get('avg_7d', 0),
                'recent_trend': historical_data.get('recent_trend', [])
            }
            
            results.append(result)
            
            # 批次间添加短暂间隔，避免429错误
            if i + batch_size < len(keywords):
                import time
                time.sleep(0.3)
        
        # 转换为DataFrame
        new_word_df = pd.DataFrame(results)
        
        # 合并到原数据
        if not new_word_df.empty:
            # 重置索引确保合并正确
            data_reset = data.reset_index(drop=True)
            new_word_df_reset = new_word_df.reset_index(drop=True)
            
            # 合并数据
            merged_data = pd.concat([data_reset, new_word_df_reset.drop('keyword', axis=1)], axis=1)
            return merged_data
        
        return data
    
    def get_top_new_words(self, data: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """
        获取得分最高的新词
        
        参数:
            data (pd.DataFrame): 包含新词检测结果的数据
            top_n (int): 返回前N个新词
            
        返回:
            pd.DataFrame: 排序后的新词数据
        """
        if 'new_word_score' not in data.columns:
            return pd.DataFrame()
        
        # 按新词得分排序
        sorted_data = data.sort_values('new_word_score', ascending=False)
        
        return sorted_data.head(top_n)
    
    def export_results(self, data: pd.DataFrame, output_path: str = None) -> str:
        """
        导出新词检测结果
        
        参数:
            data (pd.DataFrame): 新词检测结果数据
            output_path (str): 输出路径
            
        返回:
            str: 输出文件路径
        """
        if output_path is None:
            output_path = FileUtils.generate_filename('new_word_detection', 'csv')
        
        # 选择要导出的列
        export_columns = [
            'keyword', 'new_word_score', 'new_word_grade', 'grade_description',
            'avg_12m', 'avg_90d', 'avg_30d', 'avg_7d'
        ]
        
        # 过滤存在的列
        available_columns = [col for col in export_columns if col in data.columns]
        
        if available_columns:
            export_data = data[available_columns]
            export_data.to_csv(output_path, index=False, encoding='utf-8-sig')
            self.logger.info(f"新词检测结果已导出到: {output_path}")
        
        return output_path