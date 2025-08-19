#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SEO集成使用示例
演示如何使用SEO增强版建站工具和SEO优化工具
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.website_builder.seo_enhanced_website_builder import SEOEnhancedWebsiteBuilder
from src.seo.website_seo_optimizer import WebsiteSEOOptimizer

def demo_seo_enhanced_website_builder():
    """演示SEO增强版网站建设工具"""
    print("=== SEO增强版网站建设工具演示 ===\n")
    
    # 创建示例数据
    sample_data_path = "data/test_intent_keywords.csv"
    output_dir = "seo_demo_output"
    
    # 检查示例数据是否存在
    if not os.path.exists(sample_data_path):
        print(f"示例数据文件不存在: {sample_data_path}")
        print("请先准备包含 'query' 和 'intent_primary' 列的CSV文件")
        return
    
    try:
        # 初始化SEO增强版建站工具
        builder = SEOEnhancedWebsiteBuilder(
            intent_data_path=sample_data_path,
            output_dir=output_dir,
            enable_seo=True
        )
        
        # 加载意图数据
        if not builder.load_intent_data():
            print("加载意图数据失败")
            return
        
        print(f"成功加载 {len(builder.intent_data)} 条关键词数据")
        
        # 生成SEO优化的网站
        print("\n1. 生成SEO优化的网站结构...")
        website_structure = builder.generate_seo_optimized_website()
        
        # 创建SEO增强的内容计划
        print("\n2. 创建SEO增强的内容计划...")
        content_plan = builder.create_seo_enhanced_content_plan()
        
        # 显示结果摘要
        print(f"\n=== 建站结果摘要 ===")
        print(f"网站结构文件: {output_dir}/seo_optimized_website_*.json")
        print(f"内容计划文件: {output_dir}/seo_enhanced_content_plan_*.json")
        
        if 'seo_report' in website_structure:
            seo_report = website_structure['seo_report']
            print(f"SEO覆盖率: {seo_report.get('seo_coverage_percentage', 0)}%")
            print(f"平均SEO评分: {seo_report.get('average_seo_score', 0)}")
        
        print(f"内容计划项目数: {len(content_plan)}")
        
        return website_structure
        
    except Exception as e:
        print(f"SEO增强版建站演示失败: {e}")
        return None

def demo_website_seo_optimizer():
    """演示网站SEO优化工具"""
    print("\n=== 网站SEO优化工具演示 ===\n")
    
    # 使用之前生成的网站结构文件
    website_files = []
    for root, dirs, files in os.walk("seo_demo_output"):
        for file in files:
            if file.startswith("seo_optimized_website_") and file.endswith(".json"):
                website_files.append(os.path.join(root, file))
    
    if not website_files:
        print("未找到网站结构文件，请先运行SEO增强版建站工具")
        return
    
    # 使用最新的网站文件
    latest_website_file = max(website_files, key=os.path.getmtime)
    print(f"使用网站文件: {latest_website_file}")
    
    try:
        # 初始化SEO优化工具
        optimizer = WebsiteSEOOptimizer("src/seo/seo_optimization_workflow.json")
        
        # 分析网站结构
        print("\n1. 分析网站结构...")
        analysis_result = optimizer.analyze_website_structure(latest_website_file)
        
        print(f"发现页面: {analysis_result['pages_found']}")
        print(f"SEO问题: {len(analysis_result['seo_issues'])}")
        
        if analysis_result['seo_issues']:
            print("主要SEO问题:")
            for issue in analysis_result['seo_issues'][:3]:
                print(f"  - {issue}")
        
        # 执行SEO优化
        print("\n2. 执行SEO优化...")
        optimization_results = optimizer.optimize_website(
            analysis_result['website_data'], 
            "seo_optimizer_output"
        )
        
        print(f"优化完成:")
        print(f"  成功优化: {optimization_results['pages_optimized']} 页面")
        print(f"  优化失败: {optimization_results['pages_failed']} 页面")
        
        return optimization_results
        
    except Exception as e:
        print(f"网站SEO优化演示失败: {e}")
        return None

def main():
    """主演示函数"""
    print("SEO集成工具演示\n")
    print("本演示将展示:")
    print("1. SEO增强版网站建设工具")
    print("2. 网站SEO优化工具")
    print("3. 完整的SEO工作流程")
    print("-" * 50)
    
    # 演示1: SEO增强版建站工具
    website_structure = demo_seo_enhanced_website_builder()
    
    # 演示2: 网站SEO优化工具
    if website_structure:
        optimization_results = demo_website_seo_optimizer()
    
    print("\n" + "=" * 50)
    print("演示完成!")
    print("\n生成的文件:")
    print("- seo_demo_output/: SEO增强版建站结果")
    print("- seo_optimizer_output/: SEO优化结果")
    print("\n使用方法:")
    print("1. 准备包含关键词和意图的CSV文件")
    print("2. 运行SEO增强版建站工具生成网站")
    print("3. 使用SEO优化工具进一步优化现有网站")

if __name__ == "__main__":
    main()