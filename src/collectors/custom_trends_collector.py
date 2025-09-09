
"""
自定义Google Trends数据采集器
替代pytrends库，提供更灵活的控制和更新能力
"""

import requests
import json
import time
import random
from typing import List, Dict, Optional, Callable, TypeVar, Any, Union
import pandas as pd
import logging
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

from .google_trends_session import GoogleTrendsSession

# 类型变量定义
T = TypeVar('T')
DataFrame = pd.DataFrame
JsonDict = Dict[str, Any]

class TrendsAPIClient:
    """Google Trends API客户端基类"""
    
    # Google Trends API endpoints
    GENERAL_URL = 'https://trends.google.com/trends/api/explore'
    INTEREST_OVER_TIME_URL = 'https://trends.google.com/trends/api/widgetdata/multiline'
    INTEREST_BY_REGION_URL = 'https://trends.google.com/trends/api/widgetdata/comparedgeo'
    RELATED_TOPICS_URL = 'https://trends.google.com/trends/api/widgetdata/relatedsearches'
    TRENDING_SEARCHES_URL = 'https://trends.google.com/trends/hottrends/visualize/internal/data'
    TOP_CHARTS_URL = 'https://trends.google.com/trends/api/topcharts'
    SUGGESTIONS_URL = 'https://trends.google.com/trends/api/autocomplete'
    CATEGORIES_URL = 'https://trends.google.com/trends/api/explore/pickers/category'
    REALTIME_TRENDING_URL = 'https://trends.google.com/trends/api/realtimetrends'
    TODAY_SEARCHES_URL = 'https://trends.google.com/trends/api/dailytrends'

    # 使用公共session管理，不再需要DEFAULT_HEADERS
    pass
    
    def __init__(self, hl: str = 'en-US', tz: int = 360, 
                 timeout: tuple[float, float] = (3, 7), proxies: Optional[Dict[str, str]] = None, 
                 retries: int = 2, backoff_factor: float = 0.3):
        """初始化API客户端
        
        Args:
            hl: 语言设置 (默认: 'en-US')
            tz: 时区偏移 (默认: 360)
            timeout: 请求超时设置，格式为 (连接超时秒数, 读取超时秒数)
            proxies: 代理设置
            retries: 请求失败时的重试次数
            backoff_factor: 重试间隔的退避因子
        """
        self.hl = hl
        self.tz = tz
        self.timeout = timeout  # (connect_timeout, read_timeout)
        self.proxies = proxies
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.initialized = False
        
        # 会话管理 - 使用全局session避免重复初始化
        from .google_trends_session import get_global_session
        self.trends_session = get_global_session()
        self.session = self.trends_session.get_session()
        
        # 简单的内存缓存
        self._cache: Dict[str, Any] = {}
    
    # _init_session 方法已移至 GoogleTrendsSession 类中统一管理
    
    def _get_data(self, url: str, method: str = 'get', trim_chars: int = 0, 
                  use_cache: bool = True, **kwargs) -> Union[dict[Any, Any], None, Any]:
        """发送请求获取数据"""
        # 生成缓存键
        cache_key = None
        if use_cache:
            cache_data = {
                'url': url,
                'method': method,
                'kwargs': kwargs
            }
            cache_key = hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
            if cache_key in self._cache:
                logger.debug(f"使用缓存数据: {url}")
                return self._cache[cache_key]
        
        # 直接发送请求，无锁
        s = self.session
        s.headers.update({'accept-language': self.hl})
        
        if self.proxies:
            s.proxies.update(self.proxies)
        
        # 在每个请求前添加固定延迟，避免并发请求
        # 增强延迟机制：基础延迟 + 随机延迟避免请求冲突
        base_delay = 2.0  # 基础延迟增加到2秒
        random_delay = random.uniform(0.5, 1.5)  # 随机延迟0.5-1.5秒
        total_delay = base_delay + random_delay
        time.sleep(total_delay)
        
        for attempt in range(self.retries + 1):
            try:
                # 添加随机延迟避免429错误
                if attempt > 0:
                    delay = random.uniform(5, 10) + (attempt * 3)
                    time.sleep(delay)
                
                # 使用GoogleTrendsSession的make_request方法，支持代理
                response = self.trends_session.make_request(method.upper(), url, timeout=self.timeout, **kwargs)
                
                # 特殊处理429错误 - 增强等待时间
                if response.status_code == 429:
                    if attempt < self.retries:
                        # 增加更长的等待时间避免频繁触发429
                        base_wait = 15 + (attempt * 20)  # 基础等待时间增加
                        random_wait = random.uniform(10, 25)  # 随机等待时间增加
                        wait_time = base_wait + random_wait
                        logger.warning(f"遇到429错误，等待{wait_time:.1f}秒后重试...")
                        logger.warning(f"请求 url 地址: {url}")
                        logger.warning(f"这是第{attempt + 1}次重试，将使用更长的等待时间")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("多次遇到429错误，请求失败")
                        logger.error("建议：1) 减少并发请求 2) 增加请求间隔 3) 检查代理设置")
                        return {}
                
                response.raise_for_status()
                
                # 处理响应数据
                content = response.text[trim_chars:] if trim_chars > 0 else response.text
                
                # 尝试解析JSON
                try:
                    result = json.loads(content)
                    # 缓存结果
                    if cache_key:
                        self._cache[cache_key] = result
                    return result
                except json.JSONDecodeError:
                    logger.warning(f"无法解析JSON响应: {content[:100]}...")
                    return {}
                    
            except requests.exceptions.RequestException as e:
                if attempt < self.retries:
                    # 对于连接中断，增加更长的等待时间
                    if "Connection aborted" in str(e) or "RemoteDisconnected" in str(e):
                        wait_time = (self.backoff_factor * (2 ** attempt) + random.uniform(3, 8)) * 2
                        logger.warning(f"连接中断，等待{wait_time:.1f}秒后重试: {e}")
                    else:
                        wait_time = self.backoff_factor * (2 ** attempt) + random.uniform(1, 3)
                        logger.warning(f"请求失败，等待{wait_time:.1f}秒后重试: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"请求最终失败: {e}")
                    return {}
    
    def clear_cache(self) -> None:
        """清除请求缓存"""
        self._cache.clear()
        logger.info("请求缓存已清除")
    
    def reset_session(self) -> None:
        """重置会话"""
        try:
            from .google_trends_session import reset_global_session
            reset_global_session()
            self.trends_session = get_global_session()
            self.session = self.trends_session.get_session()
            logger.info("会话已重置")
        except Exception as e:
            logger.error(f"重置会话失败: {e}")
    
    def __enter__(self) -> 'TrendsAPIClient':
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口"""
        try:
            self.session.close()
        except:
            pass
    
    def __del__(self) -> None:
        """析构函数"""
        try:
            self.session.close()
        except:
            pass


def error_handler(default_return: Any = None) -> Callable:
    """错误处理装饰器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{func.__name__} 失败: {e}")
                return default_return() if callable(default_return) else default_return
        return wrapper
    return decorator


class CustomTrendsCollector(TrendsAPIClient):
    """自定义Google Trends数据采集器"""
    
    def __init__(self, hl: str = 'en-US', tz: int = 360, geo: str = '', 
                 timeout: tuple = (5, 20), proxies: Optional[Dict[str, str]] = None, 
                 retries: int = 1, backoff_factor: float = 0.5):
        """初始化采集器"""
        super().__init__(hl, tz, timeout, proxies, retries, backoff_factor)
        
        # 请求参数
        self.kw_list: List[str] = []
        self.cat: int = 0
        self.timeframe: str = 'today 12-m'
        self.geo: str = geo
        self.gprop: str = ''
    
    def build_payload(self, kw_list: List[str], cat: int = 0, timeframe: str = 'today 12-m', 
                     geo: str = '', gprop: str = '') -> JsonDict:
        """构建请求载荷"""
        self.kw_list = kw_list
        self.cat = cat
        self.timeframe = timeframe
        self.geo = geo
        self.gprop = gprop
        
        # 标准化时间格式
        normalized_timeframe = self._normalize_timeframe(timeframe)
        
        # 构建比较数据结构
        comparisonItem = [{'keyword': kw, 'geo': geo, 'time': normalized_timeframe} for kw in kw_list]
        
        return {
            'comparisonItem': comparisonItem,
            'category': cat,
            'property': gprop
        }
    
    def _normalize_timeframe(self, timeframe: str) -> str:
        """标准化时间格式为Google Trends API接受的格式"""
        # 移除空格并转换为小写
        timeframe = timeframe.strip().lower()
        
        # 时间格式映射表
        timeframe_mapping = {
            '1d': 'now 1-d',
            '7d': 'now 7-d', 
            '30d': 'today 1-m',
            '90d': 'today 3-m',
            '12m': 'today 12-m',
            '5y': 'today 5-y',
            # 保持原有格式
            'now 1-d': 'now 1-d',
            'now 7-d': 'now 7-d',
            'today 1-m': 'today 1-m',
            'today 3-m': 'today 3-m', 
            'today 12-m': 'today 12-m',
            'today 5-y': 'today 5-y',
            'all': 'all'
        }
        
        # 如果在映射表中找到，使用映射值
        if timeframe in timeframe_mapping:
            normalized = timeframe_mapping[timeframe]
            logger.debug(f"时间格式标准化: {timeframe} -> {normalized}")
            return normalized
        
        # 如果已经是标准格式，直接返回
        if timeframe.startswith(('now ', 'today ')) or timeframe == 'all':
            return timeframe
        
        # 默认返回原格式，但记录警告
        logger.warning(f"未识别的时间格式: {timeframe}，使用原格式")
        return timeframe
    
    def _get_token_response(self) -> JsonDict:
        """获取token响应"""
        if not self.kw_list:
            raise ValueError("请先设置关键词列表")
        
        payload = self.build_payload(self.kw_list, self.cat, self.timeframe, self.geo, self.gprop)
        
        token_payload = {
            'hl': self.hl,
            'tz': self.tz,
            'req': json.dumps(payload)
        }
        
        return self._get_data(
            self.GENERAL_URL,
            method='get',
            params=token_payload,
            trim_chars=4
        )
    
    def _find_widget(self, token_response: JsonDict, widget_id: str) -> Optional[JsonDict]:
        """查找特定ID的widget"""
        if not token_response or 'widgets' not in token_response:
            return None
            
        for widget in token_response['widgets']:
            if widget.get('id') == widget_id:
                return widget
                
        return None
    
    def _get_widget_data(self, widget: JsonDict, url: str) -> JsonDict:
        """获取widget数据"""
        data_payload = {
            'hl': self.hl,
            'tz': self.tz,
            'req': json.dumps(widget['request']),
            'token': widget['token']
        }
        
        return self._get_data(
            url,
            method='get',
            params=data_payload,
            trim_chars=5
        )
    
    def _with_temp_settings(self, func: Callable[[], T], **kwargs) -> T:
        """使用临时设置执行函数"""
        # 保存原始设置
        original_settings = {
            'kw_list': self.kw_list,
            'timeframe': self.timeframe,
            'geo': self.geo,
            'cat': self.cat,
            'gprop': self.gprop
        }
        
        # 应用临时设置
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        try:
            # 执行函数
            return func()
        finally:
            # 恢复原始设置
            for key, value in original_settings.items():
                setattr(self, key, value)
    
    @error_handler(pd.DataFrame)
    def interest_over_time(self) -> DataFrame:
        """获取关键词随时间变化的兴趣度"""
        token_response = self._get_token_response()
        
        # 找到时间序列widget
        widget = self._find_widget(token_response, 'TIMESERIES')
        
        if not widget:
            logger.error("未找到时间序列widget")
            return pd.DataFrame()
        
        # 获取实际数据
        data_response = self._get_widget_data(widget, self.INTEREST_OVER_TIME_URL)
        
        if not data_response or 'default' not in data_response:
            logger.error("无法获取时间序列数据")
            return pd.DataFrame()
        
        # 解析数据
        timeline_data = data_response['default']['timelineData']
        
        # 构建DataFrame
        df_data = []
        for point in timeline_data:
            row = {'date': point['formattedTime']}
            for i, value in enumerate(point['value']):
                if i < len(self.kw_list):
                    row[self.kw_list[i]] = value
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        
        # 转换日期格式
        if not df.empty:
            try:
                df['date'] = pd.to_datetime(df['date'], format='mixed', errors='coerce')
                df.set_index('date', inplace=True)
            except:
                logger.warning("日期格式转换失败")
        
        return df
    
    @error_handler(pd.DataFrame)
    def interest_by_region(self, resolution: str = 'COUNTRY', inc_low_vol: bool = True, 
                          inc_geo_code: bool = False) -> DataFrame:
        """获取按地区分布的兴趣度"""
        token_response = self._get_token_response()
        
        # 找到地区widget
        widget = self._find_widget(token_response, 'GEO_MAP')
        
        if not widget:
            logger.error("未找到地区widget")
            return pd.DataFrame()
        
        # 修改请求参数
        widget['request']['resolution'] = resolution
        widget['request']['includeLowSearchVolumeGeos'] = inc_low_vol
        
        # 获取实际数据
        data_response = self._get_widget_data(widget, self.INTEREST_BY_REGION_URL)
        
        if not data_response or 'default' not in data_response:
            logger.error("无法获取地区数据")
            return pd.DataFrame()
        
        # 解析数据
        geo_data = data_response['default']['geoMapData']
        
        df_data = []
        for item in geo_data:
            row = {
                'geoName': item['geoName'],
                'geoCode': item['geoCode'] if inc_geo_code else None
            }
            for i, value in enumerate(item['value']):
                if i < len(self.kw_list):
                    row[self.kw_list[i]] = value
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        if not inc_geo_code and 'geoCode' in df.columns:
            df.drop('geoCode', axis=1, inplace=True)
        
        return df
    
    def _process_ranked_list(self, ranked_list: JsonDict, is_topic: bool = True) -> DataFrame:
        """处理排名列表数据"""
        items = []
        for item in ranked_list.get('rankedKeyword', []):
            if is_topic:
                topic_data = item.get('topic', {})
                items.append({
                    'topic_title': topic_data.get('title', ''),
                    'topic_type': topic_data.get('type', ''),
                    'value': item.get('value', 0)
                })
            else:
                items.append({
                    'query': item.get('query', ''),
                    'value': item.get('value', 0)
                })
        
        return pd.DataFrame(items)
    
    @error_handler(dict)
    def related_topics(self) -> Dict[str, Dict[str, DataFrame]]:
        """获取相关主题"""
        token_response = self._get_token_response()
        results: Dict[str, Dict[str, DataFrame]] = {}
        
        # 查找相关主题widgets
        for widget in token_response.get('widgets', []):
            if widget.get('id') == 'RELATED_TOPICS':
                data_response = self._get_widget_data(widget, self.RELATED_TOPICS_URL)
                
                if data_response and 'default' in data_response:
                    # 解析相关主题数据
                    related_data = data_response['default']
                    
                    # 处理top和rising数据
                    for kw in self.kw_list:
                        if kw not in results:
                            results[kw] = {}
                        
                        if 'rankedList' in related_data:
                            for ranked_list in related_data['rankedList']:
                                list_type = 'top' if ranked_list.get('rankedKeyword', [{}])[0].get('topic', {}).get('type') == 'ENTITY' else 'rising'
                                results[kw][list_type] = self._process_ranked_list(ranked_list, is_topic=True)
        
        return results
    
    @error_handler(dict)
    def related_queries(self) -> Dict[str, Dict[str, DataFrame]]:
        """获取相关查询"""
        token_response = self._get_token_response()
        results: Dict[str, Dict[str, DataFrame]] = {}
        
        # 查找相关查询widgets
        for widget in token_response.get('widgets', []):
            if widget.get('id') == 'RELATED_QUERIES':
                data_response = self._get_widget_data(widget, self.RELATED_TOPICS_URL)
                
                if data_response and 'default' in data_response:
                    related_data = data_response['default']
                    
                    for kw in self.kw_list:
                        if kw not in results:
                            results[kw] = {}
                        
                        if 'rankedList' in related_data:
                            for ranked_list in related_data['rankedList']:
                                list_type = 'top' if 'top' in str(ranked_list) else 'rising'
                                results[kw][list_type] = self._process_ranked_list(ranked_list, is_topic=False)
        
        return results

    @error_handler(dict)
    def batch_related_queries(
        self,
        keywords: List[str],
        timeframe: str = 'today 3-m',
        geo: str = '',
        cat: int = 0,
        gprop: str = '',
        delay_per_batch: int = 5
    ) -> Dict[str, Dict[str, DataFrame]]:
        """为大量关键词自动分批获取其'相关查询'"""
        final_results: Dict[str, Dict[str, DataFrame]] = {}
        batch_size = 5  # Google Trends API 限制

        logger.info(f"开始为 {len(keywords)} 个关键词批量获取相关查询...")

        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            logger.info(f"正在处理批次 {i//batch_size + 1}，关键词: {batch}")

            # 设置当前批次的关键词
            self.build_payload(batch, cat=cat, timeframe=timeframe, geo=geo, gprop=gprop)
            
            # 获取相关查询数据
            batch_result = self.related_queries()

            if batch_result:
                final_results.update(batch_result)
            else:
                logger.warning(f"批次 {i//batch_size + 1} 未返回任何数据。")

            # 在批次之间添加延迟
            if i + batch_size < len(keywords):
                logger.info(f"批次处理完成，暂停 {delay_per_batch} 秒...")
                time.sleep(delay_per_batch)
        
        logger.info(f"所有批次处理完成，共获取了 {len(final_results)} 个关键词的相关查询。")
        return final_results
    
    @error_handler(pd.DataFrame)
    def trending_searches(self, pn: str = 'united_states') -> DataFrame:
        """获取热门搜索"""
        params = {
            'hl': self.hl,
            'tz': self.tz,
            'geo': pn,
            'ns': 15
        }
        
        response = self._get_data(
            self.TRENDING_SEARCHES_URL,
            method='get',
            params=params
        )
        
        if not response:
            return pd.DataFrame()
        
        # 解析热门搜索数据
        trending_data = []
        if isinstance(response, dict) and 'default' in response:
            for item in response['default'].get('trendingSearchesDays', []):
                for search in item.get('trendingSearches', []):
                    trending_data.append({
                        'title': search.get('title', {}).get('query', ''),
                        'traffic': search.get('formattedTraffic', ''),
                        'date': item.get('date', '')
                    })
        
        return pd.DataFrame(trending_data)
    
    @error_handler(list)
    def suggestions(self, keyword: str) -> List[Dict[str, str]]:
        """获取关键词建议"""
        params = {
            'hl': self.hl,
            'tz': self.tz,
            'q': keyword
        }
        
        response = self._get_data(
            self.SUGGESTIONS_URL,
            method='get',
            params=params,
            trim_chars=5
        )
        
        if not response or 'default' not in response:
            return []
        
        suggestions = []
        for item in response['default'].get('topics', []):
            suggestions.append({
                'title': item.get('title', ''),
                'type': item.get('type', ''),
                'mid': item.get('mid', '')
            })
        
        return suggestions
    
    def get_historical_interest(self, keyword: str, start_date: Optional[str] = None, 
                               end_date: Optional[str] = None) -> DataFrame:
        """获取历史兴趣数据"""
        timeframe = f"{start_date} {end_date}" if start_date and end_date else self.timeframe
        
        # 使用临时设置执行
        return self._with_temp_settings(
            self.interest_over_time,
            kw_list=[keyword],
            timeframe=timeframe
        )
    
    @error_handler(dict)
    def get_search_volume_estimate(self, keyword: str, timeframe: str = 'today 12-m') -> JsonDict:
        """获取搜索量估算（基于趋势数据）"""
        df = self._with_temp_settings(
            self.interest_over_time,
            kw_list=[keyword],
            timeframe=timeframe
        )
        
        if df.empty:
            return {'keyword': keyword, 'estimate': 'No data', 'trend': 'Unknown'}
        
        # 计算基本统计
        values = df[keyword].dropna()
        if values.empty:
            return {'keyword': keyword, 'estimate': 'No data', 'trend': 'Unknown'}
        
        avg_interest = values.mean()
        max_interest = values.max()
        min_interest = values.min()
        
        # 计算趋势方向
        if len(values) >= 2:
            recent_avg = values.tail(4).mean()  # 最近4个数据点
            earlier_avg = values.head(4).mean()  # 最早4个数据点
            
            if recent_avg > earlier_avg * 1.1:
                trend = 'Rising'
            elif recent_avg < earlier_avg * 0.9:
                trend = 'Declining'
            else:
                trend = 'Stable'
        else:
            trend = 'Unknown'
        
        # 估算搜索量级别
        if avg_interest >= 80:
            volume_estimate = 'Very High'
        elif avg_interest >= 60:
            volume_estimate = 'High'
        elif avg_interest >= 40:
            volume_estimate = 'Medium'
        elif avg_interest >= 20:
            volume_estimate = 'Low'
        else:
            volume_estimate = 'Very Low'
        
        return {
            'keyword': keyword,
            'estimate': volume_estimate,
            'trend': trend,
            'avg_interest': round(avg_interest, 2),
            'max_interest': max_interest,
            'min_interest': min_interest,
            'data_points': len(values)
        }
    
    @error_handler(pd.DataFrame)
    def get_trends_data(self, keywords, timeframe='today 12-m', geo=''):
        """获取关键词的趋势数据 (兼容方法)"""
        # 构建payload并获取数据
        self.build_payload(keywords, timeframe=timeframe, geo=geo)
        return self.interest_over_time()
    
    @error_handler(dict)
    def get_keyword_trends(self, keyword, timeframe='today 12-m', geo=''):
        """获取关键词趋势数据 - 为root_word_trends_analyzer提供的接口

        Args:
            keyword: 关键词（字符串或列表）
            timeframe: 时间范围
            geo: 地理位置

        Returns:
            包含趋势数据和相关查询的字典
        """
        try:
            # 确保keyword是列表格式
            if isinstance(keyword, str):
                keywords = [keyword]
            else:
                keywords = keyword

            # 构建payload
            self.build_payload(keywords, timeframe=timeframe, geo=geo)

            # 获取趋势数据
            interest_data = self.interest_over_time()

            # 获取相关查询
            related_queries = self.related_queries()

            # 构建返回数据
            result = {
                'interest_over_time': interest_data,
                'related_queries': related_queries,
                'keyword': keywords[0] if len(keywords) == 1 else keywords,
                'timeframe': timeframe,
                'geo': geo
            }

            return result

        except Exception as e:
            logger.error(f"获取关键词趋势失败: {e}")
            return {}

# 全局session实例
_global_session = None

def get_global_session() -> GoogleTrendsSession:
    """获取全局session实例"""
    global _global_session
    if _global_session is None:
        _global_session = GoogleTrendsSession()
    return _global_session

def reset_global_session() -> None:
    """重置全局session"""
    global _global_session
    if _global_session:
        _global_session.reset_session()
    else:
        _global_session = GoogleTrendsSession()