#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新词检测器 - New Word Detector
用于识别和评估新兴关键词的潜力
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import requests
import json
import time
import hashlib
from pathlib import Path

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
        self.cache_dir = Path('data/cache/new_word_trends')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache_ttl = timedelta(minutes=30)
        self.disk_cache_ttl = timedelta(hours=12)
        self.max_retries = 3
        self.retry_backoff = 1.5
        self.retry_delay_base = 0.8

        
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
        self._trends_cache = {}  # cache_key -> {'data': Dict, 'timestamp': datetime}
        
        # 新词等级定义
        self.new_word_grades = {
            'S': {'min_score': 90, 'description': '超级新词 - 爆发式增长'},
            'A': {'min_score': 80, 'description': '强新词 - 快速增长'},
            'B': {'min_score': 70, 'description': '中新词 - 稳定增长'},
            'C': {'min_score': 60, 'description': '弱新词 - 缓慢增长'},
            'D': {'min_score': 0, 'description': '非新词 - 传统关键词'}
        }

    def _empty_trend_result(self) -> Dict[str, Any]:
        """Return a default trend payload with all expected keys."""
        return {
            'avg_12m': 0.0,
            'max_12m': 0.0,
            'avg_90d': 0.0,
            'max_90d': 0.0,
            'avg_30d': 0.0,
            'max_30d': 0.0,
            'avg_7d': 0.0,
            'max_7d': 0.0,
            'recent_trend': [],
            'growth_rate_7d_vs_30d': 0.0,
            'mom_growth': 0.0,
            'yoy_growth': 0.0,
            'z_score': 0.0,
            'std_12m': 0.0,
            'series_length': 0,
            'series_12m': []
        }

    def _get_cache_file_path(self, keyword: str) -> Path:
        digest = hashlib.md5(keyword.lower().encode('utf-8')).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def _load_cache_from_disk(self, keyword: str) -> Tuple[Optional[Dict[str, Any]], Optional[datetime]]:
        cache_file = self._get_cache_file_path(keyword)
        if not cache_file.exists():
            return None, None
        try:
            with cache_file.open('r', encoding='utf-8') as fh:
                payload = json.load(fh)
            timestamp_str = payload.get('timestamp')
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else None
            data = payload.get('data', {})
            return data, timestamp
        except Exception as exc:
            self.logger.warning(f"读取新词检测缓存失败 ({keyword}): {exc}")
            return None, None

    def _store_cache(self, cache_key: str, keyword: str, data: Dict[str, Any]) -> None:
        now = datetime.utcnow()
        self._trends_cache[cache_key] = {'data': data, 'timestamp': now}
        try:
            payload = {'keyword': keyword, 'timestamp': now.isoformat(), 'data': data}
            with self._get_cache_file_path(keyword).open('w', encoding='utf-8') as fh:
                json.dump(payload, fh, ensure_ascii=False)
        except Exception as exc:
            self.logger.warning(f"写入新词检测缓存失败 ({keyword}): {exc}")

    def _fetch_trends_dataframe(self, keyword: str, timeframe: str) -> pd.DataFrame:
        if not self.trends_collector:
            return pd.DataFrame()
        last_exception: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                sleep_time = min(self.retry_delay_base * attempt, 3)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                df = self.trends_collector.get_trends_data([keyword], timeframe=timeframe)
                if not df.empty:
                    return df
            except Exception as exc:
                last_exception = exc
                self.logger.warning(f"获取 {keyword} ({timeframe}) 趋势数据失败，第 {attempt} 次尝试: {exc}")
            backoff = min(self.retry_backoff ** attempt, 5)
            time.sleep(backoff)
        if last_exception:
            self.logger.warning(f"多次尝试后仍无法获取 {keyword} ({timeframe}) 数据: {last_exception}")
        return pd.DataFrame()

    @staticmethod
    def _percent_change(current: float, previous: Optional[float]) -> float:
        if previous is None or previous <= 0:
            return 0.0
        return float(round(((current - previous) / previous) * 100, 2))

    def _summarize_trends(self, keyword: str, data_12m: pd.DataFrame) -> Dict[str, Any]:
        result = self._empty_trend_result()
        if data_12m.empty or keyword not in data_12m.columns:
            return result

    @staticmethod
    def _score_growth_signal(value: Optional[float], positive_bands: List[Tuple[float, float]], negative_bands: Optional[List[Tuple[float, float]]] = None) -> float:
        if value is None:
            return 0.0
        score = 0.0
        for threshold, points in positive_bands:
            if value >= threshold:
                score = points
                break
        if negative_bands:
            for threshold, penalty in negative_bands:
                if value <= threshold:
                    score -= penalty
                    break
        return max(score, 0.0)

        series = data_12m[keyword].fillna(0).astype(float).values
        if len(series) == 0:
            return result
        arr = np.nan_to_num(np.array(series, dtype=float), nan=0.0)
        result['series_length'] = int(len(arr))
        result['series_12m'] = arr.tolist()

        def safe_avg(values: np.ndarray) -> float:
            return float(np.mean(values)) if values.size > 0 else 0.0

        def safe_max(values: np.ndarray) -> float:
            return float(np.max(values)) if values.size > 0 else 0.0

        arr_90 = arr[-90:] if arr.size >= 90 else arr
        arr_30 = arr[-30:] if arr.size >= 30 else arr
        arr_7 = arr[-7:] if arr.size >= 7 else arr
        arr_prev_30 = arr[-60:-30] if arr.size >= 60 else np.array([])
        arr_yoy_window = arr[-365:-335] if arr.size >= 365 else np.array([])

        result['avg_12m'] = safe_avg(arr)
        result['max_12m'] = safe_max(arr)
        result['avg_90d'] = safe_avg(arr_90)
        result['max_90d'] = safe_max(arr_90)
        result['avg_30d'] = safe_avg(arr_30)
        result['max_30d'] = safe_max(arr_30)
        result['avg_7d'] = safe_avg(arr_7)
        result['max_7d'] = safe_max(arr_7)
        result['recent_trend'] = arr_7.tolist() if arr_7.size > 0 else arr.tolist()[-7:]

        avg_30d = result['avg_30d']
        avg_7d = result['avg_7d']
        prev_30_avg = safe_avg(arr_prev_30) if arr_prev_30.size > 0 else None
        yoy_avg = safe_avg(arr_yoy_window) if arr_yoy_window.size > 0 else None

        result['growth_rate_7d_vs_30d'] = self._percent_change(avg_7d, avg_30d if avg_30d > 0 else None)
        result['mom_growth'] = self._percent_change(avg_30d, prev_30_avg)
        result['yoy_growth'] = self._percent_change(avg_30d, yoy_avg)

        std_12m = float(np.std(arr)) if arr.size > 1 else 0.0
        result['std_12m'] = std_12m
        if std_12m > 0:
            result['z_score'] = float(round((avg_7d - result['avg_12m']) / std_12m, 2))
        else:
            result['z_score'] = 0.0

        return result

    
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
        """获取关键字的历史趋势数据，并带有内存/磁盘缓存及重试退避。"""
        keyword = keyword.strip() if keyword else ''
        if not keyword:
            return self._empty_trend_result()

        cache_key = f"trends_{keyword.lower()}"
        now = datetime.utcnow()

        cache_entry = self._trends_cache.get(cache_key)
        if cache_entry and now - cache_entry['timestamp'] <= self.memory_cache_ttl:
            return cache_entry['data']

        disk_data, disk_timestamp = self._load_cache_from_disk(keyword)
        stale_disk_data = None
        if disk_data is not None:
            if disk_timestamp and now - disk_timestamp <= self.disk_cache_ttl:
                self._trends_cache[cache_key] = {'data': disk_data, 'timestamp': now}
                return disk_data
            stale_disk_data = disk_data

        if not self.trends_collector:
            return stale_disk_data if stale_disk_data is not None else self._empty_trend_result()

        data_12m = self._fetch_trends_dataframe(keyword, 'today 12-m')
        if data_12m.empty:
            data_12m = self._fetch_trends_dataframe(keyword, 'today 3-m')

        if data_12m.empty:
            if stale_disk_data is not None:
                self.logger.warning(f"使用缓存趋势数据作为 {keyword} 的回退")
                self._trends_cache[cache_key] = {'data': stale_disk_data, 'timestamp': now}
                return stale_disk_data
            self.logger.warning(f"无法获取 {keyword} 的趋势数据，使用默认值")
            return self._empty_trend_result()

        result = self._summarize_trends(keyword, data_12m)
        self._store_cache(cache_key, keyword, result)
        return result

    def calculate_new_word_score(self, historical_data: Dict) -> float:
        """计算新词得分"""
        score = 0.0

        avg_12m = float(historical_data.get('avg_12m', 0.0) or 0.0)
        avg_90d = float(historical_data.get('avg_90d', 0.0) or 0.0)
        avg_30d = float(historical_data.get('avg_30d', 0.0) or 0.0)
        avg_7d = float(historical_data.get('avg_7d', 0.0) or 0.0)

        short_term_growth = historical_data.get('growth_rate_7d_vs_30d', 0.0)
        mom_growth = historical_data.get('mom_growth', 0.0)
        yoy_growth = historical_data.get('yoy_growth', 0.0)
        z_score_value = historical_data.get('z_score', 0.0)

        # 低历史搜索量加分（最多20分）
        low_volume_score = 0.0
        if avg_12m <= self.thresholds['low_volume_12m']:
            low_volume_score += 8
        if avg_90d <= self.thresholds['low_volume_90d']:
            low_volume_score += 7
        if avg_30d <= self.thresholds['low_volume_30d']:
            low_volume_score += 5
        score += min(low_volume_score, 20.0)

        # 近期趋势加速（7天对比30天）
        score += self._score_growth_signal(
            short_term_growth,
            [(300, 20.0), (200, 16.0), (120, 12.0), (60, 8.0), (30, 4.0)],
            [(-20, 4.0), (-40, 8.0)]
        )

        # 环比（月度）增长
        score += self._score_growth_signal(
            mom_growth,
            [(200, 15.0), (120, 12.0), (80, 9.0), (40, 6.0), (20, 3.0)],
            [(-15, 3.0), (-30, 6.0)]
        )

        # 同比（去年同期）增长
        score += self._score_growth_signal(
            yoy_growth,
            [(250, 15.0), (150, 12.0), (100, 9.0), (50, 6.0), (25, 3.0)],
            [(-10, 3.0), (-25, 6.0)]
        )

        # Z 分数衡量异动强度
        score += self._score_growth_signal(
            z_score_value,
            [(3.0, 15.0), (2.5, 13.0), (2.0, 11.0), (1.5, 8.0), (1.0, 5.0), (0.5, 2.0)],
            [(-0.5, 2.0), (-1.0, 4.0)]
        )

        # 近期搜索量底线
        volume_score = 0.0
        min_recent = self.thresholds['min_recent_volume']
        if avg_7d >= min_recent * 2:
            volume_score = 15.0
        elif avg_7d >= min_recent * 1.2:
            volume_score = 12.0
        elif avg_7d >= min_recent:
            volume_score = 10.0
        elif avg_7d >= min_recent * 0.75:
            volume_score = 6.0
        elif avg_7d >= min_recent * 0.5:
            volume_score = 3.0
        score += volume_score

        score = max(0.0, min(score, 100.0))
        return round(score, 2)
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

                result = {
                    'keyword': keyword,
                    'new_word_score': score,
                    'new_word_grade': grade,
                    'is_new_word': score >= 60,
                    'confidence_level': 'high' if score >= 80 else 'medium' if score >= 60 else 'low',
                    'grade_description': self.new_word_grades[grade]['description'],
                    'avg_12m': historical_data.get('avg_12m', 0),
                    'avg_90d': historical_data.get('avg_90d', 0),
                    'avg_30d': historical_data.get('avg_30d', 0),
                    'avg_7d': historical_data.get('avg_7d', 0),
                    'recent_trend': historical_data.get('recent_trend', []),
                    'growth_rate_7d_vs_30d': historical_data.get('growth_rate_7d_vs_30d', 0.0),
                    'mom_growth': historical_data.get('mom_growth', 0.0),
                    'yoy_growth': historical_data.get('yoy_growth', 0.0),
                    'z_score': historical_data.get('z_score', 0.0),
                    'std_12m': historical_data.get('std_12m', 0.0)
                }

                results.append(result)

                if j < len(batch_keywords) - 1:
                    import time
                    time.sleep(0.2)

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
