#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
需求挖掘分析工具 - 统一主入口文件
整合六大需求挖掘方法的完整执行入口
"""

import argparse
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

def get_reports_dir() -> str:
    """从配置文件获取报告输出目录"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config/integrated_workflow_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('output_settings', {}).get('reports_dir', 'output/reports')
    except:
        pass
    return 'output/reports'
from src.demand_mining.tools.multi_platform_keyword_discovery import MultiPlatformKeywordDiscovery
from src.utils.enhanced_features import (
        monitor_competitors, predict_keyword_trends, generate_seo_audit,
        batch_build_websites
    )
# 直接导入需求挖掘管理器组件
from src.demand_mining.managers import KeywordManager, DiscoveryManager, TrendManager
from src.utils.logger import setup_logger

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


class IntegratedDemandMiningManager:
    """集成需求挖掘管理器 - 统一所有功能"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.logger = setup_logger(__name__)
        
        # 初始化各个管理器
        self.keyword_manager = KeywordManager(config_path)
        self.discovery_manager = DiscoveryManager(config_path)
        self.trend_manager = TrendManager(config_path)
        
        # 初始化新词检测器
        try:
            from src.demand_mining.analyzers.new_word_detector import NewWordDetector
            self.new_word_detector = NewWordDetector()
            self.new_word_detection_available = True
            print("✅ 新词检测器初始化成功")
        except ImportError as e:
            self.new_word_detector = None
            self.new_word_detection_available = False
            print(f"⚠️ 新词检测器初始化失败: {e}")

        print("🚀 集成需求挖掘管理器初始化完成")
        print("📊 已加载关键词管理器、发现管理器、趋势管理器")
        if self.new_word_detection_available:
            print("🔍 新词检测功能已启用")

    def analyze_keywords(self, input_file: str, output_dir: str = None, enable_serp: bool = False) -> Dict[str, Any]:
        """分析关键词文件（包含新词检测和可选的SERP分析）"""
        # 执行基础关键词分析
        result = self.keyword_manager.analyze(input_file, 'file', output_dir)

        # 如果启用SERP分析，执行SERP分析
        if enable_serp:
            try:
                print("🔍 正在进行SERP分析...")
                result = self._perform_serp_analysis(result, input_file)
                print("✅ SERP分析完成")
            except Exception as e:
                print(f"⚠️ SERP分析失败: {e}")
                result['serp_analysis_error'] = str(e)

        # 添加新词检测
        if self.new_word_detection_available:
            try:
                print("🔍 正在进行新词检测...")

                # 读取关键词数据
                import pandas as pd
                df = pd.read_csv(input_file)

                # 执行新词检测
                new_word_results = self.new_word_detector.detect_new_words(df)

                # 将新词检测结果合并到分析结果中
                if 'keywords' in result:
                    for i, keyword_data in enumerate(result['keywords']):
                        if i < len(new_word_results):
                            # 添加新词检测信息
                            row = new_word_results.iloc[i]
                            keyword_data['new_word_detection'] = {
                                'is_new_word': bool(row.get('is_new_word', False)),
                                'new_word_score': float(row.get('new_word_score', 0)),
                                'new_word_grade': str(row.get('new_word_grade', 'D')),
                                'growth_rate_7d': float(row.get('growth_rate_7d', 0)),
                                'confidence_level': str(row.get('confidence_level', 'low'))
                            }

                            # 如果是新词，增加机会分数加成
                            if row.get('is_new_word', False):
                                original_score = keyword_data.get('opportunity_score', 0)
                                new_word_bonus = row.get('new_word_score', 0) * 0.1  # 10%加成
                                keyword_data['opportunity_score'] = min(100, original_score + new_word_bonus)
                                keyword_data['new_word_bonus'] = new_word_bonus

                # 生成新词检测摘要
                new_words_count = len(new_word_results[new_word_results['is_new_word'] == True])
                high_confidence_count = len(new_word_results[new_word_results['confidence_level'] == 'high'])

                result['new_word_summary'] = {
                    'total_analyzed': len(new_word_results),
                    'new_words_detected': new_words_count,
                    'high_confidence_new_words': high_confidence_count,
                    'new_word_percentage': round(new_words_count / len(new_word_results) * 100, 1) if len(new_word_results) > 0 else 0
                }

                print(f"✅ 新词检测完成: 发现 {new_words_count} 个新词 ({high_confidence_count} 个高置信度)")

            except Exception as e:
                print(f"⚠️ 新词检测失败: {e}")
                result['new_word_summary'] = {
                    'error': str(e),
                    'new_words_detected': 0
                }

        return result

    def _perform_serp_analysis(self, result: Dict[str, Any], input_file: str) -> Dict[str, Any]:
        """执行SERP分析"""
        try:
            from src.demand_mining.analyzers.serp_analyzer import SerpAnalyzer
            
            # 初始化SERP分析器
            serp_analyzer = SerpAnalyzer()
            
            # 读取关键词数据
            import pandas as pd
            df = pd.read_csv(input_file)
            
            # 对每个关键词进行SERP分析
            serp_results = []
            total_keywords = len(df)
            
            for i, row in df.iterrows():
                keyword = row.get('query', row.get('keyword', ''))
                if keyword:
                    print(f"  分析关键词 {i+1}/{total_keywords}: {keyword}")
                    serp_result = serp_analyzer.analyze_keyword_serp(keyword)
                    serp_results.append({
                        'keyword': keyword,
                        'serp_features': serp_result.get('serp_features', {}),
                        'serp_intent': serp_result.get('intent', 'I'),
                        'serp_confidence': serp_result.get('confidence', 0.0),
                        'serp_secondary_intent': serp_result.get('secondary_intent', None)
                    })
            
            # 将SERP分析结果合并到原结果中
            if 'keywords' in result and serp_results:
                for i, keyword_data in enumerate(result['keywords']):
                    if i < len(serp_results):
                        serp_data = serp_results[i]
                        keyword_data['serp_analysis'] = {
                            'features': serp_data['serp_features'],
                            'intent': serp_data['serp_intent'],
                            'confidence': serp_data['serp_confidence'],
                            'secondary_intent': serp_data['serp_secondary_intent']
                        }
                        
                        # 如果SERP分析置信度高，可以调整机会分数
                        if serp_data['serp_confidence'] > 0.8:
                            original_score = keyword_data.get('opportunity_score', 0)
                            serp_bonus = serp_data['serp_confidence'] * 5  # 最多5分加成
                            keyword_data['opportunity_score'] = min(100, original_score + serp_bonus)
                            keyword_data['serp_bonus'] = serp_bonus
            
            # 生成SERP分析摘要
            high_confidence_serp = len([r for r in serp_results if r['serp_confidence'] > 0.8])
            commercial_intent = len([r for r in serp_results if r['serp_intent'] in ['C', 'T']])
            
            result['serp_summary'] = {
                'total_analyzed': len(serp_results),
                'high_confidence_serp': high_confidence_serp,
                'commercial_intent_keywords': commercial_intent,
                'serp_analysis_enabled': True
            }
            
            return result
            
        except ImportError:
            print("⚠️ SERP分析器未找到，跳过SERP分析")
            result['serp_summary'] = {
                'error': 'SERP分析器未找到',
                'serp_analysis_enabled': False
            }
            return result
        except Exception as e:
            print(f"⚠️ SERP分析过程中出错: {e}")
            result['serp_summary'] = {
                'error': str(e),
                'serp_analysis_enabled': False
            }
            return result
    
    def analyze_root_words(self, output_dir: str = None) -> Dict[str, Any]:
        """分析词根趋势"""
        try:
            # 使用已有的趋势管理器，避免创建新的分析器实例
            analyzer_output_dir = output_dir or f"{get_reports_dir()}/root_word_trends"
            
            # 直接使用趋势管理器进行分析
            results = self.trend_manager.analyze(
                'root_trends',
                timeframe="now 7-d",
                batch_size=5,
                output_dir=analyzer_output_dir
            )
            
            # 检查结果是否为空
            if results is None:
                results = {
                    'total_root_words': 0,
                    'summary': {
                        'successful_analyses': 0,
                        'failed_analyses': 0,
                        'top_trending_words': [],
                        'declining_words': [],
                        'stable_words': []
                    }
                }
            
            # 转换为兼容格式
            return {
                'total_root_words': results.get('total_root_words', 0),
                'successful_analyses': results.get('summary', {}).get('successful_analyses', 0),
                'failed_analyses': results.get('summary', {}).get('failed_analyses', 0),
                'top_trending_words': results.get('summary', {}).get('top_trending_words', []),
                'declining_words': results.get('summary', {}).get('declining_words', []),
                'stable_words': results.get('summary', {}).get('stable_words', []),
                'output_path': analyzer_output_dir
            }
            
        except Exception as e:
            self.logger.error(f"词根趋势分析失败: {e}")
            return {
                'error': f'词根趋势分析失败: {e}',
                'total_root_words': 0,
                'successful_analyses': 0,
                'top_trending_words': []
            }
    
    
    def generate_daily_report(self, date: str = None) -> str:
        """生成日报"""
        report_date = date or datetime.now().strftime("%Y-%m-%d")
        report_path = f"{get_reports_dir()}/daily_report_{report_date}.txt"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"需求挖掘日报 - {report_date}\n")
                f.write("=" * 50 + "\n\n")
                
                # 获取各管理器统计
                stats = self.get_manager_stats()
                for manager_name, manager_stats in stats.items():
                    f.write(f"{manager_name}:\n")
                    if isinstance(manager_stats, dict):
                        for key, value in manager_stats.items():
                            f.write(f"  {key}: {value}\n")
                    else:
                        f.write(f"  状态: {manager_stats}\n")
                    f.write("\n")
            
            return report_path
        except Exception as e:
            return f"报告生成失败: {e}"

    def get_manager_stats(self) -> Dict[str, Any]:
        """获取所有管理器的统计信息"""
        return {
            'keyword_manager': self.keyword_manager.get_stats(),
            'discovery_manager': self.discovery_manager.get_discovery_stats(),
            'trend_manager': self.trend_manager.get_stats(),
        }


def print_quiet_summary(result):
    """静默模式下的简要结果显示"""
    print("\n🎯 需求挖掘分析结果摘要:")
    print(f"   • 关键词总数: {result.get('total_keywords', 0)}")
    print(f"   • 高机会关键词: {result.get('market_insights', {}).get('high_opportunity_count', 0)}")
    print(f"   • 平均机会分数: {result.get('market_insights', {}).get('avg_opportunity_score', 0)}")
    
    # 显示Top 3关键词
    top_keywords = result.get('market_insights', {}).get('top_opportunities', [])[:3]
    if top_keywords:
        print("\n🏆 Top 3 机会关键词:")
        for i, kw in enumerate(top_keywords):
            intent_desc = kw.get('intent', {}).get('intent_description', '未知')
            score = kw.get('opportunity_score', 0)
            print(f"   {i+1}. {kw['keyword']} (机会分数: {score}, 意图: {intent_desc})")


def main():
    """主函数 - 提供统一的执行入口"""
    
    print("🔍 需求挖掘分析工具 v2.0")
    print("整合六大需求挖掘方法的智能分析系统")
    print("=" * 60)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='需求挖掘分析工具 - 整合六大挖掘方法',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🎯 六大需求挖掘方法:
  1. 基于词根关键词拓展 (52个核心词根)
  2. 基于SEO大站流量分析 (8个竞品网站)
  3. 搜索引擎下拉推荐
  4. 循环挖掘法
  5. 付费广告关键词分析
  6. 收入排行榜分析

📋 使用示例:
  # 分析关键词文件
  python main.py --input data/keywords.csv
  
  # 分析关键词文件并启用SERP分析
  python main.py --input data/keywords.csv --serp
  
  # 分析单个关键词
  python main.py --keywords "ai generator" "ai converter"
  
  # 分析单个关键词并启用SERP分析
  python main.py --keywords "AI" --serp
  
  # 多平台关键词发现
  python main.py --discover "AI image generator" "AI writing tool"
  
  # 使用默认搜索词进行多平台发现
  python main.py --discover default
  
  # 生成分析报告
  python main.py --report

  # 使用51个词根进行趋势分析
  python main.py --use-root-words

  # 静默模式分析
  python main.py --input data/keywords.csv --quiet

🚀 增强功能示例:
  # 监控竞品关键词变化
  python main.py --monitor-competitors --sites canva.com midjourney.com

  # 预测关键词趋势
  python main.py --predict-trends --timeframe 30d

  # SEO审计
  python main.py --seo-audit --domain your-site.com --keywords "ai tool" "ai generator"

  # 批量生成网站
  python main.py --build-websites --top-keywords 5
        """
    )
    
    # 输入方式选择 - 修改为非必需，支持默认词根分析
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument('--input', help='输入CSV文件路径')
    input_group.add_argument('--keywords', nargs='+', help='直接输入关键词（可以是多个）')
    input_group.add_argument('--discover', nargs='+', help='多平台关键词发现（可指定搜索词汇）')
    input_group.add_argument('--report', action='store_true', help='生成今日分析报告')
    
    # 增强功能组
    enhanced_group = parser.add_argument_group('增强功能')
    enhanced_group.add_argument('--monitor-competitors', action='store_true', help='监控竞品关键词变化')
    enhanced_group.add_argument('--sites', nargs='+', help='竞品网站列表')
    enhanced_group.add_argument('--predict-trends', action='store_true', help='预测关键词趋势')
    enhanced_group.add_argument('--timeframe', default='30d', help='预测时间范围')
    enhanced_group.add_argument('--seo-audit', action='store_true', help='生成SEO优化建议')
    enhanced_group.add_argument('--domain', help='要审计的域名')
    enhanced_group.add_argument('--build-websites', action='store_true', help='批量生成网站')
    enhanced_group.add_argument('--top-keywords', type=int, default=10, help='使用前N个关键词')

    # 其他参数
    parser.add_argument('--output', default=get_reports_dir(), help='输出目录')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式，只显示最终结果')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细模式，显示所有中间过程')
    parser.add_argument('--stats', action='store_true', help='显示管理器统计信息')
    parser.add_argument('--use-root-words', action='store_true', help='使用51个词根进行趋势分析')
    parser.add_argument('--serp', action='store_true', help='启用SERP分析功能')
    
    args = parser.parse_args()
    
    # 显示分析参数
    if not args.quiet:
        if args.input:
            print(f"📁 输入文件: {args.input}")
        elif args.keywords:
            print(f"🔤 分析关键词: {', '.join(args.keywords)}")
        elif args.report:
            print("📊 生成今日分析报告")
        print(f"📂 输出目录: {args.output}")
        print("")
    
    try:
        # 创建集成需求挖掘管理器
        manager = IntegratedDemandMiningManager(args.config)
        
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
        
        if args.input:
            # 分析关键词文件
            if not args.quiet:
                print("🚀 开始分析关键词文件...")
                if args.serp:
                    print("🔍 已启用SERP分析功能")
            
            result = manager.analyze_keywords(args.input, args.output, enable_serp=args.serp)
            
            # 显示结果
            if args.quiet:
                print_quiet_summary(result)
            else:
                print(f"\n🎉 分析完成! 共分析 {result['total_keywords']} 个关键词")
                print(f"📊 高机会关键词: {result['market_insights']['high_opportunity_count']} 个")
                print(f"📈 平均机会分数: {result['market_insights']['avg_opportunity_score']}")
                
                # 显示新词检测摘要
                if 'new_word_summary' in result and result['new_word_summary'].get('new_words_detected', 0) > 0:
                    summary = result['new_word_summary']
                    print(f"🔍 新词检测: 发现 {summary['new_words_detected']} 个新词 ({summary['new_word_percentage']}%)")
                    print(f"   高置信度新词: {summary['high_confidence_new_words']} 个")

                # 显示SERP分析摘要
                if 'serp_summary' in result and result['serp_summary'].get('serp_analysis_enabled', False):
                    serp_summary = result['serp_summary']
                    print(f"🔍 SERP分析: 分析了 {serp_summary['total_analyzed']} 个关键词")
                    print(f"   高置信度SERP: {serp_summary['high_confidence_serp']} 个")
                    print(f"   商业意图关键词: {serp_summary['commercial_intent_keywords']} 个")

                # 显示Top 5关键词
                top_keywords = result['market_insights']['top_opportunities'][:5]
                if top_keywords:
                    print("\n🏆 Top 5 机会关键词:")
                    for i, kw in enumerate(top_keywords, 1):
                        intent_desc = kw['intent']['intent_description']
                        score = kw['opportunity_score']
                        new_word_info = ""
                        if 'new_word_detection' in kw and kw['new_word_detection']['is_new_word']:
                            new_word_grade = kw['new_word_detection']['new_word_grade']
                            new_word_info = f" [新词-{new_word_grade}级]"
                        print(f"   {i}. {kw['keyword']} (分数: {score}, 意图: {intent_desc}){new_word_info}")
        
        elif args.keywords:
            # 分析单个关键词
            if not args.quiet:
                print("🚀 开始分析输入的关键词...")
            
            # 创建临时CSV文件
            import pandas as pd
            import tempfile
            
            temp_df = pd.DataFrame([{'query': kw} for kw in args.keywords])
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
                temp_df.to_csv(f.name, index=False)
                temp_file = f.name
            
            try:
                result = manager.analyze_keywords(temp_file, args.output, enable_serp=args.serp)
                
                # 显示结果
                if args.quiet:
                    print_quiet_summary(result)
                else:
                    print(f"\n🎉 分析完成! 共分析 {len(args.keywords)} 个关键词")
                    
                    # 显示每个关键词的结果
                    print("\n📋 关键词分析结果:")
                    for kw_result in result['keywords']:
                        keyword = kw_result['keyword']
                        score = kw_result['opportunity_score']
                        intent = kw_result['intent']['intent_description']
                        print(f"   • {keyword}: 机会分数 {score}, 意图: {intent}")
            finally:
                # 清理临时文件
                os.unlink(temp_file)
        
        elif args.discover:
            # 多平台关键词发现
            search_terms = args.discover if args.discover != ['default'] else ['AI tool', 'AI generator', 'AI assistant']
            
            if not args.quiet:
                print("🔍 开始多平台关键词发现...")
                print(f"📊 搜索词汇: {', '.join(search_terms)}")
            
            try:
                # 导入多平台发现工具

                
                # 创建发现工具
                discoverer = MultiPlatformKeywordDiscovery()
                
                # 执行发现
                df = discoverer.discover_all_platforms(search_terms)


                if not df.empty:
                    # 分析趋势
                    analysis = discoverer.analyze_keyword_trends(df)
                    
                    # 保存结果
                    output_dir = os.path.join(args.output, 'multi_platform_discovery')
                    csv_path, json_path = discoverer.save_results(df, analysis, output_dir)
                    
                    if args.quiet:
                        # 静默模式显示
                        print(f"\n🎯 多平台关键词发现结果:")
                        print(f"   • 发现关键词: {analysis['total_keywords']} 个")
                        print(f"   • 平台分布: {analysis['platform_distribution']}")
                        
                        # 显示Top 3关键词
                        top_keywords = analysis['top_keywords_by_score'][:3]
                        if top_keywords:
                            print("\n🏆 Top 3 热门关键词:")
                            for i, kw in enumerate(top_keywords, 1):
                                print(f"   {i}. {kw['keyword']} (评分: {kw['score']}, 来源: {kw['platform']})")
                    else:
                        # 详细模式显示
                        print(f"\n🎉 多平台关键词发现完成!")
                        print(f"📊 发现 {analysis['total_keywords']} 个关键词")
                        print(f"🌐 平台分布: {analysis['platform_distribution']}")
                        
                        print(f"\n🏆 热门关键词:")
                        for i, kw in enumerate(analysis['top_keywords_by_score'][:5], 1):
                            print(f"  {i}. {kw['keyword']} (评分: {kw['score']}, 来源: {kw['platform']})")
                    
                    print(f"\n📁 结果已保存:")
                    print(f"  CSV: {csv_path}")
                    print(f"  JSON: {json_path}")
                    
                    # 询问是否要立即分析发现的关键词
                    if not args.quiet:
                        user_input = input("\n🤔 是否要立即分析这些关键词的意图和市场机会? (y/n): ")
                        if user_input.lower() in ['y', 'yes', '是']:
                            print("🔄 开始分析发现的关键词...")
                            result = manager.analyze_keywords(csv_path, args.output)
                            print(f"✅ 关键词分析完成! 共分析 {result['total_keywords']} 个关键词")
                            print(f"📊 高机会关键词: {result['market_insights']['high_opportunity_count']} 个")
                else:
                    print("⚠️ 未发现任何关键词，请检查网络连接或调整搜索参数")
                    
            except ImportError as e:
                print(f"❌ 导入多平台发现工具失败: {e}")
                print("请确保所有依赖已正确安装")
            except Exception as e:
                print(f"❌ 多平台关键词发现失败: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
        
        elif args.monitor_competitors:
            # 竞品监控
            sites = args.sites or ['canva.com', 'midjourney.com', 'openai.com']
            if not args.quiet:
                print(f"🔍 开始监控 {len(sites)} 个竞品网站...")
            
            result = monitor_competitors(sites, args.output)
            print(f"✅ 竞品监控完成: 分析了 {len(result['competitors'])} 个竞品")
            
            if not args.quiet:
                print("\n📊 监控结果摘要:")
                for comp in result['competitors'][:3]:
                    print(f"  • {comp['site']}: {comp['new_keywords_count']} 个新关键词")
        
        elif args.predict_trends:
            # 趋势预测
            if not args.quiet:
                print(f"📈 开始预测未来 {args.timeframe} 的关键词趋势...")
            
            result = predict_keyword_trends(args.timeframe, args.output)
            print(f"✅ 趋势预测完成: 预测了 {len(result['rising_keywords'])} 个上升关键词")
            
            if not args.quiet:
                print("\n📈 趋势预测摘要:")
                for kw in result['rising_keywords'][:3]:
                    print(f"  📈 {kw['keyword']}: {kw['predicted_growth']} (置信度: {kw['confidence']:.0%})")
        
        elif args.seo_audit:
            # SEO审计
            if not args.domain:
                print("❌ 请指定要审计的域名 (--domain)")
                return
            
            if not args.quiet:
                print(f"🔍 开始SEO审计: {args.domain}")
            
            result = generate_seo_audit(args.domain, args.keywords)
            print(f"✅ SEO审计完成: 发现 {len(result['keyword_opportunities'])} 个关键词机会")
            
            if not args.quiet:
                print("\n🎯 SEO优化建议:")
                for gap in result['content_gaps'][:3]:
                    print(f"  • {gap}")
        
        elif args.build_websites:
            # 批量建站
            if not args.quiet:
                print(f"🏗️ 开始批量生成 {args.top_keywords} 个网站...")
            
            result = batch_build_websites(args.top_keywords, args.output)
            print(f"✅ 批量建站完成: 成功构建 {result['successful_builds']} 个网站")
            
            if not args.quiet:
                print("\n🌐 构建的网站:")
                for site in result['websites'][:3]:
                    print(f"  • {site['keyword']}: {site['domain_suggestion']}")

        elif args.report:
            # 生成分析报告
            if not args.quiet:
                print("📊 生成今日分析报告...")
            
            report_path = manager.generate_daily_report()
            print(f"✅ 报告已生成: {report_path}")
        
        elif args.use_root_words:
            # 使用51个词根进行趋势分析
            if not args.quiet:
                print("🌱 开始使用51个词根进行趋势分析...")
            
            result = manager.analyze_root_words(args.output)
            
            # 显示结果
            if args.quiet:
                print_quiet_summary(result)
            else:
                print(f"\n🎉 词根趋势分析完成! 共分析 {result.get('total_root_words', 0)} 个词根")
                print(f"📊 成功分析: {result.get('successful_analyses', 0)} 个")
                print(f"📈 上升趋势词根: {len(result.get('top_trending_words', []))}")
                
                # 显示Top 5词根
                top_words = result.get('top_trending_words', [])[:5]
                if top_words:
                    print("\n🏆 Top 5 热门词根:")
                    for i, word_data in enumerate(top_words, 1):
                        print(f"   {i}. {word_data['word']}: 平均兴趣度 {word_data['average_interest']:.1f}")
        
        else:
            # 默认：使用 fetch_rising_queries 获取关键词并进行需求挖掘
            if not args.quiet:
                print("🔥 未指定参数，使用 Rising Queries 获取热门关键词并进行需求挖掘...")
            
            try:
                # 导入 TrendsCollector
                from src.collectors.trends_collector import TrendsCollector
                
                # 创建 TrendsCollector 实例
                trends_collector = TrendsCollector()
                
                # 使用 fetch_rising_queries 获取热门关键词
                if not args.quiet:
                    print("🔍 正在获取 Rising Queries...")
                
                rising_queries = trends_collector.fetch_rising_queries()
                
                # 将 rising queries 转换为DataFrame格式
                import pandas as pd
                if rising_queries and len(rising_queries) > 0:
                    # 如果返回的是字符串列表
                    if isinstance(rising_queries[0], str):
                        trending_df = pd.DataFrame([
                            {'query': query}
                            for query in rising_queries[:20]  # 限制前20个
                        ])
                    # 如果返回的是字典列表
                    elif isinstance(rising_queries[0], dict):
                        trending_df = pd.DataFrame([
                            {
                                'query': item.get('query', item.get('keyword', str(item))),
                                'value': item.get('value', item.get('interest', 0))
                            }
                            for item in rising_queries[:20]  # 限制前20个
                        ])
                    else:
                        # 其他格式，尝试转换为字符串
                        trending_df = pd.DataFrame([
                            {'query': str(query)}
                            for query in rising_queries[:20]
                        ])
                else:
                    trending_df = pd.DataFrame(columns=['query'])

                if not trending_df.empty:
                    # 保存热门关键词到临时文件
                    import tempfile
                    from datetime import datetime
                    
                    # 确保DataFrame有正确的列名
                    if 'query' not in trending_df.columns and len(trending_df.columns) > 0:
                        # 如果没有query列，使用第一列作为关键词
                        trending_df = trending_df.rename(columns={trending_df.columns[0]: 'query'})
                    
                    # 创建临时文件进行需求挖掘分析
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
                        trending_df.to_csv(f.name, index=False)
                        temp_file = f.name
                    
                    try:
                        if not args.quiet:
                            print(f"🔍 获取到 {len(trending_df)} 个 Rising Queries，开始需求挖掘分析...")
                        
                        # 执行需求挖掘分析，禁用新词检测避免429错误
                        manager.new_word_detection_available = False
                        result = manager.analyze_keywords(temp_file, args.output, enable_serp=False)
                        
                        # 显示结果
                        if args.quiet:
                            print_quiet_summary(result)
                        else:
                            print(f"\n🎉 需求挖掘分析完成! 共分析 {result['total_keywords']} 个 Rising Queries")
                            print(f"📊 高机会关键词: {result['market_insights']['high_opportunity_count']} 个")
                            print(f"📈 平均机会分数: {result['market_insights']['avg_opportunity_score']}")
                            
                            # 显示新词检测摘要
                            if 'new_word_summary' in result and result['new_word_summary'].get('new_words_detected', 0) > 0:
                                summary = result['new_word_summary']
                                print(f"🔍 新词检测: 发现 {summary['new_words_detected']} 个新词 ({summary['new_word_percentage']}%)")
                                print(f"   高置信度新词: {summary['high_confidence_new_words']} 个")

                            # 显示Top 5机会关键词
                            top_keywords = result['market_insights']['top_opportunities'][:5]
                            if top_keywords:
                                print("\n🏆 Top 5 机会关键词:")
                                for i, kw in enumerate(top_keywords, 1):
                                    intent_desc = kw['intent']['intent_description']
                                    score = kw['opportunity_score']
                                    new_word_info = ""
                                    if 'new_word_detection' in kw and kw['new_word_detection']['is_new_word']:
                                        new_word_grade = kw['new_word_detection']['new_word_grade']
                                        new_word_info = f" [新词-{new_word_grade}级]"
                                    print(f"   {i}. {kw['keyword']} (分数: {score}, 意图: {intent_desc}){new_word_info}")
                            
                            # 显示原始Rising Queries信息
                            print(f"\n🔥 原始 Rising Queries 数据:")
                            print(f"   • 数据来源: Google Trends Rising Queries")
                            if 'value' in trending_df.columns:
                                print(f"   • 平均热度: {trending_df['value'].mean():.1f}")
                            
                            # 保存原始Rising Queries
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            trending_output_file = os.path.join(args.output, f"rising_queries_raw_{timestamp}.csv")
                            os.makedirs(args.output, exist_ok=True)
                            trending_df.to_csv(trending_output_file, index=False, encoding='utf-8')
                            print(f"📁 原始 Rising Queries 已保存到: {trending_output_file}")
                        
                    finally:
                        # 清理临时文件
                        os.unlink(temp_file)
                        
                else:
                    # 当无法获取Rising Queries时，直接报告失败
                    print("❌ 无法获取 Rising Queries，可能的原因:")
                    print("💡 建议:")
                    print("   1. 检查网络连接")
                    print("   2. 稍后重试")
                    print("   3. 或使用 --input 参数指定关键词文件进行分析")
                    sys.exit(1)
                    
            except Exception as e:
                print(f"❌ 获取 Rising Queries 或需求挖掘时出错: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
        
        print(f"\n📁 详细结果已保存到 {args.output} 目录")
        
    except KeyboardInterrupt:
        print("\n⚠️ 分析被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()