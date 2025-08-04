#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SERP配置测试脚本
用于测试Google Custom Search API配置是否正确
"""

import sys
import os

# 添加src目录到Python路径
sys.path.append('src')

def test_config():
    """测试配置"""
    print("=== SERP配置测试 ===\n")
    
    try:
        from src.config.settings import Config
        
        print("1. 检查配置文件...")
        
        # 检查API密钥
        if Config.GOOGLE_API_KEY:
            print(f"✓ Google API Key: {Config.GOOGLE_API_KEY[:10]}...")
        else:
            print("✗ Google API Key 未配置")
            return False
        
        # 检查搜索引擎ID
        if Config.GOOGLE_CSE_ID and Config.GOOGLE_CSE_ID != "请替换为你的搜索引擎ID":
            print(f"✓ Google CSE ID: {Config.GOOGLE_CSE_ID}")
        else:
            print("✗ Google CSE ID 未配置或使用默认值")
            print("请访问 https://cse.google.com/cse/ 创建自定义搜索引擎")
            return False
        
        print("\n2. 测试SERP分析器初始化...")
        
        from src.analyzers.serp_analyzer import SerpAnalyzer
        
        analyzer = SerpAnalyzer()
        print("✓ SERP分析器初始化成功")
        
        print("\n3. 测试API连接...")
        
        # 测试简单搜索
        test_query = "Python教程"
        print(f"测试查询: {test_query}")
        
        result = analyzer.search_google(test_query, num_results=3)
        
        if result and 'items' in result:
            print(f"✓ API连接成功，返回 {len(result['items'])} 个结果")
            
            # 显示第一个结果
            if result['items']:
                first_item = result['items'][0]
                print(f"  第一个结果: {first_item.get('title', 'N/A')}")
                print(f"  URL: {first_item.get('link', 'N/A')}")
        else:
            print("✗ API连接失败或无结果返回")
            return False
        
        print("\n4. 测试SERP特征提取...")
        
        features = analyzer.extract_serp_features(result)
        print(f"✓ 提取到 {len(features)} 个特征")
        print(f"  有机结果数量: {features['organic_count']}")
        print(f"  总结果数: {features['total_results']}")
        print(f"  搜索时间: {features['search_time']}秒")
        
        print("\n5. 测试意图分析...")
        
        intent, confidence, secondary = analyzer.analyze_serp_intent(features)
        print(f"✓ 意图分析完成")
        print(f"  主要意图: {intent}")
        print(f"  置信度: {confidence}")
        print(f"  次要意图: {secondary}")
        
        print("\n=== 所有测试通过！ ===")
        print("SERP分析功能已准备就绪，可以开始使用。")
        
        return True
        
    except ImportError as e:
        print(f"✗ 导入错误: {e}")
        print("请确保所有必要的包都已安装")
        return False
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_intent_analyzer():
    """测试意图分析器"""
    print("\n=== 意图分析器测试 ===\n")
    
    try:
        from src.analyzers.intent_analyzer import IntentAnalyzer
        
        # 测试基础功能
        print("1. 测试基础意图分析...")
        analyzer = IntentAnalyzer(use_serp=False)
        
        test_keywords = ["如何学习Python", "购买iPhone", "最佳笔记本电脑"]
        
        for keyword in test_keywords:
            intent, confidence, secondary = analyzer.detect_intent_from_keyword(keyword)
            print(f"  {keyword}: {intent} (置信度: {confidence})")
        
        # 测试SERP增强功能
        print("\n2. 测试SERP增强意图分析...")
        serp_analyzer = IntentAnalyzer(use_serp=True)
        
        if serp_analyzer.use_serp:
            print("✓ SERP分析已启用")
            
            # 测试一个关键词
            test_keyword = "Python教程"
            print(f"测试关键词: {test_keyword}")
            
            intent, confidence, secondary = serp_analyzer.detect_intent_from_serp(test_keyword)
            print(f"  SERP分析结果: {intent} (置信度: {confidence})")
        else:
            print("✗ SERP分析未启用")
        
        print("\n=== 意图分析器测试完成 ===")
        return True
        
    except Exception as e:
        print(f"✗ 意图分析器测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始配置测试...\n")
    
    # 测试配置和SERP分析
    config_ok = test_config()
    
    if config_ok:
        # 测试意图分析器
        test_intent_analyzer()
    else:
        print("\n请先完成配置后再运行测试。")
        print("\n配置步骤:")
        print("1. 访问 https://cse.google.com/cse/ 创建自定义搜索引擎")
        print("2. 获取搜索引擎ID")
        print("3. 更新 config/.env 文件中的 GOOGLE_CSE_ID")