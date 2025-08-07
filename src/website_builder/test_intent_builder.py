#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试基于搜索意图的网站建设工具
"""

import os
import sys
import pandas as pd
from src.analyzers.intent_analyzer_v2 import IntentAnalyzerV2, analyze_single_keyword

def main():
    """主函数"""
    print("测试基于搜索意图的网站建设工具")
    
    # 创建意图分析器实例
    analyzer = IntentAnalyzerV2()
    
    # 测试关键词
    test_keywords = [
        "什么是Python",
        "Python教程",
        "Python vs Java",
        "Python官网",
        "Python下载",
        "最好的Python IDE",
        "Python IDE对比",
        "购买Python书籍",
        "Python书籍价格",
        "Python安装问题",
        "Python错误解决",
        "附近Python培训",
        "Python培训机构地址"
    ]
    
    # 创建DataFrame
    df = pd.DataFrame({'query': test_keywords})
    
    # 分析关键词
    analysis_results = analyzer.analyze_keywords(df, query_col='query')
    
    print("\n分析关键词意图:")
    for result in analysis_results['results']:
        print(f"关键词: {result['query']} -> 主意图: {result['intent_primary']} -> 子意图: {result['sub_intent']}")
    
    # 测试单个关键词分析函数
    print("\n测试单个关键词分析:")
    result = analyze_single_keyword("Python最佳实践")
    print(f"关键词: Python最佳实践 -> 主意图: {result['intent_primary']} -> 子意图: {result['sub_intent']}")
    
    print("\n测试完成")

if __name__ == "__main__":
    main()