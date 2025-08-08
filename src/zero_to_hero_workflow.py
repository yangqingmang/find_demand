#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从零开始的需求挖掘工作流
无需预先准备关键词文件，从种子词开始自动挖掘
"""

import os
import sys
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.demand_mining.demand_mining_main import DemandMiningManager
from src.integrated_workflow import IntegratedWorkflow


class ZeroToHeroWorkflow:
    """
    从零开始的完整工作流
    基于路漫漫分享的六大需求挖掘方法，从种子词开始自动发现需求
    """
    
    def __init__(self):
        """初始化从零开始工作流"""
        self.demand_miner = DemandMiningManager()
        self.output_dir = "output/zero_to_hero"
        self._ensure_output_dirs()
        
        print("🌱 从零开始需求挖掘工作流初始化完成")
        print("🎯 支持从种子词自动发现高价值关键词")
    
    def _ensure_output_dirs(self):
        """确保输出目录存在"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'discovered_keywords'), exist_ok=True)
    
    def discover_keywords_from_seeds(self, seed_words: List[str], target_count: int = 50) -> str:
        """
        从种子词开始发现关键词
        
        Args:
            seed_words: 种子关键词列表
            target_count: 目标发现的关键词数量
            
        Returns:
            生成的关键词文件路径
        """
        print(f"🌱 开始从 {len(seed_words)} 个种子词发现关键词...")
        print(f"🎯 目标发现 {target_count} 个关键词")
        
        discovered_keywords = []
        
        # 方法一：基于词根关键词拓展
        print("\n📊 方法一：基于词根关键词拓展")
        root_keywords = self._expand_from_roots(seed_words)
        discovered_keywords.extend(root_keywords)
        print(f"   发现 {len(root_keywords)} 个词根拓展关键词")
        
        # 方法二：基于AI前缀组合
        print("\n🤖 方法二：基于AI前缀组合")
        ai_keywords = self._generate_ai_combinations(seed_words)
        discovered_keywords.extend(ai_keywords)
        print(f"   发现 {len(ai_keywords)} 个AI组合关键词")
        
        # 方法三：基于竞品分析（模拟）
        print("\n🔍 方法三：基于竞品分析")
        competitor_keywords = self._analyze_competitors(seed_words)
        discovered_keywords.extend(competitor_keywords)
        print(f"   发现 {len(competitor_keywords)} 个竞品关键词")
        
        # 方法四：基于搜索建议（模拟）
        print("\n💡 方法四：基于搜索建议")
        suggestion_keywords = self._get_search_suggestions(seed_words)
        discovered_keywords.extend(suggestion_keywords)
        print(f"   发现 {len(suggestion_keywords)} 个搜索建议关键词")
        
        # 去重并限制数量
        unique_keywords = list(set(discovered_keywords))[:target_count]
        
        # 生成关键词文件
        keywords_file = self._save_discovered_keywords(unique_keywords)
        
        print(f"\n✅ 关键词发现完成！")
        print(f"📊 总计发现 {len(unique_keywords)} 个独特关键词")
        print(f"💾 已保存到: {keywords_file}")
        
        return keywords_file
    
    def _expand_from_roots(self, seed_words: List[str]) -> List[str]:
        """基于核心词根拓展关键词"""
        expanded = []
        
        # 使用需求挖掘管理器的核心词根
        core_roots = self.demand_miner.core_roots
        ai_prefixes = self.demand_miner.ai_prefixes
        
        for seed in seed_words:
            for root in core_roots[:20]:  # 使用前20个词根
                # 组合方式1: seed + root
                expanded.append(f"{seed} {root}")
                # 组合方式2: root + seed  
                expanded.append(f"{root} {seed}")
                
                # AI相关组合
                for ai_prefix in ai_prefixes[:3]:  # 使用前3个AI前缀
                    expanded.append(f"{ai_prefix} {seed} {root}")
        
        return expanded
    
    def _generate_ai_combinations(self, seed_words: List[str]) -> List[str]:
        """生成AI相关关键词组合"""
        ai_combinations = []
        
        ai_prefixes = ['ai', 'artificial intelligence', 'machine learning', 'automated']
        ai_suffixes = ['tool', 'generator', 'assistant', 'maker', 'creator', 'builder']
        modifiers = ['free', 'online', 'best', 'professional', 'advanced']
        
        for seed in seed_words:
            for prefix in ai_prefixes:
                for suffix in ai_suffixes:
                    # 基本组合
                    ai_combinations.append(f"{prefix} {seed} {suffix}")
                    
                    # 带修饰词的组合
                    for modifier in modifiers[:2]:  # 只用前2个修饰词
                        ai_combinations.append(f"{modifier} {prefix} {seed} {suffix}")
        
        return ai_combinations
    
    def _analyze_competitors(self, seed_words: List[str]) -> List[str]:
        """分析竞品关键词（模拟实现）"""
        competitor_keywords = []
        
        # 模拟竞品分析结果
        competitor_patterns = [
            "{seed} alternative",
            "{seed} vs",
            "best {seed} tool",
            "{seed} comparison",
            "free {seed} online",
            "{seed} without registration",
            "{seed} no watermark",
            "professional {seed}",
            "{seed} for business",
            "{seed} api"
        ]
        
        for seed in seed_words:
            for pattern in competitor_patterns:
                competitor_keywords.append(pattern.format(seed=seed))
        
        return competitor_keywords
    
    def _get_search_suggestions(self, seed_words: List[str]) -> List[str]:
        """获取搜索建议（模拟实现）"""
        suggestions = []
        
        # 模拟搜索建议模式
        suggestion_patterns = [
            "how to {seed}",
            "{seed} tutorial",
            "{seed} step by step",
            "learn {seed}",
            "{seed} for beginners",
            "{seed} tips",
            "{seed} examples",
            "{seed} guide",
            "{seed} best practices",
            "why use {seed}"
        ]
        
        for seed in seed_words:
            for pattern in suggestion_patterns:
                suggestions.append(pattern.format(seed=seed))
        
        return suggestions
    
    def _save_discovered_keywords(self, keywords: List[str]) -> str:
        """保存发现的关键词到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"discovered_keywords_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, 'discovered_keywords', filename)
        
        # 创建DataFrame并添加模拟数据
        df_data = []
        for i, keyword in enumerate(keywords):
            # 模拟搜索量、竞争度和CPC数据
            search_volume = max(100, 10000 - i * 100)  # 递减的搜索量
            competition = min(0.9, 0.2 + i * 0.01)     # 递增的竞争度
            cpc = max(0.5, 3.0 - i * 0.05)             # 递减的CPC
            
            df_data.append({
                'query': keyword,
                'search_volume': search_volume,
                'competition': round(competition, 2),
                'cpc': round(cpc, 2)
            })
        
        df = pd.DataFrame(df_data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return filepath
    
    def run_complete_discovery_workflow(self, seed_words: List[str], target_count: int = 30) -> Dict[str, Any]:
        """
        运行完整的从零开始发现工作流
        
        Args:
            seed_words: 种子关键词
            target_count: 目标关键词数量
            
        Returns:
            完整工作流结果
        """
        print("🚀 开始从零到英雄的完整工作流")
        print("=" * 50)
        
        workflow_results = {
            'start_time': datetime.now().isoformat(),
            'seed_words': seed_words,
            'target_count': target_count,
            'steps_completed': [],
            'status': 'running'
        }
        
        try:
            # 步骤1: 从种子词发现关键词
            print(f"🌱 步骤1: 从种子词发现关键词")
            keywords_file = self.discover_keywords_from_seeds(seed_words, target_count)
            workflow_results['steps_completed'].append('keyword_discovery')
            workflow_results['keywords_file'] = keywords_file
            
            # 步骤2: 运行集成工作流
            print(f"\n🔄 步骤2: 运行集成分析和建站工作流")
            integrated_workflow = IntegratedWorkflow({
                'min_opportunity_score': 50,  # 降低阈值以便演示
                'max_projects_per_batch': 3,
                'auto_deploy': False
            })
            
            integrated_results = integrated_workflow.run_complete_workflow(keywords_file)
            workflow_results['steps_completed'].append('integrated_workflow')
            workflow_results['integrated_results'] = integrated_results
            
            workflow_results['end_time'] = datetime.now().isoformat()
            workflow_results['status'] = 'success'
            
            print(f"\n🎉 从零到英雄工作流完成！")
            print(f"🌱 种子词数量: {len(seed_words)}")
            print(f"📊 发现关键词: {target_count}")
            print(f"🎯 高价值关键词: {len(integrated_results.get('high_value_keywords', []))}")
            print(f"🏗️ 生成网站: {len(integrated_results.get('generated_projects', []))}")
            
            return workflow_results
            
        except Exception as e:
            workflow_results['end_time'] = datetime.now().isoformat()
            workflow_results['status'] = 'failed'
            workflow_results['error'] = str(e)
            print(f"❌ 工作流执行失败: {e}")
            return workflow_results


def main():
    """主函数"""
    print("🌱 从零开始需求挖掘演示")
    print("基于路漫漫分享的六大需求挖掘方法")
    print("=" * 50)
    
    # 定义种子词（你的目标领域）
    seed_words = [
        'image',      # 图像处理
        'text',       # 文本处理  
        'video',      # 视频处理
        'code',       # 代码工具
        'pdf'         # 文档处理
    ]
    
    print(f"🎯 种子词: {', '.join(seed_words)}")
    print(f"🎯 目标: 发现AI工具相关的高价值关键词")
    
    try:
        # 创建从零开始工作流
        workflow = ZeroToHeroWorkflow()
        
        # 运行完整发现流程
        results = workflow.run_complete_discovery_workflow(
            seed_words=seed_words,
            target_count=25  # 发现25个关键词用于演示
        )
        
        if results['status'] == 'success':
            print(f"\n✅ 演示成功完成！")
            print(f"📁 关键词文件: {results.get('keywords_file', '')}")
            
            integrated_results = results.get('integrated_results', {})
            if integrated_results.get('report_path'):
                print(f"📋 详细报告: {integrated_results['report_path']}")
        else:
            print(f"\n❌ 演示失败: {results.get('error', '')}")
        
        return 0
        
    except Exception as e:
        print(f"❌ 程序执行异常: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())