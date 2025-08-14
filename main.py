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

# 导入最新的需求挖掘管理器
from src.demand_mining.demand_mining_main import DemandMiningManager
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
  
  # 生成分析报告
  python main.py --report
  
  # 静默模式分析
  python main.py --input data/keywords.csv --quiet
        """
    )
    
    # 输入方式选择 - 修改为非必需，支持默认词根分析
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument('--input', help='输入CSV文件路径')
    input_group.add_argument('--keywords', nargs='+', help='直接输入关键词（可以是多个）')
    input_group.add_argument('--report', action='store_true', help='生成今日分析报告')
    
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
        
        elif args.report:
            # 生成分析报告
            if not args.quiet:
                print("📊 生成今日分析报告...")
            
            report_path = manager.generate_daily_report()
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