#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
需求挖掘模块测试脚本
"""

import os
import sys
import pandas as pd
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from demand_mining_main import DemandMiningManager
from tools.keyword_extractor import KeywordExtractor
from config import get_config, validate_config

def test_config():
    """测试配置模块"""
    print("🔧 测试配置模块...")
    
    config = get_config()
    if validate_config(config):
        print("✅ 配置模块测试通过")
        return True
    else:
        print("❌ 配置模块测试失败")
        return False

def test_keyword_extractor():
    """测试关键词提取器"""
    print("\n🔍 测试关键词提取器...")
    
    try:
        extractor = KeywordExtractor()
        
        # 测试文本提取
        sample_text = "AI tools and machine learning platforms are becoming popular"
        keywords = extractor.extract_from_text(sample_text)
        
        if keywords:
            print(f"✅ 文本提取成功，提取到 {len(keywords)} 个关键词")
            print(f"   示例: {keywords[:3]}")
        else:
            print("❌ 文本提取失败")
            return False
        
        # 测试种子关键词扩展
        seed_keywords = ['ai tools']
        expanded = extractor.expand_seed_keywords(seed_keywords)
        
        if len(expanded) > len(seed_keywords):
            print(f"✅ 关键词扩展成功，从 {len(seed_keywords)} 个扩展到 {len(expanded)} 个")
        else:
            print("❌ 关键词扩展失败")
            return False
        
        print("✅ 关键词提取器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 关键词提取器测试失败: {e}")
        return False

def test_demand_mining_manager():
    """测试需求挖掘管理器"""
    print("\n📊 测试需求挖掘管理器...")
    
    try:
        # 创建测试数据
        test_data = pd.DataFrame({
            'query': [
                'best ai tools',
                'how to use chatgpt',
                'ai tool comparison',
                'buy ai software',
                'chatgpt tutorial'
            ]
        })
        
        # 保存测试数据
        test_file = 'data/test_keywords_temp.csv'
        os.makedirs('data', exist_ok=True)
        test_data.to_csv(test_file, index=False)
        
        # 创建管理器
        manager = DemandMiningManager()
        print("✅ 需求挖掘管理器创建成功")
        
        # 测试关键词分析
        results = manager.analyze_keywords(test_file)
        
        if results and results['total_keywords'] > 0:
            print(f"✅ 关键词分析成功，分析了 {results['total_keywords']} 个关键词")
            print(f"   意图分布: {results['intent_summary']['intent_distribution']}")
            print(f"   平均机会分数: {results['market_insights']['avg_opportunity_score']}")
        else:
            print("❌ 关键词分析失败")
            return False
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
        
        print("✅ 需求挖掘管理器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 需求挖掘管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """测试整体集成"""
    print("\n🔗 测试整体集成...")
    
    try:
        # 检查目录结构
        required_dirs = [
            'src/demand_mining/data',
            'src/demand_mining/analyzers',
            'src/demand_mining/tools',
            'src/demand_mining/reports'
        ]
        
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                print(f"❌ 缺少目录: {dir_path}")
                return False
        
        print("✅ 目录结构检查通过")
        
        # 检查关键文件
        required_files = [
            'src/demand_mining/demand_mining_main.py',
            'src/demand_mining/config.py',
            'src/demand_mining/tools/keyword_extractor.py'
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                print(f"❌ 缺少文件: {file_path}")
                return False
        
        print("✅ 关键文件检查通过")
        print("✅ 整体集成测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 整体集成测试失败: {e}")
        return False

def generate_test_report():
    """生成测试报告"""
    print("\n📋 生成测试报告...")
    
    report_content = f"""# 需求挖掘模块测试报告

## 测试时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 测试结果

### ✅ 已通过的测试
- 配置模块测试
- 关键词提取器测试  
- 需求挖掘管理器测试
- 整体集成测试

### 📊 模块功能
- ✅ 关键词分析和意图识别
- ✅ 市场数据模拟和机会评分
- ✅ 分析结果保存和报告生成
- ✅ 配置管理和参数调整

### 🎯 应用场景
- AI工具站关键词研究
- 内容策略制定
- 市场需求分析
- 竞争对手研究

### 📈 下一步计划
- 集成真实的市场数据API
- 增强SERP分析功能
- 添加更多数据源
- 优化分析算法

---
*测试报告自动生成*
"""
    
    report_path = 'src/demand_mining/reports/test_report.md'
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ 测试报告已生成: {report_path}")

def main():
    """主测试函数"""
    print("🚀 开始需求挖掘模块测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行各项测试
    test_results.append(("配置模块", test_config()))
    test_results.append(("关键词提取器", test_keyword_extractor()))
    test_results.append(("需求挖掘管理器", test_demand_mining_manager()))
    test_results.append(("整体集成", test_integration()))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！需求挖掘模块已准备就绪")
        generate_test_report()
    else:
        print("⚠️ 部分测试失败，请检查相关模块")
    
    return passed == total

if __name__ == '__main__':
    main()