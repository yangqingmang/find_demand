#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场需求分析工具 - 统一执行入口
简化版本，专注于最终结果展示
"""

import argparse
import sys
import os
from datetime import datetime
from market_analyzer import MarketAnalyzer

def main():
    """主函数 - 提供简化的执行入口"""
    
    print("🚀 市场需求分析工具")
    print("=" * 50)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='市场需求分析工具 - 统一执行入口',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run_analysis.py "ai tools"
  python run_analysis.py "ai tools" --geo US
  python run_analysis.py "ai tools" "marketing automation" --geo US --timeframe "today 6-m"
        """
    )
    
    parser.add_argument('keywords', nargs='+', help='要分析的关键词（可以是多个）')
    parser.add_argument('--geo', default='', help='目标地区代码（如: US, GB, CN等），默认为全球')
    parser.add_argument('--timeframe', default='today 3-m', 
                       choices=['today 1-m', 'today 3-m', 'today 12-m', 'today 5-y'],
                       help='分析时间范围，默认为过去3个月')
    parser.add_argument('--output', default='data', help='输出目录，默认为data')
    parser.add_argument('--min-score', type=int, default=10, help='最低评分过滤，默认为10')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式，只显示最终结果')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细模式，显示所有中间过程')
    
    args = parser.parse_args()
    
    # 参数验证
    if not args.keywords:
        print("❌ 错误: 请至少提供一个关键词")
        sys.exit(1)
    
    # 显示分析参数
    if not args.quiet:
        print(f"📋 分析参数:")
        print(f"   关键词: {', '.join(args.keywords)}")
        print(f"   地区: {args.geo or '全球'}")
        print(f"   时间范围: {args.timeframe}")
        print(f"   最低评分: {args.min_score}")
        print(f"   输出目录: {args.output}")
        print()
    
    try:
        # 创建分析器
        analyzer = MarketAnalyzer(args.output)
        
        # 如果是静默模式，重定向日志输出
        if args.quiet:
            # 临时重定向stdout到文件
            import io
            from contextlib import redirect_stdout
            
            log_buffer = io.StringIO()
            with redirect_stdout(log_buffer):
                # 运行分析
                result = analyzer.run_analysis(
                    keywords=args.keywords,
                    geo=args.geo,
                    timeframe=args.timeframe,
                    min_score=args.min_score,
                    enrich=True
                )
        else:
            # 正常模式运行
            result = analyzer.run_analysis(
                keywords=args.keywords,
                geo=args.geo,
                timeframe=args.timeframe,
                min_score=args.min_score,
                enrich=True
            )
        
        # 检查结果
        if 'error' in result:
            print(f"❌ 分析失败: {result['error']}")
            sys.exit(1)
        
        # 如果是静默模式，只显示关键信息
        if args.quiet:
            print_quiet_summary(result)
        
        # 显示成功信息
        print(f"\n✅ 分析完成! 详细结果已保存到 {args.output} 目录")
        print(f"📊 分析报告: {result['输出文件']['分析报告'] if '分析报告' in result.get('输出文件', {}) else os.path.join(args.output, f'analysis_report_{datetime.now().strftime(\"%Y-%m-%d\")}.json')}")
        
    except KeyboardInterrupt:
        print("\n⚠️  分析被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def print_quiet_summary(result):
    """静默模式下的简要结果显示"""
    print("\n📊 分析结果摘要:")
    print(f"   • 关键词总数: {result.get('关键词总数', 0)}")
    print(f"   • 高分关键词: {result.get('高分关键词数', 0)}")
    print(f"   • 分析耗时: {result.get('分析耗时(秒)', 0)} 秒")
    
    # 显示Top 3关键词
    top_keywords = result.get('Top5关键词', [])[:3]
    if top_keywords:
        print(f"\n🏆 Top 3 关键词:")
        intent_names = {'I': '信息型', 'N': '导航型', 'C': '商业型', 'E': '交易型', 'B': '行为型'}
        for i, kw in enumerate(top_keywords):
            intent_name = intent_names.get(kw['intent'], kw['intent'])
            print(f"   {i+1}. {kw['query']} (分数: {kw['score']}, {intent_name})")

if __name__ == "__main__":
    main()