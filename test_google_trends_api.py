#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Trends API 连接测试脚本
用于验证API访问问题
"""

import requests
from pytrends.request import TrendReq
import time
import json

def test_direct_api_access():
    """直接测试Google Trends API访问"""
    print("=== 直接API访问测试 ===")
    
    # Google Trends的基础URL
    base_urls = [
        "https://trends.google.com",
        "https://trends.google.com/trends/api/explore",
        "https://www.google.com/trends"
    ]
    
    for url in base_urls:
        try:
            print(f"测试访问: {url}")
            response = requests.get(url, timeout=10)
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            print("✓ 访问成功\n")
        except Exception as e:
            print(f"❌ 访问失败: {e}\n")

def test_pytrends_connection():
    """测试pytrends库连接"""
    print("=== pytrends库连接测试 ===")
    
    # 不同的配置参数
    configs = [
        {"hl": "en-US", "tz": 360},
        {"hl": "zh-CN", "tz": 360},
        {"hl": "en-US", "tz": 0},
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"配置 {i}: {config}")
        try:
            pytrends = TrendReq(**config, timeout=(20, 30))
            print("✓ pytrends对象创建成功")
            
            # 尝试简单查询
            pytrends.build_payload(["python"], timeframe='today 1-m')
            print("✓ payload构建成功")
            
            # 获取兴趣度数据
            interest_over_time = pytrends.interest_over_time()
            print(f"✓ 获取兴趣度数据成功，数据量: {len(interest_over_time)}")
            
            return True
            
        except Exception as e:
            print(f"❌ 配置 {i} 失败: {e}")
            print(f"错误类型: {type(e).__name__}")
            
        print("-" * 50)
        time.sleep(2)  # 避免请求过快
    
    return False

def test_specific_keywords():
    """测试特定关键词"""
    print("=== 特定关键词测试 ===")
    
    keywords = ["AI", "python", "machine learning", "chatgpt"]
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(20, 30))
        
        for keyword in keywords:
            print(f"测试关键词: {keyword}")
            try:
                pytrends.build_payload([keyword], timeframe='today 1-m')
                
                # 获取相关查询
                related_queries = pytrends.related_queries()
                print(f"✓ 相关查询获取成功: {keyword}")
                
                if keyword in related_queries:
                    rising = related_queries[keyword].get('rising')
                    top = related_queries[keyword].get('top')
                    print(f"  - Rising queries: {len(rising) if rising is not None else 0}")
                    print(f"  - Top queries: {len(top) if top is not None else 0}")
                
            except Exception as e:
                print(f"❌ 关键词 {keyword} 失败: {e}")
            
            time.sleep(3)  # 避免请求过快
            
    except Exception as e:
        print(f"❌ pytrends初始化失败: {e}")

def check_network_and_proxy():
    """检查网络和代理设置"""
    print("=== 网络和代理检查 ===")
    
    # 检查基本网络连接
    test_urls = [
        "https://www.google.com",
        "https://www.baidu.com",
        "https://httpbin.org/ip"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            print(f"✓ {url}: {response.status_code}")
        except Exception as e:
            print(f"❌ {url}: {e}")
    
    # 检查IP地址
    try:
        response = requests.get("https://httpbin.org/ip", timeout=10)
        ip_info = response.json()
        print(f"当前IP: {ip_info.get('origin', 'Unknown')}")
    except:
        print("无法获取IP信息")

def main():
    """主测试函数"""
    print("🔍 Google Trends API 连接诊断工具")
    print("=" * 60)
    
    # 1. 检查网络连接
    check_network_and_proxy()
    print()
    
    # 2. 直接API访问测试
    test_direct_api_access()
    print()
    
    # 3. pytrends连接测试
    success = test_pytrends_connection()
    print()
    
    # 4. 如果基础连接成功，测试特定关键词
    if success:
        test_specific_keywords()
    
    print("=" * 60)
    print("测试完成！")
    
    # 输出建议
    print("\n💡 问题排查建议:")
    print("1. 如果所有测试都失败，可能是网络连接问题")
    print("2. 如果只有特定关键词失败，可能是关键词格式问题")
    print("3. 如果出现429错误，说明请求频率过高，需要增加延迟")
    print("4. 如果出现400错误，可能是参数格式问题")
    print("5. 考虑使用VPN或代理服务器")

if __name__ == "__main__":
    main()