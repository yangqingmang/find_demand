#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时性分析测试脚本
用于测试新增的实时性分析功能
"""

import pandas as pd
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.demand_mining.analyzers.timeliness_analyzer import TimelinessAnalyzer
from src.demand_mining.analyzers.keyword_scorer import KeywordScorer

def create_test_data():
    """创建测试数据"""
    test_keywords = [
        # AI相关热门关键词
        'chatgpt tutorial',
        'ai image generator',
        'openai api',
        'stable diffusion',
        'midjourney alternative',
        
        # 工具类关键词
        'free pdf converter',
        'online video editor',
        'password generator',
        'qr code maker',
        'image compressor',
        
        # 教程类关键词
        'how to learn python',
        'excel tutorial',
        'photoshop guide',
        'wordpress setup',
        'seo basics',
        
        # 季节性关键词
        'christmas gift ideas',
        'summer vacation planning',
        'back to school supplies',
        'new year resolutions',
        'valentine day gifts'
    ]
    
    # 创建DataFrame
    df = pd.DataFrame({
        'query': test_keywords,
        'value': [1000, 2500, 1800, 3200, 800, 1200, 900, 600, 400, 750, 
                 500, 800, 600, 400, 300, 200, 150, 180, 100, 120],
        'growth': [50, 80, 60, 120, 40, 20, 15, 10, 5, 25,
                  8, 12, 6, 4, 2, 300, 80, 150, 50, 200]
    })
    
    return df

def test_timeliness_analyzer():
    """测试实时性分析器"""
    print("=== 测试实时性分析器 ===")
    
    # 创建测试数据
    df = create_test_data()
    print(f"创建了 {len(df)} 个测试关键词")
    
    # 初始化分析器
    analyzer = TimelinessAnalyzer()
    
    # 分析实时性
    result_df = analyzer.analyze_timeliness(df)
    
    # 显示结果
    print("\n前10个关键词的实时性分析结果:")
    columns_to_show = ['query', 'timeliness_score', 'timeliness_grade', 'trend_direction', 'viral_potential']
    print(result_df[columns_to_show].head(10).to_string(index=False))
    
    # 生成摘要
    summary = analyzer.generate_timeliness_summary(result_df)
    print(f"\n=== 实时性分析摘要 ===")
    print(f"总关键词数: {summary['total_keywords']}")
    print(f"平均实时性评分: {summary['average_timeliness_score']}")
    print(f"等级分布: {summary['grade_distribution']}")
    print(f"高时效性关键词数: {len(summary['high_timeliness_keywords'])}")
    print(f"上升趋势关键词数: {len(summary['rising_trend_keywords'])}")
    print(f"病毒潜力关键词数: {len(summary['viral_potential_keywords'])}")
    
    return result_df

def test_integrated_scorer():
    """测试集成了实时性分析的关键词评分器"""
    print("\n=== 测试集成实时性分析的关键词评分器 ===")
    
    # 创建测试数据
    df = create_test_data()
    
    # 初始化评分器（包含实时性权重）
    scorer = KeywordScorer(
        volume_weight=0.25,
        growth_weight=0.25,
        kd_weight=0.15,
        kgr_weight=0.15,
        timeliness_weight=0.2
    )
    
    # 进行评分
    scored_df = scorer.score_keywords(df, calculate_timeliness=True)
    
    # 显示结果
    print("\n前10个关键词的综合评分结果:")
    columns_to_show = ['query', 'score', 'grade', 'timeliness_score', 'timeliness_grade', 'trend_direction']
    print(scored_df[columns_to_show].head(10).to_string(index=False))
    
    # 按评分排序显示top关键词
    top_keywords = scored_df.nlargest(5, 'score')
    print(f"\n=== Top 5 关键词 ===")
    for idx, row in top_keywords.iterrows():
        print(f"{row['query']}: {row['score']}分 (等级: {row['grade']}, 实时性: {row['timeliness_score']:.1f})")
    
    return scored_df

def test_comparison():
    """对比启用和禁用实时性分析的差异"""
    print("\n=== 对比启用/禁用实时性分析的差异 ===")
    
    df = create_test_data()
    
    # 创建两个评分器
    scorer_with_timeliness = KeywordScorer(
        volume_weight=0.25, growth_weight=0.25, kd_weight=0.15, 
        kgr_weight=0.15, timeliness_weight=0.2
    )
    
    scorer_without_timeliness = KeywordScorer(
        volume_weight=0.33, growth_weight=0.33, kd_weight=0.17, 
        kgr_weight=0.17, timeliness_weight=0.0
    )
    
    # 分别评分
    with_timeliness = scorer_with_timeliness.score_keywords(df, calculate_timeliness=True)
    without_timeliness = scorer_without_timeliness.score_keywords(df, calculate_timeliness=False)
    
    # 对比结果
    comparison_df = pd.DataFrame({
        'keyword': df['query'],
        'score_with_timeliness': with_timeliness['score'],
        'score_without_timeliness': without_timeliness['score'],
        'timeliness_score': with_timeliness['timeliness_score'],
        'difference': with_timeliness['score'] - without_timeliness['score']
    })
    
    print("\n评分对比 (前10个关键词):")
    print(comparison_df.head(10).to_string(index=False))
    
    # 找出差异最大的关键词
    biggest_changes = comparison_df.nlargest(5, 'difference')
    print(f"\n实时性分析影响最大的5个关键词:")
    for idx, row in biggest_changes.iterrows():
        print(f"{row['keyword']}: +{row['difference']:.0f}分 (实时性评分: {row['timeliness_score']:.1f})")

def main():
    """主函数"""
    print("开始测试实时性分析功能...")
    
    try:
        # 测试实时性分析器
        timeliness_result = test_timeliness_analyzer()
        
        # 测试集成评分器
        integrated_result = test_integrated_scorer()
        
        # 对比分析
        test_comparison()
        
        print("\n✅ 所有测试完成！实时性分析功能运行正常。")
        
        # 保存测试结果
        timeliness_result.to_csv('test_output/timeliness_analysis_test.csv', index=False, encoding='utf-8-sig')
        integrated_result.to_csv('test_output/integrated_scoring_test.csv', index=False, encoding='utf-8-sig')
        print("测试结果已保存到 test_output/ 目录")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs('test_output', exist_ok=True)
    main()