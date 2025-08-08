#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于搜索意图的网站自动建设工具 - 主入口文件
这个文件现在只是一个简单的入口，实际功能已经拆分到各个模块中
"""

import sys
import argparse

# 导入所有必要的类和函数
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.website_builder.builder_core import IntentBasedWebsiteBuilder

# 为了保持向后兼容性，我们重新导出主要的类
__all__ = ['IntentBasedWebsiteBuilder']

def main():
    """主函数 - 提供命令行接口"""
    parser = argparse.ArgumentParser(description='基于搜索意图的网站自动建设工具')
    
    parser.add_argument('--input', '-i', type=str, help='输入文件路径（CSV或JSON）')
    parser.add_argument('--output', '-o', type=str, default='output', help='输出目录路径')
    parser.add_argument('--action', '-a', type=str, 
                        choices=['analyze', 'structure', 'content', 'all'], 
                        default='all', help='执行的操作')
    parser.add_argument('--version', '-v', action='version', 
                        version='基于搜索意图的网站自动建设工具 v2.0.0 (模块化版本)')
    
    args = parser.parse_args()
    
    if not args.input:
        parser.error("必须提供输入文件(--input)")
    
    try:
        builder = IntentBasedWebsiteBuilder(
            intent_data_path=args.input,
            output_dir=args.output
        )
        
        if not builder.load_intent_data():
            print("加载意图数据失败，程序退出")
            return 1
        
        if args.action == 'analyze' or args.action == 'all':
            print("意图数据分析完成")
        
        if args.action == 'structure' or args.action == 'all':
            structure = builder.generate_website_structure()
            if structure:
                print("网站结构生成完成")
            else:
                print("网站结构生成失败")
                return 1
        
        if args.action == 'content' or args.action == 'all':
        if args.action == 'content' or args.action == 'all':
            content_plan = builder.create_content_plan()
            if content_plan:
                print("内容计划创建完成")
            else:
                print("内容计划创建失败")
                return 1
        
        # 部署功能
        if args.deploy or args.action == 'deploy':
            # 准备自定义配置
            custom_config = {}
            if args.project_name:
                custom_config['project_name'] = args.project_name
            if args.custom_domain:
                custom_config['custom_domain'] = args.custom_domain
            
            success, result = builder.deploy_website(
                deployer_name=args.deployer,
                custom_config=custom_config if custom_config else None
            )
            
            if not success:
                print(f"部署失败: {result}")
                return 1
        
        print("所有操作完成成功！")
        return 0
        
    except Exception as e:
        print(f"执行过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())