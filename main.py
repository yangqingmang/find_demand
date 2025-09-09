#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
需求挖掘分析工具 - 统一主入口文件
整合六大需求挖掘方法的完整执行入口
"""

import sys
import os
import time

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 导入重构后的模块
from src.cli_parser import setup_argument_parser, display_analysis_parameters, print_quiet_summary
from src.demand_mining_manager import IntegratedDemandMiningManager
from src.command_handlers import (
    handle_stats_display, handle_input_file_analysis, handle_keywords_analysis,
    handle_discover_analysis, handle_enhanced_features, handle_hot_keywords,
    handle_all_workflow, handle_demand_validation
)


def main():
    """主函数 - 提供统一的执行入口"""
    print("🔍 需求挖掘分析工具 v2.0")
    print("整合六大需求挖掘方法的智能分析系统")
    print("=" * 60)
    
    # 解析命令行参数
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # 显示分析参数
    display_analysis_parameters(args)
    
    try:
        # 创建集成需求挖掘管理器
        manager = IntegratedDemandMiningManager(args.config)
        
        # 显示管理器统计信息
        if handle_stats_display(manager, args):
            return
        
        if handle_input_file_analysis(manager, args):
            return
        
        elif handle_keywords_analysis(manager, args):
            # 如果同时指定了predict-trends，在关键词分析完成后执行趋势预测
            if args.predict_trends:
                print("\n📈 关键词分析完成，现在执行趋势预测...")
                time.sleep(3)  # 添加间隔避免API冲突
                handle_enhanced_features(manager, args)
            return
        
        elif handle_discover_analysis(manager, args):
            return
        
        elif handle_enhanced_features(manager, args):
            return

        elif args.report:
            # 生成分析报告
            if not args.quiet:
                print("📊 生成今日分析报告...")
            
            report_path = manager.generate_daily_report()
            print(f"✅ 报告已生成: {report_path}")
        
        elif args.use_root_words:
            # 使用51个词根进行趋势分析
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
        
        elif handle_hot_keywords(manager, args):
            return
        
        elif handle_all_workflow(manager, args):
            return
        
        elif args.expand:
            # 增强关键词扩展
            if not args.quiet:
                print("🚀 开始增强关键词扩展...")
                print(f"🌱 种子关键词: {', '.join(args.expand)}")
            
            result = manager.expand_keywords_comprehensive(
                args.expand, 
                output_dir=args.output,
                max_expanded=200,
                max_longtails=100
            )
            
            if 'error' in result:
                print(f"❌ 关键词扩展失败: {result['error']}")
            else:
                if args.quiet:
                    print(f"🎯 关键词扩展结果:")
                    print(f"   • 种子关键词: {result['summary']['seed_count']}")
                    print(f"   • 扩展关键词: {result['summary']['expanded_count']}")
                    print(f"   • 长尾关键词: {result['summary']['longtail_count']}")
                    print(f"   • 总关键词数: {result['summary']['total_count']}")
                    print(f"   • 扩展倍数: {result['summary']['expansion_ratio']:.1f}x")
                    
                    # 显示Top 5扩展关键词
                    if result['expanded_keywords']:
                        print(f"🏆 Top 5 扩展关键词:")
                        for i, kw in enumerate(result['expanded_keywords'][:5], 1):
                            print(f"   {i}. {kw}")
                    
                    # 显示Top 5长尾关键词
                    if result['longtail_keywords']:
                        print(f"🔗 Top 5 长尾关键词:")
                        for i, kw in enumerate(result['longtail_keywords'][:5], 1):
                            print(f"   {i}. {kw}")
                else:
                    print(f"🎉 增强关键词扩展完成!")
                    print(f"📊 扩展统计:")
                    for key, value in result['summary'].items():
                        print(f"   {key}: {value}")
                    
                    if 'output_files' in result:
                        print(f"📁 结果文件:")
                        for file_type, file_path in result['output_files'].items():
                            print(f"   {file_type}: {file_path}")
        
        elif args.demand_validation:
            handle_demand_validation(manager, args)
        
        else:
            # 无参数时显示帮助信息
            parser.print_help()
            return
        
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