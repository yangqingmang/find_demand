#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场需求分析工具 - 主入口文件
Market Demand Analysis Toolkit - Main Entry Point
"""

import argparse
import sys
import os
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.market_analyzer import MarketAnalyzer

def setup_console_encoding():
    """设置控制台编码以正确显示中文"""
    if sys.platform.startswith('win'):
        try:
            # Windows系统设置
            import locale
            import codecs
            
            # 设置标准输出编码
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8')
            
            # 设置控制台代码页为UTF-8
            os.system('chcp 65001 >nul 2>&1')
            
        except Exception:
            # 如果设置失败，使用备用方案
            pass

def safe_print(text):
    """安全的打印函数，处理编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 如果出现编码错误，移除emoji和特殊字符
        import re
        clean_text = re.sub(r'[^\u4e00-\u9fff\u0020-\u007f]', '', text)
        print(clean_text)

def print_quiet_summary(result):
    """静默模式下的简要结果显示"""
    safe_print("\n分析结果摘要:")
    safe_print(f"   • 关键词总数: {result.get('关键词总数', 0)}")
    safe_print(f"   • 高分关键词: {result.get('高分关键词数', 0)}")
    safe_print(f"   • 分析耗时: {result.get('分析耗时(秒)', 0)} 秒")
    
    # 显示Top 3关键词
    top_keywords = result.get('Top5关键词', [])[:3]
    if top_keywords:
        safe_print("\nTop 3 关键词:")
        intent_names = {'I': '信息型', 'N': '导航型', 'C': '商业型', 'E': '交易型', 'B': '行为型'}
        for i, kw in enumerate(top_keywords):
            intent_name = intent_names.get(kw['intent'], kw['intent'])
            safe_print(f"   {i+1}. {kw['query']} (分数: {kw['score']}, {intent_name})")

def main():
    """主函数 - 提供统一的执行入口"""
    
    # 设置控制台编码
    setup_console_encoding()
    
    safe_print("市场需求分析工具 v1.0")
    safe_print("=" * 50)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='市场需求分析工具 - 统一执行入口',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py "ai tools"
  python main.py "ai tools" --geo US
  python main.py "ai tools" "marketing automation" --geo US --timeframe "today 6-m"
  python main.py "chatgpt" --min-score 50 --quiet
        """
    )
    
    parser.add_argument('keywords', nargs='+', help='要分析的关键词（可以是多个）')
    parser.add_argument('--geo', default='', help='目标地区代码（如: US, GB, CN等），默认为全球')
    parser.add_argument('--timeframe', default='today 3-m', 
                       choices=['today 1-m', 'today 3-m', 'today 12-m', 'today 5-y'],
                       help='分析时间范围，默认为过去3个月')
    parser.add_argument('--output', default='data', help='输出目录，默认为data')
    parser.add_argument('--min-score', type=int, default=10, help='最低评分过滤，默认为10')
    parser.add_argument('--volume-weight', type=float, default=0.4, help='搜索量权重，默认0.4')
    parser.add_argument('--growth-weight', type=float, default=0.4, help='增长率权重，默认0.4')
    parser.add_argument('--kd-weight', type=float, default=0.2, help='关键词难度权重，默认0.2')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式，只显示最终结果')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细模式，显示所有中间过程')
    parser.add_argument('--no-enrich', action='store_true', help='不丰富关键词数据')
    
    args = parser.parse_args()
    
    # 参数验证
    if not args.keywords:
        safe_print("错误: 请至少提供一个关键词")
        sys.exit(1)
    
    # 验证权重总和
    total_weight = args.volume_weight + args.growth_weight + args.kd_weight
    if not (0.99 <= total_weight <= 1.01):
        safe_print(f"错误: 权重总和应为1.0，当前为{total_weight:.2f}")
        sys.exit(1)
    
    # 显示分析参数
    if not args.quiet:
        safe_print("分析参数:")
        safe_print(f"   关键词: {', '.join(args.keywords)}")
        safe_print(f"   地区: {args.geo or '全球'}")
        safe_print(f"   时间范围: {args.timeframe}")
        safe_print(f"   最低评分: {args.min_score}")
        safe_print(f"   权重配置: 搜索量{args.volume_weight}, 增长率{args.growth_weight}, 难度{args.kd_weight}")
        safe_print(f"   输出目录: {args.output}")
        safe_print("")
    
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
                    volume_weight=args.volume_weight,
                    growth_weight=args.growth_weight,
                    kd_weight=args.kd_weight,
                    min_score=args.min_score,
                    enrich=not args.no_enrich
                )
        else:
            # 正常模式运行
            result = analyzer.run_analysis(
                keywords=args.keywords,
                geo=args.geo,
                timeframe=args.timeframe,
                volume_weight=args.volume_weight,
                growth_weight=args.growth_weight,
                kd_weight=args.kd_weight,
                min_score=args.min_score,
                enrich=not args.no_enrich
            )
        
        # 检查结果
        if 'error' in result:
            safe_print(f"分析失败: {result['error']}")
            sys.exit(1)
        
        # 如果是静默模式，只显示关键信息
        if args.quiet:
            print_quiet_summary(result)
        
        # 显示成功信息
        safe_print(f"\n分析完成! 详细结果已保存到 {args.output} 目录")
        report_file = result.get('输出文件', {}).get('分析报告', 
                                os.path.join(args.output, f'analysis_report_{datetime.now().strftime("%Y-%m-%d")}.json'))
        safe_print(f"分析报告: {report_file}")
        
    except KeyboardInterrupt:
        safe_print("\n分析被用户中断")
        sys.exit(1)
    except Exception as e:
        safe_print(f"分析过程中出现错误: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()