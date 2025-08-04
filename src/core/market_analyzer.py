#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场需求分析工具集主脚本
Market Analyzer - 核心分析器
"""

import argparse
import os
import sys
import time
import json
from datetime import datetime
import pandas as pd

# 导入各个模块
try:
    from ..collectors.trends_collector import TrendsCollector
    from ..analyzers.keyword_scorer import KeywordScorer
    from ..analyzers.intent_analyzer import IntentAnalyzer
    from ..utils import (
        Logger, FileUtils, safe_print, INTENT_TYPES, 
        ExceptionHandler, AnalysisError
    )
except ImportError:
    # 兼容直接运行的情况
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from collectors.trends_collector import TrendsCollector
    from analyzers.keyword_scorer import KeywordScorer
    from analyzers.intent_analyzer import IntentAnalyzer
    from utils import (
        Logger, FileUtils, safe_print, INTENT_TYPES,
        ExceptionHandler, AnalysisError
    )

class MarketAnalyzer:
    """市场需求分析工具集主类"""
    
    def __init__(self, output_dir='data'):
        """
        初始化市场分析器
        
        参数:
            output_dir (str): 输出目录
        """
        self.output_dir = output_dir
        self.date_str = FileUtils.get_date_str()
        
        # 确保输出目录存在
        FileUtils.ensure_dir(output_dir)
        
        # 初始化各个模块
        self.trends_collector = TrendsCollector()
        self.keyword_scorer = KeywordScorer()
        self.intent_analyzer = IntentAnalyzer()
        
        # 初始化日志记录器
        log_file = os.path.join(output_dir, f'analysis_log_{self.date_str}.txt')
        self.logger = Logger(log_file)
        
    
    def run_analysis(self, keywords, geo='', timeframe='today 3-m', 
                    volume_weight=0.4, growth_weight=0.4, kd_weight=0.2,
                    min_score=None, enrich=True):
        """
        运行完整的市场需求分析流程
        
        参数:
            keywords (list): 要分析的关键词列表
            geo (str): 地区代码
            timeframe (str): 时间范围
            volume_weight (float): 搜索量权重
            growth_weight (float): 增长率权重
            kd_weight (float): 关键词难度权重
            min_score (int): 最低评分过滤
            enrich (bool): 是否丰富数据
            
        返回:
            dict: 分析结果摘要
        """
        self.logger.info(f"开始市场需求分析 - 关键词: {keywords}, 地区: {geo or '全球'}")
        start_time = time.time()
        
        # 步骤1: 获取Google Trends数据
        self.logger.info("步骤1: 获取Google Trends数据")
        trends_results = self.trends_collector.fetch_multiple_keywords(keywords, geo, timeframe)
        
        if not trends_results:
            self.logger.warning("未获取到任何Google Trends数据")
            return {"error": "未获取到Google Trends数据"}
        
        # 合并所有结果
        trends_df = pd.concat(trends_results.values(), ignore_index=True) if trends_results else pd.DataFrame()
        
        if trends_df.empty:
            self.logger.warning("合并后的Google Trends数据为空")
            return {"error": "Google Trends数据为空"}
        
        # 保存Trends结果
        trends_filename = FileUtils.generate_filename('trends_all', extension='csv')
        trends_file = FileUtils.save_dataframe(trends_df, self.output_dir, trends_filename)
        self.logger.info(f"已保存Google Trends数据到: {trends_file}")
        
        # 步骤2: 关键词评分
        self.logger.info("步骤2: 关键词评分")
        
        # 丰富数据（可选）
        if enrich:
            self.logger.info("正在丰富关键词数据...")
            trends_df = self.keyword_scorer.enrich_with_ads_data(trends_df)
        
        # 评分
        scored_df = self.keyword_scorer.score_keywords(
            trends_df, 
            volume_col='value', 
            growth_col='growth' if 'growth' in trends_df.columns else None
        )
        
        # 过滤（可选）
        if min_score:
            scored_df = self.keyword_scorer.filter_keywords(scored_df, min_score=min_score)
            self.logger.info(f"过滤后剩余 {len(scored_df)} 条关键词")
        
        # 保存评分结果
        scored_filename = FileUtils.generate_filename('scored', extension='csv')
        scored_file = FileUtils.save_dataframe(scored_df, self.output_dir, scored_filename)
        self.logger.info(f"已保存评分结果到: {scored_file}")
        
        # 保存高分关键词
        high_score_df = scored_df[scored_df['score'] >= 70].sort_values('score', ascending=False)
        if not high_score_df.empty:
            high_score_filename = FileUtils.generate_filename('scored_high_score', extension='csv')
            high_score_file = FileUtils.save_dataframe(high_score_df, self.output_dir, high_score_filename)
            self.logger.info(f"已保存高分关键词 ({len(high_score_df)}个) 到: {high_score_file}")
        
        # 步骤3: 搜索意图分析
        self.logger.info("步骤3: 搜索意图分析")
        result_df = self.intent_analyzer.analyze_keywords(scored_df)
        
        # 生成摘要
        summary = self.intent_analyzer.generate_intent_summary(result_df)
        
        # 保存意图分析结果
        intent_filename = FileUtils.generate_filename('intent', extension='csv')
        intent_file = FileUtils.save_dataframe(result_df, self.output_dir, intent_filename)
        self.logger.info(f"已保存意图分析结果到: {intent_file}")
        
        # 保存摘要为JSON
        summary_filename = FileUtils.generate_filename('intent_summary', extension='json')
        summary_file = FileUtils.save_json(summary, self.output_dir, summary_filename)
        self.logger.info(f"已保存意图分析摘要到: {summary_file}")
        
        # 按意图分组保存
        for intent, keywords in summary['intent_keywords'].items():
            if keywords:
                intent_df = result_df[result_df['intent'] == intent]
                intent_filename = FileUtils.generate_filename(f'intent_{intent}', extension='csv')
                intent_path = FileUtils.save_dataframe(intent_df, self.output_dir, intent_filename)
                intent_name = INTENT_TYPES.get(intent, intent)
                self.logger.info(f"已保存 {intent} ({intent_name}) 意图关键词到: {intent_path}")
        
        # 生成最终报告
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        
        report = {
            "分析日期": self.date_str,
            "分析关键词": keywords,
            "地区": geo or "全球",
            "时间范围": timeframe,
            "分析耗时(秒)": duration,
            "关键词总数": len(result_df),
            "高分关键词数": len(high_score_df) if 'high_score_df' in locals() else 0,
            "意图分布": summary['intent_percentages'],
            "Top5关键词": result_df.sort_values('score', ascending=False).head(5)[['query', 'score', 'intent']].to_dict('records'),
            "输出文件": {
                "Google Trends数据": trends_file,
                "评分结果": scored_file,
                "意图分析结果": intent_file,
                "意图分析摘要": summary_file
            }
        }
        
        # 保存最终报告
        report_filename = FileUtils.generate_filename('analysis_report', extension='json')
        report_file = FileUtils.save_json(report, self.output_dir, report_filename)
        self.logger.info(f"已保存分析报告到: {report_file}")
        
        # 打印最终结果摘要
        self.print_final_summary(report, summary)
        
        return report
    
    
    def print_final_summary(self, report, summary):
        """打印最终结果摘要"""
        safe_print("\n" + "="*80)
        safe_print("市场需求分析完成!")
        safe_print("="*80)
        
        safe_print("分析概览:")
        safe_print(f"   • 分析关键词: {', '.join(report['分析关键词'])}")
        safe_print(f"   • 目标地区: {report['地区']}")
        safe_print(f"   • 分析耗时: {report['分析耗时(秒)']} 秒")
        safe_print(f"   • 发现关键词: {report['关键词总数']} 个")
        safe_print(f"   • 高分关键词: {report['高分关键词数']} 个")
        
        safe_print("\n搜索意图分布:")
        for intent, percentage in report['意图分布'].items():
            intent_name = INTENT_TYPES.get(intent, intent)
            bar_length = int(percentage / 5)  # 每5%一个字符
            bar = "█" * bar_length + "░" * (20 - bar_length)
            safe_print(f"   {intent} ({intent_name:4s}): {bar} {percentage:5.1f}%")
        
        safe_print("\nTop 5 高分关键词:")
        for i, kw in enumerate(report["Top5关键词"]):
            intent_name = INTENT_TYPES.get(kw['intent'], kw['intent'])
            safe_print(f"   {i+1}. {kw['query']:<40} 分数: {kw['score']:3d} | 意图: {intent_name}")
        
        safe_print("\n输出文件:")
        for desc, path in report['输出文件'].items():
            safe_print(f"   • {desc}: {path}")
        
        safe_print("\n建议:")
        self.print_recommendations(report, summary)
        
        safe_print("="*80)
    
    def print_recommendations(self, report, summary):
        """打印分析建议"""
        intent_dist = report['意图分布']
        top_keywords = report["Top5关键词"]
        
        # 基于意图分布的建议
        if intent_dist.get('I', 0) > 60:
            safe_print("   信息型关键词占主导，建议创建教育性内容和指南")
        if intent_dist.get('C', 0) > 30:
            safe_print("   商业型关键词较多，建议优化产品页面和比较内容")
        if intent_dist.get('E', 0) > 20:
            safe_print("   交易型关键词较多，建议优化购买流程和着陆页")
        
        # 基于高分关键词的建议
        if report['高分关键词数'] > 0:
            safe_print(f"   发现 {report['高分关键词数']} 个高潜力关键词，建议优先投入资源")
        
        # 基于Top关键词的建议
        if top_keywords:
            top_intent = max(set(kw['intent'] for kw in top_keywords), 
                           key=lambda x: sum(1 for kw in top_keywords if kw['intent'] == x))
            intent_name = INTENT_TYPES.get(top_intent, top_intent)
            safe_print(f"   Top关键词主要为{intent_name}，建议针对性优化内容策略")
        
        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='市场需求分析工具集')
    parser.add_argument('--keywords', nargs='+', required=True, help='要分析的关键词列表')
    parser.add_argument('--geo', default='', help='地区代码，如US、GB等，默认为全球')
    parser.add_argument('--timeframe', default='today 3-m', help='时间范围，默认为过去3个月')
    parser.add_argument('--output', default='data', help='输出目录，默认为data')
    parser.add_argument('--volume-weight', type=float, default=0.4, help='搜索量权重，默认0.4')
    parser.add_argument('--growth-weight', type=float, default=0.4, help='增长率权重，默认0.4')
    parser.add_argument('--kd-weight', type=float, default=0.2, help='关键词难度权重，默认0.2')
    parser.add_argument('--min-score', type=int, help='最低评分过滤')
    parser.add_argument('--no-enrich', action='store_true', help='不丰富关键词数据')
    
    args = parser.parse_args()
    
    # 创建市场分析器
    analyzer = MarketAnalyzer(args.output)
    
    # 运行分析
    analyzer.run_analysis(
        keywords=args.keywords,
        geo=args.geo,
        timeframe=args.timeframe,
        volume_weight=args.volume_weight,
        growth_weight=args.growth_weight,
        kd_weight=args.kd_weight,
        min_score=args.min_score,
        enrich=not args.no_enrich
    )


if __name__ == "__main__":
    main()