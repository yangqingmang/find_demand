"""
词根趋势分析命令行工具
"""

import argparse
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.append(str(Path(__file__).parent / "src"))

from src.demand_mining.root_word_trends_analyzer import RootWordTrendsAnalyzer

def main():
    parser = argparse.ArgumentParser(description="分析51个词根的Google Trends趋势")
    
    parser.add_argument(
        "--timeframe", 
        default="12-m",
        choices=["1-m", "3-m", "12-m", "5-y"],
        help="分析时间范围 (默认: 12-m)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="批处理大小 (默认: 5)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="data/root_word_trends",
        help="输出目录 (默认: data/root_word_trends)"
    )
    
    parser.add_argument(
        "--single-word",
        help="只分析单个词根"
    )
    
    parser.add_argument(
        "--get-keywords",
        help="获取指定词根的相关关键词"
    )
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = RootWordTrendsAnalyzer(output_dir=args.output_dir)
    
    if args.get_keywords:
        # 获取相关关键词
        print(f"正在获取 '{args.get_keywords}' 的相关关键词...")
        keywords = analyzer.get_trending_keywords_for_root(args.get_keywords)
        
        print(f"\n'{args.get_keywords}' 的相关关键词:")
        for i, keyword in enumerate(keywords, 1):
            print(f"{i:2d}. {keyword}")
            
    elif args.single_word:
        # 分析单个词根
        print(f"正在分析词根: {args.single_word}")
        result = analyzer.analyze_single_root_word(args.single_word, args.timeframe)
        
        if result["status"] == "success":
            data = result["data"]
            print(f"\n=== {args.single_word} 趋势分析结果 ===")
            print(f"平均兴趣度: {data['average_interest']:.1f}")
            print(f"峰值兴趣度: {data['peak_interest']}")
            print(f"趋势方向: {data['trend_direction']}")
            print(f"相关查询数量: {len(data['related_queries'])}")
            
            if data['related_queries']:
                print(f"\n前5个相关查询:")
                for i, query in enumerate(data['related_queries'][:5], 1):
                    print(f"{i}. {query['query']} (值: {query['value']})")
        else:
            print(f"分析失败: {result.get('error', '未知错误')}")
    
    else:
        # 分析所有词根
        print("开始分析51个词根的趋势...")
        results = analyzer.analyze_all_root_words(
            timeframe=args.timeframe, 
            batch_size=args.batch_size
        )
        
        print(f"\n=== 分析完成 ===")
        print(f"成功分析: {results['summary']['successful_analyses']} 个词根")
        print(f"失败分析: {results['summary']['failed_analyses']} 个词根")
        
        print(f"\n=== 上升趋势词根 ({len(results['summary']['top_trending_words'])}) ===")
        for word_data in results['summary']['top_trending_words'][:10]:
            print(f"  - {word_data['word']}: 平均兴趣度 {word_data['average_interest']:.1f}")
        
        print(f"\n=== 下降趋势词根 ({len(results['summary']['declining_words'])}) ===")
        for word_data in results['summary']['declining_words'][:5]:
            print(f"  - {word_data['word']}: 平均兴趣度 {word_data['average_interest']:.1f}")
        
        print(f"\n结果已保存到: {args.output_dir}")

if __name__ == "__main__":
    main()