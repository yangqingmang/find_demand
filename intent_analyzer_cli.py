#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
搜索意图分析工具命令行接口
用于分析关键词的搜索意图
"""

import argparse
import os
import sys
import pandas as pd

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from src.analyzers.intent_analyzer_v2 import IntentAnalyzerV2, analyze_single_keyword


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='搜索意图分析工具')
    parser.add_argument('keyword', nargs='?', help='要分析的单个关键词')
    parser.add_argument('--input', help='输入CSV文件路径')
    parser.add_argument('--output', default='data', help='输出目录，默认为data')
    parser.add_argument('--query-col', default='query', help='关键词列名，默认为"query"')
    parser.add_argument('--keywords-dict', default='config/keywords_dict.yaml', help='关键词字典YAML文件路径')
    parser.add_argument('--serp-rules', default='config/serp_rules.yaml', help='SERP规则YAML文件路径')
    
    args = parser.parse_args()
    
    # 检查是分析单个关键词还是CSV文件
    if args.keyword and args.input:
        print("错误: 不能同时指定单个关键词和输入文件")
        sys.exit(1)
    
    if not args.keyword and not args.input:
        parser.print_help()
        sys.exit(1)
    
    try:
        # 如果是单个关键词
        if args.keyword:
            result = analyze_single_keyword(
                args.keyword,
                keywords_dict_path=args.keywords_dict if os.path.exists(args.keywords_dict) else None,
                serp_rules_path=args.serp_rules if os.path.exists(args.serp_rules) else None
            )
            
            # 打印结果
            print("\n搜索意图分析结果:")
            print(f"关键词: {result['query']}")
            print(f"主意图: {result['intent_primary']} ({IntentAnalyzerV2.INTENT_DESCRIPTIONS.get(result['intent_primary'], '')})")
            
            if result['intent_secondary']:
                print(f"次意图: {result['intent_secondary']} ({IntentAnalyzerV2.INTENT_DESCRIPTIONS.get(result['intent_secondary'], '')})")
            
            if result['sub_intent']:
                print(f"子意图: {result['sub_intent']} ({IntentAnalyzerV2.INTENT_DESCRIPTIONS.get(result['sub_intent'], '')})")
            
            print(f"主意图概率: {result['probability']:.2f}")
            
            if result['probability_secondary'] > 0:
                print(f"次意图概率: {result['probability_secondary']:.2f}")
            
            if result['signals_hit']:
                print(f"命中信号: {', '.join(result['signals_hit'])}")
            
            print("\n建议行动:")
            if result['intent_primary']:
                recommendations = IntentAnalyzerV2({}).get_recommendations()
                print(f"• {recommendations.get(result['intent_primary'], '无建议')}")
            else:
                print("• 无法确定意图，建议进一步分析")
        
        # 如果是CSV文件
        else:
            # 检查输入文件是否存在
            if not os.path.exists(args.input):
                print(f"错误: 输入文件 {args.input} 不存在")
                sys.exit(1)
            
            # 读取CSV文件
            df = pd.read_csv(args.input)
            
            # 检查关键词列是否存在
            if args.query_col not in df.columns:
                print(f"错误: 关键词列 '{args.query_col}' 不在CSV文件中")
                print(f"可用列: {', '.join(df.columns)}")
                sys.exit(1)
            
            # 初始化分析器
            analyzer = IntentAnalyzerV2(
                keywords_dict_path=args.keywords_dict if os.path.exists(args.keywords_dict) else None,
                serp_rules_path=args.serp_rules if os.path.exists(args.serp_rules) else None
            )
            
            # 分析关键词
            analysis_results = analyzer.analyze_keywords(df, query_col=args.query_col)
            
            # 保存结果
            saved_files = analyzer.save_results(analysis_results, args.output)
            
            # 打印摘要
            summary = analysis_results['summary']
            print("\n分析完成!")
            print(f"总关键词数: {summary['total_keywords']}")
            print("意图分布:")
            for intent, percentage in summary['intent_percentages'].items():
                if percentage > 0:
                    print(f"• {intent} ({IntentAnalyzerV2.INTENT_DESCRIPTIONS.get(intent, '')}): {percentage:.1f}%")
            
            print(f"\n详细结果已保存到 {args.output} 目录")
            for desc, path in saved_files.items():
                print(f"• {desc}: {path}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()