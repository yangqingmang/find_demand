#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成建站建议功能测试脚本
测试自动建站脚本与建站建议系统的集成效果
"""

import sys
import os
import pandas as pd
import tempfile

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_demand_mining_with_recommendations():
    """测试需求挖掘管理器的建站建议功能"""
    print("=== 测试需求挖掘管理器建站建议功能 ===")
    
    try:
        from src.demand_mining.demand_mining_main import DemandMiningManager
        
        # 创建测试数据文件
        test_data = pd.DataFrame({
            'query': [
                'best ai writing tools',
                'how to use chatgpt',
                'ai image generator free',
                'chatgpt login',
                'ai tool not working'
            ]
        })
        
        # 保存测试数据到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            test_data.to_csv(f.name, index=False)
            temp_file = f.name
        
        print(f"创建测试数据文件: {temp_file}")
        print(f"测试关键词: {', '.join(test_data['query'].tolist())}")
        
        # 创建需求挖掘管理器
        manager = DemandMiningManager()
        
        # 执行分析
        print("\n开始执行需求挖掘分析...")
        results = manager.analyze_keywords(temp_file)
        
        # 检查结果
        print(f"\n分析完成，共处理 {results['total_keywords']} 个关键词")
        
        # 显示建站建议结果
        print("\n建站建议结果:")
        for i, keyword_result in enumerate(results['keywords'], 1):
            keyword = keyword_result['keyword']
            intent_info = keyword_result['intent']
            website_recommendations = intent_info.get('website_recommendations', {})
            
            print(f"\n{i}. {keyword}")
            print(f"   意图: {intent_info.get('primary_intent', '未知')}")
            print(f"   网站类型: {website_recommendations.get('website_type', '未知')}")
            print(f"   AI类别: {website_recommendations.get('ai_tool_category', '未知')}")
            
            # 显示开发优先级
            priority_info = website_recommendations.get('development_priority', {})
            if isinstance(priority_info, dict):
                priority = priority_info.get('level', '未知')
                timeline = priority_info.get('timeline', '未知')
                print(f"   开发优先级: {priority} ({timeline})")
            
            # 显示域名建议
            domains = website_recommendations.get('domain_suggestions', [])
            if domains:
                print(f"   域名建议: {', '.join(domains[:3])}")
        
        # 清理临时文件
        os.unlink(temp_file)
        
        print("\n✓ 需求挖掘管理器建站建议功能测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 需求挖掘管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_website_builder_with_recommendations():
    """测试网站建设器的建站建议功能"""
    print("\n=== 测试网站建设器建站建议功能 ===")
    
    try:
        from src.website_builder.builder_core import IntentBasedWebsiteBuilder
        
        # 创建包含建站建议的测试数据
        test_data = pd.DataFrame({
            'query': ['ai writing assistant'],
            'intent_primary': ['E'],
            'intent_confidence': [0.85],
            'website_type': ['AI工具站 (SaaS平台)'],
            'ai_tool_category': ['AI写作工具'],
            'domain_suggestions': [['aiwriter.com', 'writeai.io', 'smartwriter.ai']],
            'monetization_strategy': [['Freemium模式', 'API调用收费', '订阅制']],
            'technical_requirements': [['AI API集成', '实时处理能力', '用户账户']],
            'development_priority': [{'level': '高', 'timeline': '1-2个月', 'score': 85}],
            'content_strategy': [['产品页面', '定价页面', '免费试用']]
        })
        
        # 保存测试数据到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            test_data.to_csv(f.name, index=False)
            temp_file = f.name
        
        print(f"创建测试意图数据文件: {temp_file}")
        
        # 创建网站建设器
        builder = IntentBasedWebsiteBuilder(
            intent_data_path=temp_file,
            output_dir="test_output",
            config={'project_name': 'test_ai_writer'}
        )
        
        # 加载数据
        print("\n加载意图数据...")
        if builder.load_intent_data():
            print("✓ 意图数据加载成功")
            
            # 生成网站结构
            print("\n生成网站结构...")
            structure = builder.generate_website_structure()
            
            if structure:
                print("✓ 网站结构生成成功")
                
                # 检查建站建议是否被正确处理
                recommendations = structure.get('website_recommendations', {})
                print(f"\n建站建议摘要:")
                print(f"  主要网站类型: {recommendations.get('primary_website_type', '未知')}")
                print(f"  主要AI类别: {recommendations.get('primary_ai_category', '未知')}")
                print(f"  域名建议数量: {len(recommendations.get('domain_suggestions', []))}")
                print(f"  技术要求数量: {len(recommendations.get('technical_requirements', []))}")
                
                # 显示开发优先级分析
                priorities = recommendations.get('development_priorities', {})
                if priorities:
                    print(f"  高优先级项目: {priorities.get('high_priority_count', 0)}")
                    print(f"  优先级比例: {priorities.get('priority_ratio', 0):.2%}")
                
                print("\n✓ 网站建设器建站建议功能测试通过")
            else:
                print("✗ 网站结构生成失败")
                return False
        else:
            print("✗ 意图数据加载失败")
            return False
        
        # 清理临时文件
        os.unlink(temp_file)
        
        return True
        
    except Exception as e:
        print(f"✗ 网站建设器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integrated_workflow():
    """测试集成工作流的建站建议功能"""
    print("\n=== 测试集成工作流建站建议功能 ===")
    
    try:
        from src.integrated_workflow import IntegratedWorkflow
        
        # 创建测试数据文件
        test_data = pd.DataFrame({
            'query': [
                'ai chatbot builder',
                'image generation api'
            ]
        })
        
        # 保存测试数据到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            test_data.to_csv(f.name, index=False)
            temp_file = f.name
        
        print(f"创建测试关键词文件: {temp_file}")
        print(f"测试关键词: {', '.join(test_data['query'].tolist())}")
        
        # 创建集成工作流
        workflow = IntegratedWorkflow({
            'min_opportunity_score': 0,  # 降低阈值以便测试
            'max_projects_per_batch': 2,
            'auto_deploy': False  # 禁用自动部署
        })
        
        # 执行工作流（仅测试前几个步骤）
        print("\n开始执行集成工作流...")
        
        # 步骤1: 需求挖掘
        print("\n执行需求挖掘...")
        demand_results = workflow._run_demand_mining(temp_file)
        
        if demand_results and 'keywords' in demand_results:
            print(f"✓ 需求挖掘完成，分析了 {len(demand_results['keywords'])} 个关键词")
            
            # 检查建站建议数据
            for keyword_data in demand_results['keywords']:
                keyword = keyword_data['keyword']
                intent_info = keyword_data.get('intent', {})
                website_recommendations = intent_info.get('website_recommendations', {})
                
                print(f"\n关键词: {keyword}")
                print(f"  网站类型: {website_recommendations.get('website_type', '未知')}")
                print(f"  AI类别: {website_recommendations.get('ai_tool_category', '未知')}")
                
                # 检查开发优先级
                priority_info = website_recommendations.get('development_priority', {})
                if isinstance(priority_info, dict):
                    print(f"  开发优先级: {priority_info.get('level', '未知')}")
            
            # 步骤2: 筛选高价值关键词
            print("\n筛选高价值关键词...")
            high_value_keywords = workflow._filter_high_value_keywords(demand_results)
            print(f"✓ 筛选出 {len(high_value_keywords)} 个高价值关键词")
            
            # 测试项目名称生成
            if high_value_keywords:
                keyword_data = high_value_keywords[0]
                keyword = keyword_data['keyword']
                intent_info = keyword_data.get('intent', {})
                website_recommendations = intent_info.get('website_recommendations', {})
                
                project_name = workflow._generate_project_name_with_recommendations(keyword, website_recommendations)
                print(f"\n生成的项目名称: {project_name}")
                
                # 测试项目配置生成
                project_config = workflow._create_project_config(website_recommendations, project_name)
                print(f"项目配置:")
                print(f"  网站类型: {project_config.get('website_type')}")
                print(f"  AI类别: {project_config.get('ai_category')}")
                print(f"  模板类型: {project_config.get('template_type')}")
                print(f"  域名选项数量: {len(project_config.get('domain_options', []))}")
            
            print("\n✓ 集成工作流建站建议功能测试通过")
        else:
            print("✗ 需求挖掘结果为空")
            return False
        
        # 清理临时文件
        os.unlink(temp_file)
        
        return True
        
    except Exception as e:
        print(f"✗ 集成工作流测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("集成建站建议功能测试")
    print("=" * 60)
    
    # 测试结果
    results = []
    
    # 1. 测试需求挖掘管理器
    results.append(test_demand_mining_with_recommendations())
    
    # 2. 测试网站建设器
    results.append(test_website_builder_with_recommendations())
    
    # 3. 测试集成工作流
    results.append(test_integrated_workflow())
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结:")
    print(f"  需求挖掘管理器: {'✓ 通过' if results[0] else '✗ 失败'}")
    print(f"  网站建设器: {'✓ 通过' if results[1] else '✗ 失败'}")
    print(f"  集成工作流: {'✓ 通过' if results[2] else '✗ 失败'}")
    
    if all(results):
        print("\n🎉 所有测试通过！建站建议系统已成功集成到自动建站脚本！")
        print("\n集成效果:")
        print("✓ 需求挖掘阶段自动生成建站建议")
        print("✓ 网站建设器基于建站建议优化结构")
        print("✓ 集成工作流智能生成项目配置")
        print("✓ 项目名称基于网站类型智能命名")
        print("✓ 域名建议和技术要求自动集成")
        print("✓ 开发优先级指导项目排序")
        
        print("\n使用方法:")
        print("```bash")
        print("# 使用集成工作流（自动包含建站建议）")
        print("python -m src.integrated_workflow keywords.csv")
        print("")
        print("# 或单独使用需求挖掘（包含建站建议）")
        print("python -m src.demand_mining.demand_mining_main keywords.csv")
        print("```")
    else:
        print("\n❌ 部分测试失败，请检查上述错误信息")
        print("\n可能的问题:")
        print("- 导入路径错误")
        print("- 依赖模块缺失")
        print("- 配置文件问题")
        print("- 数据格式不匹配")

if __name__ == "__main__":
    main()