# market_analyzer.py
# 市场需求分析工具集主脚本
import argparse
import os
import sys
import time
import json
from datetime import datetime
import pandas as pd

# 导入各个模块
try:
    from trends_collector import TrendsCollector
    from keyword_scorer import KeywordScorer
    from intent_analyzer import IntentAnalyzer
except ImportError as e:
    print(f"错误: 无法导入必要模块 - {e}")
    print("请确保所有模块文件在同一目录下")
    sys.exit(1)

class MarketAnalyzer:
    """市场需求分析工具集主类"""
    
    def __init__(self, output_dir='data'):
        """
        初始化市场分析器
        
        参数:
            output_dir (str): 输出目录
        """
        self.output_dir = output_dir
        self.date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化各个模块
        self.trends_collector = TrendsCollector()
        self.keyword_scorer = KeywordScorer()
        self.intent_analyzer = IntentAnalyzer()
        
        # 日志文件
        self.log_file = os.path.join(output_dir, f'analysis_log_{self.date_str}.txt')
        
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
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
        self.log(f"开始市场需求分析 - 关键词: {keywords}, 地区: {geo or '全球'}")
        start_time = time.time()
        
        # 步骤1: 获取Google Trends数据
        self.log("步骤1: 获取Google Trends数据")
        trends_results = self.trends_collector.fetch_multiple_keywords(keywords, geo, timeframe)
        
        if not trends_results:
            self.log("警告: 未获取到任何Google Trends数据")
            return {"error": "未获取到Google Trends数据"}
        
        # 合并所有结果
        trends_df = pd.concat(trends_results.values(), ignore_index=True) if trends_results else pd.DataFrame()
        
        if trends_df.empty:
            self.log("警告: 合并后的Google Trends数据为空")
            return {"error": "Google Trends数据为空"}
        
        # 保存Trends结果
        trends_file = os.path.join(self.output_dir, f'trends_all_{self.date_str}.csv')
        trends_df.to_csv(trends_file, index=False, encoding='utf-8-sig')
        self.log(f"已保存Google Trends数据到: {trends_file}")
        
        # 步骤2: 关键词评分
        self.log("步骤2: 关键词评分")
        
        # 丰富数据（可选）
        if enrich:
            self.log("正在丰富关键词数据...")
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
            self.log(f"过滤后剩余 {len(scored_df)} 条关键词")
        
        # 保存评分结果
        scored_file = os.path.join(self.output_dir, f'scored_{self.date_str}.csv')
        scored_df.to_csv(scored_file, index=False, encoding='utf-8-sig')
        self.log(f"已保存评分结果到: {scored_file}")
        
        # 保存高分关键词
        high_score_df = scored_df[scored_df['score'] >= 70].sort_values('score', ascending=False)
        if not high_score_df.empty:
            high_score_file = os.path.join(self.output_dir, f'scored_high_score_{self.date_str}.csv')
            high_score_df.to_csv(high_score_file, index=False, encoding='utf-8-sig')
            self.log(f"已保存高分关键词 ({len(high_score_df)}个) 到: {high_score_file}")
        
        # 步骤3: 搜索意图分析
        self.log("步骤3: 搜索意图分析")
        result_df = self.intent_analyzer.analyze_keywords(scored_df)
        
        # 生成摘要
        summary = self.intent_analyzer.generate_intent_summary(result_df)
        
        # 保存意图分析结果
        intent_file = os.path.join(self.output_dir, f'intent_{self.date_str}.csv')
        result_df.to_csv(intent_file, index=False, encoding='utf-8-sig')
        self.log(f"已保存意图分析结果到: {intent_file}")
        
        # 保存摘要为JSON
        summary_file = os.path.join(self.output_dir, f'intent_summary_{self.date_str}.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        self.log(f"已保存意图分析摘要到: {summary_file}")
        
        # 按意图分组保存
        for intent, keywords in summary['intent_keywords'].items():
            if keywords:
                intent_df = result_df[result_df['intent'] == intent]
                intent_path = os.path.join(self.output_dir, f'intent_{intent}_{self.date_str}.csv')
                intent_df.to_csv(intent_path, index=False, encoding='utf-8-sig')
                self.log(f"已保存 {intent} ({self.intent_analyzer.INTENT_TYPES[intent]}) 意图关键词到: {intent_path}")
        
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
        report_file = os.path.join(self.output_dir, f'analysis_report_{self.date_str}.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        self.log(f"已保存分析报告到: {report_file}")
        
        # 打印简要统计
        self.log("\n分析完成!")
        self.log(f"总耗时: {duration} 秒")
        self.log(f"关键词总数: {len(result_df)}")
        
        self.log("\n意图分布:")
        for intent, percentage in summary['intent_percentages'].items():
            self.log(f"  {intent} ({self.intent_analyzer.INTENT_TYPES[intent]}): {percentage}%")
        
        self.log("\nTop5高分关键词:")
        for i, kw in enumerate(report["Top5关键词"]):
            self.log(f"  {i+1}. {kw['query']} (分数: {kw['score']}, 意图: {kw['intent']})")
        
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