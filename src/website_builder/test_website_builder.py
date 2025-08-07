#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试基于搜索意图的网站建设工具
"""

import os
import sys
import pandas as pd
from intent_based_website_builder import IntentBasedWebsiteBuilder

def main():
    """主函数"""
    print("测试基于搜索意图的网站建设工具")
    
    # 创建输出目录
    os.makedirs("output", exist_ok=True)
    
    # 创建测试数据
    test_data = {
        'query': [
            "什么是Python", "Python教程", "Python vs Java", 
            "Python官网", "Python下载", "最好的Python IDE",
            "Python IDE对比", "购买Python书籍", "Python书籍价格",
            "Python安装问题", "Python错误解决", "附近Python培训"
        ],
        'intent_primary': [
            "I", "I", "C", "N", "N", "C", "C", "E", "E", "B", "B", "L"
        ],
        'sub_intent': [
            "I1", "I3", "C2", "N1", "N3", "C1", "C2", "E3", "E1", "B1", "B1", "L1"
        ]
    }
    
    # 创建DataFrame
    df = pd.DataFrame(test_data)
    
    # 保存为CSV文件
    test_file = "test_intent_data.csv"
    df.to_csv(test_file, index=False)
    print(f"已创建测试数据文件: {test_file}")
    
    try:
        # 创建网站建设工具实例
        builder = IntentBasedWebsiteBuilder(
            intent_data_path=test_file,
            output_dir="output"
        )
        
        # 加载意图数据
        if builder.load_intent_data():
            print("成功加载意图数据")
            
            # 生成网站结构
            builder.generate_website_structure()
            print("成功生成网站结构")
            
            # 创建内容计划
            builder.create_content_plan()
            print("成功创建内容计划")
            
            print("测试成功完成")
        else:
            print("加载意图数据失败")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()