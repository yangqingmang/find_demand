#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场分析主工具
整合所有分析功能的一站式解决方案
"""

import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from ..collectors.trends_collector import TrendsCollector
from ..analyzers.keyword_scorer import KeywordScorer
from ..analyzers.intent_analyzer import IntentAnalyzer
from ..analyzers.serp_analyzer import SerpAnalyzer
from ..utils.logger import Logger
from ..utils.file_utils import FileUtils
from ..utils.constants import INTENT_TYPES

# 条件导入 Google Ads 采集器
try:
    from ..collectors.ads_collector import AdsCollector
    GOOGLE_ADS_AVAILABLE = True
except ImportError:
    GOOGLE_ADS_AVAILABLE = False

class MarketAnalyzer:
    """市场分析主工具"""
    
    def __init__(self, output_dir: str = 'data'):
        """
        初始化市场分析器
        
        参数:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        self.logger = Logger('logs/market_analyzer.log')
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化各个组件
        self.trends_collector = TrendsCollector()
        self.keyword_scorer = KeywordScorer()
        self.intent_analyzer = IntentAnalyzer()
        self.serp_analyzer = SerpAnalyzer()
        
        # 条件初始化 Google Ads 采集器
        self.ads_collector = None
        if GOOGLE_ADS_AVAILABLE:
            try:
                self.ads_collector = AdsCollector()
                self.logger.info("Google Ads 采集器初始化成功")
            except Exception as e:
                self.logger.warning(f"Google Ads 采集器初始化失败: {e}")
        
        self.logger.info("市场分析器初始化完成")
    
    def run_analysis(self, 
                    keywords: List[str],
                    geo: str = '',
                    timeframe: str = 'today 3-m',
                    volume_weight: float = 0.4,
                    growth_weight: float = 0.4,
                    kd_weight: float = 0.2,
                    min_score: int = 10,
                    enrich: bool = True,
                    use_ads_data: bool = False) -> Dict[str, Any]:
        """
        运行完整的市场分析
        
        参数:
            keywords: 种子关键词列表
            geo: 地理位置
            timeframe: 时间范围
            volume_weight: 搜索量权重
            growth_weight: 增长率权重
            kd_weight: 关键词难度权重
            min_score: 最低评分过滤
            enrich: 是否丰富关键词数据
            use_ads_data: 是否使用 Google Ads 数据
            
        返回:
            分析结果字典
        """
        start_time = datetime.now()
        self.logger.info(f"开始市场分析: {keywords}")
        
        try:
            # 1. 收集趋势数据
            self.logger.info("步骤 1/6: 收集 Google Trends 数据")
            trends_df = self.trends_collector.collect_rising_queries(
                keywords, geo=geo, timeframe=timeframe
            )
            
            if trends_df.empty:
                return {'error': '未获取到趋势数据，请检查关键词或网络连接'}
            
            self.logger.info(f"获取到 {len(trends_df)} 个趋势关键词")
            
            # 2. 使用 Google Ads 数据丰富（如果启用）
            if use_ads_data and self.ads_collector:
                self.logger.info("步骤 2/6: 使用 Google Ads 数据丰富关键词信息")
                trends_df = self._enrich_with_ads_data(trends_df, geo)
            else:
                self.logger.info("步骤 2/6: 跳过 Google Ads 数据丰富")
            
            # 3. 关键词评分
            self.logger.info("步骤 3/6: 计算关键词评分")
            # 创建带权重的评分器
            scorer = KeywordScorer(
                volume_weight=volume_weight,
                growth_weight=growth_weight,
                kd_weight=kd_weight
            )
            scored_df = scorer.score_keywords(trends_df)
            
            # 4. 过滤低分关键词
            self.logger.info(f"步骤 4/6: 过滤评分低于 {min_score} 的关键词")
            high_score_df = scored_df[scored_df['score'] >= min_score].copy()
            
            if high_score_df.empty:
                return {'error': f'没有评分达到 {min_score} 的关键词，请降低最低评分要求'}
            
            # 5. 搜索意图分析
            self.logger.info("步骤 5/6: 分析搜索意图")
            intent_df = self.intent_analyzer.analyze_keywords(high_score_df)
            
            # 6. SERP 分析（可选）
            self.logger.info("步骤 6/6: 进行 SERP 分析")
            try:
                serp_df = self.serp_analyzer.analyze_keywords(intent_df['query'].tolist()[:20])  # 限制前20个
                # 合并 SERP 数据
                intent_df = intent_df.merge(
                    serp_df[['query', 'serp_features', 'ads_count', 'organic_count']],
                    on='query',
                    how='left'
                )
            except Exception as e:
                self.logger.warning(f"SERP 分析失败: {e}")
            
            # 生成分析结果
            result = self._generate_analysis_result(
                intent_df, keywords, geo, timeframe, start_time
            )
            
            # 保存结果
            output_files = self._save_results(intent_df, result)
            result['输出文件'] = output_files
            
            self.logger.info("市场分析完成")
            return result
            
        except Exception as e:
            self.logger.error(f"市场分析失败: {e}")
            return {'error': str(e)}
    
    def _enrich_with_ads_data(self, df: pd.DataFrame, geo: str = '') -> pd.DataFrame:
        """使用 Google Ads 数据丰富关键词信息"""
        try:
            self.logger.info("开始使用 Google Ads 数据丰富关键词信息")
            
            keywords = df['query'].tolist()
            
            # 分批处理（每批最多50个关键词）
            batch_size = 50
            keyword_batches = [keywords[i:i+batch_size] for i in range(0, len(keywords), batch_size)]
            
            ads_df = self.ads_collector.batch_collect(keyword_batches, geo_target=geo)
            
            if not ads_df.empty:
                # 合并数据
                df = df.merge(
                    ads_df[['keyword', 'avg_monthly_searches', 'competition', 'avg_cpc']],
                    left_on='query',
                    right_on='keyword',
                    how='left'
                )
                
                # 更新搜索量（如果 Google Ads 有数据）
                df['volume'] = df['avg_monthly_searches'].fillna(df['volume'])
                
                # 清理临时列
                df = df.drop('keyword', axis=1, errors='ignore')
                
                self.logger.info("Google Ads 数据丰富完成")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Google Ads 数据丰富失败: {e}")
            return df
    
    def _generate_analysis_result(self, 
                                df: pd.DataFrame, 
                                keywords: List[str], 
                                geo: str, 
                                timeframe: str, 
                                start_time: datetime) -> Dict[str, Any]:
        """生成分析结果摘要"""
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 基础统计
        total_keywords = len(df)
        high_score_keywords = len(df[df['score'] >= 50])
        
        # Top 5 关键词
        top_keywords = df.nlargest(5, 'score')[['query', 'score', 'intent', 'volume']].to_dict('records')
        for kw in top_keywords:
            kw['intent'] = INTENT_TYPES.get(kw['intent'], kw['intent'])
        
        # 意图分布
        intent_distribution = df['intent'].value_counts().to_dict()
        intent_distribution = {INTENT_TYPES.get(k, k): v for k, v in intent_distribution.items()}
        
        # 平均指标
        avg_score = df['score'].mean()
        avg_volume = df['volume'].mean()
        avg_growth = df['growth_rate'].mean() if 'growth_rate' in df.columns else 0
        
        result = {
            '分析参数': {
                '种子关键词': keywords,
                '地理位置': geo or '全球',
                '时间范围': timeframe,
                '分析时间': start_time.strftime('%Y-%m-%d %H:%M:%S')
            },
            '关键词总数': total_keywords,
            '高分关键词数': high_score_keywords,
            '分析耗时(秒)': round(duration, 2),
            'Top5关键词': top_keywords,
            '意图分布': intent_distribution,
            '平均指标': {
                '平均评分': round(avg_score, 2),
                '平均搜索量': round(avg_volume, 0),
                '平均增长率': round(avg_growth, 2)
            }
        }
        
        return result
    
    def _save_results(self, df: pd.DataFrame, result: Dict[str, Any]) -> Dict[str, str]:
        """保存分析结果"""
        output_files = {}
        
        try:
            # 保存详细数据
            csv_filename = FileUtils.generate_filename('market_analysis', 'detailed', 'csv')
            csv_path = FileUtils.save_dataframe(df, self.output_dir, csv_filename)
            output_files['详细数据'] = csv_path
            
            # 保存分析报告
            json_filename = FileUtils.generate_filename('analysis_report', '', 'json')
            json_path = os.path.join(self.output_dir, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            output_files['分析报告'] = json_path
            
            # 按意图分组保存
            for intent in df['intent'].unique():
                intent_df = df[df['intent'] == intent]
                intent_name = INTENT_TYPES.get(intent, intent)
                intent_filename = FileUtils.generate_filename('keywords', intent_name, 'csv')
                intent_path = FileUtils.save_dataframe(intent_df, self.output_dir, intent_filename)
                output_files[f'{intent_name}关键词'] = intent_path
            
            self.logger.info(f"分析结果已保存到 {self.output_dir} 目录")
            
        except Exception as e:
            self.logger.error(f"保存结果失败: {e}")
        
        return output_files

def main():
    """测试函数"""
    analyzer = MarketAnalyzer()
    
    # 测试关键词
    test_keywords = ['ai tools', 'chatgpt']
    
    try:
        result = analyzer.run_analysis(
            keywords=test_keywords,
            geo='US',
            timeframe='today 3-m',
            min_score=10
        )
        
        if 'error' in result:
            print(f"分析失败: {result['error']}")
        else:
            print("分析成功完成!")
            print(f"关键词总数: {result['关键词总数']}")
            print(f"高分关键词: {result['高分关键词数']}")
            print(f"分析耗时: {result['分析耗时(秒)']} 秒")
            
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    main()