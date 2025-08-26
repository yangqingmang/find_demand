#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
搜索意图分析工具 V2 - 精简版
基于规则的搜索意图分析，使用6主意图×24子意图的分类体系
"""

import csv
import json
import os
import re
import yaml
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional, Any
from collections import defaultdict

from .base_analyzer import BaseAnalyzer
try:
    from src.utils import Logger, FileUtils
except ImportError:
    class Logger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    class FileUtils:
        @staticmethod
        def generate_filename(prefix, extension='csv'):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"{prefix}_{timestamp}.{extension}"


class IntentAnalyzerV2(BaseAnalyzer):
    """搜索意图分析器V2，基于规则判断关键词意图"""

    # 意图配置
    MAIN_INTENTS = ['I', 'N', 'C', 'E', 'B', 'L']
    SUB_INTENTS = {
        'I': ['I1', 'I2', 'I3', 'I4'], 'N': ['N1', 'N2', 'N3'],
        'C': ['C1', 'C2', 'C3'], 'E': ['E1', 'E2', 'E3'],
        'B': ['B1', 'B2', 'B3'], 'L': ['L1', 'L2', 'L3']
    }
    
    INTENT_DESCRIPTIONS = {
        'I': '信息获取', 'N': '导航直达', 'C': '商业评估', 'E': '交易购买', 'B': '行为后续', 'L': '本地/到店',
        'I1': '定义/概念', 'I2': '原理/源码', 'I3': '教程/步骤', 'I4': '事实求证',
        'N1': '官方主页', 'N2': '登录/控制台', 'N3': '下载/安装包',
        'C1': '榜单/推荐', 'C2': '对比/评测', 'C3': '口碑/点评',
        'E1': '价格/报价', 'E2': '优惠/折扣', 'E3': '下单/预订',
        'B1': '故障/报错', 'B2': '高级用法', 'B3': '配置/设置',
        'L1': '附近门店', 'L2': '预约/路线', 'L3': '开放时间'
    }

    def __init__(self, keywords_dict_path: str = None, serp_rules_path: str = None):
        super().__init__()
        self.keywords_dict = self._load_config(keywords_dict_path, 'keywords_dict')
        self.serp_rules = self._load_config(serp_rules_path, 'serp_rules')
        self.pending_review = set()

    def _load_config(self, file_path: str, config_type: str) -> Dict:
        """加载配置文件"""
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                self.logger.error(f"加载{config_type}失败: {e}")
        
        # 返回默认配置
        if config_type == 'keywords_dict':
            return self._get_default_keywords()
        else:
            return self._get_default_serp_rules()

    def _get_default_keywords(self) -> Dict[str, List[str]]:
        """默认关键词字典"""
        return {
            'I1': ['what is', '是什么', '定义'], 'I2': ['原理', '源码', 'algorithm'],
            'I3': ['how to', '教程', '步骤'], 'I4': ['是否', '好吗', 'true or false'],
            'N1': ['官网', 'official site'], 'N2': ['login', '登陆', '控制台'],
            'N3': ['download', '下载', 'installer'], 'C1': ['best', '推荐', 'top'],
            'C2': ['vs', '对比', 'compare'], 'C3': ['review', '点评', '评价'],
            'E1': ['price', '价格', '多少钱'], 'E2': ['coupon', '优惠', '折扣'],
            'E3': ['buy', '购买', 'order'], 'B1': ['error', '报错', 'fix'],
            'B2': ['advanced', '高级', '进阶'], 'B3': ['config', '配置', '设置'],
            'L1': ['near me', '附近', '周边'], 'L2': ['route', '路线', '预约'],
            'L3': ['opening hours', '营业时间']
        }

    def _get_default_serp_rules(self) -> Dict[str, Dict[str, float]]:
        """默认SERP规则"""
        return {
            'shopping_ads': {'E': 0.8}, 'price_snippet': {'E1': 0.6},
            'official_site': {'N1': 0.8}, 'video_block': {'I3': 0.4},
            'map_pack': {'L': 1.0}, 'stackoverflow': {'B1': 0.8}
        }

    def preprocess_query(self, query: str) -> str:
        """预处理查询关键词"""
        query = query.lower()
        query = re.sub(r'[^\w\s]', ' ', query)
        return re.sub(r'\s+', ' ', query).strip()

    def detect_intent(self, query: str, serp_signals: Dict[str, bool] = None) -> Dict[str, Any]:
        """检测单个关键词的意图"""
        processed_query = self.preprocess_query(query)
        intent_scores = defaultdict(float)
        sub_intent_scores = defaultdict(float)
        signals_hit = []
        
        # 词面分析
        for intent, keywords in self.keywords_dict.items():
            for keyword in keywords:
                if keyword in processed_query:
                    signals_hit.append(f"词面:{keyword}")
                    sub_intent_scores[intent] += 1
                    main_intent = intent[0]
                    intent_scores[main_intent] += 0.6
        
        # SERP分析
        if serp_signals:
            for signal, present in serp_signals.items():
                if present and signal in self.serp_rules:
                    signals_hit.append(f"SERP:{signal}")
                    for intent, score in self.serp_rules[signal].items():
                        if len(intent) == 1:
                            intent_scores[intent] += score
                        else:
                            sub_intent_scores[intent] += score
        
        # 处理无匹配情况
        if not intent_scores and not sub_intent_scores:
            self.pending_review.add(query)
            return self._default_result(query, signals_hit)
        
        # 计算概率
        total_score = sum(intent_scores.values())
        if total_score == 0:
            return self._default_result(query, signals_hit)
        
        intent_probs = {intent: score / total_score for intent, score in intent_scores.items()}
        sorted_intents = sorted(intent_probs.items(), key=lambda x: x[1], reverse=True)
        
        # 获取主次意图
        intent_primary = sorted_intents[0][0] if sorted_intents else ''
        probability = sorted_intents[0][1] if sorted_intents else 0
        
        intent_secondary = ''
        probability_secondary = 0
        if len(sorted_intents) > 1 and sorted_intents[1][1] >= 0.2:
            intent_secondary = sorted_intents[1][0]
            probability_secondary = sorted_intents[1][1]
        
        # 确定子意图
        sub_intent = ''
        if intent_primary:
            possible_sub_intents = [si for si in sub_intent_scores.keys() if si.startswith(intent_primary)]
            if possible_sub_intents:
                sub_intent = max(possible_sub_intents, key=lambda si: sub_intent_scores[si])
        
        return {
            'query': query, 'intent_primary': intent_primary, 'intent_secondary': intent_secondary,
            'sub_intent': sub_intent, 'probability': round(probability, 2),
            'probability_secondary': round(probability_secondary, 2), 'signals_hit': signals_hit
        }

    def _default_result(self, query: str, signals_hit: List[str]) -> Dict[str, Any]:
        """返回默认结果"""
        return {
            'query': query, 'intent_primary': 'I', 'intent_secondary': '',
            'sub_intent': 'I1', 'probability': 0.5, 'probability_secondary': 0,
            'signals_hit': signals_hit + ['默认:信息获取意图']
        }

    def analyze(self, data, keyword_col='query', **kwargs):
        """实现基础分析器的抽象方法"""
        return self.analyze_keywords(data, keyword_col)

    def analyze_keywords(self, data, query_col='query') -> Dict[str, Any]:
        """分析关键词列表"""
        # 处理不同类型的输入数据
        if isinstance(data, list):
            # 如果是列表，转换为字典列表
            keywords = [{'query': kw} for kw in data]
            self.log_analysis_start("搜索意图V2", f"，共 {len(keywords)} 个关键词")
        elif hasattr(data, 'iterrows'):
            # 如果是DataFrame
            keywords = []
            for idx, row in data.iterrows():
                keywords.append({'query': str(row[query_col])})
            self.log_analysis_start("搜索意图V2", f"，共 {len(keywords)} 个关键词")
        elif isinstance(data, dict):
            # 如果是单个字典
            if query_col in data:
                keywords = [{'query': str(data[query_col])}]
            else:
                # 尝试获取第一个值作为关键词
                first_value = list(data.values())[0] if data else ""
                keywords = [{'query': str(first_value)}]
            self.log_analysis_start("搜索意图V2", f"，共 {len(keywords)} 个关键词")
        else:
            # 其他情况，返回空结果
            return {'results': [], 'summary': {}, 'dataframe': None}
        
        results = []
        intent_counts = defaultdict(int)
        intent_keywords = defaultdict(list)
        
        for kw_data in keywords:
            query = kw_data['query']
            intent_result = self.detect_intent(query)
            results.append(intent_result)
            
            if intent_result['intent_primary']:
                intent_counts[intent_result['intent_primary']] += 1
                intent_keywords[intent_result['intent_primary']].append(query)
        
        # 生成摘要
        total_keywords = len(results)
        intent_percentages = {
            intent: (count / total_keywords * 100) if total_keywords > 0 else 0
            for intent, count in intent_counts.items()
        }
        
        summary = {
            'total_keywords': total_keywords,
            'intent_counts': dict(intent_counts),
            'intent_percentages': {k: round(v, 1) for k, v in intent_percentages.items()},
            'intent_keywords': dict(intent_keywords),
            'recommendations': self.get_recommendations(),
            'intent_descriptions': self.INTENT_DESCRIPTIONS
        }
        
        # 创建结果DataFrame
        import pandas as pd
        result_df = pd.DataFrame(results)
        
        if not result_df.empty:
            result_df['intent_description'] = result_df['intent_primary'].map(
                lambda x: self.INTENT_DESCRIPTIONS.get(x, '') if x else ''
            )
            result_df['recommended_action'] = result_df['intent_primary'].map(
                lambda x: self.get_recommendations().get(x, '') if x else ''
            )
        
        return {'results': results, 'summary': summary, 'dataframe': result_df}

    def get_recommendations(self) -> Dict[str, str]:
        """获取各意图的行动建议"""
        return {
            'I': '创建入门指南和教程内容', 'N': '优化网站导航和登录页面',
            'C': '创建对比页和评测内容', 'E': '优化购买流程和促销活动',
            'B': '提供故障排查和高级教程', 'L': '优化本地搜索和地图展示'
        }

    def save_results(self, analysis_results: Dict[str, Any], output_dir: str) -> Dict[str, str]:
        """保存分析结果"""
        os.makedirs(output_dir, exist_ok=True)
        today = datetime.now().strftime('%Y-%m-%d')
        saved_files = {}
        
        # 保存完整结果
        results_file = os.path.join(output_dir, f'intent_{today}.csv')
        with open(results_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'query', 'intent_primary', 'intent_secondary', 'sub_intent',
                'probability', 'probability_secondary', 'signals_hit'
            ])
            writer.writeheader()
            for result in analysis_results['results']:
                result_copy = result.copy()
                result_copy['signals_hit'] = ', '.join(result_copy['signals_hit'])
                writer.writerow(result_copy)
        
        saved_files['完整结果'] = results_file
        
        # 保存摘要
        summary_file = os.path.join(output_dir, f'intent_summary_{today}.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results['summary'], f, ensure_ascii=False, indent=2)
        
        saved_files['意图摘要'] = summary_file
        
        # 保存未命中关键词
        if self.pending_review:
            pending_file = os.path.join(output_dir, f'pending_review_{today}.txt')
            with open(pending_file, 'w', encoding='utf-8') as f:
                for query in sorted(self.pending_review):
                    f.write(f"{query}\n")
            saved_files['待审核关键词'] = pending_file
        
        return saved_files

    def detect_intent_from_keyword(self, keyword: str) -> Tuple[str, float, Optional[str]]:
        """简化的意图检测方法"""
        result = self.detect_intent(keyword)
        return (
            result['intent_primary'],
            result['probability'],
            result['intent_secondary'] if result['intent_secondary'] else None
        )


def analyze_single_keyword(keyword, keywords_dict_path=None, serp_rules_path=None):
    """分析单个关键词的意图"""
    analyzer = IntentAnalyzerV2(keywords_dict_path, serp_rules_path)
    import pandas as pd
    df = pd.DataFrame([{'query': keyword}])
    analysis_results = analyzer.analyze_keywords(df, query_col='query')
    
    return analysis_results['results'][0] if analysis_results['results'] else {
        'query': keyword, 'intent_primary': '', 'intent_secondary': '',
        'sub_intent': '', 'probability': 0, 'probability_secondary': 0, 'signals_hit': []
    }