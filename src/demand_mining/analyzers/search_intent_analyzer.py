#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
搜索意图分析器
分析关键词的搜索意图，优先识别高转化意图的长尾词
"""

from .base_analyzer import BaseAnalyzer
from typing import Dict, Any, List
import re

class SearchIntentAnalyzer(BaseAnalyzer):
    """搜索意图分析器类"""
    
    def __init__(self):
        """初始化搜索意图分析器"""
        super().__init__()
        
        # 定义不同意图的关键词模式
        self.intent_patterns = {
            'informational': {
                'patterns': [
                    r'\b(what is|how to|tutorial|guide|learn|understand|explain)\b',
                    r'\b(definition|meaning|introduction|basics|fundamentals)\b'
                ],
                'score': 2.0,  # 信息类意图，适合内容营销
                'description': '信息搜索意图'
            },
            'navigational': {
                'patterns': [
                    r'\b(login|sign in|download|official|website|homepage)\b',
                    r'\b(app store|google play|github|documentation)\b'
                ],
                'score': 1.5,  # 导航类意图
                'description': '导航搜索意图'
            },
            'transactional': {
                'patterns': [
                    r'\b(buy|purchase|price|cost|free|trial|subscription)\b',
                    r'\b(discount|coupon|deal|offer|sale)\b'
                ],
                'score': 3.0,  # 交易类意图，转化率最高
                'description': '交易搜索意图'
            },
            'commercial': {
                'patterns': [
                    r'\b(best|top|review|comparison|vs|alternative)\b',
                    r'\b(pros and cons|features|benefits|advantages)\b'
                ],
                'score': 2.5,  # 商业调研意图，转化率较高
                'description': '商业调研意图'
            },
            'problem_solving': {
                'patterns': [
                    r'\b(fix|solve|troubleshoot|error|problem|issue)\b',
                    r'\b(not working|broken|help|support)\b'
                ],
                'score': 2.2,  # 问题解决意图，有一定转化价值
                'description': '问题解决意图'
            },
            'local': {
                'patterns': [
                    r'\b(near me|local|nearby|in [A-Z][a-z]+)\b',
                    r'\b(address|location|directions|map)\b'
                ],
                'score': 1.8,  # 本地搜索意图
                'description': '本地搜索意图'
            }
        }
        
        # 长尾词特征模式
        self.long_tail_indicators = [
            'step by step', 'for beginners', 'complete guide', 'detailed tutorial',
            'without coding', 'easy way', 'simple method', 'quick guide',
            'beginner friendly', 'getting started', 'from scratch'
        ]
    
    def analyze(self, data, **kwargs):
        """
        实现基础分析器的抽象方法
        
        Args:
            data: 关键词数据
            **kwargs: 其他参数
            
        Returns:
            分析结果
        """
        if isinstance(data, list):
            return self.analyze_keywords_intent(data)
        elif hasattr(data, 'iterrows'):  # DataFrame
            keywords = data['query'].tolist() if 'query' in data.columns else data.iloc[:, 0].tolist()
            return self.analyze_keywords_intent(keywords)
        elif isinstance(data, dict):
            if 'query' in data:
                keywords = [data['query']] if isinstance(data['query'], str) else data['query']
            elif 'keyword' in data:
                keywords = [data['keyword']] if isinstance(data['keyword'], str) else data['keyword']
            else:
                keywords = list(data.values())[:1] if data else []
            return self.analyze_keywords_intent(keywords)
        else:
            return {}
    
    def analyze_keywords_intent(self, keywords: List[str]) -> Dict[str, Any]:
        """
        分析关键词列表的搜索意图
        
        Args:
            keywords: 关键词列表
            
        Returns:
            意图分析结果字典
        """
        results = {}
        
        for keyword in keywords:
            intent_analysis = self.analyze_single_keyword_intent(keyword)
            results[keyword] = intent_analysis
        
        # 生成整体统计
        intent_distribution = {}
        total_score = 0
        long_tail_count = 0
        
        for keyword, analysis in results.items():
            primary_intent = analysis['primary_intent']
            if primary_intent not in intent_distribution:
                intent_distribution[primary_intent] = 0
            intent_distribution[primary_intent] += 1
            
            total_score += analysis['intent_score']
            if analysis['is_long_tail']:
                long_tail_count += 1
        
        # 添加整体统计信息
        results['_summary'] = {
            'total_keywords': len(keywords),
            'intent_distribution': intent_distribution,
            'average_intent_score': total_score / len(keywords) if keywords else 0,
            'long_tail_percentage': (long_tail_count / len(keywords) * 100) if keywords else 0,
            'high_value_keywords': [
                kw for kw, analysis in results.items() 
                if isinstance(analysis, dict) and analysis.get('intent_score', 0) >= 2.5
            ]
        }
        
        return results
    
    def analyze_single_keyword_intent(self, keyword: str) -> Dict[str, Any]:
        """
        分析单个关键词的搜索意图
        
        Args:
            keyword: 关键词
            
        Returns:
            意图分析结果
        """
        keyword_lower = keyword.lower()
        word_count = len(keyword.split())
        
        # 检测各种意图
        detected_intents = []
        max_score = 0
        primary_intent = 'general'
        
        for intent_type, intent_config in self.intent_patterns.items():
            for pattern in intent_config['patterns']:
                if re.search(pattern, keyword_lower, re.IGNORECASE):
                    detected_intents.append(intent_type)
                    if intent_config['score'] > max_score:
                        max_score = intent_config['score']
                        primary_intent = intent_type
                    break
        
        # 检测长尾词特征
        is_long_tail = word_count >= 3 and len(keyword) >= 15
        has_long_tail_indicators = any(
            indicator in keyword_lower for indicator in self.long_tail_indicators
        )
        
        # 计算综合意图评分
        intent_score = max_score
        
        # 长尾词加权
        if is_long_tail:
            intent_score *= 1.3
        if has_long_tail_indicators:
            intent_score *= 1.2
        
        # 基于词数的额外加权
        if word_count >= 5:
            intent_score *= 1.4
        elif word_count >= 4:
            intent_score *= 1.2
        
        return {
            'primary_intent': primary_intent,
            'detected_intents': list(set(detected_intents)),
            'intent_score': round(intent_score, 2),
            'is_long_tail': is_long_tail,
            'has_long_tail_indicators': has_long_tail_indicators,
            'word_count': word_count,
            'intent_description': self.intent_patterns.get(primary_intent, {}).get('description', '通用意图'),
            'conversion_potential': self._assess_conversion_potential(intent_score, is_long_tail, primary_intent)
        }
    
    def _assess_conversion_potential(self, intent_score: float, is_long_tail: bool, primary_intent: str) -> str:
        """
        评估转化潜力
        
        Args:
            intent_score: 意图评分
            is_long_tail: 是否为长尾词
            primary_intent: 主要意图
            
        Returns:
            转化潜力等级
        """
        # 基础转化潜力评估
        if primary_intent == 'transactional':
            base_potential = 'high'
        elif primary_intent in ['commercial', 'problem_solving']:
            base_potential = 'medium_high'
        elif primary_intent == 'informational':
            base_potential = 'medium'
        else:
            base_potential = 'low'
        
        # 长尾词提升转化潜力
        if is_long_tail and base_potential in ['medium', 'medium_high']:
            if base_potential == 'medium':
                return 'medium_high'
            else:
                return 'high'
        
        # 高意图评分提升转化潜力
        if intent_score >= 3.0:
            return 'very_high'
        elif intent_score >= 2.5:
            return 'high' if base_potential != 'low' else 'medium_high'
        
        return base_potential
    
    def get_high_value_keywords(self, analysis_results: Dict[str, Any], min_score: float = 2.5) -> List[Dict[str, Any]]:
        """
        获取高价值关键词
        
        Args:
            analysis_results: 分析结果
            min_score: 最小意图评分
            
        Returns:
            高价值关键词列表
        """
        high_value_keywords = []
        
        for keyword, analysis in analysis_results.items():
            if isinstance(analysis, dict) and analysis.get('intent_score', 0) >= min_score:
                high_value_keywords.append({
                    'keyword': keyword,
                    'intent_score': analysis['intent_score'],
                    'primary_intent': analysis['primary_intent'],
                    'conversion_potential': analysis['conversion_potential'],
                    'is_long_tail': analysis['is_long_tail']
                })
        
        # 按意图评分排序
        high_value_keywords.sort(key=lambda x: x['intent_score'], reverse=True)
        
        return high_value_keywords


def main():
    """测试搜索意图分析器"""
    analyzer = SearchIntentAnalyzer()
    
    print("🚀 搜索意图分析器测试")
    print("=" * 50)
    
    # 测试关键词
    test_keywords = [
        'ai image generator',
        'how to use chatgpt for writing',
        'best free ai tools for small business',
        'step by step guide to machine learning',
        'buy premium ai software',
        'chatgpt vs google bard comparison',
        'troubleshooting ai model errors'
    ]
    
    # 分析意图
    results = analyzer.analyze_keywords_intent(test_keywords)
    
    print("📊 意图分析结果:")
    for keyword, analysis in results.items():
        if keyword != '_summary':
            print(f"\n🔍 关键词: {keyword}")
            print(f"  主要意图: {analysis['primary_intent']} ({analysis['intent_description']})")
            print(f"  意图评分: {analysis['intent_score']}")
            print(f"  转化潜力: {analysis['conversion_potential']}")
            print(f"  长尾词: {'是' if analysis['is_long_tail'] else '否'}")
    
    # 显示摘要
    summary = results['_summary']
    print(f"\n📈 整体统计:")
    print(f"  总关键词数: {summary['total_keywords']}")
    print(f"  平均意图评分: {summary['average_intent_score']:.2f}")
    print(f"  长尾词比例: {summary['long_tail_percentage']:.1f}%")
    print(f"  高价值关键词数: {len(summary['high_value_keywords'])}")
    
    # 获取高价值关键词
    high_value = analyzer.get_high_value_keywords(results, min_score=2.0)
    print(f"\n🏆 高价值关键词 (评分≥2.0):")
    for i, kw_data in enumerate(high_value[:5], 1):
        print(f"  {i}. {kw_data['keyword']} (评分: {kw_data['intent_score']}, 潜力: {kw_data['conversion_potential']})")
    
    print(f"\n✅ 搜索意图分析器测试完成!")


if __name__ == '__main__':
    main()