#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Ads API 集成测试脚本
用于验证 Google Ads API 配置和功能
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_google_ads_import():
    """测试Google Ads包导入"""
    print("=== 测试 Google Ads 包导入 ===")
    try:
        from google.ads.googleads.client import GoogleAdsClient
        print("✓ google-ads 包导入成功")
        return True
    except ImportError as e:
        print(f"✗ google-ads 包导入失败: {e}")
        print("请运行: pip install google-ads==22.1.0")
        return False

def test_config():
    """测试配置"""
    print("\n=== 测试配置 ===")
    try:
        from src.config.settings import config
        
        # 显示基础配置状态
        print("基础配置状态:")
        print(f"  Google API Key: {'✓ 已配置' if config.GOOGLE_API_KEY else '✗ 未配置'}")
        print(f"  Google CSE ID: {'✓ 已配置' if config.GOOGLE_CSE_ID else '✗ 未配置'}")
        
        # 显示Google Ads配置状态
        print("\nGoogle Ads API 配置状态:")
        print(f"  Developer Token: {'✓ 已配置' if config.GOOGLE_ADS_DEVELOPER_TOKEN else '✗ 未配置'}")
        print(f"  Client ID: {'✓ 已配置' if config.GOOGLE_ADS_CLIENT_ID else '✗ 未配置'}")
        print(f"  Client Secret: {'✓ 已配置' if config.GOOGLE_ADS_CLIENT_SECRET else '✗ 未配置'}")
        print(f"  Refresh Token: {'✓ 已配置' if config.GOOGLE_ADS_REFRESH_TOKEN else '✗ 未配置'}")
        print(f"  Customer ID: {'✓ 已配置' if config.GOOGLE_ADS_CUSTOMER_ID else '✗ 未配置'}")
        
        # 检查是否可以进行Google Ads API测试
        ads_configured = all([
            config.GOOGLE_ADS_DEVELOPER_TOKEN,
            config.GOOGLE_ADS_CLIENT_ID,
            config.GOOGLE_ADS_CLIENT_SECRET,
            config.GOOGLE_ADS_REFRESH_TOKEN,
            config.GOOGLE_ADS_CUSTOMER_ID
        ])
        
        if ads_configured:
            print("\n✓ Google Ads API 配置完整，可以进行API测试")
            return True
        else:
            print("\n⚠ Google Ads API 配置不完整，请运行 python setup_config.py 进行配置")
            return False
            
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False

def test_ads_collector():
    """测试Google Ads数据采集器"""
    print("\n=== 测试 Google Ads 数据采集器 ===")
    try:
        from src.collectors.ads_collector import AdsCollector
        
        # 创建采集器实例
        collector = AdsCollector()
        print("✓ Google Ads 采集器创建成功")
        
        # 测试关键词
        test_keywords = ['ai tools']
        print(f"测试关键词: {test_keywords}")
        
        # 获取关键词数据
        print("正在获取关键词数据...")
        df = collector.get_keyword_ideas(test_keywords, geo_target='US')
        
        if not df.empty:
            print(f"✓ 成功获取 {len(df)} 个关键词数据")
            print("\n前3个结果:")
            print(df.head(3)[['keyword', 'avg_monthly_searches', 'competition', 'avg_cpc']])
            
            # 保存测试结果
            filepath = collector.save_results(df, 'data')
            print(f"\n测试结果已保存到: {filepath}")
            
            return True
        else:
            print("✗ 未获取到关键词数据")
            return False
            
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        print("请确保已安装 google-ads 包: pip install google-ads==22.1.0")
        return False
    except ValueError as e:
        print(f"✗ 配置错误: {e}")
        return False
    except Exception as e:
        print(f"✗ API测试失败: {e}")
        print("\n可能的原因:")
        print("1. API密钥配置错误")
        print("2. Google Ads账户权限不足")
        print("3. API配额已用完")
        print("4. 网络连接问题")
        return False

def test_integration_with_main_analyzer():
    """测试与主分析器的集成"""
    print("\n=== 测试与主分析器集成 ===")
    try:
        from src.core.market_analyzer import MarketAnalyzer
        
        # 创建分析器
        analyzer = MarketAnalyzer()
        print("✓ 主分析器创建成功")
        
        # 测试是否可以集成Google Ads数据
        # 这里只是测试导入，不实际运行分析
        print("✓ Google Ads 集成准备就绪")
        
        return True
        
    except Exception as e:
        print(f"✗ 集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("Google Ads API 集成测试")
    print("=" * 50)
    
    # 测试结果
    results = []
    
    # 1. 测试包导入
    results.append(test_google_ads_import())
    
    # 2. 测试配置
    config_ok = test_config()
    results.append(config_ok)
    
    # 3. 如果配置正确，测试API功能
    if config_ok and results[0]:  # 包导入成功且配置正确
        results.append(test_ads_collector())
    else:
        print("\n⚠ 跳过API功能测试（配置不完整或包未安装）")
        results.append(False)
    
    # 4. 测试集成
    results.append(test_integration_with_main_analyzer())
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"  包导入: {'✓ 通过' if results[0] else '✗ 失败'}")
    print(f"  配置检查: {'✓ 通过' if results[1] else '✗ 失败'}")
    print(f"  API功能: {'✓ 通过' if results[2] else '✗ 失败'}")
    print(f"  集成测试: {'✓ 通过' if results[3] else '✗ 失败'}")
    
    if all(results):
        print("\n🎉 所有测试通过！Google Ads API 集成成功！")
        print("\n下一步:")
        print("1. 在主分析中使用: python main.py \"关键词\" --use-ads-data")
        print("2. 查看详细文档: docs/Google_Ads_API_集成指南.md")
    else:
        print("\n❌ 部分测试失败，请检查上述错误信息")
        print("\n解决方案:")
        if not results[0]:
            print("- 安装Google Ads包: pip install google-ads==22.1.0")
        if not results[1]:
            print("- 配置API密钥: python setup_config.py")
        if not results[2]:
            print("- 检查API密钥和权限")
            print("- 查看详细指南: docs/Google_Ads_API_集成指南.md")

if __name__ == "__main__":
    main()