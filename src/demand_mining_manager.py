#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成需求挖掘管理器模块
统一管理所有需求挖掘功能
"""

import os
import sys
import json
import pandas as pd
import tempfile
from datetime import datetime
from typing import Dict, Any, List

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.demand_mining.managers import KeywordManager, DiscoveryManager, TrendManager
from src.utils.logger import setup_logger


def get_reports_dir() -> str:
    """从配置文件获取报告输出目录"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config/integrated_workflow_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('output_settings', {}).get('reports_dir', 'output/reports')
    except:
        pass
    return 'output/reports'


class IntegratedDemandMiningManager:
    """集成需求挖掘管理器 - 统一所有功能"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.logger = setup_logger(__name__)
        
        # 初始化各个管理器
        self.keyword_manager = KeywordManager(config_path)
        self.discovery_manager = DiscoveryManager(config_path)
        self.trend_manager = TrendManager(config_path)
        self.config = getattr(self.keyword_manager, 'config', {})
        
        # 初始化新词检测器
        try:
            from src.demand_mining.analyzers.new_word_detector import NewWordDetector
            new_word_cfg = {}
            if isinstance(self.config, dict):
                new_word_cfg = self.config.get('new_word_detection', {}) or {}

            detector_kwargs = {}
            if isinstance(new_word_cfg, dict):
                mapping = {
                    'low_volume_threshold_12m': 'low_volume_threshold_12m',
                    'low_volume_threshold_90d': 'low_volume_threshold_90d',
                    'low_volume_threshold_30d': 'low_volume_threshold_30d',
                    'high_growth_threshold_7d': 'high_growth_threshold_7d',
                    'min_recent_volume': 'min_recent_volume',
                    'score_threshold': 'new_word_score_threshold'
                }
                for cfg_key, param_name in mapping.items():
                    value = new_word_cfg.get(cfg_key)
                    if isinstance(value, (int, float)):
                        detector_kwargs[param_name] = value
                confidence_cfg = new_word_cfg.get('confidence_thresholds')
                if isinstance(confidence_cfg, dict):
                    detector_kwargs['confidence_thresholds'] = confidence_cfg
                grade_cfg = new_word_cfg.get('grade_thresholds')
                if isinstance(grade_cfg, dict):
                    detector_kwargs['grade_thresholds'] = grade_cfg

            self.new_word_detector = NewWordDetector(**detector_kwargs)
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
                df = pd.read_csv(input_file)

                # 执行新词检测
                new_word_results = self.new_word_detector.detect_new_words(df)

                # 将新词检测结果合并到分析结果中
                if 'keywords' in result:
                    thresholds = getattr(self.new_word_detector, 'thresholds', {}) if hasattr(self.new_word_detector, 'thresholds') else {}
                    min_recent_threshold = float(thresholds.get('min_recent_volume', 0) or 0.0)
                    baseline_threshold_raw = float(thresholds.get('low_volume_30d', 0) or 0.0)
                    historical_threshold_raw = float(thresholds.get('low_volume_90d', baseline_threshold_raw) or baseline_threshold_raw)
                    recent_threshold = max(min_recent_threshold, 1.0)
                    baseline_threshold = max(baseline_threshold_raw, recent_threshold) if baseline_threshold_raw else recent_threshold
                    historical_threshold = max(historical_threshold_raw, baseline_threshold) if historical_threshold_raw else baseline_threshold
                    volume_summary = {
                        'total_keywords': len(result['keywords']),
                        'status_counts': {'sufficient': 0, 'needs_review': 0, 'insufficient': 0, 'not_evaluated': 0},
                        'insufficient_keywords': [],
                        'needs_review_keywords': [],
                        'thresholds': {
                            'recent_threshold': recent_threshold,
                            'baseline_threshold': baseline_threshold,
                            'historical_threshold': historical_threshold
                        }
                    }
                    for i, keyword_data in enumerate(result['keywords']):
                        if i < len(new_word_results):
                            row = new_word_results.iloc[i]
                            keyword_data['new_word_detection'] = {
                                'is_new_word': bool(row.get('is_new_word', False)),
                                'new_word_score': float(row.get('new_word_score', 0)),
                                'new_word_grade': str(row.get('new_word_grade', 'D')),
                                'growth_rate_7d': float(row.get('growth_rate_7d', 0)),
                                'growth_rate_7d_vs_30d': float(row.get('growth_rate_7d_vs_30d', 0)),
                                'mom_growth': float(row.get('mom_growth', 0)),
                                'yoy_growth': float(row.get('yoy_growth', 0)),
                                'confidence_level': str(row.get('confidence_level', 'low')),
                                'trend_momentum': str(row.get('trend_momentum', 'unknown')),
                                'growth_label': str(row.get('growth_label', 'unknown')),
                                'trend_fetch_timeframe': row.get('trend_fetch_timeframe'),
                                'trend_fetch_geo': row.get('trend_fetch_geo'),
                                'avg_30d_delta': float(row.get('avg_30d_delta', 0.0) or 0.0),
                                'avg_7d_delta': float(row.get('avg_7d_delta', 0.0) or 0.0)
                            }

                            if row.get('is_new_word', False):
                                original_score = keyword_data.get('opportunity_score', 0)
                                new_word_bonus = row.get('new_word_score', 0) * 0.1  # 10%加成
                                keyword_data['opportunity_score'] = min(100, original_score + new_word_bonus)
                                keyword_data['new_word_bonus'] = new_word_bonus

                            avg_7d = float(row.get('avg_7d', 0.0) or 0.0)
                            avg_30d = float(row.get('avg_30d', 0.0) or 0.0)
                            avg_90d = float(row.get('avg_90d', 0.0) or 0.0)
                            avg_12m = float(row.get('avg_12m', 0.0) or 0.0)

                            meets_recent = avg_7d >= recent_threshold if recent_threshold > 0 else avg_7d > 0
                            meets_baseline = avg_30d >= baseline_threshold if baseline_threshold > 0 else avg_30d > 0
                            meets_historical = avg_90d >= historical_threshold if historical_threshold > 0 else avg_90d > 0

                            if avg_7d <= 0.0 and avg_30d <= 0.0:
                                volume_status = 'insufficient'
                                volume_note = 'recent_trend_zero'
                            elif not meets_recent and not meets_baseline:
                                volume_status = 'needs_review'
                                volume_note = 'below_volume_baseline'
                            else:
                                volume_status = 'sufficient'
                                volume_note = ''

                            volume_info = {
                                'status': volume_status,
                                'avg_7d': round(avg_7d, 2),
                                'avg_30d': round(avg_30d, 2),
                                'avg_90d': round(avg_90d, 2),
                                'avg_12m': round(avg_12m, 2),
                                'meets_recent_threshold': meets_recent,
                                'meets_baseline_threshold': meets_baseline,
                                'meets_historical_threshold': meets_historical,
                                'recent_threshold': recent_threshold,
                                'baseline_threshold': baseline_threshold,
                                'historical_threshold': historical_threshold
                            }
                            if volume_note:
                                volume_info['notes'] = volume_note

                            keyword_data['volume_validation'] = volume_info
                            volume_summary['status_counts'].setdefault(volume_status, 0)
                            volume_summary['status_counts'][volume_status] += 1

                            if volume_status == 'insufficient':
                                volume_summary['insufficient_keywords'].append({
                                    'keyword': keyword_data.get('keyword'),
                                    'avg_7d': volume_info['avg_7d'],
                                    'avg_30d': volume_info['avg_30d']
                                })
                                print(f"⚠️ 关键词 {keyword_data.get('keyword')} 最近趋势量级几乎为0，建议补充流量验证。")
                            elif volume_status == 'needs_review':
                                volume_summary['needs_review_keywords'].append({
                                    'keyword': keyword_data.get('keyword'),
                                    'avg_7d': volume_info['avg_7d'],
                                    'avg_30d': volume_info['avg_30d']
                                })
                        else:
                            keyword_data['volume_validation'] = {
                                'status': 'not_evaluated',
                                'notes': 'missing_new_word_detection'
                            }
                            volume_summary['status_counts']['not_evaluated'] += 1

                    evaluated_keywords = volume_summary['total_keywords'] - volume_summary['status_counts']['not_evaluated']
                    volume_summary['evaluated_keywords'] = max(evaluated_keywords, 0)
                    result['volume_validation_summary'] = volume_summary

                new_words_count = len(new_word_results[new_word_results['is_new_word'] == True])
                high_confidence_count = len(new_word_results[new_word_results['confidence_level'] == 'high'])

                momentum_counts = new_word_results.get('trend_momentum', pd.Series(dtype=str)).value_counts() if 'trend_momentum' in new_word_results.columns else {}
                breakout_count = int(momentum_counts.get('breakout', 0)) if momentum_counts is not None else 0
                rising_count = int(momentum_counts.get('rising', 0)) if momentum_counts is not None else 0

                result['new_word_summary'] = {
                    'total_analyzed': len(new_word_results),
                    'new_words_detected': new_words_count,
                    'high_confidence_new_words': high_confidence_count,
                    'new_word_percentage': round(new_words_count / len(new_word_results) * 100, 1) if len(new_word_results) > 0 else 0,
                    'breakout_keywords': breakout_count,
                    'rising_keywords': rising_count,
                    'score_threshold': getattr(self.new_word_detector, 'score_threshold', 0.0)
                }

                exported_reports = self._export_new_word_reports(new_word_results)
                if exported_reports:
                    result['new_word_summary']['report_files'] = exported_reports

                breakout_count = result['new_word_summary']['breakout_keywords']
                print(f"✅ 新词检测完成: 发现 {new_words_count} 个新词 ({high_confidence_count} 个高置信度, {breakout_count} 个 Breakout)")

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
            df = pd.read_csv(input_file)
            
            # 对每个关键词进行SERP分析
            serp_results = []
            total_keywords = len(df)
            
            for i, row in df.iterrows():
                keyword = row.get('query', row.get('keyword', ''))
                if keyword:
                    print(f"  分析关键词 {i+1}/{total_keywords}: {keyword}")
                    
                    # 使用增强的SERP结构分析
                    serp_structure = serp_analyzer.analyze_serp_structure(keyword)
                    serp_intent = serp_analyzer.analyze_keyword_serp(keyword)
                    
                    serp_results.append({
                        'keyword': keyword,
                        'serp_features': serp_intent.get('serp_features', {}),
                        'serp_intent': serp_intent.get('intent', 'I'),
                        'serp_confidence': serp_intent.get('confidence', 0.0),
                        'serp_secondary_intent': serp_intent.get('secondary_intent', None),
                        # 新增的增强分析结果
                        'competition_level': serp_structure.get('competition_level', '未知'),
                        'difficulty_score': serp_structure.get('difficulty_score', 0.0),
                        'competitors': serp_structure.get('competitors', [])[:5],  # 只保留前5个竞争对手
                        'serp_structure': serp_structure.get('structure', {})
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
                            'secondary_intent': serp_data['serp_secondary_intent'],
                            # 新增的增强分析结果
                            'competition_level': serp_data['competition_level'],
                            'difficulty_score': serp_data['difficulty_score'],
                            'top_competitors': serp_data['competitors'],
                            'serp_structure': serp_data['serp_structure']
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
            high_competition = len([r for r in serp_results if r['competition_level'] in ['极高', '高']])
            low_competition = len([r for r in serp_results if r['competition_level'] in ['极低', '低']])
            
            result['serp_summary'] = {
                'total_analyzed': len(serp_results),
                'high_confidence_serp': high_confidence_serp,
                'commercial_intent_keywords': commercial_intent,
                'high_competition_keywords': high_competition,
                'low_competition_keywords': low_competition,
                'serp_analysis_enabled': True,
                'enhanced_analysis_enabled': True  # 标记已启用增强分析
            }
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
            
        return result

    def _export_new_word_reports(self, new_word_results: pd.DataFrame) -> Dict[str, str]:
        if new_word_results is None or new_word_results.empty:
            return {}

        reports_dir = os.path.join(get_reports_dir(), 'new_words')
        os.makedirs(reports_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        exports: Dict[str, str] = {}

        def _save(df: pd.DataFrame, filename: str, key: str) -> None:
            if df is None or df.empty:
                return
            path = os.path.join(reports_dir, filename)
            df.to_csv(path, index=False)
            exports[key] = path

        try:
            breakout_df = new_word_results[new_word_results.get('trend_momentum') == 'breakout']
            _save(breakout_df, f'breakout_new_words_{timestamp}.csv', 'breakout')

            rising_df = new_word_results[new_word_results.get('trend_momentum').isin(['breakout', 'rising'])]
            _save(rising_df, f'rising_new_words_{timestamp}.csv', 'rising')

            top_df = new_word_results.sort_values('new_word_score', ascending=False).head(30)
            _save(top_df, f'top_new_words_{timestamp}.csv', 'top')
        except Exception as exc:
            print(f"⚠️ 导出新词报告失败: {exc}")

        return exports
    
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
    
    def expand_keywords_comprehensive(self, seed_keywords: List[str], 
                                    output_dir: str = None,
                                    max_expanded: int = 200,
                                    max_longtails: int = 100) -> Dict[str, Any]:
        """
        增强关键词扩展：集成Google自动完成、Trends相关搜索和语义相似词发现
        
        Args:
            seed_keywords: 种子关键词列表
            output_dir: 输出目录
            max_expanded: 最大扩展关键词数量
            max_longtails: 最大长尾关键词数量
            
        Returns:
            扩展结果字典
        """
        try:
            from src.demand_mining.tools.keyword_extractor import KeywordExtractor
            from src.demand_mining.tools.longtail_generator import LongtailGenerator
            
            print(f"🚀 开始增强关键词扩展...")
            print(f"🌱 种子关键词: {', '.join(seed_keywords)}")
            
            # 初始化工具
            extractor = KeywordExtractor()
            longtail_gen = LongtailGenerator()
            
            # 1. 使用KeywordExtractor扩展关键词
            print("🔍 第一阶段：基础关键词扩展...")
            expanded_results = []
            
            for seed in seed_keywords:
                print(f"   正在扩展: {seed}")
                
                # Google自动完成扩展
                autocomplete_kws = extractor.get_google_autocomplete_suggestions(seed)
                
                # 相关搜索词扩展
                related_kws = extractor.get_related_search_terms(seed)
                
                # 语义相似词扩展
                semantic_kws = extractor.expand_seed_keywords([seed], max_per_seed=20)
                
                # 合并结果
                all_expanded = set()
                all_expanded.update(autocomplete_kws)
                all_expanded.update(related_kws)
                if seed in semantic_kws:
                    all_expanded.update(semantic_kws[seed])
                
                # 过滤和评分
                for kw in all_expanded:
                    if len(kw) > 3 and len(kw) < 100:
                        difficulty = extractor.analyze_keyword_difficulty(kw)
                        expanded_results.append({
                            'seed_keyword': seed,
                            'expanded_keyword': kw,
                            'source': 'mixed',
                            'difficulty': difficulty,
                            'word_count': len(kw.split()),
                            'length': len(kw)
                        })
            
            # 去重并限制数量
            unique_expanded = {}
            for item in expanded_results:
                kw = item['expanded_keyword']
                if kw not in unique_expanded:
                    unique_expanded[kw] = item
            
            expanded_list = list(unique_expanded.values())[:max_expanded]
            
            print(f"✅ 第一阶段完成，扩展了 {len(expanded_list)} 个关键词")
            
            # 2. 使用LongtailGenerator生成长尾关键词
            print("🔗 第二阶段：长尾关键词生成...")
            
            longtail_results = longtail_gen.generate_comprehensive_longtails(
                seed_keywords, 
                max_total=max_longtails
            )
            
            longtail_list = [item['keyword'] for item in longtail_results['all_longtails']]
            
            print(f"✅ 第二阶段完成，生成了 {len(longtail_list)} 个长尾关键词")
            
            # 3. 合并所有结果
            all_keywords = set(seed_keywords)
            all_keywords.update([item['expanded_keyword'] for item in expanded_list])
            all_keywords.update(longtail_list)
            
            # 4. 生成输出文件
            output_files = {}
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # 扩展关键词CSV
                expanded_df = pd.DataFrame(expanded_list)
                expanded_file = os.path.join(output_dir, f"expanded_keywords_{timestamp}.csv")
                expanded_df.to_csv(expanded_file, index=False, encoding='utf-8-sig')
                output_files['expanded_keywords'] = expanded_file
                
                # 长尾关键词CSV
                longtail_df = pd.DataFrame(longtail_results['all_longtails'])
                longtail_file = os.path.join(output_dir, f"longtail_keywords_{timestamp}.csv")
                longtail_df.to_csv(longtail_file, index=False, encoding='utf-8-sig')
                output_files['longtail_keywords'] = longtail_file
                
                # 所有关键词合并文件
                all_kw_df = pd.DataFrame({
                    'keyword': list(all_keywords),
                    'type': ['seed' if kw in seed_keywords else 
                            'longtail' if kw in longtail_list else 'expanded' 
                            for kw in all_keywords]
                })
                all_file = os.path.join(output_dir, f"all_keywords_{timestamp}.csv")
                all_kw_df.to_csv(all_file, index=False, encoding='utf-8-sig')
                output_files['all_keywords'] = all_file
                
                # 生成摘要报告
                summary_file = os.path.join(output_dir, f"expansion_summary_{timestamp}.txt")
                with open(summary_file, 'w', encoding='utf-8') as f:
                    report_content = f"""# 关键词扩展摘要报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 扩展统计
- 种子关键词数量: {len(seed_keywords)}
- 扩展关键词数量: {len(expanded_list)}
- 长尾关键词数量: {len(longtail_list)}
- 总关键词数量: {len(all_keywords)}
- 扩展倍数: {len(all_keywords) / len(seed_keywords):.1f}x

## 种子关键词
"""
                    f.write(report_content)
                    
                    # 写入种子关键词
                    for i, kw in enumerate(seed_keywords, 1):
                        f.write(f"{i}. {kw}\n")
                    
                    # 写入扩展关键词
                    f.write("\n## Top 10 扩展关键词\n")
                    for i, item in enumerate(expanded_list[:10], 1):
                        f.write(f"{i}. {item['expanded_keyword']} (来源: {item['seed_keyword']})\n")
                    
                    # 写入长尾关键词
                    f.write("\n## Top 10 长尾关键词\n")
                    for i, item in enumerate(longtail_results['all_longtails'][:10], 1):
                        f.write(f"{i}. {item['keyword']} (评分: {item['score']:.1f})\n")
                
                output_files['summary_report'] = summary_file
            
            # 5. 构建返回结果
            result = {
                'success': True,
                'seed_keywords': seed_keywords,
                'expanded_keywords': [item['expanded_keyword'] for item in expanded_list],
                'longtail_keywords': longtail_list,
                'all_keywords': list(all_keywords),
                'summary': {
                    'seed_count': len(seed_keywords),
                    'expanded_count': len(expanded_list),
                    'longtail_count': len(longtail_list),
                    'total_count': len(all_keywords),
                    'expansion_ratio': len(all_keywords) / len(seed_keywords) if seed_keywords else 0,
                    'avg_longtail_score': longtail_results['statistics']['avg_score'],
                    'high_score_longtails': longtail_results['statistics']['high_score_count']
                },
                'longtail_statistics': longtail_results['statistics'],
                'output_files': output_files
            }
            
            print(f"🎉 关键词扩展完成!")
            print(f"📊 最终统计: {len(seed_keywords)} → {len(all_keywords)} 关键词 ({len(all_keywords) / len(seed_keywords):.1f}x)")
            
            return result
            
        except Exception as e:
            error_msg = f"关键词扩展失败: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'seed_keywords': seed_keywords,
                'expanded_keywords': [],
                'longtail_keywords': [],
                'all_keywords': seed_keywords,
                'summary': {
                    'seed_count': len(seed_keywords),
                    'expanded_count': 0,
                    'longtail_count': 0,
                    'total_count': len(seed_keywords),
                    'expansion_ratio': 1.0
                }
            }
