#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合关键词分析器 - 整合所有分析器的结果
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from .base_analyzer import BaseAnalyzer
from .intent_analyzer_v2 import IntentAnalyzerV2
from .market_analyzer import MarketAnalyzer
from .keyword_analyzer import KeywordAnalyzer
from .keyword_scorer import KeywordScorer
from .competitor_analyzer import CompetitorAnalyzer
from .timeliness_analyzer import TimelinessAnalyzer
from .website_recommendation import WebsiteRecommendationEngine
from .new_word_detector import NewWordDetector

try:
    from src.utils import Logger, FileUtils
except ImportError:
    class Logger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")


class ComprehensiveAnalyzer(BaseAnalyzer):
    """综合关键词分析器，整合所有分析器的结果"""
    
    def __init__(self):
        super().__init__()
        self.logger = Logger()
        
        # 初始化所有分析器
        self._init_analyzers()
        
        # 分析器权重配置
        self.analyzer_weights = {
            'intent': 0.20,
            'market': 0.20,
            'keyword': 0.15,
            'scorer': 0.15,
            'timeliness': 0.15,
            'competitor': 0.10,
            'website': 0.05
        }
        
        print("🔧 综合分析器初始化完成")
    
    def _init_analyzers(self):
        """初始化所有分析器"""
        try:
            self.intent_analyzer = IntentAnalyzerV2()
            self.market_analyzer = MarketAnalyzer()
            self.keyword_analyzer = KeywordAnalyzer()
            self.keyword_scorer = KeywordScorer()
            self.competitor_analyzer = CompetitorAnalyzer()
            self.timeliness_analyzer = TimelinessAnalyzer()
            self.website_analyzer = WebsiteRecommendationEngine()
            self.new_word_detector = NewWordDetector()
            
            self.logger.info("所有分析器初始化成功")
        except Exception as e:
            self.logger.error(f"分析器初始化失败: {e}")
            # 设置为None，后续会跳过失败的分析器
            self.intent_analyzer = None
            self.market_analyzer = None
            self.keyword_analyzer = None
            self.keyword_scorer = None
            self.competitor_analyzer = None
            self.timeliness_analyzer = None
            self.website_analyzer = None
            self.new_word_detector = None
    
    def analyze(self, data, **kwargs):
        """
        综合分析关键词数据
        
        Args:
            data: 关键词数据 (DataFrame 或 List)
            **kwargs: 其他参数
            
        Returns:
            综合分析结果
        """
        # 数据预处理
        if isinstance(data, list):
            df = pd.DataFrame({'query': data})
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise ValueError("数据格式不支持，请使用DataFrame或List")
        
        # 确保有query列
        if 'query' not in df.columns:
            if 'keyword' in df.columns:
                df['query'] = df['keyword']
            elif 'term' in df.columns:
                df['query'] = df['term']
            else:
                raise ValueError("未找到关键词列")
        
        self.logger.info(f"开始综合分析 {len(df)} 个关键词")
        
        # 执行各个分析器
        result_df = self._run_all_analyzers(df)
        
        # 计算综合评分
        result_df = self._calculate_comprehensive_score(result_df)
        
        # 生成分析摘要
        summary = self._generate_comprehensive_summary(result_df)
        
        return {
            'results': result_df,
            'summary': summary,
            'analysis_time': datetime.now().isoformat(),
            'total_keywords': len(result_df)
        }
    
    def _run_all_analyzers(self, df: pd.DataFrame) -> pd.DataFrame:
        """运行所有分析器"""
        result_df = df.copy()
        
        # 1. 意图分析
        if self.intent_analyzer:
            try:
                self.logger.info("🎯 执行意图分析...")
                intent_result = self.intent_analyzer.analyze_keywords(result_df)
                result_df = self._merge_results(result_df, intent_result, 'intent_')
            except Exception as e:
                self.logger.error(f"意图分析失败: {e}")
        
        # 2. 市场分析
        if self.market_analyzer:
            try:
                self.logger.info("📊 执行市场分析...")
                market_result = self.market_analyzer.analyze(result_df)
                result_df = self._merge_results(result_df, market_result, 'market_')
            except Exception as e:
                self.logger.error(f"市场分析失败: {e}")
        
        # 3. 关键词分析
        if self.keyword_analyzer:
            try:
                self.logger.info("🔍 执行关键词分析...")
                keyword_result = self.keyword_analyzer.analyze(result_df)
                result_df = self._merge_results(result_df, keyword_result, 'keyword_')
            except Exception as e:
                self.logger.error(f"关键词分析失败: {e}")
        
        # 4. 关键词评分
        if self.keyword_scorer:
            try:
                self.logger.info("⭐ 执行关键词评分...")
                keywords = result_df['query'].tolist()
                scores = self.keyword_scorer.score_keywords(keywords)
                score_df = pd.DataFrame([
                    {
                        'query': score.keyword,
                        'scorer_pray_score': score.pray_score,
                        'scorer_commercial_score': score.commercial_score,
                        'scorer_trend_score': score.trend_score,
                        'scorer_competition_score': score.competition_score,
                        'scorer_total_score': score.total_score
                    }
                    for score in scores
                ])
                result_df = result_df.merge(score_df, on='query', how='left')
            except Exception as e:
                self.logger.error(f"关键词评分失败: {e}")
        
        # 5. 时效性分析
        if self.timeliness_analyzer:
            try:
                self.logger.info("⏰ 执行时效性分析...")
                timeliness_result = self.timeliness_analyzer.analyze_timeliness(result_df)
                result_df = self._merge_results(result_df, timeliness_result, 'timeliness_')
            except Exception as e:
                self.logger.error(f"时效性分析失败: {e}")
        
        # 6. 竞争对手分析
        if self.competitor_analyzer:
            try:
                self.logger.info("🏆 执行竞争对手分析...")
                competitor_result = self.competitor_analyzer.analyze(result_df)
                result_df = self._merge_results(result_df, competitor_result, 'competitor_')
            except Exception as e:
                self.logger.error(f"竞争对手分析失败: {e}")
        
        # 7. 网站建议分析
        if self.website_analyzer:
            try:
                self.logger.info("🌐 执行网站建议分析...")
                website_result = self.website_analyzer.analyze(result_df)
                result_df = self._merge_results(result_df, website_result, 'website_')
            except Exception as e:
                self.logger.error(f"网站建议分析失败: {e}")
        
        # 8. 新词检测
        if self.new_word_detector:
            try:
                self.logger.info("🆕 执行新词检测...")
                new_word_result = self.new_word_detector.detect_new_words(result_df)
                result_df = self._merge_results(result_df, new_word_result, 'newword_')
            except Exception as e:
                self.logger.error(f"新词检测失败: {e}")
        
        return result_df
    
    def _merge_results(self, main_df: pd.DataFrame, result_df: pd.DataFrame, prefix: str) -> pd.DataFrame:
        """合并分析结果"""
        if result_df is None or result_df.empty:
            return main_df
        
        # 重命名列以避免冲突
        rename_dict = {}
        for col in result_df.columns:
            if col != 'query' and not col.startswith(prefix):
                rename_dict[col] = f"{prefix}{col}"
        
        if rename_dict:
            result_df = result_df.rename(columns=rename_dict)
        
        # 合并数据
        return main_df.merge(result_df, on='query', how='left')
    
    def _calculate_comprehensive_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算综合评分"""
        self.logger.info("🧮 计算综合评分...")
        
        # 收集各分析器的主要评分
        scores = {}
        
        # 意图分析评分
        if 'intent_confidence' in df.columns:
            scores['intent'] = df['intent_confidence'].fillna(0) * 100
        
        # 市场分析评分 (基于搜索量和竞争度)
        if 'market_search_volume' in df.columns and 'market_competition' in df.columns:
            volume_score = np.log1p(df['market_search_volume'].fillna(0)) * 10
            competition_score = (1 - df['market_competition'].fillna(0.5)) * 100
            scores['market'] = (volume_score + competition_score) / 2
        
        # 关键词分析评分
        if 'keyword_difficulty' in df.columns:
            scores['keyword'] = (1 - df['keyword_difficulty'].fillna(0.5)) * 100
        
        # 评分器总分
        if 'scorer_total_score' in df.columns:
            scores['scorer'] = df['scorer_total_score'].fillna(50)
        
        # 时效性评分
        if 'timeliness_score' in df.columns:
            scores['timeliness'] = df['timeliness_score'].fillna(50)
        
        # 竞争对手分析评分
        if 'competitor_opportunity_score' in df.columns:
            scores['competitor'] = df['competitor_opportunity_score'].fillna(50)
        
        # 网站建议评分
        if 'website_feasibility_score' in df.columns:
            scores['website'] = df['website_feasibility_score'].fillna(50)
        
        # 计算加权综合评分
        comprehensive_score = np.zeros(len(df))
        total_weight = 0
        
        for analyzer, score_series in scores.items():
            weight = self.analyzer_weights.get(analyzer, 0)
            if weight > 0:
                comprehensive_score += score_series * weight
                total_weight += weight
        
        # 归一化评分
        if total_weight > 0:
            comprehensive_score = comprehensive_score / total_weight
        else:
            comprehensive_score = np.full(len(df), 50.0)
        
        df['comprehensive_score'] = np.round(comprehensive_score, 2)
        
        # 计算综合等级
        df['comprehensive_grade'] = df['comprehensive_score'].apply(self._get_grade)
        
        # 按综合评分排序
        df = df.sort_values('comprehensive_score', ascending=False).reset_index(drop=True)
        
        return df
    
    def _get_grade(self, score: float) -> str:
        """根据评分获取等级"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C'
        elif score >= 40:
            return 'D'
        else:
            return 'F'
    
    def _generate_comprehensive_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """生成综合分析摘要"""
        summary = {
            'total_keywords': len(df),
            'average_comprehensive_score': round(df['comprehensive_score'].mean(), 2),
            'grade_distribution': df['comprehensive_grade'].value_counts().to_dict(),
            'top_10_keywords': df.head(10)[['query', 'comprehensive_score', 'comprehensive_grade']].to_dict('records'),
            'analyzer_coverage': {},
            'key_insights': []
        }
        
        # 分析器覆盖情况
        analyzer_columns = {
            'intent': 'intent_confidence',
            'market': 'market_search_volume',
            'keyword': 'keyword_difficulty',
            'scorer': 'scorer_total_score',
            'timeliness': 'timeliness_score',
            'competitor': 'competitor_opportunity_score',
            'website': 'website_feasibility_score'
        }
        
        for analyzer, col in analyzer_columns.items():
            if col in df.columns:
                coverage = df[col].notna().sum()
                summary['analyzer_coverage'][analyzer] = {
                    'covered': coverage,
                    'percentage': round(coverage / len(df) * 100, 1)
                }
        
        # 关键洞察
        high_score_count = len(df[df['comprehensive_score'] >= 80])
        if high_score_count > 0:
            summary['key_insights'].append(f"发现 {high_score_count} 个高价值关键词 (评分≥80)")
        
        if 'intent_intent' in df.columns:
            top_intent = df['intent_intent'].value_counts().index[0] if not df['intent_intent'].isna().all() else 'Unknown'
            summary['key_insights'].append(f"主要意图类型: {top_intent}")
        
        if 'timeliness_grade' in df.columns:
            high_timeliness = len(df[df['timeliness_grade'].isin(['A', 'B'])])
            if high_timeliness > 0:
                summary['key_insights'].append(f"{high_timeliness} 个关键词具有高时效性")
        
        return summary
    
    def export_comprehensive_report(self, analysis_result: Dict, output_dir: str = 'output') -> str:
        """导出综合分析报告"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存详细结果
        results_file = os.path.join(output_dir, f'comprehensive_analysis_{timestamp}.csv')
        analysis_result['results'].to_csv(results_file, index=False, encoding='utf-8-sig')
        
        # 保存摘要
        summary_file = os.path.join(output_dir, f'comprehensive_summary_{timestamp}.json')
        import json
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result['summary'], f, ensure_ascii=False, indent=2)
        
        # 生成可读性报告
        report_file = os.path.join(output_dir, f'comprehensive_report_{timestamp}.md')
        self._generate_markdown_report(analysis_result, report_file)
        
        self.logger.info(f"综合分析报告已保存到: {output_dir}")
        return results_file
    
    def _generate_markdown_report(self, analysis_result: Dict, file_path: str):
        """生成Markdown格式的报告"""
        df = analysis_result['results']
        summary = analysis_result['summary']
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# 关键词综合分析报告\n\n")
            f.write(f"**分析时间**: {analysis_result['analysis_time']}\n")
            f.write(f"**关键词总数**: {summary['total_keywords']}\n")
            f.write(f"**平均综合评分**: {summary['average_comprehensive_score']}\n\n")
            
            # 等级分布
            f.write("## 评分等级分布\n\n")
            for grade, count in summary['grade_distribution'].items():
                percentage = round(count / summary['total_keywords'] * 100, 1)
                f.write(f"- **{grade}级**: {count} 个 ({percentage}%)\n")
            
            # Top 10关键词
            f.write("\n## Top 10 关键词\n\n")
            f.write("| 排名 | 关键词 | 综合评分 | 等级 |\n")
            f.write("|------|--------|----------|------|\n")
            for i, kw in enumerate(summary['top_10_keywords'], 1):
                f.write(f"| {i} | {kw['query']} | {kw['comprehensive_score']} | {kw['comprehensive_grade']} |\n")
            
            # 分析器覆盖情况
            f.write("\n## 分析器覆盖情况\n\n")
            for analyzer, coverage in summary['analyzer_coverage'].items():
                f.write(f"- **{analyzer}**: {coverage['covered']}/{summary['total_keywords']} ({coverage['percentage']}%)\n")
            
            # 关键洞察
            f.write("\n## 关键洞察\n\n")
            for insight in summary['key_insights']:
                f.write(f"- {insight}\n")