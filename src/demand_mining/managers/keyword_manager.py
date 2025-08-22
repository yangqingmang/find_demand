#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词管理器 - 负责关键词分析功能
"""

import os
import sys
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
from src.demand_mining.analyzers.intent_analyzer_v2 import IntentAnalyzerV2 as IntentAnalyzer
from src.demand_mining.analyzers.market_analyzer import MarketAnalyzer
from src.demand_mining.analyzers.keyword_analyzer import KeywordAnalyzer

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from .base_manager import BaseManager


class KeywordManager(BaseManager):
    """关键词分析管理器"""
    
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        
        # 延迟导入分析器，避免循环导入
        self._intent_analyzer = None
        self._market_analyzer = None
        self._keyword_analyzer = None
        
        print("🔍 关键词管理器初始化完成")
    
    @property
    def intent_analyzer(self):
        """延迟加载意图分析器"""
        if self._intent_analyzer is None:
            self._intent_analyzer = IntentAnalyzer()
        return self._intent_analyzer
    
    @property
    def market_analyzer(self):
        """延迟加载市场分析器"""
        if self._market_analyzer is None:
            self._market_analyzer = MarketAnalyzer()
        return self._market_analyzer
    
    @property
    def keyword_analyzer(self):
        """延迟加载关键词分析器"""
        if self._keyword_analyzer is None:
            self._keyword_analyzer = KeywordAnalyzer()
        return self._keyword_analyzer
    
    def analyze(self, input_source: str, analysis_type: str = 'file', 
                output_dir: str = None) -> Dict[str, Any]:
        """
        分析关键词
        
        Args:
            input_source: 输入源（文件路径或关键词列表）
            analysis_type: 分析类型 ('file' 或 'keywords')
            output_dir: 输出目录
            
        Returns:
            分析结果
        """
        print(f"🚀 开始关键词分析 - 类型: {analysis_type}")
        
        if analysis_type == 'file':
            return self._analyze_from_file(input_source, output_dir)
        elif analysis_type == 'keywords':
            return self._analyze_from_keywords([input_source], output_dir)
        else:
            raise ValueError(f"不支持的分析类型: {analysis_type}")
    
    def _analyze_from_file(self, file_path: str, output_dir: str = None) -> Dict[str, Any]:
        """从文件分析关键词"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"输入文件不存在: {file_path}")
        
        # 读取数据
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            raise ValueError("不支持的文件格式，请使用CSV或JSON文件")
        
        print(f"✅ 成功读取 {len(df)} 条关键词数据")
        
        # 提取关键词列表
        keywords = []
        for col in ['query', 'keyword', 'term']:
            if col in df.columns:
                keywords = df[col].dropna().tolist()
                break
        
        if not keywords:
            raise ValueError("未找到有效的关键词列")
        
        return self._perform_analysis(keywords, output_dir)
    
    def _analyze_from_keywords(self, keywords: List[str], output_dir: str = None) -> Dict[str, Any]:
        """从关键词列表分析"""
        if not keywords:
            raise ValueError("关键词列表不能为空")
        
        print(f"✅ 接收到 {len(keywords)} 个关键词")
        return self._perform_analysis(keywords, output_dir)
    
    def _perform_analysis(self, keywords: List[str], output_dir: str = None) -> Dict[str, Any]:
        """执行关键词分析"""
        results = {
            'total_keywords': len(keywords),
            'analysis_time': datetime.now().isoformat(),
            'keywords': [],
            'intent_summary': {},
            'market_insights': {},
            'recommendations': []
        }
        
        # 逐个分析关键词
        for idx, keyword in enumerate(keywords):
            print(f"🔍 分析关键词 ({idx+1}/{len(keywords)}): {keyword}")
            
            # 意图分析
            intent_result = self._analyze_keyword_intent(keyword)
            
            # 市场分析
            market_result = self._analyze_keyword_market(keyword)
            
            # 整合结果
            keyword_result = {
                'keyword': keyword,
                'intent': intent_result,
                'market': market_result,
                'opportunity_score': self._calculate_opportunity_score(intent_result, market_result)
            }
            
            results['keywords'].append(keyword_result)
        
        # 生成摘要
        results['intent_summary'] = self._generate_intent_summary(results['keywords'])
        results['market_insights'] = self._generate_market_insights(results['keywords'])
        results['recommendations'] = self._generate_recommendations(results['keywords'])
        
        # 保存结果
        if output_dir:
            output_path = self._save_analysis_results(results, output_dir)
            results['output_path'] = output_path
        
        return results
    
    def _analyze_keyword_intent(self, keyword: str) -> Dict[str, Any]:
        """分析关键词意图"""
        try:
            if self.intent_analyzer is None:
                return self._get_default_intent_result()
            
            # 创建包含关键词的DataFrame进行分析
            df = pd.DataFrame({'query': [keyword]})
            
            # 使用意图分析器进行完整分析
            result_df = self.intent_analyzer.analyze_keywords(df)
            
            if len(result_df) > 0:
                row = result_df.iloc[0]
                return {
                    'primary_intent': row.get('intent', 'Unknown'),
                    'confidence': row.get('intent_confidence', 0.0),
                    'secondary_intent': row.get('secondary_intent'),
                    'intent_description': row.get('intent_description', ''),
                    'website_recommendations': {
                        'website_type': row.get('website_type'),
                        'ai_tool_category': row.get('ai_tool_category'),
                        'domain_suggestions': row.get('domain_suggestions', []),
                        'monetization_strategy': row.get('monetization_strategy', []),
                        'technical_requirements': row.get('technical_requirements', []),
                        'competition_analysis': row.get('competition_analysis', {}),
                        'development_priority': row.get('development_priority', {}),
                        'content_strategy': row.get('content_strategy', [])
                    }
                }
            else:
                return self._get_default_intent_result()
                
        except Exception as e:
            print(f"⚠️ 意图分析失败 ({keyword}): {e}")
            return self._get_default_intent_result()
    
    def _analyze_keyword_market(self, keyword: str) -> Dict[str, Any]:
        """分析关键词市场数据"""
        try:
            # 基础市场数据（模拟，实际可接入真实API）
            base_data = {
                'search_volume': 1000,
                'competition': 0.5,
                'cpc': 2.0,
                'trend': 'stable',
                'seasonality': 'low'
            }
            
            # AI相关关键词加分
            ai_bonus = self._calculate_ai_bonus(keyword)
            
            # 商业价值评估
            commercial_value = self._assess_commercial_value(keyword)
            
            # 整合评分
            base_data.update({
                'ai_bonus': ai_bonus,
                'commercial_value': commercial_value,
                'opportunity_indicators': self._get_opportunity_indicators(keyword)
            })
            
            return base_data
            
        except Exception as e:
            print(f"⚠️ 市场分析失败 ({keyword}): {e}")
            return {
                'search_volume': 0,
                'competition': 0.0,
                'cpc': 0.0,
                'trend': 'unknown',
                'seasonality': 'unknown',
                'ai_bonus': 0,
                'commercial_value': 0,
                'opportunity_indicators': []
            }
    
    @staticmethod
    def _calculate_opportunity_score(intent_result: Dict, market_result: Dict) -> float:
        """计算综合机会分数"""
        try:
            # 基础评分权重
            weights = {
                'intent_confidence': 0.2,
                'search_volume': 0.25,
                'competition': 0.15,
                'ai_bonus': 0.2,
                'commercial_value': 0.2
            }
            
            # 各项分数计算
            intent_score = intent_result.get('confidence', 0) * 100
            volume_score = min(market_result.get('search_volume', 0) / 1000, 1) * 100
            competition_score = (1 - market_result.get('competition', 1)) * 100
            ai_bonus = market_result.get('ai_bonus', 0)
            commercial_value = market_result.get('commercial_value', 0)
            
            # 加权计算总分
            total_score = (
                intent_score * weights['intent_confidence'] +
                volume_score * weights['search_volume'] +
                competition_score * weights['competition'] +
                ai_bonus * weights['ai_bonus'] +
                commercial_value * weights['commercial_value']
            )
            
            return round(min(total_score, 100), 2)
            
        except Exception as e:
            print(f"⚠️ 机会分数计算失败: {e}")
            return 0.0
    
    @staticmethod
    def _get_default_intent_result() -> Dict[str, Any]:
        """获取默认意图分析结果"""
        return {
            'primary_intent': 'Unknown',
            'confidence': 0.0,
            'secondary_intent': None,
            'intent_description': '分析失败',
            'website_recommendations': {}
        }
    
    @staticmethod
    def _calculate_ai_bonus(keyword: str) -> float:
        """计算AI相关关键词加分"""
        keyword_lower = keyword.lower()
        ai_score = 0
        
        # AI前缀匹配
        ai_prefixes = ['ai', 'artificial intelligence', 'machine learning', 'deep learning']
        for prefix in ai_prefixes:
            if prefix in keyword_lower:
                ai_score += 20
                break
        
        # AI工具类型匹配
        ai_tool_types = ['generator', 'detector', 'writer', 'assistant', 'chatbot']
        for tool_type in ai_tool_types:
            if tool_type in keyword_lower:
                ai_score += 15
                break
        
        return min(ai_score, 50)
    
    @staticmethod
    def _assess_commercial_value(keyword: str) -> float:
        """评估商业价值"""
        keyword_lower = keyword.lower()
        commercial_score = 0
        
        # 高价值关键词类型
        high_value_types = [
            'generator', 'converter', 'editor', 'maker', 'creator',
            'optimizer', 'enhancer', 'analyzer', 'detector'
        ]
        
        for value_type in high_value_types:
            if value_type in keyword_lower:
                commercial_score += 25
                break
        
        # 付费意愿强的领域
        high_payment_domains = [
            'business', 'marketing', 'seo', 'content', 'design',
            'video', 'image', 'writing', 'coding', 'academic'
        ]
        
        for domain in high_payment_domains:
            if domain in keyword_lower:
                commercial_score += 20
                break
        
        return min(commercial_score, 50)
    
    @staticmethod
    def _get_opportunity_indicators(keyword: str) -> List[str]:
        """获取机会指标"""
        indicators = []
        keyword_lower = keyword.lower()
        
        # AI相关
        if any(prefix in keyword_lower for prefix in ['ai', 'artificial intelligence']):
            indicators.append("AI相关需求")
        
        # 工具类
        if any(tool in keyword_lower for tool in ['generator', 'converter', 'editor']):
            indicators.append("工具类需求")
        
        # 新兴概念
        if any(concept in keyword_lower for concept in ['gpt', 'chatbot', 'neural']):
            indicators.append("新兴技术")
        
        # 出海友好
        if not any(ord(char) > 127 for char in keyword):
            indicators.append("出海友好")
        
        return indicators
    
    @staticmethod
    def _generate_intent_summary(keywords: List[Dict]) -> Dict[str, Any]:
        """生成意图摘要"""
        intent_counts = {}
        total_keywords = len(keywords)
        
        for kw in keywords:
            intent = kw['intent']['primary_intent']
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        intent_percentages = {
            intent: round(count / total_keywords * 100, 1)
            for intent, count in intent_counts.items()
        }
        
        return {
            'total_keywords': total_keywords,
            'intent_distribution': intent_counts,
            'intent_percentages': intent_percentages,
            'dominant_intent': max(intent_counts.items(), key=lambda x: x[1])[0] if intent_counts else 'Unknown'
        }

    @staticmethod
    def _generate_market_insights(keywords: List[Dict]) -> Dict[str, Any]:
        """生成市场洞察"""
        high_opportunity = [kw for kw in keywords if kw['opportunity_score'] >= 70]
        medium_opportunity = [kw for kw in keywords if 40 <= kw['opportunity_score'] < 70]
        low_opportunity = [kw for kw in keywords if kw['opportunity_score'] < 40]

        return {
            'high_opportunity_count': len(high_opportunity),
            'medium_opportunity_count': len(medium_opportunity),
            'low_opportunity_count': len(low_opportunity),
            'top_opportunities': sorted(keywords, key=lambda x: x['opportunity_score'], reverse=True)[:10],
            'avg_opportunity_score': round(sum(kw['opportunity_score'] for kw in keywords) / len(keywords), 2) if keywords else 0
        }

    @staticmethod
    def _generate_recommendations(keywords: List[Dict]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 分析关键词分布
        high_opportunity = [kw for kw in keywords if kw['opportunity_score'] >= 70]
        ai_keywords = [kw for kw in keywords if kw['market'].get('ai_bonus', 0) > 0]
        
        # 高机会关键词建议
        if high_opportunity:
            recommendations.append(f"🎯 发现 {len(high_opportunity)} 个高机会关键词，建议立即开发MVP产品")
            top_3 = sorted(high_opportunity, key=lambda x: x['opportunity_score'], reverse=True)[:3]
            for i, kw in enumerate(top_3, 1):
                recommendations.append(f"   {i}. {kw['keyword']} (机会分数: {kw['opportunity_score']})")
        
        # AI相关建议
        if ai_keywords:
            recommendations.append(f"🤖 发现 {len(ai_keywords)} 个AI相关关键词，符合出海AI工具方向")
        
        return recommendations
    
    @staticmethod
    def _save_analysis_results(results: Dict[str, Any], output_dir: str) -> str:
        """保存分析结果"""
        from src.utils.file_utils import save_results_with_timestamp
        
        # 保存JSON格式
        json_path = save_results_with_timestamp(results, output_dir, 'keyword_analysis')
        
        # 保存CSV格式（关键词详情）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = os.path.join(output_dir, f'keywords_detail_{timestamp}.csv')
        keywords_df = pd.DataFrame([
            {
                'keyword': kw['keyword'],
                'primary_intent': kw['intent']['primary_intent'],
                'confidence': kw['intent']['confidence'],
                'search_volume': kw['market']['search_volume'],
                'competition': kw['market']['competition'],
                'opportunity_score': kw['opportunity_score']
            }
            for kw in results['keywords']
        ])
        keywords_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        return json_path