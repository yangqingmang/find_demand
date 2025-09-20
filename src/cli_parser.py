#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行参数解析器模块
提供统一的命令行参数解析功能
"""

import argparse
import os
import json


def get_reports_dir() -> str:
    """从配置文件获取报告输出目录"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config/integrated_workflow_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('output_settings', {}).get('reports_dir', 'output/reports')
    except:
        pass
    return 'output/reports'


def setup_argument_parser():
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='需求挖掘分析工具 - 整合六大挖掘方法',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            🎯 六大需求挖掘方法:
              1. 基于词根关键词拓展 (52个核心词根)
              2. 基于SEO大站流量分析 (8个竞品网站)
              3. 搜索引擎下拉推荐
              4. 循环挖掘法
              5. 付费广告关键词分析
              6. 收入排行榜分析
            
            📋 使用示例:
              # 分析关键词文件
              python main.py --input data/keywords.csv
              
              # 分析关键词文件并启用SERP分析
              python main.py --input data/keywords.csv --serp
              
              # 分析单个关键词
              python main.py --keywords "ai generator" "ai converter"
              
              # 分析单个关键词并启用SERP分析
              python main.py --keywords "AI" --serp
              
              # 多平台关键词发现
              python main.py --discover "AI image generator" "AI writing tool"
              
              # 使用默认搜索词进行多平台发现
              python main.py --discover default
              
              # 生成分析报告
              python main.py --report
            
              # 使用51个词根进行趋势分析
              python main.py --use-root-words
            
              # 静默模式分析
              python main.py --input data/keywords.csv --quiet
            
            🚀 增强功能示例:
              # 监控竞品关键词变化
              python main.py --monitor-competitors --sites canva.com midjourney.com
            
              # 预测关键词趋势
              python main.py --predict-trends --timeframe 30d
            
              # SEO审计
              python main.py --seo-audit --domain your-site.com --keywords "ai tool" "ai generator"
            
              # 批量生成网站
              python main.py --build-websites --top-keywords 5
        """
    )
    
    # 输入方式选择 - 修改为非必需，支持默认词根分析
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument('--input', help='输入CSV文件路径')
    input_group.add_argument('--keywords', nargs='+', help='直接输入关键词（可以是多个）')
    input_group.add_argument('--discover', nargs='+', help='多平台关键词发现（可指定搜索词汇）')
    input_group.add_argument('--report', action='store_true', help='生成今日分析报告')
    input_group.add_argument('--hotkeywords', action='store_true', help='搜索热门关键词 (Google Trends)')
    input_group.add_argument('--trending-keywords', action='store_true', help='获取TrendingKeywords.net热门关键词')
    input_group.add_argument('--all', action='store_true', help='完整流程：整合多数据源搜索热门关键词，再进行多平台发现')
    input_group.add_argument('--demand-validation', action='store_true', help='需求验证：对高机会关键词进行多平台需求分析')
    input_group.add_argument('--expand', nargs='+', help='增强关键词扩展：使用Google自动完成、Trends相关搜索和语义相似词扩展')
    
    # 增强功能组
    enhanced_group = parser.add_argument_group('增强功能')
    enhanced_group.add_argument('--monitor-competitors', action='store_true', help='监控竞品关键词变化')
    enhanced_group.add_argument('--sites', nargs='+', help='竞品网站列表')
    enhanced_group.add_argument('--predict-trends', action='store_true', help='预测关键词趋势')
    enhanced_group.add_argument('--timeframe', default='30d', help='预测时间范围')
    enhanced_group.add_argument('--seo-audit', action='store_true', help='生成SEO优化建议')
    enhanced_group.add_argument('--domain', help='要审计的域名')
    enhanced_group.add_argument('--build-websites', action='store_true', help='批量生成网站')
    enhanced_group.add_argument('--top-keywords', type=int, default=10, help='使用前N个关键词')

    # 其他参数
    parser.add_argument('--output', default=get_reports_dir(), help='输出目录')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式，只显示最终结果')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细模式，显示所有中间过程')
    parser.add_argument('--stats', action='store_true', help='显示管理器统计信息')
    parser.add_argument('--use-root-words', action='store_true', help='使用51个词根进行趋势分析')
    parser.add_argument('--serp', action='store_true', help='启用SERP分析功能')
    parser.add_argument('--seed-profile', help='指定配置中的种子关键词档案（用于多平台发现）')
    parser.add_argument('--seed-limit', type=int, help='限制多平台发现阶段使用的种子关键词数量')
    parser.add_argument('--min-seed-terms', type=int, help='确保至少使用的种子关键词数量')

    return parser


def display_analysis_parameters(args):
    """显示分析参数"""
    if not args.quiet:
        if args.input:
            print(f"📁 输入文件: {args.input}")
        elif args.keywords:
            print(f"🔤 分析关键词: {', '.join(args.keywords)}")
        elif args.report:
            print("📊 生成今日分析报告")
        if getattr(args, 'seed_profile', None):
            print(f"🌱 种子配置: {args.seed_profile}")
        print(f"📂 输出目录: {args.output}")
        print("")


def print_quiet_summary(result):
    """静默模式下的简要结果显示"""
    print("\n🎯 需求挖掘分析结果摘要:")
    print(f"   • 关键词总数: {result.get('total_keywords', 0)}")
    print(f"   • 高机会关键词: {result.get('market_insights', {}).get('high_opportunity_count', 0)}")
    print(f"   • 平均机会分数: {result.get('market_insights', {}).get('avg_opportunity_score', 0)}")
    
    # 显示Top 3关键词
    top_keywords = result.get('market_insights', {}).get('top_opportunities', [])[:3]
    if top_keywords:
        print("\n🏆 Top 3 机会关键词:")
        for i, kw in enumerate(top_keywords):
            intent_desc = kw.get('intent', {}).get('intent_description', '未知')
            score = kw.get('opportunity_score', 0)
            print(f"   {i+1}. {kw['keyword']} (机会分数: {score}, 意图: {intent_desc})")
