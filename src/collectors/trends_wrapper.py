"""
Google Trends包装器
提供与pytrends兼容的接口，使用自定义实现
"""

import pandas as pd
from typing import List, Dict, Optional, Union
from .custom_trends_collector import CustomTrendsCollector
import logging

logger = logging.getLogger(__name__)

class TrendReq:
    """
    pytrends.TrendReq的替代实现
    提供相同的API接口，但使用自定义的采集器
    """
    
    def __init__(self, hl='en-US', tz=360, timeout=(2, 5), proxies=None, retries=0, backoff_factor=0):
        """
        初始化TrendReq对象
        
        Args:
            hl: 语言设置
            tz: 时区偏移
            timeout: 请求超时
            proxies: 代理设置
            retries: 重试次数
            backoff_factor: 退避因子
        """
        self.collector = CustomTrendsCollector(
            hl=hl, 
            tz=tz, 
            timeout=timeout, 
            proxies=proxies, 
            retries=retries, 
            backoff_factor=backoff_factor
        )
        
        # 存储当前的payload参数
        self._current_kw_list = []
        self._current_cat = 0
        self._current_timeframe = 'today 12-m'
        self._current_geo = ''
        self._current_gprop = ''
    
    def build_payload(self, kw_list: List[str], cat: int = 0, timeframe: str = 'today 12-m', 
                     geo: str = '', gprop: str = '') -> None:
        """
        构建请求载荷（兼容pytrends接口）
        
        Args:
            kw_list: 关键词列表
            cat: 分类ID
            timeframe: 时间范围
            geo: 地理位置
            gprop: 属性
        """
        self._current_kw_list = kw_list
        self._current_cat = cat
        self._current_timeframe = timeframe
        self._current_geo = geo
        self._current_gprop = gprop
        
        # 调用底层采集器的build_payload
        self.collector.build_payload(kw_list, cat, timeframe, geo, gprop)
    
    def interest_over_time(self) -> pd.DataFrame:
        """获取关键词随时间变化的兴趣度"""
        return self.collector.interest_over_time()
    
    def interest_by_region(self, resolution: str = 'COUNTRY', inc_low_vol: bool = True, 
                          inc_geo_code: bool = False) -> pd.DataFrame:
        """获取按地区分布的兴趣度"""
        return self.collector.interest_by_region(resolution, inc_low_vol, inc_geo_code)
    
    def related_topics(self) -> Dict:
        """获取相关主题"""
        return self.collector.related_topics()
    
    def related_queries(self) -> Dict:
        """获取相关查询"""
        return self.collector.related_queries()
    
    def trending_searches(self, pn: str = 'united_states') -> pd.DataFrame:
        """获取热门搜索"""
        return self.collector.trending_searches(pn)
    
    def suggestions(self, keyword: str) -> List[Dict]:
        """获取关键词建议"""
        return self.collector.suggestions(keyword)
    
    def get_historical_interest(self, kw_list: List[str], year_start: int, month_start: int, 
                               day_start: int, hour_start: int = 0, year_end: int = None, 
                               month_end: int = None, day_end: int = None, hour_end: int = 0,
                               cat: int = 0, geo: str = '', gprop: str = '', sleep: int = 0) -> pd.DataFrame:
        """
        获取历史兴趣数据（兼容pytrends接口）
        
        Args:
            kw_list: 关键词列表
            year_start: 开始年份
            month_start: 开始月份
            day_start: 开始日期
            hour_start: 开始小时
            year_end: 结束年份
            month_end: 结束月份
            day_end: 结束日期
            hour_end: 结束小时
            cat: 分类
            geo: 地理位置
            gprop: 属性
            sleep: 延迟时间
            
        Returns:
            pd.DataFrame: 历史兴趣数据
        """
        # 构建日期字符串
        start_date = f"{year_start}-{month_start:02d}-{day_start:02d}"
        
        if year_end and month_end and day_end:
            end_date = f"{year_end}-{month_end:02d}-{day_end:02d}"
        else:
            end_date = None
        
        # 对每个关键词获取历史数据
        results = []
        for keyword in kw_list:
            df = self.collector.get_historical_interest(keyword, start_date, end_date)
            if not df.empty:
                results.append(df)
        
        if results:
            # 合并所有结果
            combined_df = pd.concat(results, axis=1)
            # 去重列名
            combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
            return combined_df
        else:
            return pd.DataFrame()
    
    def multirange_interest_over_time(self) -> List[pd.DataFrame]:
        """
        多时间范围兴趣度查询（简化实现）
        """
        # 这是一个简化的实现，实际使用中可能需要更复杂的逻辑
        df = self.interest_over_time()
        return [df] if not df.empty else []
    
    def realtime_trending_searches(self, pn: str = 'US') -> pd.DataFrame:
        """
        实时热门搜索（使用trending_searches作为替代）
        """
        return self.trending_searches(pn)
    
    def top_charts(self, date: int, hl: str = 'en-US', tz: int = 300, geo: str = 'GLOBAL') -> pd.DataFrame:
        """
        获取年度热门图表（简化实现）
        """
        # 这是一个简化的实现，返回当前热门搜索
        return self.trending_searches('united_states')
    
    def categories(self) -> Dict:
        """
        获取分类列表（返回常用分类）
        """
        return {
            0: "All categories",
            3: "Arts & Entertainment",
            5: "Autos & Vehicles", 
            12: "Beauty & Fitness",
            16: "Books & Literature",
            18: "Business & Industrial",
            20: "Computers & Electronics",
            174: "Finance",
            45: "Food & Drink",
            67: "Games",
            299: "Health",
            85: "Hobbies & Leisure",
            95: "Home & Garden",
            107: "Internet & Telecom",
            100: "Jobs & Education",
            179: "Law & Government",
            958: "News",
            1237: "Online Communities",
            122: "People & Society",
            132: "Pets & Animals",
            1015: "Real Estate",
            174: "Reference",
            207: "Science",
            239: "Shopping",
            254: "Sports",
            784: "Travel"
        }


# 为了完全兼容，我们也可以提供一个直接的替换函数
def create_trends_request(hl='en-US', tz=360, timeout=(2, 5), proxies=None, retries=0, backoff_factor=0):
    """
    创建TrendReq实例的便捷函数
    """
    return TrendReq(hl=hl, tz=tz, timeout=timeout, proxies=proxies, retries=retries, backoff_factor=backoff_factor)


# 兼容性别名
TrendsCollector = TrendReq  # 为了向后兼容