#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
需求挖掘分析工具 - 主入口文件
整合六大需求挖掘方法的统一执行入口
"""

import argparse
import sys
import os
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 导入统一的需求挖掘管理器
from src.demand_mining.unified_main import UnifiedDemandMiningManager as DemandMiningManager

# 导入增强功能模块
try:
    from src.utils.enhanced_features import (
        monitor_competitors, predict_keyword_trends, generate_seo_audit,
        batch_build_websites, setup_scheduler, run_scheduler
    )
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    ENHANCED_FEATURES_AVAILABLE = False
    print("⚠️ 增强功能模块未找到，部分功能将不可用")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场需求分析工具 - 主入口文件
Market Demand Analysis Toolkit - Main Entry Point
"""


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

def main():
    """主函数 - 提供统一的执行入口"""
    
    print("🔍 需求挖掘分析工具 v2.0")
    print("整合六大需求挖掘方法的智能分析系统")
    print("=" * 60)
    
    # 解析命令行参数
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
  
  # 分析单个关键词
  python main.py --keywords "ai generator" "ai converter"
  
  # 多平台关键词发现
  python main.py --discover "AI image generator" "AI writing tool"
  
  # 使用默认搜索词进行多平台发现
  python main.py --discover default
  
  # 生成分析报告
  python main.py --report

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

  # 设置定时任务
  python main.py --schedule daily --time "09:00" --action discover --run-scheduler
        """
    )
    
    # 输入方式选择 - 修改为非必需，支持默认词根分析
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument('--input', help='输入CSV文件路径')
    input_group.add_argument('--keywords', nargs='+', help='直接输入关键词（可以是多个）')
    input_group.add_argument('--discover', nargs='+', help='多平台关键词发现（可指定搜索词汇）')
    input_group.add_argument('--report', action='store_true', help='生成今日分析报告')
    
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
    
    # 调度功能组
    schedule_group = parser.add_argument_group('定时任务')
    schedule_group.add_argument('--schedule', choices=['daily', 'weekly', 'hourly'], help='设置定时任务')
    schedule_group.add_argument('--time', help='执行时间 (HH:MM)')
    schedule_group.add_argument('--action', help='定时执行的动作')
    schedule_group.add_argument('--run-scheduler', action='store_true', help='运行调度器')
    
    # 其他参数
    parser.add_argument('--output', default='src/demand_mining/reports', help='输出目录')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式，只显示最终结果')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细模式，显示所有中间过程')
    
    args = parser.parse_args()
    
    # 显示分析参数
    if not args.quiet:
        if args.input:
            print(f"📁 输入文件: {args.input}")
        elif args.keywords:
            print(f"🔤 分析关键词: {', '.join(args.keywords)}")
        elif args.report:
            print("📊 生成今日分析报告")
        print(f"📂 输出目录: {args.output}")
        print("")
    
    try:
        # 创建需求挖掘管理器
        manager = DemandMiningManager(args.config)
        
        if args.input:
            # 分析关键词文件
            if not args.quiet:
                print("🚀 开始分析关键词文件...")
            
            result = manager.analyze_keywords(args.input, args.output)
            
            # 显示结果
            if args.quiet:
                print_quiet_summary(result)
            else:
                print(f"\n🎉 分析完成! 共分析 {result['total_keywords']} 个关键词")
                print(f"📊 高机会关键词: {result['market_insights']['high_opportunity_count']} 个")
                print(f"📈 平均机会分数: {result['market_insights']['avg_opportunity_score']}")
                
                # 显示Top 5关键词
                top_keywords = result['market_insights']['top_opportunities'][:5]
                if top_keywords:
                    print("\n🏆 Top 5 机会关键词:")
                    for i, kw in enumerate(top_keywords, 1):
                        intent_desc = kw['intent']['intent_description']
                        score = kw['opportunity_score']
                        print(f"   {i}. {kw['keyword']} (分数: {score}, 意图: {intent_desc})")
        
        elif args.keywords:
            # 分析单个关键词
            if not args.quiet:
                print("🚀 开始分析输入的关键词...")
            
            # 创建临时CSV文件
            import pandas as pd
            import tempfile
            
            temp_df = pd.DataFrame([{'query': kw} for kw in args.keywords])
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
                temp_df.to_csv(f.name, index=False)
                temp_file = f.name
            
            try:
                result = manager.analyze_keywords(temp_file, args.output)
                
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
        
        elif args.discover:
            # 多平台关键词发现
            search_terms = args.discover if args.discover != ['default'] else ['AI tool', 'AI generator', 'AI assistant']
            
            if not args.quiet:
                print("🔍 开始多平台关键词发现...")
                print(f"📊 搜索词汇: {', '.join(search_terms)}")
            
            try:
                # 导入多平台发现工具
                from src.demand_mining.tools.multi_platform_keyword_discovery import MultiPlatformKeywordDiscovery
                
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
        
        elif args.monitor_competitors and ENHANCED_FEATURES_AVAILABLE:
            # 竞品监控
            sites = args.sites or ['canva.com', 'midjourney.com', 'openai.com']
            if not args.quiet:
                print(f"🔍 开始监控 {len(sites)} 个竞品网站...")
            
            result = monitor_competitors(sites, args.output)
            print(f"✅ 竞品监控完成: 分析了 {len(result['competitors'])} 个竞品")
            
            if not args.quiet:
                print("\n📊 监控结果摘要:")
                for comp in result['competitors'][:3]:
                    print(f"  • {comp['site']}: {comp['new_keywords_count']} 个新关键词")
        
        elif args.predict_trends and ENHANCED_FEATURES_AVAILABLE:
            # 趋势预测
            if not args.quiet:
                print(f"📈 开始预测未来 {args.timeframe} 的关键词趋势...")
            
            result = predict_keyword_trends(args.timeframe, args.output)
            print(f"✅ 趋势预测完成: 预测了 {len(result['rising_keywords'])} 个上升关键词")
            
            if not args.quiet:
                print("\n📈 趋势预测摘要:")
                for kw in result['rising_keywords'][:3]:
                    print(f"  📈 {kw['keyword']}: {kw['predicted_growth']} (置信度: {kw['confidence']:.0%})")
        
        elif args.seo_audit and ENHANCED_FEATURES_AVAILABLE:
            # SEO审计
            if not args.domain:
                print("❌ 请指定要审计的域名 (--domain)")
                return
            
            if not args.quiet:
                print(f"🔍 开始SEO审计: {args.domain}")
            
            result = generate_seo_audit(args.domain, args.keywords)
            print(f"✅ SEO审计完成: 发现 {len(result['keyword_opportunities'])} 个关键词机会")
            
            if not args.quiet:
                print("\n🎯 SEO优化建议:")
                for gap in result['content_gaps'][:3]:
                    print(f"  • {gap}")
        
        elif args.build_websites and ENHANCED_FEATURES_AVAILABLE:
            # 批量建站
            if not args.quiet:
                print(f"🏗️ 开始批量生成 {args.top_keywords} 个网站...")
            
            result = batch_build_websites(args.top_keywords, args.output)
            print(f"✅ 批量建站完成: 成功构建 {result['successful_builds']} 个网站")
            
            if not args.quiet:
                print("\n🌐 构建的网站:")
                for site in result['websites'][:3]:
                    print(f"  • {site['keyword']}: {site['domain_suggestion']}")
        
        elif args.schedule and ENHANCED_FEATURES_AVAILABLE:
            # 设置定时任务
            if not args.time or not args.action:
                print("❌ 请指定执行时间 (--time) 和动作 (--action)")
                return
            
            setup_scheduler(args.schedule, args.time, args.action)
            
            if args.run_scheduler:
                run_scheduler()
        
        elif args.run_scheduler and ENHANCED_FEATURES_AVAILABLE:
            # 仅运行调度器
            run_scheduler()
        
        elif args.report:
            # 生成分析报告
            if not args.quiet:
                print("📊 生成今日分析报告...")
            
            report_path = manager.generate_daily_report(args.date)
            print(f"✅ 报告已生成: {report_path}")
        
        else:
            # 默认：使用51个词根进行趋势分析
            if not args.quiet:
                print("🌱 开始使用51个词根进行趋势分析...")
            
            result = manager.analyze_root_words(args.output)
            
            # 显示结果
            if args.quiet:
                print_quiet_summary(result)
            else:
                print(f"\n🎉 词根趋势分析完成! 共分析 {result.get('total_root_words', 0)} 个词根")
                print(f"📊 成功分析: {result.get('successful_analyses', 0)} 个")
                print(f"📈 上升趋势词根: {len(result.get('top_trending_words', []))}")
                
                # 显示Top 5词根
                top_words = result.get('top_trending_words', [])[:5]
                if top_words:
                    print("\n🏆 Top 5 热门词根:")
                    for i, word_data in enumerate(top_words, 1):
                        print(f"   {i}. {word_data['word']}: 平均兴趣度 {word_data['average_interest']:.1f}")
        
        print(f"\n📁 详细结果已保存到 {args.output} 目录")
        
    except KeyboardInterrupt:
        print("\n⚠️ 分析被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()