"""
词根趋势分析器
用于分析51个词根对应关键词的Google Trends趋势数据
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time
import logging
from pathlib import Path

from ..collectors.trends_collector import TrendsCollector
from ..utils.logger import setup_logger
from ..utils.file_utils import ensure_directory_exists

class RootWordTrendsAnalyzer:
    """词根趋势分析器"""
    
    def __init__(self, output_dir: str = "data/root_word_trends"):
        self.output_dir = output_dir
        ensure_directory_exists(self.output_dir)
        self.logger = setup_logger(__name__)
        self.trends_collector = TrendsCollector()
        
        # 51个词根列表
        self.root_words = [
            "AI", "artificial intelligence", "machine learning", "deep learning", "neural network",
            "chatbot", "GPT", "OpenAI", "ChatGPT", "language model",
            "computer vision", "natural language processing", "NLP", "automation", "robot",
            "algorithm", "data science", "big data", "analytics", "prediction",
            "classification", "clustering", "regression", "supervised learning", "unsupervised learning",
            "reinforcement learning", "transfer learning", "generative AI", "LLM", "transformer",
            "BERT", "attention mechanism", "encoder", "decoder", "embedding",
            "tokenization", "fine-tuning", "prompt engineering", "few-shot learning", "zero-shot learning",
            "multimodal", "text-to-image", "image generation", "voice synthesis", "speech recognition",
            "recommendation system", "personalization", "content generation", "code generation", "AI assistant"
        ]
    
    def analyze_single_root_word(self, root_word: str, timeframe: str = "12-m") -> Dict[str, Any]:
        """
        分析单个词根的趋势
        
        Args:
            root_word: 词根
            timeframe: 时间范围 (默认12个月)
            
        Returns:
            包含趋势数据的字典
        """
        try:
            self.logger.info(f"正在分析词根: {root_word}")
            
            # 获取趋势数据
            trend_data = self.trends_collector.get_keyword_trends([root_word], timeframe=timeframe)
            
            if not trend_data:
                self.logger.warning(f"未获取到 {root_word} 的趋势数据")
                return {"root_word": root_word, "status": "no_data", "data": None}
            
            # 处理趋势数据
            processed_data = self._process_trend_data(root_word, trend_data)
            
            # 添加延迟避免API限制
            time.sleep(1)
            
            return {
                "root_word": root_word,
                "status": "success",
                "data": processed_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"分析词根 {root_word} 时出错: {str(e)}")
            return {"root_word": root_word, "status": "error", "error": str(e)}
    
    def _process_trend_data(self, root_word: str, trend_data: Dict) -> Dict[str, Any]:
        """处理趋势数据"""
        processed = {
            "keyword": root_word,
            "trend_points": [],
            "average_interest": 0,
            "peak_interest": 0,
            "trend_direction": "stable",
            "related_queries": []
        }
        
        if "interest_over_time" in trend_data:
            interest_data = trend_data["interest_over_time"]
            if isinstance(interest_data, pd.DataFrame) and not interest_data.empty:
                # 提取趋势点
                for _, row in interest_data.iterrows():
                    processed["trend_points"].append({
                        "date": row.name.strftime("%Y-%m-%d") if hasattr(row.name, 'strftime') else str(row.name),
                        "interest": int(row.iloc[0]) if not pd.isna(row.iloc[0]) else 0
                    })
                
                # 计算统计数据
                values = [point["interest"] for point in processed["trend_points"]]
                if values:
                    processed["average_interest"] = sum(values) / len(values)
                    processed["peak_interest"] = max(values)
                    
                    # 判断趋势方向
                    if len(values) >= 2:
                        recent_avg = sum(values[-3:]) / min(3, len(values))
                        early_avg = sum(values[:3]) / min(3, len(values))
                        
                        if recent_avg > early_avg * 1.1:
                            processed["trend_direction"] = "rising"
                        elif recent_avg < early_avg * 0.9:
                            processed["trend_direction"] = "declining"
        
        # 处理相关查询
        if "related_queries" in trend_data:
            related_data = trend_data["related_queries"]
            if isinstance(related_data, dict):
                for query_type, queries in related_data.items():
                    if isinstance(queries, pd.DataFrame) and not queries.empty:
                        processed["related_queries"].extend([
                            {
                                "query": row["query"],
                                "value": row["value"],
                                "type": query_type
                            }
                            for _, row in queries.head(10).iterrows()
                        ])
        
        return processed
    
    def analyze_all_root_words(self, timeframe: str = "12-m", batch_size: int = 5) -> Dict[str, Any]:
        """
        分析所有词根的趋势
        
        Args:
            timeframe: 时间范围
            batch_size: 批处理大小
            
        Returns:
            完整的分析结果
        """
        self.logger.info(f"开始分析 {len(self.root_words)} 个词根的趋势")
        
        results = {
            "analysis_date": datetime.now().isoformat(),
            "timeframe": timeframe,
            "total_root_words": len(self.root_words),
            "results": [],
            "summary": {}
        }
        
        # 分批处理词根
        for i in range(0, len(self.root_words), batch_size):
            batch = self.root_words[i:i + batch_size]
            self.logger.info(f"处理批次 {i//batch_size + 1}: {batch}")
            
            for root_word in batch:
                result = self.analyze_single_root_word(root_word, timeframe)
                results["results"].append(result)
                
                # 批次间延迟
                time.sleep(2)
            
            # 批次间更长延迟
            if i + batch_size < len(self.root_words):
                self.logger.info("批次间休息...")
                time.sleep(10)
        
        # 生成摘要
        results["summary"] = self._generate_summary(results["results"])
        
        # 保存结果
        self._save_results(results)
        
        return results
    
    def _generate_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """生成分析摘要"""
        summary = {
            "successful_analyses": 0,
            "failed_analyses": 0,
            "top_trending_words": [],
            "declining_words": [],
            "stable_words": [],
            "average_interest_distribution": {}
        }
        
        successful_results = []
        
        for result in results:
            if result["status"] == "success" and result["data"]:
                summary["successful_analyses"] += 1
                successful_results.append(result)
            else:
                summary["failed_analyses"] += 1
        
        # 按趋势方向分类
        for result in successful_results:
            data = result["data"]
            root_word = result["root_word"]
            
            if data["trend_direction"] == "rising":
                summary["top_trending_words"].append({
                    "word": root_word,
                    "average_interest": data["average_interest"],
                    "peak_interest": data["peak_interest"]
                })
            elif data["trend_direction"] == "declining":
                summary["declining_words"].append({
                    "word": root_word,
                    "average_interest": data["average_interest"]
                })
            else:
                summary["stable_words"].append({
                    "word": root_word,
                    "average_interest": data["average_interest"]
                })
        
        # 排序
        summary["top_trending_words"].sort(key=lambda x: x["average_interest"], reverse=True)
        summary["declining_words"].sort(key=lambda x: x["average_interest"], reverse=True)
        summary["stable_words"].sort(key=lambda x: x["average_interest"], reverse=True)
        
        return summary
    
    def _save_results(self, results: Dict[str, Any]):
        """保存分析结果"""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        # 保存完整结果
        full_results_path = os.path.join(self.output_dir, f"root_word_trends_full_{timestamp}.json")
        with open(full_results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 保存摘要
        summary_path = os.path.join(self.output_dir, f"root_word_trends_summary_{timestamp}.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(results["summary"], f, ensure_ascii=False, indent=2)
        
        # 生成CSV报告
        self._generate_csv_report(results, timestamp)
        
        self.logger.info(f"结果已保存到: {self.output_dir}")
    
    def _generate_csv_report(self, results: Dict[str, Any], timestamp: str):
        """生成CSV格式的报告"""
        csv_data = []
        
        for result in results["results"]:
            if result["status"] == "success" and result["data"]:
                data = result["data"]
                csv_data.append({
                    "词根": result["root_word"],
                    "状态": "成功",
                    "平均兴趣度": round(data["average_interest"], 2),
                    "峰值兴趣度": data["peak_interest"],
                    "趋势方向": data["trend_direction"],
                    "相关查询数量": len(data["related_queries"])
                })
            else:
                csv_data.append({
                    "词根": result["root_word"],
                    "状态": "失败",
                    "平均兴趣度": 0,
                    "峰值兴趣度": 0,
                    "趋势方向": "未知",
                    "相关查询数量": 0
                })
        
        df = pd.DataFrame(csv_data)
        csv_path = os.path.join(self.output_dir, f"root_word_trends_report_{timestamp}.csv")
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        self.logger.info(f"CSV报告已生成: {csv_path}")
    
    def get_trending_keywords_for_root(self, root_word: str, limit: int = 20) -> List[str]:
        """
        获取特定词根的热门相关关键词
        
        Args:
            root_word: 词根
            limit: 返回关键词数量限制
            
        Returns:
            相关关键词列表
        """
        try:
            # 获取相关查询
            trend_data = self.trends_collector.get_keyword_trends([root_word])
            
            keywords = []
            if "related_queries" in trend_data:
                related_data = trend_data["related_queries"]
                if isinstance(related_data, dict):
                    for query_type, queries in related_data.items():
                        if isinstance(queries, pd.DataFrame) and not queries.empty:
                            for _, row in queries.head(limit).iterrows():
                                keywords.append(row["query"])
            
            return keywords[:limit]
            
        except Exception as e:
            self.logger.error(f"获取 {root_word} 相关关键词时出错: {str(e)}")
            return []

def main():
    """主函数 - 运行词根趋势分析"""
    analyzer = RootWordTrendsAnalyzer()
    
    print("开始分析51个词根的趋势...")
    results = analyzer.analyze_all_root_words(timeframe="12-m")
    
    print(f"\n分析完成!")
    print(f"成功分析: {results['summary']['successful_analyses']} 个词根")
    print(f"失败分析: {results['summary']['failed_analyses']} 个词根")
    
    print(f"\n上升趋势词根 ({len(results['summary']['top_trending_words'])}):")
    for word_data in results['summary']['top_trending_words'][:10]:
        print(f"  - {word_data['word']}: 平均兴趣度 {word_data['average_interest']:.1f}")
    
    print(f"\n下降趋势词根 ({len(results['summary']['declining_words'])}):")
    for word_data in results['summary']['declining_words'][:5]:
        print(f"  - {word_data['word']}: 平均兴趣度 {word_data['average_interest']:.1f}")

if __name__ == "__main__":
    main()