#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新词检测器 - New Word Detector
用于识别和评估新兴关键词的潜力
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Set
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


class TrendsDataUnavailable(Exception):
    """Raised when Google Trends data cannot be retrieved for new word detection."""
    pass


class NewWordDetector(BaseAnalyzer):
    """新词检测器，用于识别具有新词特征的关键词"""
    
    def __init__(self, 
                 low_volume_threshold_12m: int = 250,
                 low_volume_threshold_90d: int = 120,
                 low_volume_threshold_30d: int = 80,
                 high_growth_threshold_7d: float = 80.0,
                 min_recent_volume: int = 10,
                 new_word_score_threshold: float = 55.0,
                 confidence_thresholds: Optional[Dict[str, float]] = None,
                 grade_thresholds: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        初始化新词检测器
        
        参数:
            low_volume_threshold_12m (int): 12个月平均搜索量阈值
            low_volume_threshold_90d (int): 90天平均搜索量阈值
            low_volume_threshold_30d (int): 30天平均搜索量阈值
            high_growth_threshold_7d (float): 7天增长率阈值(%)
            min_recent_volume (int): 最近7天最低搜索量
            new_word_score_threshold (float): 判定为新词的最低得分
            confidence_thresholds (dict): 置信度阈值设置，如 {'high': 80, 'medium': 60}
            grade_thresholds (dict): 覆盖默认等级阈值和描述
        """
        super().__init__()
        
        # 新词判断阈值
        self.thresholds = {
            'low_volume_12m': max(low_volume_threshold_12m, 0),
            'low_volume_90d': max(low_volume_threshold_90d, 0),
            'low_volume_30d': max(low_volume_threshold_30d, 0),
            'high_growth_7d': float(high_growth_threshold_7d),
            'min_recent_volume': max(min_recent_volume, 0)
        }
        self.score_threshold = max(float(new_word_score_threshold), 0.0)
        default_confidence_thresholds = {
            'high': 75.0,
            'medium': max(self.score_threshold, 55.0)
        }
        if isinstance(confidence_thresholds, dict):
            for key in ('high', 'medium'):
                value = confidence_thresholds.get(key)
                if isinstance(value, (int, float)):
                    default_confidence_thresholds[key] = float(value)
        if default_confidence_thresholds['high'] < default_confidence_thresholds['medium']:
            default_confidence_thresholds['high'] = default_confidence_thresholds['medium'] + 5.0
        self.confidence_thresholds = default_confidence_thresholds
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
            'S': {'min_score': 85, 'description': '超级新词 - 爆发式增长'},
            'A': {'min_score': 70, 'description': '强新词 - 快速增长'},
            'B': {'min_score': 60, 'description': '中新词 - 稳定增长'},
            'C': {'min_score': 50, 'description': '弱新词 - 缓慢增长'},
            'D': {'min_score': 0, 'description': '非新词 - 传统关键词'}
        }
        if isinstance(grade_thresholds, dict):
            for grade, info in grade_thresholds.items():
                current = self.new_word_grades.get(grade)
                if not current:
                    continue
                min_score = info.get('min_score') if isinstance(info, dict) else None
                description = info.get('description') if isinstance(info, dict) else None
                if isinstance(min_score, (int, float)):
                    current['min_score'] = float(min_score)
                if isinstance(description, str) and description.strip():
                    current['description'] = description.strip()

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

    def _fetch_trends_dataframe(self, keyword: str, timeframe: str, geo: str = '') -> Tuple[pd.DataFrame, Dict[str, Any]]:
        if not self.trends_collector:
            return pd.DataFrame(), {'timeframe': None, 'geo': None, 'attempts': []}

        geo_candidates = [geo or '', 'US', 'GB']
        timeframe_candidates = [timeframe, 'today 3-m', 'now 7-d', 'now 1-d']
        attempts_log: List[Dict[str, Any]] = []
        seen: Set[Tuple[str, str]] = set()
        last_exception: Optional[Exception] = None

        for geo_candidate in geo_candidates:
            for timeframe_candidate in timeframe_candidates:
                combo = (timeframe_candidate, geo_candidate)
                if combo in seen:
                    continue
                seen.add(combo)
                try:
                    df = self.trends_collector.get_trends_data([keyword], timeframe=timeframe_candidate, geo=geo_candidate)
                    if not df.empty:
                        return df, {
                            'timeframe': timeframe_candidate,
                            'geo': geo_candidate,
                            'attempts': attempts_log
                        }
                except Exception as exc:
                    last_exception = exc
                    attempts_log.append({
                        'timeframe': timeframe_candidate,
                        'geo': geo_candidate,
                        'error': str(exc)
                    })
                    self.logger.warning(
                        f"获取 {keyword} ({timeframe_candidate}, {geo_candidate or 'GLOBAL'}) 趋势数据失败: {exc}"
                    )
                time.sleep(0.6)

        if last_exception:
            self.logger.warning(
                f"多次尝试后仍无法获取 {keyword} 趋势数据: {last_exception}"
            )
        return pd.DataFrame(), {'timeframe': None, 'geo': None, 'attempts': attempts_log}

    @staticmethod
    def _percent_change(current: float, previous: Optional[float]) -> float:
        if previous is None or previous <= 0:
            return 0.0
        return float(round(((current - previous) / previous) * 100, 2))

    def _summarize_trends(self, keyword: str, data_12m: pd.DataFrame) -> Dict[str, Any]:
        result = self._empty_trend_result()
        if data_12m.empty or keyword not in data_12m.columns:
            return result

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

        direction = 'stable'
        if result['growth_rate_7d_vs_30d'] >= 50 or result['mom_growth'] >= 40:
            direction = 'surging'
        elif result['growth_rate_7d_vs_30d'] <= -25 or result['mom_growth'] <= -20:
            direction = 'cooling'
        result['trend_direction'] = direction

        return result

    @staticmethod
    def _score_growth_signal(
        value: Optional[float],
        positive_bands: List[Tuple[float, float]],
        negative_bands: Optional[List[Tuple[float, float]]] = None,
    ) -> float:
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
            raise ValueError('Keyword is empty for new word detection')

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
            if stale_disk_data is not None:
                self.logger.warning(f'使用缓存趋势数据作为 {keyword} 的回退 (缺少实时收集器)')
                self._trends_cache[cache_key] = {'data': stale_disk_data, 'timestamp': now}
                return stale_disk_data
            raise TrendsDataUnavailable(f'无法获取 {keyword} 的趋势数据：TrendsCollector 不可用')

        data_12m, fetch_meta = self._fetch_trends_dataframe(keyword, 'today 12-m')

        if data_12m.empty:
            if stale_disk_data is not None:
                self.logger.warning(f'使用缓存趋势数据作为 {keyword} 的回退 (实时数据为空)')
                self._trends_cache[cache_key] = {'data': stale_disk_data, 'timestamp': now}
                return stale_disk_data
            message = f'无法获取 {keyword} 的趋势数据：Trends 接口返回空结果'
            raise TrendsDataUnavailable(message)

        result = self._summarize_trends(keyword, data_12m)
        result['trend_fetch_timeframe'] = fetch_meta.get('timeframe')
        result['trend_fetch_geo'] = fetch_meta.get('geo')
        if stale_disk_data:
            try:
                result['avg_30d_delta'] = round(
                    float(result.get('avg_30d', 0.0)) - float(stale_disk_data.get('avg_30d', 0.0) or 0.0),
                    2
                )
                result['avg_7d_delta'] = round(
                    float(result.get('avg_7d', 0.0)) - float(stale_disk_data.get('avg_7d', 0.0) or 0.0),
                    2
                )
            except Exception:
                result['avg_30d_delta'] = 0.0
                result['avg_7d_delta'] = 0.0
        else:
            result['avg_30d_delta'] = result.get('avg_30d', 0.0)
            result['avg_7d_delta'] = result.get('avg_7d', 0.0)

        result['trend_momentum'] = self._infer_trend_momentum(result)
        self._store_cache(cache_key, keyword, result)
        return result

    def _infer_trend_momentum(self, historical: Dict[str, Any]) -> str:
        delta_30 = float(historical.get('avg_30d_delta', 0.0) or 0.0)
        delta_7 = float(historical.get('avg_7d_delta', 0.0) or 0.0)
        growth = float(historical.get('growth_rate_7d_vs_30d', 0.0) or 0.0)

        if growth >= 300 or delta_7 >= 20:
            return 'breakout'
        if growth >= 120 or (delta_7 >= 10 and delta_30 >= 5):
            return 'rising'
        if growth <= -30 or delta_30 <= -5:
            return 'cooling'
        return 'stable'

    def _derive_growth_label(self, historical: Dict[str, Any]) -> str:
        momentum = historical.get('trend_momentum')
        if momentum:
            return str(momentum)

        growth = float(historical.get('growth_rate_7d_vs_30d', 0.0) or 0.0)
        mom = float(historical.get('mom_growth', 0.0) or 0.0)
        z_score = float(historical.get('z_score', 0.0) or 0.0)

        if growth >= 400 or mom >= 250 or z_score >= 2.5:
            return 'breakout'
        if growth >= 120 or mom >= 120:
            return 'rising'
        if growth <= -25 or mom <= -15:
            return 'declining'
        return 'stable'

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
            [(150, 20.0), (120, 17.0), (80, 13.0), (50, 9.0), (30, 6.0), (15, 3.0)],
            [(-25, 4.0), (-45, 8.0)]
        )

        # 环比（月度）增长
        score += self._score_growth_signal(
            mom_growth,
            [(150, 13.0), (100, 10.0), (60, 7.0), (30, 4.0), (15, 2.5)],
            [(-12, 3.0), (-25, 6.0)]
        )

        # 同比（去年同期）增长
        score += self._score_growth_signal(
            yoy_growth,
            [(200, 13.0), (120, 10.0), (80, 7.5), (40, 4.0), (20, 2.0)],
            [(-8, 3.0), (-20, 6.0)]
        )

        # Z 分数衡量异动强度
        score += self._score_growth_signal(
            z_score_value,
            [(2.5, 14.0), (2.0, 11.0), (1.5, 8.0), (1.0, 6.0), (0.7, 4.0), (0.4, 2.0)],
            [(-0.4, 2.0), (-0.8, 4.0)]
        )

        # 近期搜索量底线
        volume_score = 0.0
        min_recent = self.thresholds['min_recent_volume']
        if min_recent <= 0:
            volume_score = 12.0 if avg_7d > 0 else 0.0
        elif avg_7d >= min_recent * 2.5:
            volume_score = 15.0
        elif avg_7d >= min_recent * 1.6:
            volume_score = 12.0
        elif avg_7d >= min_recent * 1.1:
            volume_score = 10.0
        elif avg_7d >= min_recent * 0.8:
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
        result_columns = [
            'keyword', 'new_word_score', 'new_word_grade', 'is_new_word',
            'confidence_level', 'grade_description', 'avg_12m', 'avg_90d',
            'avg_30d', 'avg_7d', 'recent_trend', 'growth_rate_7d_vs_30d',
            'growth_rate_7d', 'mom_growth', 'yoy_growth', 'z_score', 'std_12m',
            'historical_pattern', 'explosion_index', 'detection_reasons',
            'growth_label', 'trend_fetch_timeframe', 'trend_fetch_geo',
            'avg_30d_delta', 'avg_7d_delta', 'trend_momentum'
        ]

        if data.empty:
            return pd.DataFrame(columns=result_columns)

        candidate_columns = []
        for col in [keyword_col, 'query', 'keyword', 'keywords', '关键词', 'term']:
            if col and col not in candidate_columns:
                candidate_columns.append(col)

        for candidate in candidate_columns:
            if candidate in data.columns:
                keyword_col = candidate
                break
        else:
            raise ValueError(f"无法在数据中找到关键词列，期望列名之一: {candidate_columns}")

        working_data = data.copy()
        keywords_series = working_data[keyword_col].fillna('').astype(str)

        results = []
        batch_size = 3

        for i in range(0, len(keywords_series), batch_size):
            batch_keywords = keywords_series.iloc[i:i + batch_size]

            for j, (idx, raw_keyword) in enumerate(batch_keywords.items()):
                keyword = raw_keyword.strip()

                if not keyword:
                    results.append({
                        'keyword': keyword,
                        'new_word_score': 0.0,
                        'new_word_grade': 'D',
                        'is_new_word': False,
                        'confidence_level': 'low',
                        'grade_description': self.new_word_grades['D']['description'],
                        'avg_12m': 0.0,
                        'avg_90d': 0.0,
                        'avg_30d': 0.0,
                        'avg_7d': 0.0,
                        'recent_trend': [],
                        'growth_rate_7d_vs_30d': 0.0,
                        'growth_rate_7d': 0.0,
                        'mom_growth': 0.0,
                        'yoy_growth': 0.0,
                        'z_score': 0.0,
                        'std_12m': 0.0,
                        'historical_pattern': 'unknown',
                        'explosion_index': 1.0,
                        'detection_reasons': 'empty_keyword',
                        'growth_label': 'unknown',
                        'trend_fetch_timeframe': None,
                        'trend_fetch_geo': None,
                        'avg_30d_delta': 0.0,
                        'avg_7d_delta': 0.0,
                        'trend_momentum': 'unknown'
                    })
                    continue

                detection_reasons = []
                try:
                    historical_data = self.get_historical_data(keyword)
                except Exception as fetch_error:
                    self.logger.warning(f"获取 {keyword} 趋势数据失败: {fetch_error}")
                    historical_data = self._empty_trend_result()
                    detection_reasons.append(str(fetch_error))

                historical_data = historical_data or {}
                score = self.calculate_new_word_score(historical_data)
                grade = self.get_new_word_grade(score)

                growth_signal = float(historical_data.get('growth_rate_7d_vs_30d', 0.0) or 0.0)
                explosion_index = round(max(score / 10.0, 1.0), 2)
                historical_pattern = str(historical_data.get('trend_direction', 'unknown') or 'unknown')
                growth_label = self._derive_growth_label(historical_data)

                if score >= self.score_threshold:
                    detection_reasons.append('rapid_growth_signals')

                result = {
                    'keyword': keyword,
                    'new_word_score': score,
                    'new_word_grade': grade,
                    'is_new_word': score >= self.score_threshold,
                    'confidence_level': 'high' if score >= self.confidence_thresholds['high'] else 'medium' if score >= self.confidence_thresholds['medium'] else 'low',
                    'grade_description': self.new_word_grades[grade]['description'],
                    'avg_12m': historical_data.get('avg_12m', 0.0),
                    'avg_90d': historical_data.get('avg_90d', 0.0),
                    'avg_30d': historical_data.get('avg_30d', 0.0),
                    'avg_7d': historical_data.get('avg_7d', 0.0),
                    'recent_trend': historical_data.get('recent_trend', []),
                    'growth_rate_7d_vs_30d': growth_signal,
                    'growth_rate_7d': growth_signal,
                    'mom_growth': historical_data.get('mom_growth', 0.0),
                    'yoy_growth': historical_data.get('yoy_growth', 0.0),
                    'z_score': historical_data.get('z_score', 0.0),
                    'std_12m': historical_data.get('std_12m', 0.0),
                    'historical_pattern': historical_pattern,
                    'explosion_index': explosion_index,
                    'detection_reasons': '; '.join(filter(None, detection_reasons)),
                    'growth_label': growth_label,
                    'trend_fetch_timeframe': historical_data.get('trend_fetch_timeframe'),
                    'trend_fetch_geo': historical_data.get('trend_fetch_geo'),
                    'avg_30d_delta': historical_data.get('avg_30d_delta', 0.0),
                    'avg_7d_delta': historical_data.get('avg_7d_delta', 0.0),
                    'trend_momentum': historical_data.get('trend_momentum', 'unknown')
                }

                results.append(result)

                if j < len(batch_keywords) - 1:
                    time.sleep(0.2)

            if i + batch_size < len(keywords_series):
                time.sleep(0.3)

        new_word_df = pd.DataFrame(results, columns=result_columns)

        if new_word_df.empty:
            return pd.DataFrame(columns=result_columns)

        data_reset = working_data.reset_index(drop=True)
        new_word_df_reset = new_word_df.reset_index(drop=True)
        merged_data = pd.concat([data_reset, new_word_df_reset.drop(columns=['keyword'], errors='ignore')], axis=1)
        return merged_data

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
