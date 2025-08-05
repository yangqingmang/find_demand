#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SERP配置测试脚本
用于测试Google Custom Search API配置是否正确
"""

import sys
import sys
import os

# 添加src目录到Python路径
sys.path.append('src')

from src.utils import Logger

def test_config():
    """测试配置"""
    logger = Logger()
    logger.info("=== SERP配置测试 ===")
    
    try:
        from src.config.settings import Config
        
        print("1. 检查配置文件...")
        logger.info("1. 检查配置文件...")
        
        # 检查API密钥
        if Config.GOOGLE_API_KEY:
            logger.info(f"✓ Google API Key: {Config.GOOGLE_API_KEY[:10]}...")
        else:
            logger.error("✗ Google API Key 未配置")
            return False
        
        # 检查搜索引擎ID
        if Config.GOOGLE_CSE_ID and Config.GOOGLE_CSE_ID != "请替换为你的搜索引擎ID":
            logger.info(f"✓ Google CSE ID: {Config.GOOGLE_CSE_ID}")
        else:
            logger.error("✗ Google CSE ID 未配置或使用默认值")
            logger.info("请访问 https://cse.google.com/cse/ 创建自定义搜索引擎")
            return False
        
        print("\n2. 测试SERP分析器初始化...")
        logger.info("2. 测试SERP分析器初始化...")
        
        from src.analyzers.serp_analyzer import SerpAnalyzer
        
        analyzer = SerpAnalyzer()
        logger.info("✓ SERP分析器初始化成功")
        
        logger.info("3. 测试API连接...")
        
        # 测试简单搜索
        test_query = "Python教程"
        logger.info(f"测试查询: {test_query}")
        
        result = analyzer.search_google(test_query, num_results=3)
        
        if result and 'items' in result:
        if result and 'items' in result:
            logger.info(f"✓ API连接成功，返回 {len(result['items'])} 个结果")
            
            # 显示第一个结果
            if result['items']:
                first_item = result['items'][0]
                logger.info(f"  第一个结果: {first_item.get('title', 'N/A')}")
                logger.info(f"  URL: {first_item.get('link', 'N/A')}")
        else:
            logger.error("✗ API连接失败或无结果返回")
            return False
        
        logger.info("4. 测试SERP特征提取...")
        
        features = analyzer.extract_serp_features(result)
        logger.info(f"✓ 提取到 {len(features)} 个特征")
        logger.info(f"  有机结果数量: {features['organic_count']}")
        logger.info(f"  总结果数: {features['total_results']}")
        logger.info(f"  搜索时间: {features['search_time']}秒")
        
        logger.info("5. 测试意图分析...")
        
        intent, confidence, secondary = analyzer.analyze_serp_intent(features)
        logger.info(f"✓ 意图分析完成")
        logger.info(f"  主要意图: {intent}")
        logger.info(f"  置信度: {confidence}")
        logger.info(f"  次要意图: {secondary}")
        
        logger.info("=== 所有测试通过！ ===")
        logger.info("SERP分析功能已准备就绪，可以开始使用。")
        
        return True
        
    except ImportError as e:
    except ImportError as e:
        logger.error(f"✗ 导入错误: {e}")
        logger.info("请确保所有必要的包都已安装")
        return False
        
    except Exception as e:
        logger.error(f"✗ 测试失败: {e}")
        return False

def test_intent_analyzer():
    """测试意图分析器"""
    logger = Logger()
    logger.info("=== 意图分析器测试 ===")
    
    try:
        from src.analyzers.intent_analyzer import IntentAnalyzer
        
        # 测试基础功能
        # 测试基础功能
        logger.info("1. 测试基础意图分析...")
        analyzer = IntentAnalyzer(use_serp=False)
        
        test_keywords = ["如何学习Python", "购买iPhone", "最佳笔记本电脑"]
        
        for keyword in test_keywords:
            intent, confidence, secondary = analyzer.detect_intent_from_keyword(keyword)
            logger.info(f"  {keyword}: {intent} (置信度: {confidence})")
        
        # 测试SERP增强功能
        logger.info("2. 测试SERP增强意图分析...")
        serp_analyzer = IntentAnalyzer(use_serp=True)
        
        if serp_analyzer.use_serp:
            logger.info("✓ SERP分析已启用")
            
            # 测试一个关键词
            test_keyword = "Python教程"
            logger.info(f"测试关键词: {test_keyword}")
            
            intent, confidence, secondary = serp_analyzer.detect_intent_from_serp(test_keyword)
            logger.info(f"  SERP分析结果: {intent} (置信度: {confidence})")
        else:
            logger.warning("✗ SERP分析未启用")
        
        logger.info("=== 意图分析器测试完成 ===")
        return True
        
    except Exception as e:
        logger.error(f"✗ 意图分析器测试失败: {e}")
        return False

if __name__ == "__main__":
    main_logger = Logger()
    main_logger.info("开始配置测试...")
    
    # 测试配置和SERP分析
    config_ok = test_config()
    
    if config_ok:
    if config_ok:
        # 测试意图分析器
        test_intent_analyzer()
    else:
        main_logger.warning("请先完成配置后再运行测试。")
        main_logger.info("配置步骤:")
        main_logger.info("1. 访问 https://cse.google.com/cse/ 创建自定义搜索引擎")
        main_logger.info("2. 获取搜索引擎ID")
        main_logger.info("3. 更新 config/.env 文件中的 GOOGLE_CSE_ID")
