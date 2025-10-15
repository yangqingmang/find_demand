#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Google Trends 数据采集模块"""

import pandas as pd
import time
import json
import urllib.parse
import argparse
from typing import Optional
from src.utils import Logger
from src.utils.constants import GOOGLE_TRENDS_CONFIG
from config.config_manager import get_config

config = get_config()

from .google_trends_session import get_global_session
from .request_rate_limiter import (
    wait_for_next_request,
    register_rate_limit_event,
)

class TrendsCollector:
    """Google Trends 数据采集类"""
    
    API_CONFIG = {
        'base_urls': {
            'explore': 'https://trends.google.com/trends/api/explore',
            'related_searches': 'https://trends.google.com/trends/api/widgetdata/relatedsearches'
        },
        'default_params': {
            'hl': GOOGLE_TRENDS_CONFIG['default_language'],
            'tz': GOOGLE_TRENDS_CONFIG['default_timezone'],
            'geo': GOOGLE_TRENDS_CONFIG['default_geo'],
            'timeframe': GOOGLE_TRENDS_CONFIG['default_timeframe'],
            'category': 0,
            'property': ''
        },
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.61 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://trends.google.com/trends/explore?hl=en-US&tz=360',
            'Origin': 'https://trends.google.com',
            'Connection': 'keep-alive',
            'DNT': '0',
            'TE': 'trailers',
            'Priority': 'u=1, i',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Ch-Ua': '"Not/A)Brand";v="99", "Google Chrome";v="126", "Chromium";v="126"',
            'Sec-Ch-Ua-Full-Version': '"126.0.6478.61"',
            'Sec-Ch-Ua-Full-Version-List': '"Not/A)Brand";v="99.0.0.0", "Google Chrome";v="126.0.6478.61", "Chromium";v="126.0.6478.61"',
            'Sec-Ch-Ua-Reduced': '"Google Chrome";v="126"',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Ch-Ua-Platform-Version': '"15.0.0"',
            'Sec-Ch-Ua-Arch': '"x86"',
            'Sec-Ch-Ua-Bitness': '"64"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Model': '""',
            'Sec-Ch-Ua-Wow64': '?0',
            'Sec-Ch-Ua-Form-Factor': '"Desktop"',
            'Sec-CH-Prefers-Color-Scheme': '"light"',
            'Sec-CH-Prefers-Reduced-Motion': '"no-preference"',
            'Viewport-Width': '1920',
            'Downlink': '10',
            'ECT': '4g',
            'RTT': '50',
            'X-Client-Data': 'CK6/ygEIlLbJAQjBtskBCKmdygEIptzKAQj8tc0BCJrdzgEIk7nOARis7c4B'
        },
        'rate_limits': GOOGLE_TRENDS_CONFIG['rate_limits']
    }
    
    def __init__(self, hl=None, tz=None, timeout=(20, 30), retries=3, backoff_factor=1.5):
        self.hl = hl or self.API_CONFIG['default_params']['hl']
        self.tz = tz or self.API_CONFIG['default_params']['tz']
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.logger = Logger()
        self._cooldown_until = 0.0
        self._last_cooldown_log = 0.0
        self._rate_limit_severity: Optional[str] = None

        # 直接使用 CustomTrendsCollector，避免循环依赖
        try:
            from .custom_trends_collector import CustomTrendsCollector
            self.trends_collector = CustomTrendsCollector()
            self.logger.info("Session初始化成功")
        except Exception as e:
            self.logger.error(f"Session初始化失败: {e}")
            self.trends_collector = None
            raise RuntimeError(f"Google Trends会话初始化失败: {e}") from e
            
        if self.trends_collector and hasattr(self.trends_collector, 'set_rate_limit_callback'):
            try:
                self.trends_collector.set_rate_limit_callback(self._handle_rate_limit_event)
            except Exception as callback_error:
                self.logger.warning(f"⚠️ 无法注册限流回调: {callback_error}")

        pd.set_option('future.no_silent_downcasting', True)

    def get_trends_data(self, keywords, timeframe='today 12-m', geo=''):
        """
        获取关键词趋势数据
        
        Args:
            keywords: 关键词列表或单个关键词
            timeframe: 时间范围，默认过去12个月
            geo: 地理位置，默认全球
            
        Returns:
            pandas.DataFrame: 趋势数据
        """
        if not self.trends_collector:
            error_msg = "Google Trends 会话未初始化，可能缺少必要的 API/代理 配置"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        if not self._ensure_ready("兴趣度数据请求"):
            raise RuntimeError("Google Trends 处于冷却期，暂未执行趋势数据请求")

        try:
            # 确保keywords是列表格式
            if isinstance(keywords, str):
                keywords = [keywords]
            
            # 打印请求参数用于调试
            self.logger.info(f"🔍 正在请求Google Trends数据:")
            self.logger.info(f"   关键词: {keywords}")
            self.logger.info(f"   时间范围: {timeframe}")
            self.logger.info(f"   地理位置: {geo}")
            
            # 构建payload
            self.trends_collector.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo, gprop='')
            
            # 获取兴趣度数据
            interest_over_time = self.trends_collector.interest_over_time()

            if interest_over_time.empty:
                warning_msg = f"未获取到关键词 {keywords} 的 Google Trends 数据"
                self.logger.warning(warning_msg)
                raise RuntimeError(warning_msg)

            # 移除 'isPartial' 列
            if 'isPartial' in interest_over_time.columns:
                interest_over_time = interest_over_time.drop('isPartial', axis=1)

            self.logger.info(f"✅ 成功获取到 {len(interest_over_time)} 条趋势数据")
            return interest_over_time

        except Exception as e:
            self.logger.error(f"❌ 获取趋势数据失败: {e}")
            self.logger.error(f"   请求参数: keywords={keywords}, timeframe={timeframe}, geo={geo}")
            raise

    def _make_api_request(self, request_type, keyword=None, geo=None, timeframe=None, 
                         widget_token=None, widget_request=None):
        """统一API请求方法"""
        time.sleep(1)
        
        geo = geo or self.API_CONFIG['default_params']['geo']
        timeframe = timeframe or self.API_CONFIG['default_params']['timeframe']

        url = ''
        params={}

        if self._is_in_cooldown():
            self.logger.warning("⚠️ TrendsCollector 仍在冷却窗口内，跳过请求: %s", request_type)
            return None

        try:
            if request_type == 'explore':
                url = self.API_CONFIG['base_urls']['explore']
                params = {
                    'hl': self.hl,
                    'tz': self.tz,
                    'req': json.dumps({
                        'comparisonItem': [{
                            'keyword': keyword,
                            'geo': geo,
                            'time': timeframe
                        }],
                        'category': 0,
                        'property': ''
                    })
                }
            elif request_type == 'related_searches':
                url = self.API_CONFIG['base_urls']['related_searches']
                params = {
                    'hl': self.hl,
                    'tz': self.tz,
                    'req': json.dumps(widget_request),
                    'token': widget_token
                }
            
            full_url = f"{url}?{urllib.parse.urlencode(params)}"

            # 打印完整的请求URL用于调试
            self.logger.debug(f"🔍 正在请求URL: {full_url}")
            self.logger.debug(f"📋 请求参数: {params}")
            
            # 使用统一的session管理
            if self.trends_collector and hasattr(self.trends_collector, 'session'):
                if not self._wait_for_slot():
                    return None
                time.sleep(2)
                request_headers = dict(self.API_CONFIG['headers'])

                if keyword:
                    referer_params = {
                        'hl': self.hl,
                        'tz': self.tz,
                        'q': keyword
                    }
                    if geo:
                        referer_params['geo'] = geo
                    request_headers['Referer'] = f"https://trends.google.com/trends/explore?{urllib.parse.urlencode(referer_params)}"
                else:
                    referer_params = {
                        'hl': self.hl,
                        'tz': self.tz
                    }
                    if geo:
                        referer_params['geo'] = geo
                    request_headers['Referer'] = f"https://trends.google.com/trends/explore?{urllib.parse.urlencode(referer_params)}"

                response = self.trends_collector.trends_session.make_request(
                    'GET',
                    url,
                    headers=request_headers,
                    params=params,
                    timeout=self.timeout
                )
            else:
                self.logger.error("trends_collector未初始化或没有session")
                return None

            # 打印响应状态
            self.logger.info(f"📡 响应状态码: {response.status_code}")

            if response.status_code == 200:
                content = response.text
                if content.startswith(")]}',"):
                    content = content[5:]
                elif content.startswith(")]}'"):
                    content = content[4:]
                return json.loads(content)
            elif response.status_code == 429:
                penalty = register_rate_limit_event('high')
                self._start_cooldown(penalty)
                self.logger.error("API请求过于频繁，触发冷却 %.1f 秒", penalty)
                return None
            else:
                self.logger.error(f"API请求失败: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"API请求异常: {e}")
            return None

    def fetch_rising_queries(self, keyword=None, geo=None, timeframe=None):
        """获取Rising Queries"""
        geo = geo or self.API_CONFIG['default_params']['geo']
        timeframe = timeframe or self.API_CONFIG['default_params']['timeframe']

        if not self._ensure_ready("related queries 数据抓取"):
            return pd.DataFrame(columns=['query', 'value', 'growth'])

        if not keyword or not keyword.strip():
            return self._fetch_trending_via_api(geo=geo, timeframe=timeframe)

        time.sleep(1)

        for attempt in range(self.retries):
            try:
                self.trends_collector.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
                related_queries = self.trends_collector.related_queries()

                if keyword in related_queries and related_queries[keyword]:
                    rising = related_queries[keyword]['rising']
                    top = related_queries[keyword]['top']

                    if rising is not None and not rising.empty:
                        return rising
                    if top is not None and not top.empty:
                        top['growth'] = 0
                        return top

                raise RuntimeError(f"未获取到关键词 {keyword} 的 related queries 数据")

            except Exception as e:
                if attempt < self.retries - 1:
                    wait_time = self.backoff_factor * (2 ** attempt)
                    self.logger.warning(f"获取数据出错，等待{wait_time:.1f}秒重试: {e}")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"多次尝试失败: {e}")
                    raise

    def _fetch_trending_via_api(self, geo=None, timeframe=None):
        """通过API获取热门关键词"""

        if not self._ensure_ready("trending API 调用"):
            return pd.DataFrame(columns=['query', 'value', 'growth'])

        try:
            # 完全按照成功的curl请求
            url = "https://trends.google.com/trends/api/explore"
            params = {
                'hl': 'en-US',
                'tz': '360',
                'req': '{"comparisonItem":[{"keyword":"","geo":"US","time":"now 7-d"}],"category":0,"property":""}'
            }

            # 使用公共session管理
            trends_session = get_global_session()

            try:
                if not self._wait_for_slot():
                    return pd.DataFrame(columns=['query', 'value', 'growth'])
                response = trends_session.get(url, params=params)
            except Exception as session_error:
                self.logger.error(f"❌ 请求失败: {session_error}")
                return pd.DataFrame(columns=['query', 'value', 'growth'])

            if response.status_code == 200:
                content = response.text
                
                # 处理Google的特殊前缀
                # 处理Google的特殊前缀
                self.logger.info(f"📄 原始响应详细: {repr(content[:20])}")
                
                # 找到JSON开始的位置
                json_start = content.find('{')
                if json_start > 0:
                    content = content[json_start:]
                    self.logger.info(f"找到JSON开始位置: {json_start}")
                elif content.startswith(")]}',"):
                    content = content[5:]
                    self.logger.info("移除了)]}',前缀")
                elif content.startswith(")]}'\n"):
                    content = content[6:]
                    self.logger.info("移除了)]}'\n前缀")
                elif content.startswith(")]}'"):
                    content = content[4:]
                    self.logger.info("移除了)]}'前缀")
                
                self.logger.info(f"📄 处理后内容前50字符: {content[:50]}")
                self.logger.info(f"📄 处理后内容前50字符: {content[:50]}")
                
                try:
                    data = json.loads(content)
                    self.logger.info("✅ 成功解析JSON数据")
                    self.logger.info(f"📊 数据结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    
                    # 解析widgets获取相关搜索的token
                    if 'widgets' in data:
                        for widget in data['widgets']:
                            self.logger.info(f"🔍 Widget类型: {widget.get('id', 'unknown')}")
                            if widget.get('id') == 'RELATED_QUERIES':
                                token = widget.get('token')
                                if token:
                                    self.logger.info(f"🎯 找到RELATED_QUERIES token: {token[:20]}...")
                                    
                                    # 请求related_searches接口获取真正的相关词
                                    related_url = "https://trends.google.com/trends/api/widgetdata/relatedsearches"
                                    related_params = {
                                        'hl': 'en-US',
                                        'tz': '360',
                                        'req': json.dumps(widget.get('request', {})),
                                        'token': token
                                    }

                                    self.logger.info("🔍 正在请求related_searches接口...")
                                    # 使用公共session管理
                                    trends_session = get_global_session()
                                    if not self._wait_for_slot():
                                        return pd.DataFrame(columns=['query', 'value', 'growth'])
                                    related_response = trends_session.get(related_url, params=related_params)

                                    if related_response.status_code == 200:
                                        related_content = related_response.text
                                        # 处理特殊前缀
                                        json_start = related_content.find('{')
                                        if json_start > 0:
                                            related_content = related_content[json_start:]
                                        
                                        try:
                                            related_data = json.loads(related_content)
                                            self.logger.info("✅ 成功获取related searches数据")
                                            self.logger.info(f"📊 Related data结构: {list(related_data.keys()) if isinstance(related_data, dict) else type(related_data)}")
                                            
                                            # 解析真正的相关搜索词
                                            keywords = []
                                            if 'default' in related_data and 'rankedList' in related_data['default']:
                                                for ranked_list in related_data['default']['rankedList']:
                                                    if 'rankedKeyword' in ranked_list:
                                                        for item in ranked_list['rankedKeyword']:
                                                            if 'query' in item:
                                                                keywords.append({
                                                                    'query': item['query'],
                                                                    'value': item.get('value', 0),
                                                                    'growth': item.get('formattedValue', 'N/A')
                                                                })
                                            
                                            if keywords:
                                                self.logger.info(f"🎯 解析到 {len(keywords)} 个真实关键词")
                                                return pd.DataFrame(keywords)
                                            
                                        except json.JSONDecodeError as e:
                                            self.logger.error(f"Related searches JSON解析失败: {e}")
                                    else:
                                        if related_response.status_code == 429:
                                            penalty_inner = register_rate_limit_event('high')
                                            self._start_cooldown(penalty_inner)
                                            self.logger.error("❌ related_searches 命中 429，冷却 %.1f 秒", penalty_inner)
                                        else:
                                            self.logger.error(
                                                f"⚠️ related_searches 请求失败: {related_response.status_code}"
                                            )
                                        return pd.DataFrame(columns=['query', 'value', 'growth'])

                                    break
                    
                    raise RuntimeError("无法从 Google Trends 获取 related searches 数据，且没有可用的备选数据源")
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON解析失败: {e}")
                    self.logger.error(f"尝试解析的内容: {content[:200]}")
                    raise
            else:
                if response.status_code == 429:
                    penalty = register_rate_limit_event('high')
                    self._start_cooldown(penalty)
                    self.logger.error("❌ trending API 命中 429，已进入冷却 %.1f 秒", penalty)
                else:
                    self.logger.error(f"❌ 请求失败，状态码: {response.status_code}")
                raise RuntimeError(f"Google Trends related searches 请求失败，状态码: {response.status_code}")

        except Exception as e:
            self.logger.error(f"API请求异常: {e}")
            raise


    def _parse_related_queries(self, data):
        """解析相关查询数据"""
        queries = []
        try:
            if 'default' in data and 'rankedList' in data['default']:
                for ranked_list in data['default']['rankedList']:
                    for item in ranked_list.get('rankedKeyword', []):
                        query = item.get('query', '')
                        value = item.get('value', 0)
                        formatted_value = item.get('formattedValue', '0')

                        growth = formatted_value if '%' in str(formatted_value) else f"{value}%"
                        queries.append({
                            'query': query,
                            'value': value,
                            'growth': growth
                        })

            return pd.DataFrame(queries) if queries else pd.DataFrame(columns=['query', 'value', 'growth'])
        except Exception as e:
            self.logger.error(f"解析数据出错: {e}")
            return pd.DataFrame(columns=['query', 'value', 'growth'])

    def get_related_queries(self, keyword, geo='', timeframe='today 12-m'):
        """获取相关查询"""
        if not self.trends_collector:
            self.logger.error("trends_collector 未初始化")
            return {}

        if not self._ensure_ready("Google Trends 相关查询"):
            return {}
            
        try:
            # 构建payload
            self.trends_collector.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo, gprop='')
            
            # 获取相关查询
            related_queries = self.trends_collector.related_queries()
            return related_queries
        except Exception as e:
            self.logger.error(f"获取相关查询失败: {e}")
            return {}

    def _is_in_cooldown(self) -> bool:
        return time.time() < self._cooldown_until

    def _start_cooldown(self, seconds: float) -> None:
        seconds = max(float(seconds or 0.0), 0.0)
        if seconds <= 0:
            return
        new_until = time.time() + seconds
        if new_until > self._cooldown_until:
            self._cooldown_until = new_until
            self.logger.warning("⏳ TrendsCollector 进入冷却，剩余 %.1f 秒", seconds)
            self._last_cooldown_log = 0.0

    def _handle_rate_limit_event(self, penalty: float, severity: str = 'medium') -> None:
        try:
            wait_seconds = float(penalty or 0.0)
        except (TypeError, ValueError):
            wait_seconds = 0.0

        if wait_seconds <= 0:
            return

        self._rate_limit_severity = severity
        self._start_cooldown(wait_seconds)

    def _ensure_ready(self, action_desc: str) -> bool:
        if not self._is_in_cooldown():
            return True

        remaining = max(self._cooldown_until - time.time(), 0.0)
        now = time.time()
        if now - self._last_cooldown_log >= 1.0:
            self.logger.warning(
                "⏸ Google Trends 冷却中 (%.1f 秒)，跳过 %s", remaining, action_desc
            )
            self._last_cooldown_log = now
        return False

    def is_in_cooldown(self) -> bool:
        """对外暴露的冷却状态查询"""
        return self._is_in_cooldown()

    def _wait_for_slot(self) -> bool:
        try:
            wait_for_next_request()
            return True
        except RuntimeError as exc:
            self.logger.error(f"❌ 请求被限流守卫阻止: {exc}")
            return False
        except Exception as exc:
            self.logger.warning(f"⚠️ 等待限流槽位时异常: {exc}")
            return True

    def get_related_topics(self, keyword, geo='', timeframe='today 12-m'):
        """获取相关主题"""
        if not self.trends_collector:
            self.logger.error("trends_collector 未初始化")
            return {}

        if not self._ensure_ready("Google Trends 相关主题"):
            return {}
            
        try:
            # 构建payload
            self.trends_collector.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo, gprop='')
            
            # 获取相关主题
            related_topics = self.trends_collector.related_topics()
            return related_topics
        except Exception as e:
            self.logger.error(f"获取相关主题失败: {e}")
            return {}

    def get_interest_by_region(self, keyword, geo='', timeframe='today 12-m'):
        """获取按地区分布的兴趣度"""
        if not self.trends_collector:
            self.logger.error("trends_collector 未初始化")
            return pd.DataFrame()

        if not self._ensure_ready("Google Trends 区域兴趣度"):
            return pd.DataFrame()
            
        try:
            # 构建payload
            self.trends_collector.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo, gprop='')
            
            # 获取地区兴趣度
            interest_by_region = self.trends_collector.interest_by_region()
            return interest_by_region
        except Exception as e:
            self.logger.error(f"获取地区兴趣度失败: {e}")
            return pd.DataFrame()

    def get_suggestions(self, keyword):
        """获取关键词建议"""
        if not self.trends_collector:
            self.logger.error("trends_collector 未初始化")
            return []

        if not self._ensure_ready("Google Trends 关键词建议"):
            return []
            
        try:
            suggestions = self.trends_collector.suggestions(keyword)
            return suggestions
        except Exception as e:
            self.logger.error(f"获取关键词建议失败: {e}")
            return []

    def trending_searches(self, pn='united_states'):
        """获取热门搜索"""
        if not self.trends_collector:
            self.logger.error("trends_collector 未初始化")
            return pd.DataFrame()

        if not self._ensure_ready("Google Trends 热门搜索"):
            return pd.DataFrame()
            
        try:
            trending = self.trends_collector.trending_searches(pn)
            return trending
        except Exception as e:
            self.logger.error(f"获取热门搜索失败: {e}")
            return pd.DataFrame()

    def get_historical_interest(self, keyword, start_date, end_date=None):
        """获取历史兴趣数据"""
        if not self.trends_collector:
            self.logger.error("trends_collector 未初始化")
            return pd.DataFrame()

        if not self._ensure_ready("Google Trends 历史数据"):
            return pd.DataFrame()
            
        try:
            historical_data = self.trends_collector.get_historical_interest(keyword, start_date, end_date)
            return historical_data
        except Exception as e:
            self.logger.error(f"获取历史兴趣数据失败: {e}")
            return pd.DataFrame()

    def get_keyword_trends(self, keyword, timeframe='today 12-m', geo=''):
        """获取关键词趋势数据 - 为root_word_trends_analyzer提供的接口"""
        if not self.trends_collector:
            error_msg = "Google Trends 会话未初始化，无法获取关键词趋势数据"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

        if not self._ensure_ready("Google Trends 单词趋势数据"):
            raise RuntimeError("Google Trends 处于冷却期，暂未执行关键词趋势请求")

        try:
            return self.trends_collector.get_keyword_trends(keyword, timeframe, geo)
        except Exception as e:
            self.logger.error(f"获取关键词趋势失败: {e}")
            raise


def main():
    """主函数 - 用于测试"""
    parser = argparse.ArgumentParser(description='Google Trends 数据采集工具')
    parser.add_argument('--keyword', '-k', type=str, required=True, help='要查询的关键词')
    parser.add_argument('--geo', '-g', type=str, default='', help='地理位置 (如: US, CN)')
    parser.add_argument('--timeframe', '-t', type=str, default='today 12-m', help='时间范围')
    parser.add_argument('--output', '-o', type=str, help='输出文件路径')
    
    args = parser.parse_args()
    
    # 创建采集器实例
    collector = TrendsCollector()
    
    print(f"🔍 正在查询关键词: {args.keyword}")
    print(f"📍 地理位置: {args.geo or '全球'}")
    print(f"⏰ 时间范围: {args.timeframe}")
    print("-" * 50)
    
    # 获取趋势数据
    trends_data = collector.get_trends_data(args.keyword, args.timeframe, args.geo)
    
    if not trends_data.empty:
        print("✅ 趋势数据获取成功!")
        print(f"📊 数据行数: {len(trends_data)}")
        print("\n📈 前5行数据:")
        print(trends_data.head())
        
        if args.output:
            trends_data.to_csv(args.output, index=False)
            print(f"💾 数据已保存到: {args.output}")
    else:
        print("❌ 未获取到趋势数据")
    
    # 获取相关查询
    print("\n🔍 获取相关查询...")
    related_queries = collector.get_related_queries(args.keyword, args.geo, args.timeframe)
    
    if related_queries:
        print("✅ 相关查询获取成功!")
        for query_type, queries in related_queries.items():
            if not queries.empty:
                print(f"\n📋 {query_type}:")
                print(queries.head())
    else:
        print("❌ 未获取到相关查询")


if __name__ == "__main__":
    main()
