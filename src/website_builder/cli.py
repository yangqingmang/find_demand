#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于搜索意图的网站自动建设工具命令行接口
"""

import os
import sys
import argparse
from src.website_builder.simple_intent_website_builder import SimpleIntentWebsiteBuilder

def main():
    """命令行入口函数"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='基于搜索意图的网站自动建设工具')
    
    # 添加命令行参数
    parser.add_argument('--input', '-i', type=str, help='输入文件路径（CSV或JSON）')
    parser.add_argument('--output', '-o', type=str, default='output', help='输出目录路径')
    parser.add_argument('--action', '-a', type=str, choices=['analyze', 'structure', 'content', 'all'], 
                        default='all', help='执行的操作')
    parser.add_argument('--version', '-v', action='version', version='基于搜索意图的网站自动建设工具 v1.0.0')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 检查必要参数
    if not args.input:
        parser.error("必须提供输入文件(--input)")
    
    # 创建网站建设工具实例
    builder = SimpleIntentWebsiteBuilder(
        intent_data_path=args.input,
        output_dir=args.output
    )
    
    # 加载意图数据
    if not builder.load_intent_data():
        print("加载意图数据失败，程序退出")
        return 1
    
    # 执行请求的操作
    if args.action == 'analyze' or args.action == 'all':
        # 已经在前面完成了分析
        pass
    
    if args.action == 'structure' or args.action == 'all':
        # 生成网站结构
        builder.generate_website_structure()
    
    if args.action == 'content' or args.action == 'all':
        # 创建内容计划
        builder.create_content_plan()
    
    print("操作完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())