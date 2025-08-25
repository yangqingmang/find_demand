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