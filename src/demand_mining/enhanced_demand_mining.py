#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强版需求挖掘管理器
整合51个网络收集词根，支持手动指定母词和智能关键词发现
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.demand_mining.demand_mining_main import DemandMiningManager
from src.demand_mining.core.root_word_manager import RootWordManager


class EnhancedDemandMiningManager(DemandMiningManager):
    """
    增强版需求挖掘管理器
    基于51个网络收集词根，支持手动指定母词和智能关键词发现
    """
    
    def __init__(self, config_path: str = None, root_config_path: str = None):
        """
        初始化增强版需求挖掘管理器
        
        Args:
            config_path: 主配置文件路径
            root_config_path: 词根配置文件路径
        """
        # 先初始化词根管理器
        self.root_manager = RootWordManager(root_config_path)
        
        # 调用父类初始化
        super().__init__(config_path)
        
        # 使用词根管理器的数据覆盖父类数据
        self.core_roots = self.root_manager.get_active_roots()
        self.ai_prefixes = self.root_manager.ai_prefixes
        
        print("🚀 增强版需求挖掘管理器初始化完成")
        print(f"📊 已整合 {len(self.core_roots)} 个网络收集词根")
        print(f"🔧 词根状态: {'手动指定' if self.root_manager.manual_roots else '默认配置'}")
    
    def set_manual_roots(self, roots: List[str]) -> None:
        """
        手动指定母词
        
        Args:
            roots: 手动指定的词根列表
        """
        self.root_manager.set_manual_roots(roots)
        # 更新当前使用的词根
        self.core_roots = self.root_manager.get_active_roots()
        print(f"✅ 已手动指定 {len(roots)} 个母词")
        print(f"🎯 当前激活词根: {len(self.core_roots)} 个")
        
        # 显示前10个激活词根
        if self.core_roots:
            print(f"📋 激活词根预览: {', '.join(self.core_roots[:10])}{'...' if len(self.core_roots) > 10 else ''}")
    
    def get_root_stats(self) -> Dict[str, Any]:
        """获取词根统计信息"""
        return self.root_manager.get_stats()
    
    def discover_keywords_from_seeds(self, 
                                   seed_words: List[str], 
                                   target_count: int = 50,
                                   include_ai: bool = True) -> List[str]:
        """
        从种子词发现关键词
        
        Args:
            seed_words: 种子词列表
            target_count: 目标关键词数量
            include_ai: 是否包含AI前缀组合
            
        Returns:
            发现的关键词列表
        """
        print(f"🌱 开始从 {len(seed_words)} 个种子词发现关键词...")
        print(f"🎯 目标数量: {target_count}")
        
        # 使用词根管理器生成关键词组合
        combinations = self.root_manager.generate_keyword_combinations(
            seed_words=seed_words,
            include_ai=include_ai,
            max_combinations=target_count
        )
        
        print(f"✅ 发现完成: {len(combinations)} 个关键词")
        return combinations
    
    def analyze_root_coverage(self, keywords: List[str]) -> Dict[str, Any]:
        """
        分析关键词的词根覆盖情况
        
        Args:
            keywords: 关键词列表
            
        Returns:
            词根覆盖分析结果
        """
        return self.root_manager.analyze_root_coverage(keywords)
    
    def suggest_missing_opportunities(self, current_keywords: List[str]) -> List[str]:
        """
        基于词根覆盖分析，建议缺失的机会关键词
        
        Args:
            current_keywords: 当前关键词列表
            
        Returns:
            建议的新关键词列表
        """
        return self.root_manager.suggest_missing_opportunities(current_keywords)
    
    def get_category_keywords(self, category: str, seed_words: List[str]) -> List[str]:
        """
        获取指定类别的关键词
        
        Args:
            category: 工具类别 (如 'content_creation', 'data_processing' 等)
            seed_words: 种子词列表
            
        Returns:
            该类别的关键词列表
        """
        category_roots = self.root_manager.get_category_roots(category)
        if not category_roots:
            print(f"⚠️ 未找到类别 '{category}' 的词根")
            return []
        
        print(f"🏷️ 生成 '{category}' 类别关键词...")
        print(f"📊 类别词根: {len(category_roots)} 个")
        
        keywords = []
        for seed in seed_words:
            for root in category_roots:
                keywords.extend([
                    f"{seed} {root}",
                    f"{root} {seed}",
                    f"ai {seed} {root}",
                    f"free {seed} {root}",
                    f"online {seed} {root}"
                ])
        
        # 去重
        unique_keywords = list(set(keywords))
        print(f"✅ 生成完成: {len(unique_keywords)} 个 '{category}' 类别关键词")
        
        return unique_keywords
    
    def run_enhanced_analysis(self, 
                            input_source: str,
                            analysis_type: str = 'file',
                            output_dir: str = None) -> Dict[str, Any]:
        """
        运行增强版分析
        
        Args:
            input_source: 输入源（文件路径或种子词列表）
            analysis_type: 分析类型 ('file' 或 'seeds')
            output_dir: 输出目录
            
        Returns:
            增强分析结果
        """
        print(f"🚀 开始增强版需求挖掘分析")
        print(f"📊 分析类型: {analysis_type}")
        
        if analysis_type == 'file':
            # 文件分析模式
            if not os.path.exists(input_source):
                raise FileNotFoundError(f"输入文件不存在: {input_source}")
            
            # 调用父类的关键词分析方法
            results = self.analyze_keywords(input_source, output_dir)
            
            # 添加词根覆盖分析
            keywords_list = [kw['keyword'] for kw in results.get('keywords', [])]
            coverage_analysis = self.analyze_root_coverage(keywords_list)
            results['root_coverage'] = coverage_analysis
            
            # 添加机会建议
            opportunity_suggestions = self.suggest_missing_opportunities(keywords_list)
            results['opportunity_suggestions'] = opportunity_suggestions
            
        elif analysis_type == 'seeds':
            # 种子词分析模式
            seed_words = input_source if isinstance(input_source, list) else [input_source]
            
            # 从种子词发现关键词
            discovered_keywords = self.discover_keywords_from_seeds(seed_words, target_count=100)
            
            # 创建临时DataFrame进行分析
            temp_df = pd.DataFrame([{'query': kw} for kw in discovered_keywords])
            
            # 分析发现的关键词
            results = {
                'total_keywords': len(discovered_keywords),
                'analysis_time': datetime.now().isoformat(),
                'seed_words': seed_words,
                'discovered_keywords': discovered_keywords,
                'keywords': [],
                'intent_summary': {},
                'market_insights': {},
                'recommendations': []
            }
            
            # 逐个分析关键词
            for keyword in discovered_keywords:
                # 意图分析
                intent_result = self._analyze_keyword_intent(keyword)
                
                # 市场分析
                market_result = self._analyze_keyword_market(keyword)
                
                # 整合结果
                keyword_result = {
                    'keyword': keyword,
                    'intent': intent_result,
                    'market': market_result,
                    'opportunity_score': self._calculate_opportunity_score(intent_result, market_result)
                }
                
                results['keywords'].append(keyword_result)
            
            # 生成摘要
            results['intent_summary'] = self._generate_intent_summary(results['keywords'])
            results['market_insights'] = self._generate_market_insights(results['keywords'])
            results['recommendations'] = self._generate_recommendations(results['keywords'])
            
            # 添加词根覆盖分析
            coverage_analysis = self.analyze_root_coverage(discovered_keywords)
            results['root_coverage'] = coverage_analysis
            
        else:
            raise ValueError(f"不支持的分析类型: {analysis_type}")
        
        # 保存增强分析结果
        if output_dir:
            output_path = self._save_enhanced_results(results, output_dir, analysis_type)
            results['output_path'] = output_path
        
        print(f"✅ 增强版分析完成!")
        return results
    
    def _save_enhanced_results(self, 
                             results: Dict[str, Any], 
                             output_dir: str,
                             analysis_type: str) -> str:
        """保存增强分析结果"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存主要结果
        main_results_path = self._save_analysis_results(results, output_dir)
        
        # 保存词根覆盖分析
        if 'root_coverage' in results:
            coverage_path = os.path.join(output_dir, f'root_coverage_{timestamp}.json')
            import json
            with open(coverage_path, 'w', encoding='utf-8') as f:
                json.dump(results['root_coverage'], f, ensure_ascii=False, indent=2)
            print(f"📊 词根覆盖分析已保存: {coverage_path}")
        
        # 保存机会建议
        if 'opportunity_suggestions' in results:
            suggestions_path = os.path.join(output_dir, f'opportunity_suggestions_{timestamp}.csv')
            suggestions_df = pd.DataFrame([
                {'suggested_keyword': kw} for kw in results['opportunity_suggestions']
            ])
            suggestions_df.to_csv(suggestions_path, index=False, encoding='utf-8-sig')
            print(f"💡 机会建议已保存: {suggestions_path}")
        
        # 保存发现的关键词（种子词模式）
        if analysis_type == 'seeds' and 'discovered_keywords' in results:
            discovered_path = os.path.join(output_dir, f'discovered_keywords_{timestamp}.csv')
            discovered_df = pd.DataFrame([
                {'keyword': kw} for kw in results['discovered_keywords']
            ])
            discovered_df.to_csv(discovered_path, index=False, encoding='utf-8-sig')
            print(f"🌱 发现的关键词已保存: {discovered_path}")
        
        return main_results_path
    
    def export_root_config(self, output_path: str) -> None:
        """导出词根配置"""
        self.root_manager.export_config(output_path)
    
    def generate_comprehensive_report(self, 
                                    analysis_results: Dict[str, Any],
                                    output_dir: str) -> str:
        """
        生成综合分析报告
        
        Args:
            analysis_results: 分析结果
            output_dir: 输出目录
            
        Returns:
            报告文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(output_dir, f'comprehensive_report_{timestamp}.md')
        
        # 获取统计数据
        total_keywords = analysis_results.get('total_keywords', 0)
        root_coverage = analysis_results.get('root_coverage', {})
        opportunity_suggestions = analysis_results.get('opportunity_suggestions', [])
        
        # 生成报告内容
        report_content = f"""# 增强版需求挖掘综合报告

## 📊 分析概览
- **分析时间**: {analysis_results.get('analysis_time', '')}
- **关键词总数**: {total_keywords}
- **词根覆盖率**: {root_coverage.get('coverage_rate', 0)}%
- **机会建议数**: {len(opportunity_suggestions)}

## 🎯 词根使用情况

### 词根覆盖统计
- **总词根数**: {root_coverage.get('total_roots', 0)}
- **已覆盖词根**: {root_coverage.get('covered_roots', 0)}
- **覆盖率**: {root_coverage.get('coverage_rate', 0)}%

### 使用最多的词根
"""
        
        # 添加词根使用排行
        if 'root_usage' in root_coverage:
            top_roots = list(root_coverage['root_usage'].items())[:10]
            for i, (root, count) in enumerate(top_roots, 1):
                report_content += f"{i}. **{root}**: {count} 次使用\n"
        
        # 添加未使用的词根
        unused_roots = root_coverage.get('unused_roots', [])
        if unused_roots:
            report_content += f"\n### 未使用的词根 ({len(unused_roots)} 个)\n"
            for root in unused_roots[:20]:  # 只显示前20个
                report_content += f"- {root}\n"
        
        # 添加机会建议
        if opportunity_suggestions:
            report_content += f"\n## 💡 机会建议关键词 (前20个)\n"
            for i, suggestion in enumerate(opportunity_suggestions[:20], 1):
                report_content += f"{i}. {suggestion}\n"
        
        # 添加高价值关键词
        high_value_keywords = [
            kw for kw in analysis_results.get('keywords', [])
            if kw.get('opportunity_score', 0) >= 70
        ]
        
        if high_value_keywords:
            report_content += f"\n## 🌟 高价值关键词 ({len(high_value_keywords)} 个)\n"
            for kw in high_value_keywords[:15]:
                report_content += f"- **{kw['keyword']}** (分数: {kw.get('opportunity_score', 0)})\n"
        
        # 添加建议
        report_content += f"""
## 📈 优化建议

### 词根优化
- 重点关注未使用的 {len(unused_roots)} 个词根，可能存在新机会
- 深入挖掘使用频率低的词根组合
- 考虑添加行业特定的词根

### 关键词拓展
- 基于高价值关键词进行长尾拓展
- 结合AI前缀创造新的关键词组合
- 关注竞争度较低的新兴词根

### 市场机会
- 优先开发机会分数70+的关键词对应产品
- 关注AI相关和新兴技术关键词
- 建立关键词监控和定期更新机制

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        # 保存报告
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📋 综合报告已生成: {report_path}")
        return report_path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='增强版需求挖掘工具 - 整合51个网络收集词根')
    parser.add_argument('--action', choices=['analyze', 'discover', 'category', 'report', 'help'], 
                       default='help', help='执行的操作')
    parser.add_argument('--input', help='输入文件路径或种子词（逗号分隔）')
    parser.add_argument('--output', help='输出目录路径')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--root-config', help='词根配置文件路径')
    parser.add_argument('--manual-roots', help='手动指定词根（逗号分隔）')
    parser.add_argument('--category', help='工具类别名称')
    parser.add_argument('--target-count', type=int, default=50, help='目标关键词数量')
    
    args = parser.parse_args()
    
    if args.action == 'help':
        print("""
🚀 增强版需求挖掘工具 - 整合51个网络收集词根

使用方法:
  # 分析关键词文件
  python enhanced_demand_mining.py --action analyze --input data/keywords.csv
  
  # 从种子词发现关键词
  python enhanced_demand_mining.py --action discover --input "image,text,video"
  
  # 生成特定类别关键词
  python enhanced_demand_mining.py --action category --category content_creation --input "image,text"
  
  # 手动指定词根
  python enhanced_demand_mining.py --action discover --input "image,text" --manual-roots "generator,converter,editor"

操作说明:
  analyze   - 分析关键词文件
  discover  - 从种子词发现关键词
  category  - 生成特定类别关键词
  report    - 生成综合报告
  help      - 显示帮助信息

类别选项:
  content_creation  - 内容创作工具
  data_processing   - 数据处理工具
  media_editing     - 媒体编辑工具
  quality_assurance - 质量保证工具
  productivity      - 生产力工具
  search_discovery  - 搜索发现工具
  file_management   - 文件管理工具
  maintenance       - 维护工具
        """)
        return
    
    try:
        # 初始化增强版管理器
        manager = EnhancedDemandMiningManager(args.config, args.root_config)
        
        # 手动指定词根
        if args.manual_roots:
            manual_roots = [root.strip() for root in args.manual_roots.split(',')]
            manager.set_manual_roots(manual_roots)
        
        # 显示词根统计
        stats = manager.get_root_stats()
        print(f"\n📊 词根统计: {stats}")
        
        if args.action == 'analyze':
            if not args.input:
                print("❌ 错误: 请指定输入文件 (--input)")
                return
            
            results = manager.run_enhanced_analysis(
                input_source=args.input,
                analysis_type='file',
                output_dir=args.output or 'output/enhanced_analysis'
            )
            
            print(f"🎉 文件分析完成! 共分析 {results['total_keywords']} 个关键词")
            print(f"📊 词根覆盖率: {results.get('root_coverage', {}).get('coverage_rate', 0)}%")
            
        elif args.action == 'discover':
            if not args.input:
                print("❌ 错误: 请指定种子词 (--input)")
                return
            
            seed_words = [word.strip() for word in args.input.split(',')]
            results = manager.run_enhanced_analysis(
                input_source=seed_words,
                analysis_type='seeds',
                output_dir=args.output or 'output/enhanced_analysis'
            )
            
            print(f"🌱 种子词发现完成! 从 {len(seed_words)} 个种子词发现 {len(results['discovered_keywords'])} 个关键词")
            
        elif args.action == 'category':
            if not args.category or not args.input:
                print("❌ 错误: 请指定类别和种子词 (--category --input)")
                return
            
            seed_words = [word.strip() for word in args.input.split(',')]
            category_keywords = manager.get_category_keywords(args.category, seed_words)
            
            # 保存类别关键词
            output_dir = args.output or 'output/category_keywords'
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(output_dir, f'{args.category}_keywords_{timestamp}.csv')
            
            df = pd.DataFrame([{'keyword': kw} for kw in category_keywords])
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            print(f"🏷️ {args.category} 类别关键词生成完成!")
            print(f"📊 生成数量: {len(category_keywords)}")
            print(f"💾 已保存到: {output_file}")
            
        elif args.action == 'report':
            print("📋 生成综合报告功能需要先运行分析...")
            
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()