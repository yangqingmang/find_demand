#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的Google Trends API请求格式
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.collectors.trends_collector import TrendsCollector

def test_new_api_format():
    """测试新的API请求格式"""
    print("🔍 测试新的Google Trends API请求格式")
    print("=" * 60)
    
    # 创建采集器
    collector = TrendsCollector()
    
    # 测试关键词
    test_keywords = ["AI", "machine learning", "chatgpt"]
    
    for keyword in test_keywords:
        print(f"\n测试关键词: {keyword}")
        print("-" * 40)
        
        try:
            # 使用新的API格式获取数据
            df = collector.fetch_rising_queries(keyword, geo='US', timeframe='today 12-m')
            
            if not df.empty:
                print(f"✅ 成功获取数据，共 {len(df)} 条记录")
                print("前5条数据:")
                print(df.head())
            else:
                print("⚠️ 未获取到数据")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    test_new_api_format()