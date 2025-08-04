# trends_collector.py
# Google Trends 数据采集模块
import pandas as pd
import time
from pytrends.request import TrendReq
import argparse
import os
from datetime import datetime

class TrendsCollector:
    """Google Trends 数据采集类"""
    
    def __init__(self, hl='zh-CN', tz=360, timeout=(10, 25), retries=3, backoff_factor=1.5):
        """
        初始化 TrendsCollector
        
        参数:
            hl (str): 语言设置，默认'zh-CN'
            tz (int): 时区，默认360
            timeout (tuple): 连接和读取超时时间(秒)
            retries (int): 重试次数
            backoff_factor (float): 重试间隔增长因子
        """
        self.hl = hl
        self.tz = tz
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.pytrends = None
        self._connect()
        
        # 设置pandas选项，消除警告
        pd.set_option('future.no_silent_downcasting', True)
    
    def _connect(self):
        """创建pytrends连接"""
        self.pytrends = TrendReq(hl=self.hl, tz=self.tz, timeout=self.timeout)
    
    def fetch_rising_queries(self, keyword, geo='', timeframe='today 3-m'):
        """
        获取关键词的Rising Queries
        
        参数:
            keyword (str): 种子关键词
            geo (str): 地区代码，如'US','GB'等，默认为全球
            timeframe (str): 时间范围，默认'today 3-m'
            
        返回:
            pandas.DataFrame: Rising Queries数据
        """
        print(f"正在获取 '{keyword}' 的Rising Queries数据 (地区: {geo or '全球'})...")
        
        for attempt in range(self.retries):
            try:
                # 构建payload
                self.pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
                
                # 获取相关查询
                related_queries = self.pytrends.related_queries()
                
                if keyword in related_queries and related_queries[keyword]:
                    rising = related_queries[keyword]['rising']
                    top = related_queries[keyword]['top']
                    
                    if rising is not None and not rising.empty:
                        print(f"成功获取 {len(rising)} 个Rising Queries")
                        return rising
                    elif top is not None and not top.empty:
                        print(f"未找到Rising Queries，返回 {len(top)} 个Top Queries")
                        # 为Top查询添加默认增长率0
                        top['growth'] = 0
                        return top
                    else:
                        print(f"未找到相关查询数据")
                        return pd.DataFrame(columns=['query', 'value', 'growth'])
                else:
                    print(f"未找到关键词 '{keyword}' 的相关查询数据")
                    return pd.DataFrame(columns=['query', 'value', 'growth'])
                    
            except Exception as e:
                wait_time = self.backoff_factor * (2 ** attempt)
                if attempt < self.retries - 1:
                    print(f"获取数据时出错: {e}")
                    print(f"等待 {wait_time:.1f} 秒后重试 ({attempt+1}/{self.retries})...")
                    time.sleep(wait_time)
                    # 重新连接
                    self._connect()
                else:
                    print(f"多次尝试后仍然失败: {e}")
                    return pd.DataFrame(columns=['query', 'value', 'growth'])
    
    def fetch_multiple_keywords(self, keywords, geo='', timeframe='today 3-m'):
        """
        批量获取多个关键词的Rising Queries
        
        参数:
            keywords (list): 种子关键词列表
            geo (str): 地区代码
            timeframe (str): 时间范围
            
        返回:
            dict: 关键词到DataFrame的映射
        """
        results = {}
        
        for keyword in keywords:
            df = self.fetch_rising_queries(keyword, geo, timeframe)
            if not df.empty:
                df['seed_keyword'] = keyword  # 添加种子关键词列
                results[keyword] = df
            
            # 避免API限制，每次请求之间等待
            if keyword != keywords[-1]:  # 如果不是最后一个关键词
                print("等待3秒以避免API限制...")
                time.sleep(3)
        
        return results
    
    def save_results(self, results, output_dir='data'):
        """
        保存结果到CSV文件
        
        参数:
            results (dict): 关键词到DataFrame的映射
            output_dir (str): 输出目录
        """
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取当前日期作为文件名一部分
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 合并所有结果
        all_df = pd.concat(results.values(), ignore_index=True) if results else pd.DataFrame()
        
        if not all_df.empty:
            # 保存合并的结果
            all_file = os.path.join(output_dir, f'trends_all_{date_str}.csv')
            all_df.to_csv(all_file, index=False, encoding='utf-8-sig')
            print(f"已保存所有结果到: {all_file}")
            
            # 为每个关键词保存单独的文件
            for keyword, df in results.items():
                # 将关键词中的特殊字符替换为下划线
                safe_keyword = keyword.replace(' ', '_').replace('/', '_')
                file_path = os.path.join(output_dir, f'trends_{safe_keyword}_{date_str}.csv')
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                print(f"已保存 '{keyword}' 的结果到: {file_path}")
        else:
            print("没有数据可保存")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Google Trends 数据采集工具')
    parser.add_argument('--keywords', nargs='+', required=True, help='要查询的关键词列表')
    parser.add_argument('--geo', default='', help='地区代码，如US、GB等，默认为全球')
    parser.add_argument('--timeframe', default='today 3-m', help='时间范围，默认为过去3个月')
    parser.add_argument('--output', default='data', help='输出目录，默认为data')
    
    args = parser.parse_args()
    
    # 创建采集器
    collector = TrendsCollector()
    
    # 获取数据
    results = collector.fetch_multiple_keywords(args.keywords, args.geo, args.timeframe)
    
    # 保存结果
    collector.save_results(results, args.output)


if __name__ == "__main__":
    main()