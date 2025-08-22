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
from .analyzers.new_word_detector import NewWordDetector

class RootWordTrendsAnalyzer:
    """词根趋势分析器"""
    
    def __init__(self, output_dir: str = "data/root_word_trends"):
        self.output_dir = output_dir
        ensure_directory_exists(self.output_dir)
        self.logger = setup_logger(__name__)
        self.trends_collector = TrendsCollector()
        
        # 初始化新词检测器
        try:
            self.new_word_detector = NewWordDetector()
            self.new_word_detection_available = True
            self.logger.info("新词检测器初始化成功")
        except Exception as e:
            self.new_word_detector = None
            self.new_word_detection_available = False
            self.logger.warning(f"新词检测器初始化失败: {e}")
        
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
    
    def analyze_single_root_word(self, root_word: str, timeframe: str = None) -> Dict[str, Any]:
        """
        分析单个词根的趋势
        
        参数:
            root_word: 要分析的词根
            timeframe: 时间范围，默认使用统一配置中的值
            
        返回:
            包含趋势数据的字典
        """
        if timeframe is None:
            from src.utils.constants import GOOGLE_TRENDS_CONFIG
            timeframe = GOOGLE_TRENDS_CONFIG['default_timeframe'].replace('today ', '')
        try:
            self.logger.info(f"正在分析词根: {root_word}")
            
            # 获取趋势数据 - 传递单个字符串而不是列表
            trend_data = self.trends_collector.get_keyword_trends(root_word, timeframe=timeframe)
            
            if not trend_data:
                self.logger.warning(f"未获取到 {root_word} 的趋势数据")
                return {"root_word": root_word, "status": "no_data", "data": None}
            
            # 处理趋势数据
            processed_data = self._process_trend_data(root_word, trend_data)
            
            # 添加延迟避免API限制 - 优化后的间隔时间
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
        
        try:
            # 处理趋势数据 - 从TrendsCollector返回的数据结构
            if isinstance(trend_data, dict):
                # 如果是字典格式，提取相关查询数据
                if "related_queries" in trend_data and trend_data["related_queries"]:
                    queries = trend_data["related_queries"]
                    if isinstance(queries, list):
                        # 处理查询列表
                        for query_item in queries[:10]:  # 限制前10个
                            if isinstance(query_item, dict):
                                query_text = query_item.get("query", "")
                                query_value = query_item.get("value", 0)
                                
                                # 为关联想词添加新词检测
                                new_word_info = self._detect_new_word_for_query(query_text)
                                
                                processed["related_queries"].append({
                                    "query": query_text,
                                    "value": query_value,
                                    "type": "related",
                                    "new_word_detection": new_word_info
                                })
                
                # 计算平均兴趣度
                if "avg_volume" in trend_data:
                    processed["average_interest"] = float(trend_data["avg_volume"])
                    processed["peak_interest"] = int(processed["average_interest"] * 1.5)  # 估算峰值
                
                # 根据数据量判断趋势方向
                total_queries = trend_data.get("total_queries", 0)
                if total_queries > 50:
                    processed["trend_direction"] = "rising"
                elif total_queries > 20:
                    processed["trend_direction"] = "stable"
                else:
                    processed["trend_direction"] = "declining"
            
            elif isinstance(trend_data, pd.DataFrame) and not trend_data.empty:
                # 如果是DataFrame格式，直接处理
                try:
                    # 安全地处理DataFrame数据
                    for idx, row in trend_data.iterrows():
                        try:
                            query_value = row.get("query", "") if hasattr(row, 'get') else str(row.iloc[0]) if len(row) > 0 else ""
                            value_data = row.get("value", 0) if hasattr(row, 'get') else (row.iloc[1] if len(row) > 1 else 0)
                            
                            # 为关联想词添加新词检测
                            new_word_info = self._detect_new_word_for_query(str(query_value))
                            
                            processed["related_queries"].append({
                                "query": str(query_value),
                                "value": int(value_data) if pd.notna(value_data) else 0,
                                "type": "related",
                                "new_word_detection": new_word_info
                            })
                        except Exception as row_error:
                            self.logger.warning(f"处理行数据时出错: {row_error}")
                            continue
                    
                    # 计算统计数据
                    if processed["related_queries"]:
                        values = [item["value"] for item in processed["related_queries"]]
                        processed["average_interest"] = sum(values) / len(values) if values else 0
                        processed["peak_interest"] = max(values) if values else 0
                        
                        # 简单的趋势判断
                        if processed["average_interest"] > 30:
                            processed["trend_direction"] = "rising"
                        elif processed["average_interest"] > 10:
                            processed["trend_direction"] = "stable"
                        else:
                            processed["trend_direction"] = "declining"
                
                except Exception as df_error:
                    self.logger.error(f"处理DataFrame时出错: {df_error}")
            
            # 如果没有获取到任何数据，提供默认值
            if not processed["related_queries"]:
                processed["average_interest"] = 10  # 默认兴趣度
                processed["peak_interest"] = 15
                processed["trend_direction"] = "stable"
        
        except Exception as e:
            self.logger.error(f"处理趋势数据时出错: {e}")
            # 返回默认数据结构
            processed = {
                "keyword": root_word,
                "trend_points": [],
                "average_interest": 5,
                "peak_interest": 10,
                "trend_direction": "stable",
                "related_queries": []
            }
        
        return processed
    
    def _detect_new_word_for_query(self, query: str) -> Dict[str, Any]:
        """
        为单个关联想词进行新词检测
        
        参数:
            query: 关联想词
            
        返回:
            新词检测结果
        """
        if not self.new_word_detection_available or not query.strip():
            return {
                "is_new_word": False,
                "new_word_score": 0.0,
                "new_word_grade": "D",
                "confidence_level": "low",
                "growth_rate_7d": 0.0,
                "historical_pattern": "unknown",
                "detection_reasons": "新词检测不可用"
            }
        
        try:
            # 创建临时DataFrame进行新词检测
            temp_df = pd.DataFrame({'query': [query]})
            
            # 使用新词检测器分析
            result_df = self.new_word_detector.detect_new_words(temp_df, 'query')
            
            if len(result_df) > 0:
                row = result_df.iloc[0]
                return {
                    "is_new_word": bool(row.get('is_new_word', False)),
                    "new_word_score": float(row.get('new_word_score', 0.0)),
                    "new_word_grade": str(row.get('new_word_grade', 'D')),
                    "confidence_level": str(row.get('confidence_level', 'low')),
                    "growth_rate_7d": float(row.get('growth_rate_7d', 0.0)),
                    "historical_pattern": str(row.get('historical_pattern', 'unknown')),
                    "detection_reasons": str(row.get('detection_reasons', ''))
                }
            else:
                return self._get_default_new_word_result()
                
        except Exception as e:
            self.logger.warning(f"关联想词 '{query}' 新词检测失败: {e}")
            return self._get_default_new_word_result()
    
    def _get_default_new_word_result(self) -> Dict[str, Any]:
        """获取默认新词检测结果"""
        return {
            "is_new_word": False,
            "new_word_score": 0.0,
            "new_word_grade": "D",
            "confidence_level": "low",
            "growth_rate_7d": 0.0,
            "historical_pattern": "unknown",
            "detection_reasons": "检测失败"
        }
    
    def analyze_all_root_words(self, timeframe: str = None, batch_size: int = 5) -> Dict[str, Any]:
        """
        分析所有词根的趋势
        
        参数:
            timeframe: 时间范围，默认使用统一配置中的值
            batch_size: 批处理大小，默认5个词根一批
            
        返回:
            完整的分析结果
        """
        if timeframe is None:
            from src.utils.constants import GOOGLE_TRENDS_CONFIG
            timeframe = GOOGLE_TRENDS_CONFIG['default_timeframe'].replace('today ', '')
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
                time.sleep(5)
        
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
                
                # 统计新词信息
                new_words_count = 0
                high_confidence_new_words = 0
                total_new_word_score = 0
                
                for query in data["related_queries"]:
                    if "new_word_detection" in query:
                        nwd = query["new_word_detection"]
                        if nwd.get("is_new_word", False):
                            new_words_count += 1
                            total_new_word_score += nwd.get("new_word_score", 0)
                            if nwd.get("confidence_level") == "high":
                                high_confidence_new_words += 1
                
                avg_new_word_score = (total_new_word_score / new_words_count) if new_words_count > 0 else 0
                
                csv_data.append({
                    "词根": result["root_word"],
                    "状态": "成功",
                    "平均兴趣度": round(data["average_interest"], 2),
                    "峰值兴趣度": data["peak_interest"],
                    "趋势方向": data["trend_direction"],
                    "相关查询数量": len(data["related_queries"]),
                    "新词数量": new_words_count,
                    "高置信度新词": high_confidence_new_words,
                    "平均新词分数": round(avg_new_word_score, 1)
                })
            else:
                csv_data.append({
                    "词根": result["root_word"],
                    "状态": "失败",
                    "平均兴趣度": 0,
                    "峰值兴趣度": 0,
                    "趋势方向": "未知",
                    "相关查询数量": 0,
                    "新词数量": 0,
                    "高置信度新词": 0,
                    "平均新词分数": 0
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
    results = analyzer.analyze_all_root_words(timeframe="now 7-d")
    
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