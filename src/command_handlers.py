#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令处理器模块
处理各种命令行参数对应的功能
"""

import os
import sys
import tempfile
import pandas as pd
from datetime import datetime
from typing import Dict, Any

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.cli_parser import print_quiet_summary
from src.utils.enhanced_features import (
    monitor_competitors, predict_keyword_trends, generate_seo_audit,
    batch_build_websites
)
from src.demand_mining.tools.multi_platform_keyword_discovery import MultiPlatformKeywordDiscovery


def handle_stats_display(manager, args):
    """处理统计信息显示"""
    if args.stats:
        stats = manager.get_manager_stats()
        print("\n📊 管理器统计信息:")
        for manager_name, manager_stats in stats.items():
            if isinstance(manager_stats, dict):
                print(f"\n{manager_name}:")
                for key, value in manager_stats.items():
                    print(f"  {key}: {value}")
            else:
                print(f"{manager_name}: {manager_stats}")
        return True
    return False


def handle_input_file_analysis(manager, args):
    """处理关键词文件分析"""
    if not args.input:
        return False
        
    # 分析关键词文件
    if not args.quiet:
        print("🚀 开始分析关键词文件...")
        if args.serp:
            print("🔍 已启用SERP分析功能")
    
    result = manager.analyze_keywords(args.input, args.output, enable_serp=args.serp)
    
    # 显示结果
    if args.quiet:
        print_quiet_summary(result)
    else:
        print(f"\n🎉 分析完成! 共分析 {result['total_keywords']} 个关键词")
        print(f"📊 高机会关键词: {result['market_insights']['high_opportunity_count']} 个")
        print(f"📈 平均机会分数: {result['market_insights']['avg_opportunity_score']}")
        
        # 显示新词检测摘要
        if 'new_word_summary' in result and result['new_word_summary'].get('new_words_detected', 0) > 0:
            summary = result['new_word_summary']
            print(f"🔍 新词检测: 发现 {summary['new_words_detected']} 个新词 ({summary['new_word_percentage']}%)")
            print(f"   高置信度新词: {summary['high_confidence_new_words']} 个")

        # 显示SERP分析摘要
        if 'serp_summary' in result and result['serp_summary'].get('serp_analysis_enabled', False):
            serp_summary = result['serp_summary']
            print(f"🔍 SERP分析: 分析了 {serp_summary['total_analyzed']} 个关键词")
            print(f"   高置信度SERP: {serp_summary['high_confidence_serp']} 个")
            print(f"   商业意图关键词: {serp_summary['commercial_intent_keywords']} 个")

        # 显示Top 5关键词
        top_keywords = result['market_insights']['top_opportunities'][:5]
        if top_keywords:
            print("\n🏆 Top 5 机会关键词:")
            for i, kw in enumerate(top_keywords, 1):
                intent_desc = kw['intent']['intent_description']
                score = kw['opportunity_score']
                new_word_info = ""
                if 'new_word_detection' in kw and kw['new_word_detection']['is_new_word']:
                    new_word_grade = kw['new_word_detection']['new_word_grade']
                    new_word_info = f" [新词-{new_word_grade}级]"
                print(f"   {i}. {kw['keyword']} (分数: {score}, 意图: {intent_desc}){new_word_info}")
    
    return True


def handle_keywords_analysis(manager, args):
    """处理单个关键词分析"""
    if not args.keywords:
        return False
        
    # 分析单个关键词
    if not args.quiet:
        print("🚀 开始分析输入的关键词...")
    
    # 创建临时CSV文件
    temp_df = pd.DataFrame([{'query': kw} for kw in args.keywords])
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        temp_df.to_csv(f.name, index=False)
        temp_file = f.name
    
    try:
        result = manager.analyze_keywords(temp_file, args.output, enable_serp=args.serp)
        
        # 显示结果
        if args.quiet:
            print_quiet_summary(result)
        else:
            print(f"\n🎉 分析完成! 共分析 {len(args.keywords)} 个关键词")
            
            # 显示每个关键词的结果
            print("\n📋 关键词分析结果:")
            for kw_result in result['keywords']:
                keyword = kw_result['keyword']
                score = kw_result['opportunity_score']
                intent = kw_result['intent']['intent_description']
                print(f"   • {keyword}: 机会分数 {score}, 意图: {intent}")
    finally:
        # 清理临时文件
        os.unlink(temp_file)
    
    return True


def handle_discover_analysis(manager, args):
    """处理多平台关键词发现"""
    if not args.discover:
        return False
        
    # 多平台关键词发现
    search_terms = args.discover if args.discover != ['default'] else ['AI tool', 'AI generator', 'AI assistant']
    
    if not args.quiet:
        print("🔍 开始多平台关键词发现...")
        print(f"📊 搜索词汇: {', '.join(search_terms)}")
    
    try:
        # 创建发现工具
        discoverer = MultiPlatformKeywordDiscovery()
        
        # 执行发现
        df = discoverer.discover_all_platforms(search_terms)

        if not df.empty:
            # 分析趋势
            analysis = discoverer.analyze_keyword_trends(df)
            
            # 保存结果
            output_dir = os.path.join(args.output, 'multi_platform_discovery')
            csv_path, json_path = discoverer.save_results(df, analysis, output_dir)
            
            if args.quiet:
                # 静默模式显示
                print(f"\n🎯 多平台关键词发现结果:")
                print(f"   • 发现关键词: {analysis['total_keywords']} 个")
                print(f"   • 平台分布: {analysis['platform_distribution']}")
                
                # 显示Top 3关键词
                top_keywords = analysis['top_keywords_by_score'][:3]
                if top_keywords:
                    print("\n🏆 Top 3 热门关键词:")
                    for i, kw in enumerate(top_keywords, 1):
                        print(f"   {i}. {kw['keyword']} (评分: {kw['score']}, 来源: {kw['platform']})")
            else:
                # 详细模式显示
                print(f"\n🎉 多平台关键词发现完成!")
                print(f"📊 发现 {analysis['total_keywords']} 个关键词")
                print(f"🌐 平台分布: {analysis['platform_distribution']}")
                
                print(f"\n🏆 热门关键词:")
                for i, kw in enumerate(analysis['top_keywords_by_score'][:5], 1):
                    print(f"  {i}. {kw['keyword']} (评分: {kw['score']}, 来源: {kw['platform']})")
            
            print(f"\n📁 结果已保存:")
            print(f"  CSV: {csv_path}")
            print(f"  JSON: {json_path}")
            
            # 询问是否要立即分析发现的关键词
            if not args.quiet:
                user_input = input("\n🤔 是否要立即分析这些关键词的意图和市场机会? (y/n): ")
                if user_input.lower() in ['y', 'yes', '是']:
                    print("🔄 开始分析发现的关键词...")
                    result = manager.analyze_keywords(csv_path, args.output)
                    print(f"✅ 关键词分析完成! 共分析 {result['total_keywords']} 个关键词")
                    print(f"📊 高机会关键词: {result['market_insights']['high_opportunity_count']} 个")
        else:
            print("⚠️ 未发现任何关键词，请检查网络连接或调整搜索参数")
            
    except ImportError as e:
        print(f"❌ 导入多平台发现工具失败: {e}")
        print("请确保所有依赖已正确安装")
    except Exception as e:
        print(f"❌ 多平台关键词发现失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
    
    return True


def handle_enhanced_features(manager, args):
    """处理增强功能 (竞品监控、趋势预测、SEO审计、批量建站)"""
    # 竞品监控
    if args.monitor_competitors:
        sites = args.sites or ['canva.com', 'midjourney.com', 'openai.com']
        if not args.quiet:
            print(f"🔍 开始监控 {len(sites)} 个竞品网站...")
        
        result = monitor_competitors(sites, args.output)
        print(f"✅ 竞品监控完成: 分析了 {len(result['competitors'])} 个竞品")
        
        if not args.quiet:
            print("\n📊 监控结果摘要:")
            for comp in result['competitors'][:3]:
                print(f"  • {comp['site']}: {comp['new_keywords_count']} 个新关键词")
        return True
    
    # 趋势预测
    if args.predict_trends:
        if not args.quiet:
            print(f"📈 开始预测未来 {args.timeframe} 的关键词趋势...")
        
        result = predict_keyword_trends(args.timeframe, args.output)
        print(f"✅ 趋势预测完成: 预测了 {len(result['rising_keywords'])} 个上升关键词")
        
        if not args.quiet:
            print("\n📈 趋势预测摘要:")
            for kw in result['rising_keywords'][:3]:
                print(f"  📈 {kw['keyword']}: {kw['predicted_growth']} (置信度: {kw['confidence']:.0%})")
        return True
    
    # SEO审计
    if args.seo_audit:
        if not args.domain:
            print("❌ 请指定要审计的域名 (--domain)")
            return True
        
        if not args.quiet:
            print(f"🔍 开始SEO审计: {args.domain}")
        
        result = generate_seo_audit(args.domain, args.keywords)
        print(f"✅ SEO审计完成: 发现 {len(result['keyword_opportunities'])} 个关键词机会")
        
        if not args.quiet:
            print("\n🎯 SEO优化建议:")
            for gap in result['content_gaps'][:3]:
                print(f"  • {gap}")
        return True
    
    # 批量建站
    if args.build_websites:
        if not args.quiet:
            print(f"🏗️ 开始批量生成 {args.top_keywords} 个网站...")
        
        result = batch_build_websites(args.top_keywords, args.output)
        print(f"✅ 批量建站完成: 成功构建 {result['successful_builds']} 个网站")
        
        if not args.quiet:
            print("\n🌐 构建的网站:")
            for site in result['websites'][:3]:
                print(f"  • {site['keyword']}: {site['domain_suggestion']}")
        return True
    
    return False


def handle_hot_keywords(manager, args):
    """处理热门关键词搜索和需求挖掘"""
    if not args.hotkeywords:
        return False
    
    # 搜索热门关键词：使用 fetch_rising_queries 获取关键词并进行需求挖掘
    if not args.quiet:
        print("🔥 开始搜索热门关键词并进行需求挖掘...")
    
    try:
        # 使用单例获取 TrendsCollector
        from src.collectors.trends_singleton import get_trends_collector
        
        # 获取 TrendsCollector 单例实例
        trends_collector = get_trends_collector()
        
        # 使用 fetch_rising_queries 获取热门关键词
        if not args.quiet:
            print("🔍 正在获取 Rising Queries...")
        
        rising_queries = trends_collector.fetch_rising_queries()
        
        # 将 rising queries 转换为DataFrame格式
        if isinstance(rising_queries, pd.DataFrame):
            # 如果已经是DataFrame，直接使用
            trending_df = rising_queries.head(20)  # 限制前20个
            # 确保有query列
            if 'query' not in trending_df.columns:
                if 'title' in trending_df.columns:
                    trending_df = trending_df.rename(columns={'title': 'query'})
                elif len(trending_df.columns) > 0:
                    trending_df = trending_df.rename(columns={trending_df.columns[0]: 'query'})
        elif rising_queries and len(rising_queries) > 0:
            # 如果返回的是字符串列表
            if isinstance(rising_queries[0], str):
                trending_df = pd.DataFrame([
                    {'query': query}
                    for query in rising_queries[:20]  # 限制前20个
                ])
            # 如果返回的是字典列表
            elif isinstance(rising_queries[0], dict):
                trending_df = pd.DataFrame([
                    {
                        'query': item.get('query', item.get('keyword', str(item))),
                        'value': item.get('value', item.get('interest', 0))
                    }
                    for item in rising_queries[:20]  # 限制前20个
                ])
            else:
                # 其他格式，尝试转换为字符串
                trending_df = pd.DataFrame([
                    {'query': str(query)}
                    for query in rising_queries[:20]
                ])
        else:
            trending_df = pd.DataFrame(columns=['query'])

        if trending_df is not None and not trending_df.empty:
            # 保存热门关键词到临时文件
            
            # 确保DataFrame有正确的列名
            if 'query' not in trending_df.columns and len(trending_df.columns) > 0:
                # 如果没有query列，使用第一列作为关键词
                trending_df = trending_df.rename(columns={trending_df.columns[0]: 'query'})
            
            # 创建临时文件进行需求挖掘分析
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
                trending_df.to_csv(f.name, index=False)
                temp_file = f.name
            
            try:
                if not args.quiet:
                    print(f"🔍 获取到 {len(trending_df)} 个 Rising Queries，开始需求挖掘分析...")
                
                # 执行需求挖掘分析，禁用新词检测避免429错误
                manager.new_word_detection_available = False
                result = manager.analyze_keywords(temp_file, args.output, enable_serp=False)
                
                # 显示结果
                if args.quiet:
                    print_quiet_summary(result)
                else:
                    print(f"\n🎉 需求挖掘分析完成! 共分析 {result['total_keywords']} 个 Rising Queries")
                    print(f"📊 高机会关键词: {result['market_insights']['high_opportunity_count']} 个")
                    print(f"📈 平均机会分数: {result['market_insights']['avg_opportunity_score']}")
                    
                    # 显示新词检测摘要
                    if 'new_word_summary' in result and result['new_word_summary'].get('new_words_detected', 0) > 0:
                        summary = result['new_word_summary']
                        print(f"🔍 新词检测: 发现 {summary['new_words_detected']} 个新词 ({summary['new_word_percentage']}%)")
                        print(f"   高置信度新词: {summary['high_confidence_new_words']} 个")

                    # 显示Top 5机会关键词
                    top_keywords = result['market_insights']['top_opportunities'][:5]
                    if top_keywords:
                        print("\n🏆 Top 5 机会关键词:")
                        for i, kw in enumerate(top_keywords, 1):
                            intent_desc = kw['intent']['intent_description']
                            score = kw['opportunity_score']
                            new_word_info = ""
                            if 'new_word_detection' in kw and kw['new_word_detection']['is_new_word']:
                                new_word_grade = kw['new_word_detection']['new_word_grade']
                                new_word_info = f" [新词-{new_word_grade}级]"
                            print(f"   {i}. {kw['keyword']} (分数: {score}, 意图: {intent_desc}){new_word_info}")
                    
                    # 显示原始Rising Queries信息
                    print(f"\n🔥 原始 Rising Queries 数据:")
                    print(f"   • 数据来源: Google Trends Rising Queries")
                    if 'value' in trending_df.columns:
                        print(f"   • 平均热度: {trending_df['value'].mean():.1f}")
                    
                    # 保存原始Rising Queries
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    trending_output_file = os.path.join(args.output, f"rising_queries_raw_{timestamp}.csv")
                    os.makedirs(args.output, exist_ok=True)
                    trending_df.to_csv(trending_output_file, index=False, encoding='utf-8')
                    print(f"📁 原始 Rising Queries 已保存到: {trending_output_file}")
                
            finally:
                # 清理临时文件
                os.unlink(temp_file)
                
        else:
            # 当无法获取Rising Queries时，直接报告失败
            print("❌ 无法获取 Rising Queries，可能的原因:")
            print("💡 建议:")
            print("   1. 检查网络连接")
            print("   2. 稍后重试")
            print("   3. 或使用 --input 参数指定关键词文件进行分析")
            sys.exit(1)

    except Exception as e:
        print(f"❌ 获取 Rising Queries 或需求挖掘时出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
    
    return True


def handle_all_workflow(manager, args):
    """处理完整的关键词分析工作流程"""
    if not args.all:
        return False
    
    if not args.quiet:
        print("🚀 开始完整的关键词分析工作流程...")
        print("   第一步: 搜索热门关键词")
        print("   第二步: 基于热门关键词进行多平台发现")
    
    try:
        # 第一步：获取热门关键词
        from src.collectors.trends_singleton import get_trends_collector
        trends_collector = get_trends_collector()
        
        if not args.quiet:
            print("🔍 正在获取 Rising Queries...")
        
        rising_queries = trends_collector.fetch_rising_queries()
        
        # 处理获取到的热门关键词
        if isinstance(rising_queries, pd.DataFrame):
            trending_df = rising_queries.head(20)
            if 'query' not in trending_df.columns:
                if 'title' in trending_df.columns:
                    trending_df = trending_df.rename(columns={'title': 'query'})
                elif len(trending_df.columns) > 0:
                    trending_df = trending_df.rename(columns={trending_df.columns[0]: 'query'})
        elif rising_queries and len(rising_queries) > 0:
            if isinstance(rising_queries[0], str):
                trending_df = pd.DataFrame([
                    {'query': query}
                    for query in rising_queries[:20]
                ])
            elif isinstance(rising_queries[0], dict):
                trending_df = pd.DataFrame([
                    {
                        'query': item.get('query', item.get('keyword', str(item))),
                        'value': item.get('value', item.get('interest', 0))
                    }
                    for item in rising_queries[:20]
                ])
            else:
                trending_df = pd.DataFrame([
                    {'query': str(query)}
                    for query in rising_queries[:20]
                ])
        else:
            trending_df = pd.DataFrame(columns=['query'])
        
        if trending_df is not None and not trending_df.empty:
            # 确保DataFrame有正确的列名
            if 'query' not in trending_df.columns and len(trending_df.columns) > 0:
                trending_df = trending_df.rename(columns={trending_df.columns[0]: 'query'})
            
            # 第一步：对热门关键词进行需求挖掘
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
                trending_df.to_csv(f.name, index=False)
                temp_file = f.name
            
            try:
                if not args.quiet:
                    print(f"🔍 第一步: 对 {len(trending_df)} 个热门关键词进行需求挖掘...")
                
                # 执行需求挖掘分析
                manager.new_word_detection_available = False
                hot_result = manager.analyze_keywords(temp_file, args.output, enable_serp=False)
                
                if not args.quiet:
                    print(f"✅ 第一步完成! 分析了 {hot_result['total_keywords']} 个热门关键词")
                    print(f"📊 发现 {hot_result['market_insights']['high_opportunity_count']} 个高机会关键词")
                
                # 第二步：使用热门关键词作为种子进行多平台发现
                if not args.quiet:
                    print("\n🌐 第二步: 基于热门关键词进行多平台关键词发现...")
                
                # 获取前10个热门关键词作为种子
                seed_keywords = trending_df['query'].head(10).tolist()
                
                # 执行多平台关键词发现
                discovery_tool = MultiPlatformKeywordDiscovery()
                
                all_discovered_keywords = []
                for keyword in seed_keywords:
                    if not args.quiet:
                        print(f"🔍 正在发现与 '{keyword}' 相关的关键词...")
                    
                    discovered = discovery_tool.discover_keywords(
                        keyword,
                        platforms=['baidu', 'google', 'bing'],
                        max_keywords_per_platform=20
                    )
                    all_discovered_keywords.extend(discovered)
                
                # 去重并保存发现的关键词
                unique_keywords = list(set(all_discovered_keywords))
                
                if unique_keywords:
                    # 创建发现关键词的CSV文件
                    discovered_df = pd.DataFrame([
                        {'keyword': kw} for kw in unique_keywords
                    ])
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    discovered_file = os.path.join(args.output, f"discovered_keywords_{timestamp}.csv")
                    os.makedirs(args.output, exist_ok=True)
                    discovered_df.to_csv(discovered_file, index=False, encoding='utf-8')
                    
                    if not args.quiet:
                        print(f"🎯 发现了 {len(unique_keywords)} 个相关关键词")
                        print(f"📁 发现的关键词已保存到: {discovered_file}")
                    
                    # 对发现的关键词进行需求挖掘分析
                    if not args.quiet:
                        print(f"\n🔍 第三步: 对发现的关键词进行需求挖掘分析...")
                    
                    discovery_result = manager.analyze_keywords(discovered_file, args.output, enable_serp=False)
                    
                    # 显示最终结果
                    if args.quiet:
                        print_quiet_summary(discovery_result)
                    else:
                        print(f"\n🎉 完整工作流程完成!")
                        print(f"📊 热门关键词分析: {hot_result['total_keywords']} 个关键词")
                        print(f"🌐 多平台发现: {len(unique_keywords)} 个相关关键词")
                        print(f"🎯 最终分析: {discovery_result['total_keywords']} 个关键词")
                        print(f"🏆 总计高机会关键词: {discovery_result['market_insights']['high_opportunity_count']} 个")
                        print(f"📈 平均机会分数: {discovery_result['market_insights']['avg_opportunity_score']}")
                        
                        # 显示Top 5机会关键词
                        top_keywords = discovery_result['market_insights']['top_opportunities'][:5]
                        if top_keywords:
                            print("\n🏆 Top 5 最终机会关键词:")
                            for i, kw in enumerate(top_keywords, 1):
                                intent_desc = kw['intent']['intent_description']
                                score = kw['opportunity_score']
                                print(f"   {i}. {kw['keyword']} (分数: {score}, 意图: {intent_desc})")
                
                else:
                    if not args.quiet:
                        print("⚠️ 未发现相关关键词，仅显示热门关键词分析结果")
                    
                    if args.quiet:
                        print_quiet_summary(hot_result)
                    else:
                        print(f"\n🎉 热门关键词分析完成! 共分析 {hot_result['total_keywords']} 个关键词")
                        print(f"📊 高机会关键词: {hot_result['market_insights']['high_opportunity_count']} 个")
                        print(f"📈 平均机会分数: {hot_result['market_insights']['avg_opportunity_score']}")
                
            finally:
                # 清理临时文件
                os.unlink(temp_file)
        
        else:
            print("❌ 无法获取热门关键词，工作流程终止")
            print("💡 建议:")
            print("   1. 检查网络连接")
            print("   2. 稍后重试")
            print("   3. 或使用其他参数进行分析")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ 完整工作流程执行时出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
    
    return True


def handle_demand_validation(manager, args):
    """
    处理需求验证流程
    
    Args:
        manager: IntegratedDemandMiningManager实例
        args: 命令行参数
    """
    print("🔍 开始需求验证流程...")
    print("📋 第一步：获取高机会关键词")
    
    try:
        from src.collectors.trends_singleton import get_trends_collector
        trends_collector = get_trends_collector()
        rising_queries = trends_collector.fetch_rising_queries()
        
        if isinstance(rising_queries, pd.DataFrame):
            trending_df = rising_queries.head(20)
            if 'query' not in trending_df.columns:
                if 'title' in trending_df.columns:
                    trending_df = trending_df.rename(columns={'title': 'query'})
                elif len(trending_df.columns) > 0:
                    trending_df = trending_df.rename(columns={trending_df.columns[0]: 'query'})
        elif rising_queries and len(rising_queries) > 0:
            if isinstance(rising_queries[0], str):
                trending_df = pd.DataFrame([{'query': query} for query in rising_queries[:20]])
            elif isinstance(rising_queries[0], dict):
                trending_df = pd.DataFrame([{
                    'query': item.get('query', item.get('keyword', str(item))),
                    'value': item.get('value', item.get('interest', 0))
                } for item in rising_queries[:20]])
            else:
                trending_df = pd.DataFrame([{'query': str(query)} for query in rising_queries[:20]])
        else:
            trending_df = pd.DataFrame(columns=['query'])

        if trending_df is not None and not trending_df.empty:
            if 'query' not in trending_df.columns and len(trending_df.columns) > 0:
                trending_df = trending_df.rename(columns={trending_df.columns[0]: 'query'})
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
                trending_df.to_csv(f.name, index=False)
                temp_file = f.name
            
            try:
                print(f"🔍 获取到 {len(trending_df)} 个关键词，开始机会分析...")
                manager.new_word_detection_available = False
                keywords_result = manager.analyze_keywords(temp_file, args.output, enable_serp=False)
                
                print(f"✅ 第一步完成! 分析了 {keywords_result['total_keywords']} 个关键词")
                
                # 第二步：多平台需求验证
                print("\n📋 第二步：多平台需求验证")
                
                try:
                    # 确保能够导入模块
                    analyzer_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'demand_mining', 'analyzers')
                    if analyzer_path not in sys.path:
                        sys.path.insert(0, analyzer_path)
                    
                    from src.demand_mining.analyzers.multi_platform_demand_analyzer import MultiPlatformDemandAnalyzer
                    
                    # 创建多平台分析器
                    demand_analyzer = MultiPlatformDemandAnalyzer()
                    
                    # 执行多平台需求分析
                    import asyncio
                    demand_results = asyncio.run(demand_analyzer.analyze_high_opportunity_keywords(
                        keywords_result.get('keywords', []),
                        min_opportunity_score=60.0,  # 降低阈值以获取更多关键词
                        max_keywords=3  # 限制分析数量避免请求过多
                    ))
                    
                    # 保存需求验证结果
                    demand_output_file = demand_analyzer.save_results(demand_results)
                    
                    print(f"✅ 第二步完成! 需求验证分析完成")
                    print(f"📊 分析了 {demand_results.get('analyzed_keywords', 0)} 个高机会关键词")
                    
                    # 显示需求验证摘要
                    summary = demand_results.get('summary', {})
                    if summary:
                        print(f"\n🎯 需求验证摘要:")
                        print(f"   • 总搜索结果: {summary.get('total_search_results', 0)}")
                        print(f"   • 发现痛点: {summary.get('total_pain_points_found', 0)} 个")
                        print(f"   • 功能需求: {summary.get('total_feature_requests_found', 0)} 个")
                        
                        high_demand = summary.get('high_demand_keywords', [])
                        if high_demand:
                            print(f"   • 高需求关键词: {', '.join(high_demand)}")
                        
                        top_opportunities = summary.get('top_opportunities', [])[:3]
                        if top_opportunities:
                            print(f"\n🏆 Top 3 验证结果:")
                            for i, opp in enumerate(top_opportunities, 1):
                                print(f"   {i}. {opp['keyword']} - {opp['demand_level']} ({opp['pain_points_count']} 个痛点)")
                    
                    print(f"\n📁 需求验证结果已保存到: {demand_output_file}")
                    
                except ImportError:
                    print("⚠️ 多平台需求分析器未找到，请确保相关模块已安装")
                except Exception as e:
                    print(f"❌ 需求验证失败: {e}")
                    if args.verbose:
                        import traceback
                        traceback.print_exc()
                
            finally:
                os.unlink(temp_file)
                
        else:
            print("❌ 无法获取关键词进行需求验证")
            
    except Exception as e:
        print(f"❌ 需求验证流程失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()