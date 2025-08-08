#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
集成工作流使用示例
演示如何使用需求挖掘 → 意图分析 → 建站部署的完整流程
"""

import os
import sys
import pandas as pd
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.integrated_workflow import IntegratedWorkflow


def create_sample_keywords_file():
    """创建示例关键词文件"""
    sample_keywords = [
        'ai image generator',
        'pdf converter online',
        'code formatter tool',
        'ai writing assistant',
        'video compressor free',
        'qr code generator',
        'password generator secure',
        'ai logo maker',
        'text to speech converter',
        'image background remover'
    ]
    
    # 创建DataFrame
    df = pd.DataFrame({'query': sample_keywords})
    
    # 保存到CSV文件
    sample_file = 'data/sample_keywords.csv'
    os.makedirs('data', exist_ok=True)
    df.to_csv(sample_file, index=False, encoding='utf-8-sig')
    
    print(f"✅ 示例关键词文件已创建: {sample_file}")
    return sample_file


def run_integrated_workflow_example():
    """运行集成工作流示例"""
    print("🚀 集成工作流示例开始")
    print("=" * 50)
    
    # 1. 创建示例数据
    keywords_file = create_sample_keywords_file()
    
    # 2. 配置工作流参数
    config = {
        'min_opportunity_score': 50,  # 降低阈值以便演示
        'max_projects_per_batch': 3,  # 限制项目数量
        'auto_deploy': False,         # 演示时不自动部署
        'deployment_platform': 'cloudflare',
        'use_tailwind': True,
        'generate_reports': True
    }
    
    # 3. 创建工作流实例
    workflow = IntegratedWorkflow(config)
    
    # 4. 执行完整工作流
    print(f"\n📊 开始分析关键词文件: {keywords_file}")
    results = workflow.run_complete_workflow(keywords_file)
    
    # 5. 显示结果
    print("\n" + "=" * 50)
    print("📋 工作流执行结果:")
    print(f"状态: {results['status']}")
    print(f"完成步骤: {', '.join(results['steps_completed'])}")
    
    if results['status'] == 'success':
        print(f"分析关键词数: {len(results.get('demand_analysis', {}).get('keywords', []))}")
        print(f"高价值关键词: {len(results.get('high_value_keywords', []))}")
        print(f"生成网站数: {len(results.get('generated_projects', []))}")
        print(f"报告路径: {results.get('report_path', '')}")
        
        # 显示高价值关键词
        print("\n🎯 发现的高价值关键词:")
        for i, kw in enumerate(results.get('high_value_keywords', [])[:5], 1):
            print(f"  {i}. {kw['keyword']} (分数: {kw.get('opportunity_score', 0)})")
        
        # 显示生成的项目
        print("\n🏗️ 生成的网站项目:")
        for project in results.get('generated_projects', []):
            status_icon = "✅" if project.get('status') == 'success' else "❌"
            print(f"  {status_icon} {project['keyword']}")
            if project.get('source_dir'):
                print(f"     项目路径: {project['source_dir']}")
    
    else:
        print(f"执行失败: {results.get('error', '')}")
    
    print("\n🎉 集成工作流示例完成!")
    return results


def demonstrate_individual_modules():
    """演示各个模块的独立使用"""
    print("\n" + "=" * 50)
    print("🔧 演示各模块独立使用")
    
    # 演示需求挖掘模块
    print("\n1. 需求挖掘模块演示:")
    from src.demand_mining.demand_mining_main import DemandMiningManager
    
    demand_miner = DemandMiningManager()
    print(f"   ✅ 已加载 {len(demand_miner.core_roots)} 个核心词根")
    print(f"   ✅ 已配置 {len(demand_miner.competitor_sites)} 个竞品分析目标")
    
    # 演示意图分析模块
    print("\n2. 意图分析模块演示:")
    from src.demand_mining.analyzers.intent_analyzer_v2 import IntentAnalyzerV2
    
    intent_analyzer = IntentAnalyzerV2()
    
    # 测试几个关键词
    test_keywords = ['ai image generator', 'how to use photoshop', 'buy domain name']
    for keyword in test_keywords:
        intent, confidence, secondary = intent_analyzer.detect_intent_from_keyword(keyword)
        print(f"   关键词: {keyword}")
        print(f"   主意图: {intent} (置信度: {confidence:.2f})")
        if secondary:
            print(f"   次意图: {secondary}")
        print()
    
    # 演示建站模块
    print("3. 建站模块演示:")
    from src.website_builder.intent_based_website_builder import IntentBasedWebsiteBuilder
    print("   ✅ 建站模块已就绪，支持基于意图的自动网站生成")
    print("   ✅ 支持TailwindCSS样式框架")
    print("   ✅ 支持多平台自动部署")


def show_integration_benefits():
    """展示集成的优势"""
    print("\n" + "=" * 50)
    print("🌟 集成工作流的优势")
    
    benefits = [
        "🔄 全流程自动化：从关键词到上线网站一键完成",
        "🎯 智能筛选：基于多维度评分自动筛选高价值关键词",
        "🤖 AI驱动：结合AI相关性、商业价值、新兴程度等智能评估",
        "📊 数据驱动：基于搜索意图生成针对性网站内容",
        "🚀 快速部署：支持多平台自动部署，快速抢占市场",
        "📋 完整报告：生成详细的分析和执行报告",
        "🔧 高度可配置：支持自定义阈值、平台、样式等参数",
        "📈 可扩展：模块化设计，易于扩展新功能"
    ]
    
    for benefit in benefits:
        print(f"  {benefit}")
    
    print("\n💡 适用场景:")
    scenarios = [
        "出海AI工具快速验证和上线",
        "批量生成利基市场网站", 
        "SEO友好的工具站点建设",
        "基于需求数据的产品开发",
        "竞品分析和市场机会发现",
        "自动化内容营销网站生成"
    ]
    
    for scenario in scenarios:
        print(f"  • {scenario}")


def main():
    """主函数"""
    print("🎯 集成工作流完整演示")
    print("整合需求挖掘 → 意图分析 → 网站生成 → 自动部署")
    print("=" * 60)
    
    try:
        # 1. 运行完整工作流示例
        results = run_integrated_workflow_example()
        
        # 2. 演示各模块独立使用
        demonstrate_individual_modules()
        
        # 3. 展示集成优势
        show_integration_benefits()
        
        print("\n" + "=" * 60)
        print("✅ 演示完成！集成工作流已准备就绪")
        
        if results.get('status') == 'success':
            print(f"📋 查看详细报告: {results.get('report_path', '')}")
            print("🚀 可以开始使用集成工作流进行实际项目开发")
        
        return 0
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
