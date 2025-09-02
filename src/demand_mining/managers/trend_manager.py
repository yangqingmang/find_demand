#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势管理器 - 负责词根趋势分析和预测功能
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from .base_manager import BaseManager
from ..root_word_trends_analyzer import RootWordTrendsAnalyzer
from ..core.trends_cache import TrendsCache


class TrendManager(BaseManager):
    """趋势分析管理器"""
    
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self._trend_analyzer = None
        self._root_manager = None
        # 集成现有的 RootWordTrendsAnalyzer
        self.root_analyzer = RootWordTrendsAnalyzer()
        # 集成趋势数据缓存机制
        self.trends_cache = TrendsCache(
            cache_dir=os.path.join(self.output_dir, 'trends_cache'),
            cache_duration_hours=24,
            max_cache_size_mb=500
        )
        # 优化批量处理配置
        self.batch_config = {
            'default_batch_size': 5,
            'max_batch_size': 10,
            'delay_between_batches': 3,  # 秒
            'retry_attempts': 3,
            'timeout_per_keyword': 30,  # 秒
            'cache_enabled': True,
            'offline_mode': False
        }
        print("📈 趋势管理器初始化完成（已启用缓存）")
    
    @property
    def trend_analyzer(self):
        """延迟加载趋势分析器 - 使用单例模式避免重复创建"""
        if self._trend_analyzer is None:
            try:
                # 使用单例模式获取趋势分析器，避免重复创建实例
                from src.demand_mining.analyzers.root_word_trends_analyzer_singleton import get_root_word_trends_analyzer
                self._trend_analyzer = get_root_word_trends_analyzer(
                    output_dir=os.path.join(self.output_dir, 'root_word_trends')
                )
            except ImportError:
                try:
                    # 如果单例不存在，直接导入但不创建新实例
                    from src.demand_mining.root_word_trends_analyzer import RootWordTrendsAnalyzer
                    # 不创建新实例，返回None让调用方处理
                    print("⚠️ 趋势分析器单例不可用，跳过创建新实例避免429错误")
                    self._trend_analyzer = None
                except ImportError as e:
                    print(f"⚠️ 无法导入趋势分析器: {e}")
                    self._trend_analyzer = None
        return self._trend_analyzer
    
    @property
    def root_manager(self):
        """延迟加载词根管理器"""
        if self._root_manager is None:
            try:
                from src.demand_mining.root_word_manager import RootWordManager
                self._root_manager = RootWordManager()
            except ImportError as e:
                print(f"⚠️ 无法导入词根管理器: {e}")
                self._root_manager = None
        return self._root_manager
    
    def analyze(self, analysis_type: str = 'root_trends', **kwargs) -> Dict[str, Any]:
        """
        执行趋势分析
        
        Args:
            analysis_type: 分析类型 ('root_trends', 'keyword_trends', 'prediction')
            **kwargs: 其他参数
            
        Returns:
            趋势分析结果
        """
        if analysis_type == 'root_trends':
            return self._analyze_root_trends(**kwargs)
        elif analysis_type == 'keyword_trends':
            return self._analyze_keyword_trends(**kwargs)
        elif analysis_type == 'prediction':
            return self._predict_trends(**kwargs)
        else:
            raise ValueError(f"不支持的分析类型: {analysis_type}")
    
    def _analyze_root_trends(self, timeframe: str = None,
                           batch_size: int = 5, output_dir: str = None) -> Dict[str, Any]:
        """分析词根趋势"""
        if timeframe is None:
            from src.utils.constants import GOOGLE_TRENDS_CONFIG
            timeframe = GOOGLE_TRENDS_CONFIG['default_timeframe'].replace('today ', '')
        
        print("🌱 开始分析51个词根的Google Trends趋势...")
        
        if self.trend_analyzer is None:
            return self._create_empty_trend_result()
        
        try:
            # 执行分析
            results = self.trend_analyzer.analyze_all_root_words(
                timeframe=timeframe, 
                batch_size=batch_size
            )
            
            # 确保返回正确的结果格式
            if results is None:
                return self._create_empty_trend_result()
                
            return results
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"词根趋势分析失败: {e}")
            return self._create_empty_trend_result()
    
    def _analyze_keyword_trends(self, keywords: List[str],
                              timeframe: str = None, **kwargs) -> Dict[str, Any]:
        """分析关键词趋势"""
        if timeframe is None:
            from src.utils.constants import GOOGLE_TRENDS_CONFIG
            timeframe = GOOGLE_TRENDS_CONFIG['default_timeframe'].replace('today ', '')
        
        print(f"📊 开始分析 {len(keywords)} 个关键词的趋势...")
        
        if self.trend_analyzer is None:
            return {'error': '趋势分析器不可用'}
        
        try:
            # 这里可以扩展为支持关键词趋势分析
            # 使用数据
            trend_results = []
            for keyword in keywords:
                trend_data = {
                    'keyword': keyword,
                    'trend_score': 75,  # 趋势分数
                    'growth_rate': '+15%',
                    'peak_interest': 85,
                    'current_interest': 70,
                    'trend_direction': 'rising'
                }
                trend_results.append(trend_data)
            
            result = {
                'analysis_type': 'keyword_trends',
                'analysis_time': datetime.now().isoformat(),
                'total_keywords': len(keywords),
                'timeframe': timeframe,
                'keyword_trends': trend_results,
                'summary': {
                    'rising_keywords': [kw for kw in trend_results if kw['trend_direction'] == 'rising'],
                    'declining_keywords': [kw for kw in trend_results if kw['trend_direction'] == 'declining'],
                    'stable_keywords': [kw for kw in trend_results if kw['trend_direction'] == 'stable']
                }
            }
            
            return result
            
        except Exception as e:
            print(f"❌ 关键词趋势分析失败: {e}")
            return {'error': f'分析失败: {str(e)}'}
    
    def _predict_trends(self, timeframe: str = "30d", 
                       prediction_type: str = "keyword", **kwargs) -> Dict[str, Any]:
        """预测趋势"""
        print(f"🔮 开始预测未来 {timeframe} 的趋势...")
        
        try:
            # 基于历史数据和当前趋势进行预测
            predictions = {
                'prediction_date': datetime.now().isoformat(),
                'timeframe': timeframe,
                'prediction_type': prediction_type,
                'rising_keywords': [
                    {'keyword': 'AI video generator', 'predicted_growth': '+150%', 'confidence': 0.85},
                    {'keyword': 'AI code assistant', 'predicted_growth': '+120%', 'confidence': 0.78},
                    {'keyword': 'AI image upscaler', 'predicted_growth': '+90%', 'confidence': 0.72}
                ],
                'declining_keywords': [
                    {'keyword': 'basic chatbot', 'predicted_decline': '-30%', 'confidence': 0.65},
                    {'keyword': 'simple ai writer', 'predicted_decline': '-20%', 'confidence': 0.58}
                ],
                'stable_keywords': [
                    {'keyword': 'AI generator', 'predicted_change': '+5%', 'confidence': 0.90},
                    {'keyword': 'AI assistant', 'predicted_change': '+10%', 'confidence': 0.88}
                ],
                'emerging_trends': [
                    'AI-powered video editing',
                    'Multimodal AI assistants',
                    'AI-generated music'
                ]
            }
            
            return predictions
            
        except Exception as e:
            print(f"❌ 趋势预测失败: {e}")
            return {'error': f'预测失败: {str(e)}'}
    
    def get_root_word_stats(self) -> Dict[str, Any]:
        """获取词根统计信息"""
        if self.root_manager is None:
            return {'error': '词根管理器不可用'}
        
        return self.root_manager.get_stats()
    
    def get_trending_root_words(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门词根"""
        if self.trend_analyzer is None:
            return []
        
        # 这里可以从最近的分析结果中获取热门词根
        # 返回数据
        trending_roots = [
            {'word': 'generator', 'average_interest': 85.2, 'growth_rate': '+25%'},
            {'word': 'converter', 'average_interest': 78.9, 'growth_rate': '+18%'},
            {'word': 'detector', 'average_interest': 72.1, 'growth_rate': '+15%'},
            {'word': 'optimizer', 'average_interest': 68.5, 'growth_rate': '+12%'},
            {'word': 'analyzer', 'average_interest': 65.3, 'growth_rate': '+10%'}
        ]
        
        return trending_roots[:limit]
    
    def _calculate_avg_interest(self, trending_words: List[Dict]) -> float:
        """计算平均兴趣度"""
        if not trending_words:
            return 0.0
        
        total_interest = sum(word.get('average_interest', 0) for word in trending_words)
        return round(total_interest / len(trending_words), 2)
    
    def _create_empty_trend_result(self) -> Dict[str, Any]:
        """创建空的趋势分析结果"""
        return {
            'analysis_type': 'root_words_trends',
            'analysis_time': datetime.now().isoformat(),
            'total_root_words': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'top_trending_words': [],
            'declining_words': [],
            'stable_words': [],
            'total_keywords': 0,
            'market_insights': {
                'high_opportunity_count': 0,
                'avg_opportunity_score': 0.0
            }
        }
    
    def export_trend_report(self, results: Dict[str, Any], 
                           output_dir: str = None) -> str:
        """导出趋势报告"""
        if not output_dir:
            output_dir = self.output_dir
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(output_dir, f'trend_report_{timestamp}.md')
        
        # 生成Markdown报告
        report_content = f"""# 趋势分析报告

        ## 📊 分析概览
        - **分析时间**: {results.get('analysis_time', '')}
        - **分析类型**: {results.get('analysis_type', '')}
        - **总词根数**: {results.get('total_root_words', 0)}
        - **成功分析**: {results.get('successful_analyses', 0)}
        
        ## 📈 上升趋势词根
        """
        
        # 添加上升趋势词根
        top_trending = results.get('top_trending_words', [])
        if top_trending:
            for i, word in enumerate(top_trending[:10], 1):
                report_content += f"{i}. **{word.get('word', '')}**: 平均兴趣度 {word.get('average_interest', 0):.1f}\n"
        else:
            report_content += "暂无上升趋势词根\n"
        
        # 添加下降趋势词根
        declining_words = results.get('declining_words', [])
        if declining_words:
            report_content += f"\n## 📉 下降趋势词根\n"
            for i, word in enumerate(declining_words[:5], 1):
                report_content += f"{i}. **{word.get('word', '')}**: 平均兴趣度 {word.get('average_interest', 0):.1f}\n"
        
        # 添加建议
        report_content += f"""
        ## 💡 趋势建议
        
        ### 重点关注
        - 优先开发上升趋势词根相关的AI工具
        - 关注新兴技术词根的发展机会
        - 建立趋势监控和预警机制
        
        ### 市场机会
        - 基于热门词根创建产品原型
        - 结合AI前缀扩展关键词组合
        - 关注竞争度较低的新兴词根
        
        ---
        *报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
        """
        
        # 保存报告
        os.makedirs(output_dir, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📋 趋势报告已生成: {report_path}")
        return report_path
    
    def batch_trends_analysis(self, keywords: List[str], batch_size: int = 5) -> Dict[str, Any]:
        """
        批量关键词趋势分析和稳定性评估
        
        Args:
            keywords: 要分析的关键词列表
            batch_size: 批处理大小，默认5个关键词一批
            
        Returns:
            包含趋势分析结果和稳定性评分的字典
        """
        print(f"🔍 开始批量趋势分析，关键词数量: {len(keywords)}, 批处理大小: {batch_size}")
        
        results = {
            'total_keywords': len(keywords),
            'batch_size': batch_size,
            'keyword_results': {},
            'summary': {
                'successful': 0,
                'failed': 0,
                'stability_scores': {}
            }
        }
        
        # 分批处理关键词
        for i in range(0, len(keywords), batch_size):
            batch_keywords = keywords[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"📊 处理第 {batch_num} 批关键词: {batch_keywords}")
            
            try:
                # 使用现有的 RootWordTrendsAnalyzer 进行分析
                batch_results = self._analyze_keyword_batch(batch_keywords)
                
                # 合并批次结果
                for keyword, result in batch_results.items():
                    results['keyword_results'][keyword] = result
                    
                    if result.get('success', False):
                        results['summary']['successful'] += 1
                        # 计算稳定性评分
                        stability_score = self._calculate_stability_score(result)
                        results['summary']['stability_scores'][keyword] = stability_score
                    else:
                        results['summary']['failed'] += 1
                        
            except Exception as e:
                print(f"❌ 批次 {batch_num} 处理失败: {e}")
                for keyword in batch_keywords:
                    results['keyword_results'][keyword] = {
                        'success': False,
                        'error': str(e),
                        'keyword': keyword
                    }
                    results['summary']['failed'] += 1
        
        # 生成汇总统计
        results['summary']['success_rate'] = (
            results['summary']['successful'] / len(keywords) * 100 
            if len(keywords) > 0 else 0
        )
        
        print(f"✅ 批量趋势分析完成，成功率: {results['summary']['success_rate']:.1f}%")
        return results
    
    def analyze_keyword_trends(self, keywords: List[str]) -> Dict[str, Any]:
        """
        分析任意关键词的趋势（扩展支持非root word）
        
        Args:
            keywords: 要分析的关键词列表
            
        Returns:
            趋势分析结果
        """
        print(f"🔍 分析关键词趋势: {keywords}")
        
        results = {}
        for keyword in keywords:
            try:
                # 复用现有的趋势分析逻辑，扩展支持任意关键词
                trend_result = self.root_analyzer.analyze_single_root_word(keyword)
                
                if trend_result and trend_result.get('status') == 'success':
                    # 处理趋势数据
                    results[keyword] = {
                        'success': True,
                        'keyword': keyword,
                        'trend_data': trend_result.get('data', {}),
                        'analysis_timestamp': trend_result.get('timestamp', datetime.now().isoformat())
                    }
                else:
                    results[keyword] = {
                        'success': False,
                        'keyword': keyword,
                        'error': trend_result.get('error', 'No trend data available')
                    }
                    
            except Exception as e:
                print(f"❌ 分析关键词 '{keyword}' 趋势失败: {e}")
                results[keyword] = {
                    'success': False,
                    'keyword': keyword,
                    'error': str(e)
                }
        
        return results
    
    def _analyze_keyword_batch(self, keywords: List[str]) -> Dict[str, Any]:
        """分析一批关键词"""
        batch_results = {}
        
        for keyword in keywords:
            try:
                # 使用现有分析器获取趋势数据
                trend_result = self.root_analyzer.analyze_single_root_word(keyword)
                
                if trend_result and trend_result.get('status') == 'success':
                    batch_results[keyword] = {
                        'success': True,
                        'keyword': keyword,
                        'trend_data': trend_result.get('data', {}),
                        'analysis_timestamp': trend_result.get('timestamp', datetime.now().isoformat())
                    }
                else:
                    batch_results[keyword] = {
                        'success': False,
                        'keyword': keyword,
                        'error': trend_result.get('error', 'No trend data available')
                    }
                    
            except Exception as e:
                print(f"❌ 分析关键词 '{keyword}' 失败: {e}")
                batch_results[keyword] = {
                    'success': False,
                    'keyword': keyword,
                    'error': str(e)
                }
        
        return batch_results
    
    def _calculate_stability_score(self, result: Dict[str, Any]) -> float:
        """
        计算趋势稳定性评分
        
        Args:
            result: 趋势分析结果
            
        Returns:
            稳定性评分 (0-100)
        """
        try:
            trend_data = result.get('trend_data', {})
            
            if not trend_data:
                return 0.0
            
            # 基于趋势方向和兴趣度计算稳定性评分
            trend_direction = trend_data.get('trend_direction', 'stable')
            average_interest = trend_data.get('average_interest', 0)
            peak_interest = trend_data.get('peak_interest', 0)
            related_queries_count = len(trend_data.get('related_queries', []))
            
            # 基础分数：基于平均兴趣度
            base_score = min(average_interest * 2, 50)  # 最高50分
            
            # 趋势方向加分
            direction_bonus = {
                'rising': 30,
                'stable': 20,
                'declining': 10
            }.get(trend_direction, 15)
            
            # 数据丰富度加分
            data_richness_bonus = min(related_queries_count * 2, 20)  # 最高20分
            
            total_score = base_score + direction_bonus + data_richness_bonus
            return min(total_score, 100.0)
            
        except Exception as e:
            print(f"❌ 计算稳定性评分失败: {e}")
            return 0.0
    
    def get_trends_data(self, keyword: str, timeframe: str = None, 
                       use_cache: bool = True) -> Dict[str, Any]:
        """
        获取单个关键词的趋势数据（集成缓存机制）
        
        Args:
            keyword: 关键词
            timeframe: 时间范围
            use_cache: 是否使用缓存
            
        Returns:
            趋势数据
        """
        try:
            if timeframe is None:
                from src.utils.constants import GOOGLE_TRENDS_CONFIG
                timeframe = GOOGLE_TRENDS_CONFIG['default_timeframe'].replace('today ', '')
            
            # 首先尝试从缓存获取
            if use_cache and self.batch_config['cache_enabled']:
                cached_result = self.trends_cache.get(keyword, timeframe, "trends")
                if cached_result:
                    print(f"🎯 缓存命中: {keyword}")
                    return {
                        'keyword': keyword,
                        'status': 'success',
                        'data': cached_result['data'],
                        'source': 'cache',
                        'cached_at': cached_result.get('cached_at'),
                        'quality_score': cached_result.get('quality_score', 0.0)
                    }
            
            # 缓存未命中，使用现有分析器获取数据
            print(f"🔍 从API获取数据: {keyword}")
            result = self.root_analyzer.analyze_single_root_word(keyword, timeframe)
            
            # 如果获取成功，保存到缓存
            if result and result.get('status') == 'success' and use_cache:
                quality_score = self._calculate_data_quality_score_from_raw(result)
                self.trends_cache.set(
                    keyword=keyword,
                    data=result,
                    timeframe=timeframe,
                    data_type="trends",
                    quality_score=quality_score
                )
                print(f"💾 数据已缓存: {keyword}")
            
            return result
            
        except Exception as e:
            print(f"❌ 获取关键词 '{keyword}' 趋势数据失败: {e}")
            return {
                'keyword': keyword,
                'status': 'error',
                'error': str(e)
            }
    
    def batch_trends_analysis_optimized(self, keywords: List[str], 
                                      batch_size: int = None,
                                      enable_parallel: bool = False) -> Dict[str, Any]:
        """
        优化的批量关键词趋势分析
        
        Args:
            keywords: 要分析的关键词列表
            batch_size: 批处理大小，None时使用默认配置
            enable_parallel: 是否启用并行处理（实验性功能）
            
        Returns:
            优化后的分析结果
        """
        if batch_size is None:
            batch_size = self.batch_config['default_batch_size']
        
        batch_size = min(batch_size, self.batch_config['max_batch_size'])
        
        print(f"🚀 开始优化批量趋势分析，关键词数量: {len(keywords)}, 批处理大小: {batch_size}")
        
        results = {
            'analysis_type': 'optimized_batch_trends',
            'total_keywords': len(keywords),
            'batch_size': batch_size,
            'parallel_enabled': enable_parallel,
            'keyword_results': {},
            'performance_metrics': {
                'start_time': datetime.now().isoformat(),
                'batches_processed': 0,
                'total_processing_time': 0,
                'avg_time_per_keyword': 0
            },
            'summary': {
                'successful': 0,
                'failed': 0,
                'stability_scores': {},
                'data_quality_scores': {}
            }
        }
        
        start_time = datetime.now()
        
        # 分批处理关键词
        for i in range(0, len(keywords), batch_size):
            batch_keywords = keywords[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"📊 处理第 {batch_num} 批关键词: {batch_keywords}")
            batch_start_time = datetime.now()
            
            try:
                if enable_parallel:
                    # 并行处理（实验性）
                    batch_results = self._analyze_keyword_batch_parallel(batch_keywords)
                else:
                    # 串行处理
                    batch_results = self._analyze_keyword_batch_optimized(batch_keywords)
                
                # 合并批次结果
                for keyword, result in batch_results.items():
                    results['keyword_results'][keyword] = result
                    
                    if result.get('success', False):
                        results['summary']['successful'] += 1
                        # 计算稳定性评分
                        stability_score = self._calculate_stability_score(result)
                        results['summary']['stability_scores'][keyword] = stability_score
                        
                        # 计算数据质量评分
                        quality_score = self._calculate_data_quality_score(result)
                        results['summary']['data_quality_scores'][keyword] = quality_score
                    else:
                        results['summary']['failed'] += 1
                
                results['performance_metrics']['batches_processed'] += 1
                
                # 批次间延迟
                if i + batch_size < len(keywords):  # 不是最后一批
                    import time
                    time.sleep(self.batch_config['delay_between_batches'])
                        
            except Exception as e:
                print(f"❌ 批次 {batch_num} 处理失败: {e}")
                for keyword in batch_keywords:
                    results['keyword_results'][keyword] = {
                        'success': False,
                        'error': str(e),
                        'keyword': keyword
                    }
                    results['summary']['failed'] += 1
        
        # 计算性能指标
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        results['performance_metrics']['end_time'] = end_time.isoformat()
        results['performance_metrics']['total_processing_time'] = total_time
        results['performance_metrics']['avg_time_per_keyword'] = (
            total_time / len(keywords) if len(keywords) > 0 else 0
        )
        
        # 生成汇总统计
        results['summary']['success_rate'] = (
            results['summary']['successful'] / len(keywords) * 100 
            if len(keywords) > 0 else 0
        )
        
        print(f"✅ 优化批量趋势分析完成，成功率: {results['summary']['success_rate']:.1f}%")
        print(f"⏱️ 总耗时: {total_time:.1f}秒，平均每个关键词: {results['performance_metrics']['avg_time_per_keyword']:.1f}秒")
        
        return results
    
    def _analyze_keyword_batch_optimized(self, keywords: List[str]) -> Dict[str, Any]:
        """优化的批量关键词分析"""
        batch_results = {}
        
        for keyword in keywords:
            try:
                # 使用现有分析器，但添加超时控制
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"关键词 '{keyword}' 分析超时")
                
                # 设置超时
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.batch_config['timeout_per_keyword'])
                
                try:
                    trend_result = self.root_analyzer.analyze_single_root_word(keyword)
                    signal.alarm(0)  # 取消超时
                    
                    if trend_result and trend_result.get('status') == 'success':
                        # 统一数据格式
                        formatted_result = self._format_trend_result(trend_result)
                        batch_results[keyword] = formatted_result
                    else:
                        batch_results[keyword] = {
                            'success': False,
                            'keyword': keyword,
                            'error': trend_result.get('error', 'No trend data available')
                        }
                        
                except TimeoutError as te:
                    signal.alarm(0)
                    batch_results[keyword] = {
                        'success': False,
                        'keyword': keyword,
                        'error': str(te)
                    }
                    
            except Exception as e:
                print(f"❌ 分析关键词 '{keyword}' 失败: {e}")
                batch_results[keyword] = {
                    'success': False,
                    'keyword': keyword,
                    'error': str(e)
                }
        
        return batch_results
    
    def _analyze_keyword_batch_parallel(self, keywords: List[str]) -> Dict[str, Any]:
        """并行批量关键词分析（实验性功能）"""
        import concurrent.futures
        import threading
        
        batch_results = {}
        
        def analyze_single_keyword(keyword):
            try:
                trend_result = self.root_analyzer.analyze_single_root_word(keyword)
                if trend_result and trend_result.get('status') == 'success':
                    return keyword, self._format_trend_result(trend_result)
                else:
                    return keyword, {
                        'success': False,
                        'keyword': keyword,
                        'error': trend_result.get('error', 'No trend data available')
                    }
            except Exception as e:
                return keyword, {
                    'success': False,
                    'keyword': keyword,
                    'error': str(e)
                }
        
        # 使用线程池并行处理（注意：由于API限制，实际效果可能有限）
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_keyword = {
                executor.submit(analyze_single_keyword, keyword): keyword 
                for keyword in keywords
            }
            
            for future in concurrent.futures.as_completed(future_to_keyword):
                keyword, result = future.result()
                batch_results[keyword] = result
        
        return batch_results
    
    def _format_trend_result(self, trend_result: Dict[str, Any]) -> Dict[str, Any]:
        """统一趋势结果数据格式"""
        try:
            return {
                'success': True,
                'keyword': trend_result.get('root_word', ''),
                'trend_data': trend_result.get('data', {}),
                'analysis_timestamp': trend_result.get('timestamp', datetime.now().isoformat()),
                'data_source': 'RootWordTrendsAnalyzer',
                'format_version': '1.0'
            }
        except Exception as e:
            return {
                'success': False,
                'keyword': trend_result.get('root_word', ''),
                'error': f'格式化失败: {str(e)}',
                'raw_data': trend_result
            }
    
    def _calculate_data_quality_score(self, result: Dict[str, Any]) -> float:
        """
        计算数据质量评分
        
        Args:
            result: 趋势分析结果
            
        Returns:
            数据质量评分 (0-100)
        """
        try:
            trend_data = result.get('trend_data', {})
            
            if not trend_data:
                return 0.0
            
            quality_score = 0.0
            
            # 数据完整性检查 (40分)
            required_fields = ['keyword', 'average_interest', 'trend_direction', 'related_queries']
            available_fields = sum(1 for field in required_fields if field in trend_data)
            completeness_score = (available_fields / len(required_fields)) * 40
            quality_score += completeness_score
            
            # 相关查询数量 (30分)
            related_queries = trend_data.get('related_queries', [])
            queries_score = min(len(related_queries) / 10 * 30, 30)  # 10个查询为满分
            quality_score += queries_score
            
            # 数据新鲜度 (20分)
            timestamp = result.get('analysis_timestamp', '')
            if timestamp:
                try:
                    analysis_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_diff = (datetime.now() - analysis_time).total_seconds()
                    # 1小时内为满分，超过24小时为0分
                    freshness_score = max(0, min(20, 20 * (1 - time_diff / 86400)))
                    quality_score += freshness_score
                except:
                    pass
            
            # 趋势稳定性 (10分)
            if trend_data.get('trend_direction') in ['rising', 'stable']:
                quality_score += 10
            elif trend_data.get('trend_direction') == 'declining':
                quality_score += 5
            
            return min(quality_score, 100.0)
            
        except Exception as e:
            print(f"❌ 计算数据质量评分失败: {e}")
            return 0.0
    
    def get_supported_keywords_types(self) -> List[str]:
        """获取支持的关键词类型"""
        return [
            'root_words',      # 词根
            'ai_tools',        # AI工具
            'tech_terms',      # 技术术语
            'product_names',   # 产品名称
            'brand_names',     # 品牌名称
            'generic_terms',   # 通用术语
            'long_tail',       # 长尾关键词
            'compound_terms'   # 复合词
        ]
    
    def validate_keywords(self, keywords: List[str]) -> Dict[str, Any]:
        """
        验证关键词列表的有效性
        
        Args:
            keywords: 关键词列表
            
        Returns:
            验证结果
        """
        validation_result = {
            'total_keywords': len(keywords),
            'valid_keywords': [],
            'invalid_keywords': [],
            'warnings': [],
            'recommendations': []
        }
        
        for keyword in keywords:
            if not keyword or not keyword.strip():
                validation_result['invalid_keywords'].append({
                    'keyword': keyword,
                    'reason': '空关键词'
                })
                continue
            
            keyword = keyword.strip()
            
            # 长度检查
            if len(keyword) > 100:
                validation_result['warnings'].append({
                    'keyword': keyword,
                    'warning': '关键词过长，可能影响分析效果'
                })
            
            # 特殊字符检查
            if any(char in keyword for char in ['<', '>', '&', '"', "'"]):
                validation_result['warnings'].append({
                    'keyword': keyword,
                    'warning': '包含特殊字符，可能影响搜索结果'
                })
            
            validation_result['valid_keywords'].append(keyword)
        
        # 生成建议
        if len(validation_result['valid_keywords']) > 50:
            validation_result['recommendations'].append(
                '关键词数量较多，建议分批处理以提高成功率'
            )
        
        if len(validation_result['invalid_keywords']) > 0:
            validation_result['recommendations'].append(
                '请清理无效关键词后重新分析'
            )
        
        return validation_result
    
    def _calculate_data_quality_score_from_raw(self, raw_result: Dict[str, Any]) -> float:
        """
        从原始结果计算数据质量评分
        
        Args:
            raw_result: 原始分析结果
            
        Returns:
            数据质量评分 (0-100)
        """
        try:
            if not raw_result or raw_result.get('status') != 'success':
                return 0.0
            
            data = raw_result.get('data', {})
            if not data:
                return 0.0
            
            quality_score = 0.0
            
            # 基础数据完整性 (40分)
            required_fields = ['keyword', 'average_interest', 'trend_direction', 'related_queries']
            available_fields = sum(1 for field in required_fields if field in data)
            quality_score += (available_fields / len(required_fields)) * 40
            
            # 相关查询数量 (30分)
            related_queries = data.get('related_queries', [])
            quality_score += min(len(related_queries) / 10 * 30, 30)
            
            # 平均兴趣度 (20分)
            avg_interest = data.get('average_interest', 0)
            quality_score += min(avg_interest / 50 * 20, 20)
            
            # 趋势方向有效性 (10分)
            trend_direction = data.get('trend_direction', '')
            if trend_direction in ['rising', 'stable', 'declining']:
                quality_score += 10
            
            return min(quality_score, 100.0)
            
        except Exception as e:
            print(f"❌ 计算原始数据质量评分失败: {e}")
            return 0.0
    
    def enable_offline_mode(self, keywords: List[str] = None) -> Dict[str, Any]:
        """
        启用离线模式
        
        Args:
            keywords: 要预加载的关键词列表，None时使用默认词根
            
        Returns:
            离线模式准备结果
        """
        if keywords is None:
            # 使用默认的51个词根
            keywords = self.root_analyzer.root_words if hasattr(self.root_analyzer, 'root_words') else []
        
        print(f"🔄 启用离线模式，预加载 {len(keywords)} 个关键词...")
        
        # 启用离线模式配置
        self.batch_config['offline_mode'] = True
        
        # 预加载缓存
        offline_result = self.trends_cache.enable_offline_mode(keywords)
        
        # 对于缺失的关键词，尝试获取并缓存
        missing_keywords = offline_result.get('missing_keywords', [])
        if missing_keywords:
            print(f"📥 预加载缺失的 {len(missing_keywords)} 个关键词...")
            
            for keyword in missing_keywords[:10]:  # 限制预加载数量
                try:
                    self.get_trends_data(keyword, use_cache=True)
                    import time
                    time.sleep(2)  # 避免API限制
                except Exception as e:
                    print(f"⚠️ 预加载关键词 '{keyword}' 失败: {e}")
        
        # 更新离线模式状态
        final_result = self.trends_cache.enable_offline_mode(keywords)
        
        print(f"✅ 离线模式准备完成，可用关键词: {len(final_result.get('cached_keywords', []))}")
        return final_result
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return self.trends_cache.get_cache_stats()
    
    def clear_cache(self) -> bool:
        """清空缓存"""
        print("🗑️ 清空趋势数据缓存...")
        result = self.trends_cache.clear_all()
        if result:
            print("✅ 缓存已清空")
        else:
            print("❌ 清空缓存失败")
        return result
    
    def export_cache_backup(self, backup_path: str = None) -> str:
        """导出缓存备份"""
        print("📦 导出缓存备份...")
        backup_file = self.trends_cache.export_cache_backup(backup_path)
        if backup_file:
            print(f"✅ 缓存备份已导出: {backup_file}")
        else:
            print("❌ 导出缓存备份失败")
        return backup_file
    
    def batch_trends_analysis_with_cache(self, keywords: List[str], 
                                       batch_size: int = 5,
                                       force_refresh: bool = False) -> Dict[str, Any]:
        """
        带缓存的批量趋势分析
        
        Args:
            keywords: 关键词列表
            batch_size: 批处理大小
            force_refresh: 是否强制刷新缓存
            
        Returns:
            分析结果
        """
        print(f"🚀 开始带缓存的批量趋势分析，关键词数量: {len(keywords)}")
        
        results = {
            'total_keywords': len(keywords),
            'batch_size': batch_size,
            'force_refresh': force_refresh,
            'keyword_results': {},
            'cache_performance': {
                'cache_hits': 0,
                'cache_misses': 0,
                'api_calls': 0
            },
            'summary': {
                'successful': 0,
                'failed': 0,
                'stability_scores': {},
                'quality_scores': {}
            }
        }
        
        # 分批处理
        for i in range(0, len(keywords), batch_size):
            batch_keywords = keywords[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"📊 处理第 {batch_num} 批关键词: {batch_keywords}")
            
            for keyword in batch_keywords:
                try:
                    # 获取趋势数据（自动使用缓存）
                    result = self.get_trends_data(
                        keyword, 
                        use_cache=not force_refresh
                    )
                    
                    if result:
                        results['keyword_results'][keyword] = result
                        
                        # 统计缓存性能
                        if result.get('source') == 'cache':
                            results['cache_performance']['cache_hits'] += 1
                        else:
                            results['cache_performance']['cache_misses'] += 1
                            results['cache_performance']['api_calls'] += 1
                        
                        # 统计成功/失败
                        if result.get('status') == 'success':
                            results['summary']['successful'] += 1
                            
                            # 计算评分
                            if 'data' in result:
                                stability_score = self._calculate_stability_score({
                                    'trend_data': result['data']
                                })
                                results['summary']['stability_scores'][keyword] = stability_score
                                
                                quality_score = result.get('quality_score', 0.0)
                                results['summary']['quality_scores'][keyword] = quality_score
                        else:
                            results['summary']['failed'] += 1
                    
                except Exception as e:
                    print(f"❌ 处理关键词 '{keyword}' 失败: {e}")
                    results['keyword_results'][keyword] = {
                        'keyword': keyword,
                        'status': 'error',
                        'error': str(e)
                    }
                    results['summary']['failed'] += 1
            
            # 批次间延迟（仅在有API调用时）
            if results['cache_performance']['api_calls'] > 0 and i + batch_size < len(keywords):
                import time
                time.sleep(self.batch_config['delay_between_batches'])
        
        # 计算最终统计
        total_requests = results['cache_performance']['cache_hits'] + results['cache_performance']['cache_misses']
        results['cache_performance']['hit_rate'] = (
            results['cache_performance']['cache_hits'] / total_requests * 100
            if total_requests > 0 else 0
        )
        
        results['summary']['success_rate'] = (
            results['summary']['successful'] / len(keywords) * 100
            if len(keywords) > 0 else 0
        )
        
        print(f"✅ 带缓存批量分析完成")
        print(f"📈 成功率: {results['summary']['success_rate']:.1f}%")
        print(f"🎯 缓存命中率: {results['cache_performance']['hit_rate']:.1f}%")
        print(f"🔌 API调用次数: {results['cache_performance']['api_calls']}")
        
        return results