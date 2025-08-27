"""
自定义Google Trends数据采集器
替代pytrends库，提供更灵活的控制和更新能力
"""

import requests
import json
import time
import random
from urllib.parse import quote, urlencode
from typing import List, Dict, Optional, Union
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CustomTrendsCollector:
    """自定义Google Trends数据采集器"""
    
    def __init__(self, hl='en-US', tz=360, geo='', timeout=(2, 5), proxies=None, retries=0, backoff_factor=0):
        """
        初始化采集器
        
        Args:
            hl: 语言设置 (默认: 'en-US')
            tz: 时区偏移 (默认: 360)
            geo: 地理位置 (默认: '')
            timeout: 请求超时设置
            proxies: 代理设置
            retries: 重试次数
            backoff_factor: 退避因子
        """
        self.hl = hl
        self.tz = tz
        self.geo = geo
        self.timeout = timeout
        self.proxies = proxies
        self.retries = retries
        self.backoff_factor = backoff_factor
        
        # Google Trends API endpoints
        self.GENERAL_URL = 'https://trends.google.com/trends/api/explore'
        self.INTEREST_OVER_TIME_URL = 'https://trends.google.com/trends/api/widgetdata/multiline'
        self.INTEREST_BY_REGION_URL = 'https://trends.google.com/trends/api/widgetdata/comparedgeo'
        self.RELATED_TOPICS_URL = 'https://trends.google.com/trends/api/widgetdata/relatedsearches'
        self.TRENDING_SEARCHES_URL = 'https://trends.google.com/trends/hottrends/visualize/internal/data'
        self.TOP_CHARTS_URL = 'https://trends.google.com/trends/api/topcharts'
        self.SUGGESTIONS_URL = 'https://trends.google.com/trends/api/autocomplete'
        self.CATEGORIES_URL = 'https://trends.google.com/trends/api/explore/pickers/category'
        self.REALTIME_TRENDING_URL = 'https://trends.google.com/trends/api/realtimetrends'
        self.TODAY_SEARCHES_URL = 'https://trends.google.com/trends/api/dailytrends'
        
        # 会话管理
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://trends.google.com/',
            'Origin': 'https://trends.google.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # 初始化会话
        self._init_session()
        
        # 请求参数
        self.kw_list = []
        self.cat = 0
        self.timeframe = 'today 12-m'
        self.geo = geo
        self.gprop = ''
    
    def _init_session(self):
        """初始化会话，获取必要的cookies"""
        try:
            # 首先访问主页获取cookies
            response = self.session.get('https://trends.google.com/', timeout=self.timeout)
            if response.status_code == 200:
                logger.info("会话初始化成功")
            else:
                logger.warning(f"会话初始化警告: {response.status_code}")
        except Exception as e:
            logger.warning(f"会话初始化失败: {e}")
        
    def build_payload(self, kw_list: List[str], cat: int = 0, timeframe: str = 'today 12-m', 
                     geo: str = '', gprop: str = '') -> Dict:
        """构建请求载荷"""
        self.kw_list = kw_list
        self.cat = cat
        self.timeframe = timeframe
        self.geo = geo
        self.gprop = gprop
        
        # 构建比较数据结构
        comparisonItem = []
        for kw in kw_list:
            comparisonItem.append({
                'keyword': kw,
                'geo': geo,
                'time': timeframe
            })
        
        payload = {
            'comparisonItem': comparisonItem,
            'category': cat,
            'property': gprop
        }
        
        return payload
    
    def _get_data(self, url: str, method: str = 'get', trim_chars: int = 0, **kwargs) -> Dict:
        """发送请求获取数据"""
        s = self.session
        s.headers.update({'accept-language': self.hl})
        
        if self.proxies:
            s.proxies.update(self.proxies)
        
        for attempt in range(self.retries + 1):
            try:
                # 添加随机延迟避免429错误
                if attempt > 0:
                    delay = random.uniform(2, 5) + (attempt * 2)
                    time.sleep(delay)
                
                if method.lower() == 'get':
                    response = s.get(url, timeout=self.timeout, **kwargs)
                else:
                    response = s.post(url, timeout=self.timeout, **kwargs)
                
                # 特殊处理429错误
                if response.status_code == 429:
                    if attempt < self.retries:
                        wait_time = 10 + (attempt * 5) + random.uniform(0, 5)
                        logger.warning(f"遇到429错误，等待{wait_time:.1f}秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("多次遇到429错误，请求失败")
                        return {}
                
                response.raise_for_status()
                
                # 处理响应数据
                content = response.text
                if trim_chars > 0:
                    content = content[trim_chars:]
                
                # 尝试解析JSON
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"无法解析JSON响应: {content[:100]}...")
                    return {}
                    
            except requests.exceptions.RequestException as e:
                if attempt < self.retries:
                    wait_time = self.backoff_factor * (2 ** attempt) + random.uniform(1, 3)
                    logger.warning(f"请求失败，等待{wait_time:.1f}秒后重试: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"请求最终失败: {e}")
                    return {}
    
    def interest_over_time(self) -> pd.DataFrame:
        """获取关键词随时间变化的兴趣度"""
        if not self.kw_list:
            raise ValueError("请先设置关键词列表")
        
        # 构建请求参数
        payload = self.build_payload(self.kw_list, self.cat, self.timeframe, self.geo, self.gprop)
        
        # 获取token
        token_payload = {
            'hl': self.hl,
            'tz': self.tz,
            'req': json.dumps(payload)
        }
        
        try:
            # 第一步：获取token
            token_response = self._get_data(
                self.GENERAL_URL,
                method='get',
                params=token_payload,
                trim_chars=4
            )
            
            if not token_response or 'widgets' not in token_response:
                logger.error("无法获取有效的token响应")
                return pd.DataFrame()
            
            # 找到时间序列widget
            widget = None
            for w in token_response['widgets']:
                if w.get('id') == 'TIMESERIES':
                    widget = w
                    break
            
            if not widget:
                logger.error("未找到时间序列widget")
                return pd.DataFrame()
            
            # 第二步：获取实际数据
            data_payload = {
                'hl': self.hl,
                'tz': self.tz,
                'req': json.dumps(widget['request']),
                'token': widget['token']
            }
            
            data_response = self._get_data(
                self.INTEREST_OVER_TIME_URL,
                method='get',
                params=data_payload,
                trim_chars=5
            )
            
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
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                except:
                    logger.warning("日期格式转换失败")
            
            return df
            
        except Exception as e:
            logger.error(f"获取时间序列数据失败: {e}")
            return pd.DataFrame()
    
    def interest_by_region(self, resolution: str = 'COUNTRY', inc_low_vol: bool = True, 
                          inc_geo_code: bool = False) -> pd.DataFrame:
        """获取按地区分布的兴趣度"""
        if not self.kw_list:
            raise ValueError("请先设置关键词列表")
        
        payload = self.build_payload(self.kw_list, self.cat, self.timeframe, self.geo, self.gprop)
        
        # 获取token
        token_payload = {
            'hl': self.hl,
            'tz': self.tz,
            'req': json.dumps(payload)
        }
        
        try:
            token_response = self._get_data(
                self.GENERAL_URL,
                method='get',
                params=token_payload,
                trim_chars=4
            )
            
            if not token_response or 'widgets' not in token_response:
                return pd.DataFrame()
            
            # 找到地区widget
            widget = None
            for w in token_response['widgets']:
                if w.get('id') == 'GEO_MAP':
                    widget = w
                    break
            
            if not widget:
                return pd.DataFrame()
            
            # 修改请求参数
            widget['request']['resolution'] = resolution
            widget['request']['includeLowSearchVolumeGeos'] = inc_low_vol
            
            data_payload = {
                'hl': self.hl,
                'tz': self.tz,
                'req': json.dumps(widget['request']),
                'token': widget['token']
            }
            
            data_response = self._get_data(
                self.INTEREST_BY_REGION_URL,
                method='get',
                params=data_payload,
                trim_chars=5
            )
            
            if not data_response or 'default' not in data_response:
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
            
        except Exception as e:
            logger.error(f"获取地区数据失败: {e}")
            return pd.DataFrame()
    
    def related_topics(self) -> Dict:
        """获取相关主题"""
        if not self.kw_list:
            raise ValueError("请先设置关键词列表")
        
        payload = self.build_payload(self.kw_list, self.cat, self.timeframe, self.geo, self.gprop)
        
        token_payload = {
            'hl': self.hl,
            'tz': self.tz,
            'req': json.dumps(payload)
        }
        
        try:
            token_response = self._get_data(
                self.GENERAL_URL,
                method='get',
                params=token_payload,
                trim_chars=4
            )
            
            if not token_response or 'widgets' not in token_response:
                return {}
            
            results = {}
            
            # 查找相关主题widgets
            for widget in token_response['widgets']:
                if widget.get('id') == 'RELATED_TOPICS':
                    data_payload = {
                        'hl': self.hl,
                        'tz': self.tz,
                        'req': json.dumps(widget['request']),
                        'token': widget['token']
                    }
                    
                    data_response = self._get_data(
                        self.RELATED_TOPICS_URL,
                        method='get',
                        params=data_payload,
                        trim_chars=5
                    )
                    
                    if data_response and 'default' in data_response:
                        # 解析相关主题数据
                        related_data = data_response['default']
                        
                        # 处理top和rising数据
                        for kw_idx, kw in enumerate(self.kw_list):
                            if kw not in results:
                                results[kw] = {}
                            
                            if 'rankedList' in related_data:
                                for ranked_list in related_data['rankedList']:
                                    list_type = 'top' if ranked_list.get('rankedKeyword', [{}])[0].get('topic', {}).get('type') == 'ENTITY' else 'rising'
                                    
                                    topics = []
                                    for item in ranked_list.get('rankedKeyword', []):
                                        topic_data = item.get('topic', {})
                                        topics.append({
                                            'topic_title': topic_data.get('title', ''),
                                            'topic_type': topic_data.get('type', ''),
                                            'value': item.get('value', 0)
                                        })
                                    
                                    results[kw][list_type] = pd.DataFrame(topics)
            
            return results
            
        except Exception as e:
            logger.error(f"获取相关主题失败: {e}")
            return {}
    
    def related_queries(self) -> Dict:
        """获取相关查询"""
        if not self.kw_list:
            raise ValueError("请先设置关键词列表")
        
        payload = self.build_payload(self.kw_list, self.cat, self.timeframe, self.geo, self.gprop)
        
        token_payload = {
            'hl': self.hl,
            'tz': self.tz,
            'req': json.dumps(payload)
        }
        
        try:
            token_response = self._get_data(
                self.GENERAL_URL,
                method='get',
                params=token_payload,
                trim_chars=4
            )
            
            if not token_response or 'widgets' not in token_response:
                return {}
            
            results = {}
            
            # 查找相关查询widgets
            for widget in token_response['widgets']:
                if widget.get('id') == 'RELATED_QUERIES':
                    data_payload = {
                        'hl': self.hl,
                        'tz': self.tz,
                        'req': json.dumps(widget['request']),
                        'token': widget['token']
                    }
                    
                    data_response = self._get_data(
                        self.RELATED_TOPICS_URL,  # 使用相同的URL
                        method='get',
                        params=data_payload,
                        trim_chars=5
                    )
                    
                    if data_response and 'default' in data_response:
                        related_data = data_response['default']
                        
                        for kw_idx, kw in enumerate(self.kw_list):
                            if kw not in results:
                                results[kw] = {}
                            
                            if 'rankedList' in related_data:
                                for ranked_list in related_data['rankedList']:
                                    list_type = 'top' if 'top' in str(ranked_list) else 'rising'
                                    
                                    queries = []
                                    for item in ranked_list.get('rankedKeyword', []):
                                        queries.append({
                                            'query': item.get('query', ''),
                                            'value': item.get('value', 0)
                                        })
                                    
                                    results[kw][list_type] = pd.DataFrame(queries)
            
            return results
            
        except Exception as e:
            logger.error(f"获取相关查询失败: {e}")
            return {}
    
    def trending_searches(self, pn: str = 'united_states') -> pd.DataFrame:
        """获取热门搜索"""
        try:
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
            
        except Exception as e:
            logger.error(f"获取热门搜索失败: {e}")
            return pd.DataFrame()
    
    def suggestions(self, keyword: str) -> List[Dict]:
        """获取关键词建议"""
        try:
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
            
        except Exception as e:
            logger.error(f"获取关键词建议失败: {e}")
            return []
    
    def get_historical_interest(self, keyword: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取历史兴趣数据"""
        if start_date and end_date:
            timeframe = f"{start_date} {end_date}"
        else:
            timeframe = self.timeframe
        
        # 临时保存当前设置
        original_kw_list = self.kw_list
        original_timeframe = self.timeframe
        
        try:
            # 设置单个关键词
            self.kw_list = [keyword]
            self.timeframe = timeframe
            
            # 获取数据
            df = self.interest_over_time()
            
            return df
            
        finally:
            # 恢复原始设置
            self.kw_list = original_kw_list
            self.timeframe = original_timeframe
    
    def get_historical_daily_data(
        self,
        keywords: List[str],
        start_date: str,
        end_date: str,
        geo: str = '',
        cat: int = 0,
        gprop: str = '',
        overlap_days: int = 60,
        delay: int = 2,
        max_chunks: int = 50
    ) -> pd.DataFrame:
        """
        获取长时间跨度的每日精确兴趣度数据，通过分块请求和数据拼接来避免Google Trends的降采样。

        Args:
            keywords: 要查询的关键词列表.
            start_date: 开始日期, 格式 'YYYY-MM-DD'.
            end_date: 结束日期, 格式 'YYYY-MM-DD'.
            geo: 地理位置.
            cat: 类别.
            gprop: Google Property.
            overlap_days: 用于计算缩放比例的重叠天数 (30-90).
            delay: 每次API请求之间的延迟（秒）.
            max_chunks: 最大分块数量限制.

        Returns:
            一个包含拼接和标准化后每日数据的Pandas DataFrame.
        
        Raises:
            ValueError: 当参数无效时抛出.
        """
        # 参数验证
        if not keywords or not isinstance(keywords, list):
            raise ValueError("关键词列表不能为空且必须是列表类型")
        
        if len(keywords) > 5:
            logger.warning("Google Trends最多支持5个关键词，将使用前5个")
            keywords = keywords[:5]
        
        # 验证并解析日期
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError as e:
            raise ValueError(f"日期格式错误，请使用 'YYYY-MM-DD' 格式: {e}")

        if start_dt >= end_dt:
            raise ValueError("开始日期必须早于结束日期")
        
        if (end_dt - start_dt).days > 365 * 10:  # 限制最大10年
            raise ValueError("时间跨度过长，最大支持10年")
        
        # 验证重叠天数
        if not 30 <= overlap_days <= 90:
            logger.warning("重叠天数建议在30-90天之间，已调整为60天")
            overlap_days = 60

        try:
            # Google Trends在约270天内提供每日数据，使用保守窗口
            chunk_duration_days = 260
            
            if (end_dt - start_dt).days <= chunk_duration_days:
                # 时间范围足够短，直接请求
                self.build_payload(keywords, cat=cat, timeframe=f'{start_date} {end_date}', geo=geo, gprop=gprop)
                return self.interest_over_time()

            # --- 数据分块逻辑 ---
            date_chunks = []
            current_start = start_dt
            chunk_count = 0
            
            while current_start < end_dt and chunk_count < max_chunks:
                chunk_end = min(current_start + timedelta(days=chunk_duration_days), end_dt)
                date_chunks.append((current_start.strftime('%Y-%m-%d'), chunk_end.strftime('%Y-%m-%d')))
                
                # 计算下一个分块的起始点
                if chunk_end >= end_dt:
                    break
                    
                next_start_point = chunk_end - timedelta(days=overlap_days)
                
                # 防止死循环：确保有进展
                if next_start_point <= current_start:
                    logger.warning("分块逻辑异常，强制推进到下一个时间点")
                    next_start_point = current_start + timedelta(days=chunk_duration_days - overlap_days + 1)
                
                current_start = next_start_point
                chunk_count += 1

            if chunk_count >= max_chunks:
                logger.warning(f"达到最大分块数量限制 ({max_chunks})，可能无法获取完整数据")

            # --- 获取并拼接数据 ---
            all_data = []
            logger.info(f"时间范围过长，将分为 {len(date_chunks)} 块进行请求...")
            
            for i, (start, end) in enumerate(date_chunks):
                try:
                    logger.info(f"正在获取第 {i+1}/{len(date_chunks)} 块数据: {start} 到 {end}")
                    
                    self.build_payload(keywords, cat=cat, timeframe=f'{start} {end}', geo=geo, gprop=gprop)
                    chunk_df = self.interest_over_time()
                    
                    if not chunk_df.empty:
                        # 验证数据质量
                        if len(chunk_df) < 7:  # 少于一周的数据可能有问题
                            logger.warning(f"时间段 {start} 到 {end} 数据点过少: {len(chunk_df)} 个")
                        all_data.append(chunk_df)
                    else:
                        logger.warning(f"时间段 {start} 到 {end} 未获取到数据")
                    
                    # 动态调整延迟
                    actual_delay = delay + (i * 0.5)  # 随着请求增多，延迟递增
                    logger.info(f"暂停 {actual_delay:.1f} 秒...")
                    time.sleep(actual_delay)
                    
                except Exception as e:
                    logger.error(f"获取时间段 {start} 到 {end} 数据时出错: {e}")
                    continue

            if not all_data:
                logger.error("所有分块请求均未返回有效数据")
                return pd.DataFrame()

            if len(all_data) == 1:
                logger.info("只有一个数据块，直接返回")
                return all_data[0].sort_index()

            # --- 数据标准化与拼接 ---
            logger.info("开始拼接和标准化数据...")
            stitched_df = all_data[0].copy()
            
            for i in range(1, len(all_data)):
                next_df = all_data[i].copy()
                
                # 找到重叠部分
                overlap_start = max(next_df.index.min(), stitched_df.index.min())
                overlap_end = min(stitched_df.index.max(), next_df.index.max())
                
                if overlap_start > overlap_end:
                    # 没有重叠，直接拼接
                    logger.warning(f"第 {i+1} 块数据与前面数据无重叠，直接拼接")
                    stitched_df = pd.concat([stitched_df, next_df])
                    continue

                # 获取重叠数据
                try:
                    overlap_stitched = stitched_df.loc[overlap_start:overlap_end]
                    overlap_next = next_df.loc[overlap_start:overlap_end]
                except KeyError:
                    logger.warning(f"第 {i+1} 块数据重叠部分索引异常，直接拼接")
                    stitched_df = pd.concat([stitched_df, next_df])
                    continue

                if overlap_stitched.empty or overlap_next.empty:
                    logger.warning(f"第 {i+1} 块数据重叠部分为空，直接拼接")
                    stitched_df = pd.concat([stitched_df, next_df])
                    continue

                # 计算缩放因子
                scaling_factors = {}
                for keyword in keywords:
                    if keyword in overlap_stitched.columns and keyword in overlap_next.columns:
                        old_values = overlap_stitched[keyword].dropna()
                        new_values = overlap_next[keyword].dropna()
                        
                        if len(old_values) == 0 or len(new_values) == 0:
                            scaling_factors[keyword] = 1.0
                            continue
                            
                        old_mean = old_values.mean()
                        new_mean = new_values.mean()
                        
                        if new_mean > 0 and old_mean >= 0:
                            scaling_factors[keyword] = old_mean / new_mean
                        elif old_mean == 0 and new_mean == 0:
                            scaling_factors[keyword] = 1.0
                        else:
                            # 如果新数据为0但旧数据不为0，保持原始比例
                            scaling_factors[keyword] = 1.0
                            logger.warning(f"关键词 '{keyword}' 在第 {i+1} 块中缩放因子异常，使用1.0")
                    else:
                        scaling_factors[keyword] = 1.0
                
                # 应用缩放因子
                for keyword, factor in scaling_factors.items():
                    if keyword in next_df.columns and factor != 1.0:
                        next_df[keyword] = next_df[keyword] * factor
                        logger.debug(f"关键词 '{keyword}' 应用缩放因子: {factor:.3f}")
                
                # 拼接非重叠部分
                non_overlap_next = next_df[next_df.index > overlap_end]
                if not non_overlap_next.empty:
                    stitched_df = pd.concat([stitched_df, non_overlap_next])

            # 最终处理
            result_df = stitched_df.sort_index()
            
            # 去除重复索引
            if result_df.index.duplicated().any():
                logger.warning("发现重复索引，正在去重...")
                result_df = result_df[~result_df.index.duplicated(keep='first')]
            
            # 填充缺失值
            if result_df.isnull().any().any():
                logger.info("填充缺失值...")
                result_df = result_df.fillna(method='ffill').fillna(0)
            
            logger.info(f"数据拼接完成，共 {len(result_df)} 个数据点")
            return result_df
            
        except Exception as e:
            logger.error(f"获取历史每日数据失败: {e}")
            return pd.DataFrame()

    def top_charts(self, date: int = None, geo: str = 'GLOBAL', cat: str = '') -> pd.DataFrame:
        """获取年度热门图表"""
        try:
            if date is None:
                date = datetime.now().year
            
            params = {
                'hl': self.hl,
                'tz': self.tz,
                'date': str(date),
                'geo': geo,
                'cat': cat
            }
            
            response = self._get_data(
                self.TOP_CHARTS_URL,
                method='get',
                params=params,
                trim_chars=5
            )
            
            if not response or 'topCharts' not in response:
                return pd.DataFrame()
            
            charts_data = []
            for chart in response['topCharts']:
                for item in chart.get('data', []):
                    charts_data.append({
                        'title': item.get('title', ''),
                        'exploreQuery': item.get('exploreQuery', ''),
                        'formattedTraffic': item.get('formattedTraffic', ''),
                        'link': item.get('link', ''),
                        'picture': item.get('picture', {}).get('source', ''),
                        'newsArticles': len(item.get('newsArticles', []))
                    })
            
            return pd.DataFrame(charts_data)
            
        except Exception as e:
            logger.error(f"获取年度热门图表失败: {e}")
            return pd.DataFrame()
    
    def categories(self) -> Dict:
        """获取所有可用的分类"""
        try:
            params = {
                'hl': self.hl,
                'tz': self.tz
            }
            
            response = self._get_data(
                self.CATEGORIES_URL,
                method='get',
                params=params,
                trim_chars=5
            )
            
            if not response:
                return {}
            
            categories = {}
            
            def parse_categories(items, parent_id=''):
                for item in items:
                    cat_id = item.get('id', '')
                    cat_name = item.get('name', '')
                    
                    if cat_id and cat_name:
                        full_id = f"{parent_id}-{cat_id}" if parent_id else cat_id
                        categories[full_id] = cat_name
                        
                        # 递归处理子分类
                        if 'children' in item:
                            parse_categories(item['children'], full_id)
            
            if 'children' in response:
                parse_categories(response['children'])
            
            return categories
            
        except Exception as e:
            logger.error(f"获取分类失败: {e}")
            return {}
    
    def realtime_trending_searches(self, geo: str = 'US', cat: str = 'all') -> pd.DataFrame:
        """获取实时热门搜索"""
        try:
            params = {
                'hl': self.hl,
                'tz': self.tz,
                'geo': geo,
                'cat': cat,
                'fi': 0,
                'fs': 10,
                'ri': 300,
                'rs': 20,
                'sort': 0
            }
            
            response = self._get_data(
                self.REALTIME_TRENDING_URL,
                method='get',
                params=params,
                trim_chars=5
            )
            
            if not response or 'storySummaries' not in response:
                return pd.DataFrame()
            
            trending_data = []
            for story in response['storySummaries']['trendingStories']:
                for article in story.get('articles', []):
                    trending_data.append({
                        'title': story.get('title', ''),
                        'entityNames': ', '.join(story.get('entityNames', [])),
                        'traffic': story.get('formattedTraffic', ''),
                        'article_title': article.get('articleTitle', ''),
                        'article_url': article.get('url', ''),
                        'article_source': article.get('source', ''),
                        'article_time': article.get('time', ''),
                        'image': story.get('image', {}).get('source', '')
                    })
            
            return pd.DataFrame(trending_data)
            
        except Exception as e:
            logger.error(f"获取实时热门搜索失败: {e}")
            return pd.DataFrame()
    
    def today_searches(self, geo: str = 'US') -> pd.DataFrame:
        """获取今日搜索趋势"""
        try:
            params = {
                'hl': self.hl,
                'tz': self.tz,
                'geo': geo,
                'ns': 15
            }
            
            response = self._get_data(
                self.TODAY_SEARCHES_URL,
                method='get',
                params=params,
                trim_chars=5
            )
            
            if not response or 'default' not in response:
                return pd.DataFrame()
            
            today_data = []
            trending_searches = response['default'].get('trendingSearchesDays', [])
            
            if trending_searches:
                # 获取最新一天的数据
                latest_day = trending_searches[0]
                for search in latest_day.get('trendingSearches', []):
                    today_data.append({
                        'title': search.get('title', {}).get('query', ''),
                        'formattedTraffic': search.get('formattedTraffic', ''),
                        'relatedQueries': ', '.join([q.get('query', '') for q in search.get('relatedQueries', [])]),
                        'image': search.get('image', {}).get('source', ''),
                        'newsUrl': search.get('articles', [{}])[0].get('url', '') if search.get('articles') else '',
                        'date': latest_day.get('date', '')
                    })
            
            return pd.DataFrame(today_data)
            
        except Exception as e:
            logger.error(f"获取今日搜索失败: {e}")
            return pd.DataFrame()
    
    def hourly_searches(self, geo: str = 'US') -> pd.DataFrame:
        """获取小时级搜索数据"""
        try:
            # 使用实时趋势API获取更细粒度的数据
            params = {
                'hl': self.hl,
                'tz': self.tz,
                'geo': geo,
                'cat': 'all',
                'fi': 0,
                'fs': 10,
                'ri': 60,  # 60分钟间隔
                'rs': 20,
                'sort': 0
            }
            
            response = self._get_data(
                self.REALTIME_TRENDING_URL,
                method='get',
                params=params,
                trim_chars=5
            )
            
            if not response:
                return pd.DataFrame()
            
            hourly_data = []
            
            # 解析实时数据并按小时组织
            if 'storySummaries' in response:
                for story in response['storySummaries'].get('trendingStories', []):
                    # 提取时间信息
                    traffic_class = story.get('trafficClass', '')
                    
                    hourly_data.append({
                        'title': story.get('title', ''),
                        'traffic': story.get('formattedTraffic', ''),
                        'traffic_class': traffic_class,
                        'entityNames': ', '.join(story.get('entityNames', [])),
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:00:00'),
                        'image': story.get('image', {}).get('source', '')
                    })
            
            return pd.DataFrame(hourly_data)
            
        except Exception as e:
            logger.error(f"获取小时级搜索失败: {e}")
            return pd.DataFrame()
    
    def get_trending_topics(self, geo: str = 'US', timeframe: str = 'now 1-d') -> pd.DataFrame:
        """获取趋势主题（综合方法）"""
        try:
            # 结合多个数据源获取趋势主题
            results = []
            
            # 1. 获取实时趋势
            realtime_df = self.realtime_trending_searches(geo=geo)
            if not realtime_df.empty:
                for _, row in realtime_df.iterrows():
                    results.append({
                        'topic': row.get('title', ''),
                        'type': 'realtime',
                        'traffic': row.get('traffic', ''),
                        'source': 'realtime_trending'
                    })
            
            # 2. 获取今日搜索
            today_df = self.today_searches(geo=geo)
            if not today_df.empty:
                for _, row in today_df.iterrows():
                    results.append({
                        'topic': row.get('title', ''),
                        'type': 'daily',
                        'traffic': row.get('formattedTraffic', ''),
                        'source': 'today_searches'
                    })
            
            return pd.DataFrame(results)
            
        except Exception as e:
            logger.error(f"获取趋势主题失败: {e}")
            return pd.DataFrame()
    
    def get_category_trends(self, category: int, geo: str = '', timeframe: str = 'today 12-m') -> pd.DataFrame:
        """获取特定分类的趋势数据"""
        try:
            # 临时保存当前设置
            original_cat = self.cat
            original_geo = self.geo
            original_timeframe = self.timeframe
            
            # 设置分类参数
            self.cat = category
            self.geo = geo
            self.timeframe = timeframe
            
            # 构建请求获取该分类下的热门关键词
            payload = {
                'comparisonItem': [],
                'category': category,
                'property': ''
            }
            
            token_payload = {
                'hl': self.hl,
                'tz': self.tz,
                'req': json.dumps(payload)
            }
            
            token_response = self._get_data(
                self.GENERAL_URL,
                method='get',
                params=token_payload,
                trim_chars=4
            )
            
            if not token_response:
                return pd.DataFrame()
            
            # 从响应中提取趋势数据
            trends_data = []
            
            # 这里可以进一步解析分类相关的趋势数据
            # 由于Google Trends API的复杂性，这里提供基础框架
            
            return pd.DataFrame(trends_data)
            
        except Exception as e:
            logger.error(f"获取分类趋势失败: {e}")
            return pd.DataFrame()
        finally:
            # 恢复原始设置
            self.cat = original_cat
            self.geo = original_geo
            self.timeframe = original_timeframe
    
    def compare_keywords(self, keywords: List[str], timeframe: str = 'today 12-m', geo: str = '') -> pd.DataFrame:
        """比较多个关键词的趋势"""
        if len(keywords) > 5:
            logger.warning("Google Trends最多支持5个关键词比较，将使用前5个")
            keywords = keywords[:5]
        
        # 临时保存当前设置
        original_kw_list = self.kw_list
        original_timeframe = self.timeframe
        original_geo = self.geo
        
        try:
            # 设置比较参数
            self.kw_list = keywords
            self.timeframe = timeframe
            self.geo = geo
            
            # 获取时间序列数据
            df = self.interest_over_time()
            
            return df
            
        finally:
            # 恢复原始设置
            self.kw_list = original_kw_list
            self.timeframe = original_timeframe
            self.geo = original_geo
    
    def get_geo_suggestions(self, keyword: str = '') -> List[Dict]:
        """获取地理位置建议"""
        try:
            # 这个功能通常通过分析现有的地区数据来实现
            # 由于API限制，这里提供一个基础的地区列表
            
            common_geos = [
                {'code': 'US', 'name': 'United States'},
                {'code': 'GB', 'name': 'United Kingdom'},
                {'code': 'CA', 'name': 'Canada'},
                {'code': 'AU', 'name': 'Australia'},
                {'code': 'DE', 'name': 'Germany'},
                {'code': 'FR', 'name': 'France'},
                {'code': 'JP', 'name': 'Japan'},
                {'code': 'CN', 'name': 'China'},
                {'code': 'IN', 'name': 'India'},
                {'code': 'BR', 'name': 'Brazil'}
            ]
            
            return common_geos
            
        except Exception as e:
            logger.error(f"获取地理位置建议失败: {e}")
            return []
    
    def get_timeframe_suggestions(self) -> List[str]:
        """获取时间范围建议"""
        return [
            'now 1-H',      # 过去1小时
            'now 4-H',      # 过去4小时
            'now 1-d',      # 过去1天
            'now 7-d',      # 过去7天
            'today 1-m',    # 过去1个月
            'today 3-m',    # 过去3个月
            'today 12-m',   # 过去12个月
            'today 5-y',    # 过去5年
            '2019-01-01 2019-12-31',  # 自定义时间范围示例
            'all'           # 所有时间
        ]
    
    def validate_keywords(self, keywords: List[str]) -> Dict[str, bool]:
        """验证关键词是否有效"""
        results = {}
        
        for keyword in keywords:
            # 基本验证规则
            is_valid = True
            
            # 检查长度
            if len(keyword.strip()) == 0:
                is_valid = False
            elif len(keyword) > 100:  # Google Trends关键词长度限制
                is_valid = False
            
            # 检查特殊字符
            invalid_chars = ['<', '>', '"', '&']
            if any(char in keyword for char in invalid_chars):
                is_valid = False
            
            results[keyword] = is_valid
        
        return results
    
    def get_search_volume_estimate(self, keyword: str, timeframe: str = 'today 12-m') -> Dict:
        """获取搜索量估算（基于趋势数据）"""
        try:
            # 临时设置
            original_kw_list = self.kw_list
            original_timeframe = self.timeframe
            
            self.kw_list = [keyword]
            self.timeframe = timeframe
            
            # 获取时间序列数据
            df = self.interest_over_time()
            
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
            
        except Exception as e:
            logger.error(f"获取搜索量估算失败: {e}")
            return {'keyword': keyword, 'estimate': 'Error', 'trend': 'Unknown'}
        finally:
            # 恢复设置
            self.kw_list = original_kw_list
            self.timeframe = original_timeframe
    
    def batch_keyword_analysis(self, keywords: List[str], max_batch_size: int = 5) -> Dict:
        """批量关键词分析"""
        results = {
            'interest_over_time': {},
            'interest_by_region': {},
            'related_topics': {},
            'related_queries': {},
            'search_volume_estimates': {}
        }
        
        # 分批处理关键词
        for i in range(0, len(keywords), max_batch_size):
            batch = keywords[i:i + max_batch_size]
            
            try:
                # 设置当前批次
                self.kw_list = batch
                
                # 获取各种数据
                results['interest_over_time'][f'batch_{i//max_batch_size + 1}'] = self.interest_over_time()
                results['interest_by_region'][f'batch_{i//max_batch_size + 1}'] = self.interest_by_region()
                results['related_topics'][f'batch_{i//max_batch_size + 1}'] = self.related_topics()
                results['related_queries'][f'batch_{i//max_batch_size + 1}'] = self.related_queries()
                
                # 获取搜索量估算
                for keyword in batch:
                    results['search_volume_estimates'][keyword] = self.get_search_volume_estimate(keyword)
                
                # 添加延迟避免请求过快
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"批次 {i//max_batch_size + 1} 分析失败: {e}")
                continue
        
        return results
    
    def export_data(self, data: Union[pd.DataFrame, Dict], filename: str, format: str = 'csv') -> bool:
        """导出数据到文件"""
        try:
            if format.lower() == 'csv' and isinstance(data, pd.DataFrame):
                data.to_csv(filename, index=True, encoding='utf-8')
            elif format.lower() == 'json':
                if isinstance(data, pd.DataFrame):
                    data.to_json(filename, orient='records', force_ascii=False, indent=2)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
            elif format.lower() == 'excel' and isinstance(data, pd.DataFrame):
                data.to_excel(filename, index=True)
            else:
                logger.error(f"不支持的格式: {format}")
                return False
            
            logger.info(f"数据已导出到: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            return False
    
    def get_api_status(self) -> Dict:
        """获取API状态信息"""
        try:
            # 测试基本连接
            test_response = self.session.get('https://trends.google.com/', timeout=5)
            
            status = {
                'connection': 'OK' if test_response.status_code == 200 else 'Failed',
                'status_code': test_response.status_code,
                'response_time': test_response.elapsed.total_seconds(),
                'session_cookies': len(self.session.cookies),
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return status
            
        except Exception as e:
            return {
                'connection': 'Failed',
                'error': str(e),
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def reset_session(self):
        """重置会话"""
        try:
            self.session.close()
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://trends.google.com/',
                'Origin': 'https://trends.google.com',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            })
            self._init_session()
            logger.info("会话已重置")
        except Exception as e:
            logger.error(f"重置会话失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        try:
            self.session.close()
        except:
            pass
    
    def __del__(self):
        """析构函数"""
        try:
            self.session.close()
        except:
            pass
