#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竞争对手分析功能测试脚本
"""

import pandas as pd
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.demand_mining.analyzers.competitor_analyzer import CompetitorAnalyzer
from src.demand_mining.analyzers.keyword_scorer import KeywordScorer

def create_test_data():
    """创建测试数据"""
    test_keywords = [
        "best ai tools 2025",
        "chatgpt alternatives",
        "free ai writing assistant",
        "ai image generator",
        "machine learning tutorial",
        "deep learning course",
        "ai for business",
        "automated content creation",
        "ai chatbot development",
        "neural network basics",
        "ai productivity tools",
        "openai api pricing",
        "stable diffusion guide",
        "ai art generator",
        "natural language processing"
    ]
    
    # 创建测试DataFrame
    df = pd.DataFrame({
        'query': test_keywords,
        'value': [12000, 8500, 15000, 22000, 5500, 4200, 9800, 3200, 6700, 7800, 11000, 4500, 8900, 18000, 6200],
        'growth': [150, 80, 200, 300, 45, 30, 120, 25, 90, 110, 180, 60, 140, 250, 75],
        'kd': [65, 45, 70, 85, 35, 25, 55, 20, 40, 50, 60, 30, 75, 80, 45]
    })
    
    return df

def test_competitor_analyzer():
    """测试竞争对手分析器"""
    print("=== 测试竞争对手分析器 ===")
    
    # 创建测试数据
    df = create_test_data()
    print(f"创建测试数据: {len(df)} 个关键词")
    
    # 创建竞争对手分析器
    analyzer = CompetitorAnalyzer()
    
    # 分析竞争对手
    print("\n正在进行竞争对手分析...")
    result_df = analyzer.analyze_competitors(df, 'query')
    
    # 显示结果
    print(f"\n分析完成! 结果包含 {len(result_df)} 个关键词")
    print("\n=== 竞争分析结果摘要 ===")
    
    # 显示前5个关键词的详细信息
    print("\n前5个关键词的竞争分析结果:")
    print("可用列:", list(result_df.columns))
    
    # 动态选择可用的列
    base_columns = ['query', 'competition_score', 'competition_grade', 'opportunity_score']
    display_columns = [col for col in base_columns if col in result_df.columns]
    
    if 'top_competitors' in result_df.columns:
        display_columns.append('top_competitors')
    elif 'main_competitors' in result_df.columns:
        display_columns.append('main_competitors')
    
    print(result_df[display_columns].head().to_string(index=False))
    
    # 统计信息
    print(f"\n=== 统计信息 ===")
    print(f"平均竞争评分: {result_df['competition_score'].mean():.1f}")
    print(f"平均机会评分: {result_df['opportunity_score'].mean():.1f}")
    
    # 竞争等级分布
    competition_dist = result_df['competition_grade'].value_counts().sort_index()
    print(f"\n竞争等级分布:")
    for grade, count in competition_dist.items():
        print(f"  {grade}级: {count} 个关键词")
    
    # 低竞争高机会关键词
    low_comp_high_opp = result_df[
        (result_df['competition_grade'].isin(['D', 'F'])) & 
        (result_df['opportunity_score'] >= 70)
    ]
    print(f"\n低竞争高机会关键词: {len(low_comp_high_opp)} 个")
    if not low_comp_high_opp.empty:
        print("推荐关键词:")
        for _, row in low_comp_high_opp.head(3).iterrows():
            print(f"  - {row['query']} (机会评分: {row['opportunity_score']:.1f})")
    
    return result_df

def test_integrated_scoring():
    """测试集成评分功能"""
    print("\n\n=== 测试集成评分功能 ===")
    
    # 创建测试数据
    df = create_test_data()
    
    # 创建关键词评分器（包含竞争对手分析）
    scorer = KeywordScorer(
        volume_weight=0.2,
        growth_weight=0.2,
        kd_weight=0.15,
        kgr_weight=0.15,
        timeliness_weight=0.15,
        competitor_weight=0.15
    )
    
    # 进行综合评分
    print("正在进行综合评分（包含竞争对手分析）...")
    scored_df = scorer.score_keywords(
        df,
        calculate_kgr=True,
        calculate_timeliness=True,
        calculate_competitor=True
    )
    
    # 显示结果
    print(f"\n综合评分完成! 结果包含 {len(scored_df)} 个关键词")
    
    # 显示前5个关键词的综合评分
    print("\n前5个关键词的综合评分结果:")
    display_columns = [
        'query', 'score', 'grade', 
        'volume_score', 'growth_score', 'kd_score', 
        'kgr_score', 'timeliness_score', 'opportunity_score'
    ]
    available_columns = [col for col in display_columns if col in scored_df.columns]
    print(scored_df[available_columns].head().to_string(index=False))
    
    # 评分统计
    print(f"\n=== 综合评分统计 ===")
    print(f"平均综合评分: {scored_df['score'].mean():.1f}")
    print(f"最高评分: {scored_df['score'].max()}")
    print(f"最低评分: {scored_df['score'].min()}")
    
    # 等级分布
    grade_dist = scored_df['grade'].value_counts().sort_index()
    print(f"\n评分等级分布:")
    for grade, count in grade_dist.items():
        print(f"  {grade}级: {count} 个关键词")
    
    # 高分关键词
    high_score_keywords = scored_df[scored_df['score'] >= 70].sort_values('score', ascending=False)
    print(f"\n高分关键词 (≥70分): {len(high_score_keywords)} 个")
    if not high_score_keywords.empty:
        print("推荐关键词:")
        for _, row in high_score_keywords.head(3).iterrows():
            print(f"  - {row['query']} (综合评分: {row['score']})")
    
    # 保存结果
    output_file = 'test_output/integrated_scoring_test.csv'
    os.makedirs('test_output', exist_ok=True)
    scored_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n结果已保存到: {output_file}")
    
    return scored_df

def main():
    """主函数"""
    print("竞争对手分析功能测试")
    print("=" * 50)
    
    try:
        # 测试竞争对手分析器
        competitor_result = test_competitor_analyzer()
        
        # 测试集成评分功能
        integrated_result = test_integrated_scoring()
        
        print("\n" + "=" * 50)
        print("所有测试完成!")
        print("竞争对手分析功能运行正常 ✓")
        print("集成评分功能运行正常 ✓")
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()