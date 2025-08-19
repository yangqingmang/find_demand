#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一需求挖掘主程序
整合所有需求挖掘功能的统一入口
"""

import argparse
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.demand_mining.managers import KeywordManager, DiscoveryManager, TrendManager


class UnifiedDemandMiningManager:
    """统一需求挖掘管理器 - 整合所有功能"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        
        # 初始化各个管理器
        self.keyword_manager = KeywordManager(config_path)
        self.discovery_manager = DiscoveryManager(config_path)
        self.trend_manager = TrendManager(config_path)
        
        self.enhanced_features_available = self._check_enhanced_features()
        
        print("🚀 统一需求挖掘管理器初始化完成")
        print("📊 已加载关键词管理器、发现管理器、趋势管理器")
    
    def _check_enhanced_features(self) -> bool:
        """检查增强功能是否可用"""
        try:
            from src.utils.enhanced_features import monitor_competitors
            return True
        except ImportError:
            return False
    
    def run_unified_analysis(self, **kwargs) -> Dict[str, Any]:
        """运行统一分析流程"""
        analysis_type = kwargs.get('analysis_type', 'keywords')
        
        if analysis_type == 'keywords':
            return self._run_keyword_analysis(**kwargs)
        elif analysis_type == 'discovery':
            return self._run_keyword_discovery(**kwargs)
        elif analysis_type == 'root_trends':
            return self._run_root_trends_analysis(**kwargs)
        elif analysis_type == 'competitor':
            return self._run_competitor_analysis(**kwargs)
        else:
            raise ValueError(f"不支持的分析类型: {analysis_type}")
    
    def _run_keyword_analysis(self, **kwargs) -> Dict[str, Any]:
        """运行关键词分析"""
        input_file = kwargs.get('input_file')
        keywords = kwargs.get('keywords')
        output_dir = kwargs.get('output_dir')
        
        if input_file:
            return self.keyword_manager.analyze(input_file, 'file', output_dir)
        elif keywords:
            return self.keyword_manager.analyze(keywords, 'keywords', output_dir)
        else:
            raise ValueError("请提供输入文件或关键词列表")
    
    def _run_keyword_discovery(self, **kwargs) -> Dict[str, Any]:
        """运行关键词发现"""
        search_terms = kwargs.get('search_terms', ['AI tool', 'AI generator'])
        output_dir = kwargs.get('output_dir')
        
        return self.discovery_manager.analyze(search_terms, output_dir)
    
    def _run_root_trends_analysis(self, **kwargs) -> Dict[str, Any]:
        """运行词根趋势分析"""
        output_dir = kwargs.get('output_dir')
        timeframe = kwargs.get('timeframe', '12-m')
        batch_size = kwargs.get('batch_size', 5)
        
        return self.trend_manager.analyze(
            'root_trends',
            timeframe=timeframe,
            batch_size=batch_size,
            output_dir=output_dir
        )
    
    def _run_competitor_analysis(self, **kwargs) -> Dict[str, Any]:
        """运行竞品分析"""
        if not self.enhanced_features_available:
            return {'error': '增强功能不可用'}
        
        try:
            from src.utils.enhanced_features import monitor_competitors
            
            sites = kwargs.get('sites', ['canva.com', 'midjourney.com'])
            output_dir = kwargs.get('output_dir')
            
            return monitor_competitors(sites, output_dir)
        except Exception as e:
            return {'error': f'竞品分析失败: {e}'}
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """获取所有管理器的统计信息"""
        return {
            'keyword_manager': self.keyword_manager.get_stats(),
            'discovery_manager': self.discovery_manager.get_discovery_stats(),
            'trend_manager': self.trend_manager.get_stats(),
            'enhanced_features_available': self.enhanced_features_available
        }


def main():
    """统一主函数"""
    parser = argparse.ArgumentParser(
        description='统一需求挖掘分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🎯 统一功能入口:
  
基础分析:
  --analyze-file FILE        分析关键词文件
  --analyze-keywords KW...   分析指定关键词
  --discover TERMS...        多平台关键词发现
  --root-trends             词根趋势分析
  
增强功能:
  --competitor-analysis      竞品分析
  --trend-prediction        趋势预测
  --seo-audit DOMAIN        SEO审计
  
使用示例:
  # 分析文件
  python unified_main.py --analyze-file data/keywords.csv
  
  # 分析关键词
  python unified_main.py --analyze-keywords "ai tool" "ai generator"
  
  # 多平台发现
  python unified_main.py --discover "AI image" "AI text"
  
  # 词根趋势
  python unified_main.py --root-trends
  
  # 竞品分析
  python unified_main.py --competitor-analysis --sites canva.com midjourney.com
        """
    )
    
    # 基础分析选项
    analysis_group = parser.add_mutually_exclusive_group()
    analysis_group.add_argument('--analyze-file', help='分析关键词文件')
    analysis_group.add_argument('--analyze-keywords', nargs='+', help='分析指定关键词')
    analysis_group.add_argument('--discover', nargs='*', help='多平台关键词发现')
    analysis_group.add_argument('--root-trends', action='store_true', help='词根趋势分析')
    analysis_group.add_argument('--competitor-analysis', action='store_true', help='竞品分析')
    
    # 增强功能选项
    parser.add_argument('--sites', nargs='+', help='竞品网站列表')
    parser.add_argument('--trend-prediction', action='store_true', help='趋势预测')
    parser.add_argument('--seo-audit', help='SEO审计域名')
    
    # 通用选项
    parser.add_argument('--output', help='输出目录')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细模式')
    parser.add_argument('--stats', action='store_true', help='显示管理器统计信息')
    
    args = parser.parse_args()
    
    # 如果没有指定任何操作，显示帮助
    if not any([args.analyze_file, args.analyze_keywords, args.discover is not None, 
                args.root_trends, args.competitor_analysis, args.stats]):
        parser.print_help()
        return
    
    try:
        # 创建统一管理器
        manager = UnifiedDemandMiningManager(args.config)
        
        # 显示管理器统计信息
        if args.stats:
            stats = manager.get_manager_stats()
            print("\n📊 管理器统计信息:")
            for manager_name, manager_stats in stats.items():
                if isinstance(manager_stats, dict):
                    print(f"\n{manager_name}:")
                    for key, value in manager_stats.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"{manager_name}: {manager_stats}")
            return
        
        # 确定分析类型和参数
        if args.analyze_file:
            result = manager.run_unified_analysis(
                analysis_type='keywords',
                input_file=args.analyze_file,
                output_dir=args.output
            )
            if not args.quiet:
                print(f"✅ 文件分析完成: {result.get('total_keywords', 0)} 个关键词")
                if 'market_insights' in result:
                    print(f"📊 高机会关键词: {result['market_insights'].get('high_opportunity_count', 0)} 个")
        
        elif args.analyze_keywords:
            result = manager.run_unified_analysis(
                analysis_type='keywords',
                keywords=args.analyze_keywords,
                output_dir=args.output
            )
            if not args.quiet:
                print(f"✅ 关键词分析完成: {len(args.analyze_keywords)} 个关键词")
                if 'market_insights' in result:
                    print(f"📊 高机会关键词: {result['market_insights'].get('high_opportunity_count', 0)} 个")
        
        elif args.discover is not None:
            search_terms = args.discover if args.discover else ['AI tool', 'AI generator']
            result = manager.run_unified_analysis(
                analysis_type='discovery',
                search_terms=search_terms,
                output_dir=args.output
            )
            if not args.quiet:
                if 'error' in result:
                    print(f"❌ 发现失败: {result['error']}")
                else:
                    print(f"✅ 关键词发现完成: {result.get('total_keywords', 0)} 个关键词")
                    if 'platform_distribution' in result:
                        print(f"🌐 平台分布: {result['platform_distribution']}")
        
        elif args.root_trends:
            result = manager.run_unified_analysis(
                analysis_type='root_trends',
                output_dir=args.output
            )
            if not args.quiet:
                print(f"✅ 词根趋势分析完成: {result.get('successful_analyses', 0)} 个词根")
                if result.get('top_trending_words'):
                    print(f"📈 上升趋势词根: {len(result['top_trending_words'])} 个")
        
        elif args.competitor_analysis:
            sites = args.sites or ['canva.com', 'midjourney.com']
            result = manager.run_unified_analysis(
                analysis_type='competitor',
                sites=sites,
                output_dir=args.output
            )
            if not args.quiet:
                if 'error' in result:
                    print(f"❌ 竞品分析失败: {result['error']}")
                else:
                    print(f"✅ 竞品分析完成: {len(result.get('competitors', []))} 个竞品")
        
        # 显示详细结果
        if args.verbose and 'error' not in result:
            print(f"\n📊 详细结果:")
            for key, value in result.items():
                if key not in ['keywords', 'output_files', 'keyword_trends']:
                    if isinstance(value, (int, float, str)):
                        print(f"  {key}: {value}")
                    elif isinstance(value, dict) and len(value) < 10:
                        print(f"  {key}: {value}")
        
        # 显示输出文件路径
        if 'output_path' in result:
            print(f"\n📁 详细结果已保存到: {result['output_path']}")
        elif 'output_files' in result:
            print(f"\n📁 结果已保存:")
            for file_type, file_path in result['output_files'].items():
                print(f"  {file_type.upper()}: {file_path}")
    
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()