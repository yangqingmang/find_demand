#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建站建议功能测试脚本
用于测试基于搜索意图的建站建议功能
"""

import sys
import os
import pandas as pd

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_website_recommendations():
    """测试建站建议功能"""
    print("=== 测试建站建议功能 ===")
    
    try:
        from src.demand_mining.analyzers.intent_analyzer import IntentAnalyzer
        from src.demand_mining.analyzers.website_recommendation import WebsiteRecommendationEngine
        
        # 创建测试数据
        test_data = pd.DataFrame({
            'query': [
                'best ai writing tools',
                'how to use chatgpt',
                'ai image generator free',
                'chatgpt login',
                'ai tool not working',
                'ai tools near me',
                'buy ai software',
                'ai vs human writing',
                'download stable diffusion',
                'ai coding assistant'
            ],
            'volume': [5000, 3000, 4000, 2000, 1500, 800, 2500, 1800, 3500, 2800],
            'growth': [120, 80, 200, 50, 30, 60, 150, 90, 180, 110]
        })
        
        print(f"测试数据包含 {len(test_data)} 个关键词:")
        for idx, row in test_data.iterrows():
            print(f"  {idx+1}. {row['query']} (搜索量: {row['volume']})")
        
        # 测试1: 使用集成的意图分析器（包含建站建议）
        print("\n=== 测试1: 集成意图分析 + 建站建议 ===")
        analyzer = IntentAnalyzer(
            use_serp=False, 
            use_v2=False, 
            enable_website_recommendations=True
        )
        
        result_df = analyzer.analyze_keywords(test_data, keyword_col='query')
        
        # 显示结果
        print("\n意图分析 + 建站建议结果:")
        display_columns = [
            'query', 'intent', 'intent_description', 
            'website_type', 'ai_tool_category', 'development_priority'
        ]
        
        for idx, row in result_df.iterrows():
            print(f"\n{idx+1}. {row['query']}")
            print(f"   意图: {row['intent']} - {row.get('intent_description', '')}")
            print(f"   建议网站类型: {row.get('website_type', '未知')}")
            print(f"   AI工具类别: {row.get('ai_tool_category', '未知')}")
            
            # 显示开发优先级
            priority_info = row.get('development_priority', {})
            if isinstance(priority_info, dict):
                priority = priority_info.get('level', '未知')
                timeline = priority_info.get('timeline', '未知')
                print(f"   开发优先级: {priority} ({timeline})")
            
            # 显示域名建议
            domains = row.get('domain_suggestions', [])
            if isinstance(domains, list) and domains:
                print(f"   域名建议: {', '.join(domains[:3])}")
            
            # 显示变现策略
            monetization = row.get('monetization_strategy', [])
            if isinstance(monetization, list) and monetization:
                print(f"   变现策略: {', '.join(monetization[:2])}")
        
        # 测试2: 单独测试建站建议引擎
        print("\n=== 测试2: 单独建站建议引擎 ===")
        
        # 先进行简单的意图分析
        simple_intent_data = test_data.copy()
        simple_intent_data['intent'] = ['C', 'I', 'E', 'N', 'B', 'L', 'E', 'C', 'N', 'E']
        
        # 创建建站建议引擎
        recommender = WebsiteRecommendationEngine()
        
        # 生成建站建议
        recommendations_df = recommender.generate_website_recommendations(
            simple_intent_data, 
            keyword_col='query', 
            intent_col='intent'
        )
        
        print("\n单独建站建议结果:")
        for idx, row in recommendations_df.iterrows():
            print(f"\n{idx+1}. {row['query']} (意图: {row['intent']})")
            print(f"   网站类型: {row.get('website_type', '未知')}")
            print(f"   AI类别: {row.get('ai_tool_category', '未知')}")
            
            # 显示技术要求
            tech_reqs = row.get('technical_requirements', [])
            if isinstance(tech_reqs, list) and tech_reqs:
                print(f"   技术要求: {', '.join(tech_reqs[:3])}")
            
            # 显示竞争分析
            competition = row.get('competition_analysis', {})
            if isinstance(competition, dict):
                level = competition.get('level', '未知')
                advice = competition.get('advice', '')
                print(f"   竞争程度: {level} - {advice}")
        
        # 测试3: 生成摘要报告
        print("\n=== 测试3: 摘要报告生成 ===")
        
        summary_report = recommender.generate_summary_report(recommendations_df)
        
        print("\n摘要报告:")
        print(f"总关键词数: {summary_report.get('total_keywords', 0)}")
        
        print("\n网站类型分布:")
        for website_type, count in summary_report.get('website_type_distribution', {}).items():
            print(f"  {website_type}: {count}")
        
        print("\nAI工具类别分布:")
        for ai_category, count in summary_report.get('ai_category_distribution', {}).items():
            print(f"  {ai_category}: {count}")
        
        print("\n开发优先级分布:")
        for priority, count in summary_report.get('priority_distribution', {}).items():
            print(f"  {priority}: {count}")
        
        print("\n高优先级项目:")
        for project in summary_report.get('high_priority_projects', []):
            print(f"  - {project.get('query', '')}: {project.get('website_type', '')}")
        
        print("\n立即行动建议:")
        for recommendation in summary_report.get('recommendations', {}).get('immediate_action', []):
            print(f"  • {recommendation}")
        
        print("\n市场机会:")
        for opportunity in summary_report.get('recommendations', {}).get('market_opportunities', []):
            print(f"  • {opportunity}")
        
        print("\n技术重点:")
        for focus in summary_report.get('recommendations', {}).get('technical_focus', []):
            print(f"  • {focus}")
        
        print("\n✓ 建站建议功能测试完成!")
        return True
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_tool_detection():
    """测试AI工具类别检测"""
    print("\n=== 测试AI工具类别检测 ===")
    
    try:
        from src.demand_mining.analyzers.website_recommendation import WebsiteRecommendationEngine
        
        recommender = WebsiteRecommendationEngine()
        
        test_keywords = [
            'chatgpt alternative',
            'ai image generator',
            'code completion tool',
            'voice synthesis ai',
            'video editing ai',
            'business automation tool',
            'research assistant ai',
            'writing helper tool',
            'regular calculator',  # 非AI工具
            'weather forecast'     # 非AI工具
        ]
        
        print("AI工具类别检测结果:")
        for keyword in test_keywords:
            category = recommender._detect_ai_tool_category(keyword.lower())
            print(f"  {keyword}: {category}")
        
        return True
        
    except Exception as e:
        print(f"✗ AI工具检测测试失败: {e}")
        return False

def test_domain_suggestions():
    """测试域名建议生成"""
    print("\n=== 测试域名建议生成 ===")
    
    try:
        from src.demand_mining.analyzers.website_recommendation import WebsiteRecommendationEngine
        
        recommender = WebsiteRecommendationEngine()
        
        test_cases = [
            ('ai writing tool', 'AI写作工具'),
            ('best chatgpt alternative', 'AI对话工具'),
            ('image generator free', 'AI图像生成'),
            ('code assistant', 'AI编程工具'),
            ('business automation', 'AI商业工具')
        ]
        
        print("域名建议生成结果:")
        for keyword, ai_category in test_cases:
            domains = recommender._generate_domain_suggestions(keyword.lower(), ai_category)
            print(f"\n{keyword} ({ai_category}):")
            for i, domain in enumerate(domains[:5], 1):
                print(f"  {i}. {domain}")
        
        return True
        
    except Exception as e:
        print(f"✗ 域名建议测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("建站建议功能测试")
    print("=" * 50)
    
    # 测试结果
    results = []
    
    # 1. 测试建站建议功能
    results.append(test_website_recommendations())
    
    # 2. 测试AI工具检测
    results.append(test_ai_tool_detection())
    
    # 3. 测试域名建议
    results.append(test_domain_suggestions())
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"  建站建议功能: {'✓ 通过' if results[0] else '✗ 失败'}")
    print(f"  AI工具检测: {'✓ 通过' if results[1] else '✗ 失败'}")
    print(f"  域名建议: {'✓ 通过' if results[2] else '✗ 失败'}")
    
    if all(results):
        print("\n🎉 所有测试通过！建站建议功能已成功集成！")
        print("\n功能特性:")
        print("✓ 基于搜索意图的网站类型推荐")
        print("✓ AI工具类别自动识别")
        print("✓ 智能域名建议生成")
        print("✓ 变现策略推荐")
        print("✓ 技术要求分析")
        print("✓ 竞争程度评估")
        print("✓ 开发优先级评估")
        print("✓ 内容策略建议")
        print("\n使用方法:")
        print("```python")
        print("from src.demand_mining.analyzers.intent_analyzer import IntentAnalyzer")
        print("analyzer = IntentAnalyzer(enable_website_recommendations=True)")
        print("result = analyzer.analyze_keywords(df)")
        print("# 结果将包含完整的建站建议")
        print("```")
    else:
        print("\n❌ 部分测试失败，请检查上述错误信息")

if __name__ == "__main__":
    main()