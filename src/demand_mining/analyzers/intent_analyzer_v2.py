#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
搜索意图分析工具 V2
基于规则的搜索意图分析，无需机器学习模型
使用6主意图×24子意图的分类体系
"""

import csv
import json
import os
import re
import sys
import yaml
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional, Any, Union
from collections import defaultdict

from .base_analyzer import BaseAnalyzer
try:
    from src.utils import Logger, FileUtils
except ImportError:
    # 如果无法导入utils，使用简化版本
    class Logger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    class FileUtils:
        @staticmethod
        def generate_filename(prefix, extension='csv'):
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"{prefix}_{timestamp}.{extension}"


class IntentAnalyzerV2(BaseAnalyzer):
    """搜索意图分析器V2，基于规则判断关键词意图"""

    # 主意图列表
    MAIN_INTENTS = ['I', 'N', 'C', 'E', 'B', 'L']
    
    # 子意图映射
    SUB_INTENTS = {
        'I': ['I1', 'I2', 'I3', 'I4'],
        'N': ['N1', 'N2', 'N3'],
        'C': ['C1', 'C2', 'C3'],
        'E': ['E1', 'E2', 'E3'],
        'B': ['B1', 'B2', 'B3'],
        'L': ['L1', 'L2', 'L3']
    }
    
    # 意图说明
    INTENT_DESCRIPTIONS = {
        'I': '信息获取',
        'N': '导航直达',
        'C': '商业评估',
        'E': '交易购买',
        'B': '行为后续',
        'L': '本地/到店',
        'I1': '定义/概念',
        'I2': '原理/源码',
        'I3': '教程/步骤',
        'I4': '事实求证',
        'N1': '官方主页',
        'N2': '登录/控制台',
        'N3': '下载/安装包',
        'C1': '榜单/推荐',
        'C2': '对比/评测',
        'C3': '口碑/点评',
        'E1': '价格/报价',
        'E2': '优惠/折扣',
        'E3': '下单/预订',
        'B1': '故障/报错',
        'B2': '高级用法',
        'B3': '配置/设置',
        'L1': '附近门店',
        'L2': '预约/路线',
        'L3': '开放时间'
    }

    def __init__(self, keywords_dict_path: str = None, serp_rules_path: str = None):
        """
        初始化意图分析器
        
        Args:
            keywords_dict_path: 关键词字典YAML文件路径
            serp_rules_path: SERP规则YAML文件路径
        """
        super().__init__()
        
        # 加载关键词字典
        self.keywords_dict = self._load_yaml(keywords_dict_path) if keywords_dict_path else self._get_default_keywords()
        
        # 加载SERP规则
        self.serp_rules = self._load_yaml(serp_rules_path) if serp_rules_path else self._get_default_serp_rules()
        
        # 未命中关键词记录
        self.pending_review = set()

    def _load_yaml(self, file_path: str) -> Dict:
        """加载YAML文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"加载YAML文件失败: {e}")
            return {}

    def _get_default_keywords(self) -> Dict[str, List[str]]:
        """获取默认关键词字典"""
        return {
            'I1': ['what is', 'definition', 'mean', '意味', '是什么', '定义'],
            'I2': ['architecture', 'algorithm', '原理', '源码', 'protocol'],
            'I3': ['how to', 'tutorial', 'step by step', '教程', '方法', '步骤'],
            'I4': ['is ... good', 'true or false', '是否', '好吗', '真假'],
            'N1': ['official site', '官网', 'home page', '官方网站'],
            'N2': ['login', 'signin', '控制台', '后台', '登陆'],
            'N3': ['download', 'installer', 'setup.exe', '离线包', 'dmg'],
            'C1': ['best', 'top 10', '推荐', '排行', '榜单', 'tool', 'tools'],
            'C2': ['vs', 'versus', 'compare', '对比'],
            'C3': ['review', 'rating', '点评', '评价'],
            'E1': ['price', 'cost', '多少钱', '价格', 'quote'],
            'E2': ['coupon', 'discount', 'promo', '优惠', '折扣'],
            'E3': ['buy', 'purchase', 'order', '下单', '预订'],
            'B1': ['error', 'fix', 'troubleshoot', '报错', '解决'],
            'B2': ['advanced', 'pro tips', '高级', '进阶'],
            'B3': ['config', 'setting', '配置', '设置'],
            'L1': ['near me', '附近', '周边', '哪里有'],
            'L2': ['route', 'directions', '路线', '怎么去', '预约'],
            'L3': ['opening hours', '营业时间', '几点关门'],
            'I': ['information', 'info', 'guide', 'learn', '学习', '指南'],
            'N': ['website', 'site', 'app', 'platform', '网站', '应用'],
            'C': ['tool', 'tools', 'software', '工具', '软件'],
            'E': ['buy', 'purchase', '购买'],
            'B': ['help', 'support', '帮助', '支持'],
            'L': ['location', 'store', '位置', '商店']
        }

    def _get_default_serp_rules(self) -> Dict[str, Dict[str, float]]:
        """获取默认SERP规则"""
        return {
            'shopping_ads': {'E': 0.8, 'E3': 0.5},
            'price_snippet': {'E': 0.6, 'E1': 0.4},
            'official_site': {'N': 0.8, 'N1': 0.6},
            'video_block': {'I': 0.4, 'I3': 0.3},
            'top_stories': {'I': 0.3},
            'map_pack': {'L': 1.0, 'L1': 0.6},
            'stackoverflow': {'B': 0.8, 'B1': 0.6}
        }

    def preprocess_query(self, query: str) -> str:
        """
        预处理查询关键词
        
        Args:
            query: 原始查询关键词
            
        Returns:
            处理后的关键词
        """
        # 转小写
        query = query.lower()
        
        # 全角转半角
        query = self._full_to_half(query)
        
        # 去除特殊符号
        query = re.sub(r'[^\w\s]', ' ', query)
        
        # 去除多余空格
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query

    def _full_to_half(self, text: str) -> str:
        """全角字符转半角字符"""
        result = ""
        for char in text:
            code = ord(char)
            if code == 0x3000:  # 全角空格
                result += ' '
            elif 0xFF01 <= code <= 0xFF5E:  # 全角字符
                result += chr(code - 0xFEE0)
            else:
                result += char
        return result

    def detect_intent(self, query: str, serp_signals: Dict[str, bool] = None) -> Dict[str, Any]:
        """
        检测单个关键词的意图
        
        Args:
            query: 查询关键词
            serp_signals: SERP信号，如{'shopping_ads': True, 'price_snippet': False, ...}
            
        Returns:
            意图分析结果字典
        """
        # 预处理查询
        processed_query = self.preprocess_query(query)
        
        # 初始化分数
        intent_scores = defaultdict(float)
        sub_intent_scores = defaultdict(float)
        signals_hit = []
        
        # 词面分析
        for intent, keywords in self.keywords_dict.items():
            for keyword in keywords:
                if keyword in processed_query:
                    # 记录命中信号
                    signals_hit.append(f"词面:{keyword}")
                    
                    # 子意图得分
                    sub_intent_scores[intent] += 1
                    
                    # 主意图得分
                    main_intent = intent[0]  # 取第一个字符作为主意图
                    intent_scores[main_intent] += 0.6  # 主意图得分权重为0.6
        
        # SERP分析
        if serp_signals:
            for signal, present in serp_signals.items():
                if present and signal in self.serp_rules:
                    # 记录命中信号
                    signals_hit.append(f"SERP:{signal}")
                    
                    # 添加SERP规则分数
                    for intent, score in self.serp_rules[signal].items():
                        if len(intent) == 1:  # 主意图
                            intent_scores[intent] += score
                        else:  # 子意图
                            sub_intent_scores[intent] += score
        
        # 如果没有任何得分，记录到待审核列表并提供默认意图
        if not intent_scores and not sub_intent_scores:
            self.pending_review.add(query)
            # 提供默认的信息型意图
            return {
                'query': query,
                'intent_primary': 'I',
                'intent_secondary': '',
                'sub_intent': 'I1',
                'probability': 0.5,
                'probability_secondary': 0,
                'signals_hit': ['默认:信息获取意图']
            }
        
        # 计算总分
        total_score = sum(intent_scores.values())
        
        # 如果总分为0，提供默认意图
        if total_score == 0:
            return {
                'query': query,
                'intent_primary': 'I',
                'intent_secondary': '',
                'sub_intent': 'I1',
                'probability': 0.5,
                'probability_secondary': 0,
                'signals_hit': signals_hit + ['默认:信息获取意图']
            }
        
        # 归一化为概率
        intent_probs = {intent: score / total_score for intent, score in intent_scores.items()}
        
        # 按概率排序
        sorted_intents = sorted(intent_probs.items(), key=lambda x: x[1], reverse=True)
        
        # 获取主意图和次意图
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
            # 获取该主意图下的所有子意图
            possible_sub_intents = [si for si in sub_intent_scores.keys() if si.startswith(intent_primary)]
            
            # 如果有子意图得分，选择得分最高的
            if possible_sub_intents:
                sub_intent = max(possible_sub_intents, key=lambda si: sub_intent_scores[si])
        
        return {
            'query': query,
            'intent_primary': intent_primary,
            'intent_secondary': intent_secondary,
            'sub_intent': sub_intent,
            'probability': round(probability, 2),
            'probability_secondary': round(probability_secondary, 2),
            'signals_hit': signals_hit
        }

    def analyze(self, data, keyword_col='query', **kwargs):
        """
        实现基础分析器的抽象方法
        
        Args:
            data: 关键词数据DataFrame
            keyword_col: 关键词列名
            **kwargs: 其他参数
            
        Returns:
            添加了意图分析结果的DataFrame
        """
        return self.analyze_keywords(data, keyword_col)

    def analyze_keywords(self, df, query_col='query') -> Dict[str, Any]:
        """
        分析关键词列表
        
        Args:
            df: 包含关键词的DataFrame
            query_col: 关键词列名
            
        Returns:
            分析结果字典
        """
        self.log_analysis_start("搜索意图V2", f"，共 {len(df)} 个关键词")
        
        results = []
        intent_counts = defaultdict(int)
        intent_keywords = defaultdict(list)
        
        for idx, row in df.iterrows():
            query = str(row[query_col])
            
            # 分析意图
            intent_result = self.detect_intent(query)
            
            # 添加到结果列表
            results.append(intent_result)
            
            # 统计意图数量
            if intent_result['intent_primary']:
                intent_counts[intent_result['intent_primary']] += 1
                intent_keywords[intent_result['intent_primary']].append(query)
        
        # 计算意图百分比
        total_keywords = len(results)
        intent_percentages = {
            intent: (count / total_keywords * 100) if total_keywords > 0 else 0
            for intent, count in intent_counts.items()
        }
        
        # 生成意图摘要
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
        
        # 添加意图描述和推荐行动
        if not result_df.empty:
            result_df['intent_description'] = result_df['intent_primary'].map(
                lambda x: self.INTENT_DESCRIPTIONS.get(x, '') if x else ''
            )
            result_df['recommended_action'] = result_df['intent_primary'].map(
                lambda x: self.get_recommendations().get(x, '') if x else ''
            )
        
        return {
            'results': results,
            'summary': summary,
            'dataframe': result_df
        }

    def get_recommendations(self) -> Dict[str, str]:
        """获取各意图的行动建议"""
        return {
            'I': '创建入门指南和教程内容',
            'N': '优化网站导航和登录页面',
            'C': '创建对比页和评测内容',
            'E': '优化购买流程和促销活动',
            'B': '提供故障排查和高级教程',
            'L': '优化本地搜索和地图展示'
        }

    def save_pending_review(self, output_dir: str) -> None:
        """保存未命中关键词到待审核文件"""
        if not self.pending_review:
            return
            
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名
        today = datetime.now().strftime('%Y-%m-%d')
        file_path = os.path.join(output_dir, f'pending_review_{today}.txt')
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            for query in sorted(self.pending_review):
                f.write(f"{query}\n")
        
        self.logger.info(f"已将{len(self.pending_review)}个未命中关键词保存到 {file_path}")

    def save_results(self, analysis_results: Dict[str, Any], output_dir: str) -> Dict[str, str]:
        """
        保存分析结果
        
        Args:
            analysis_results: 分析结果
            output_dir: 输出目录
            
        Returns:
            保存的文件路径字典
        """
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名
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
                # 将signals_hit列表转换为字符串
                result_copy = result.copy()
                result_copy['signals_hit'] = ', '.join(result_copy['signals_hit'])
                writer.writerow(result_copy)
        
        saved_files['完整结果'] = results_file
        self.logger.info(f"已保存完整结果到: {results_file}")
        
        # 保存摘要
        summary_file = os.path.join(output_dir, f'intent_summary_{today}.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results['summary'], f, ensure_ascii=False, indent=2)
        
        saved_files['意图摘要'] = summary_file
        self.logger.info(f"已保存意图摘要到: {summary_file}")
        
        # 按意图分类保存
        for intent in self.MAIN_INTENTS:
            intent_keywords = analysis_results['summary']['intent_keywords'].get(intent, [])
            if intent_keywords:
                intent_file = os.path.join(output_dir, f'intent_{intent}_{today}.csv')
                with open(intent_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['query'])
                    for keyword in intent_keywords:
                        writer.writerow([keyword])
                
                saved_files[f'{intent}意图关键词'] = intent_file
                self.logger.info(f"已保存{intent}意图关键词到: {intent_file}")
        
        # 保存未命中关键词
        self.save_pending_review(output_dir)
        
        return saved_files

    def detect_intent_from_keyword(self, keyword: str) -> Tuple[str, float, Optional[str]]:
        """
        简化的意图检测方法，用于主程序调用
        
        Args:
            keyword: 关键词
            
        Returns:
            (主意图, 置信度, 次意图)
        """
        result = self.detect_intent(keyword)
        return (
            result['intent_primary'],
            result['probability'],
            result['intent_secondary'] if result['intent_secondary'] else None
        )


def analyze_single_keyword(keyword, keywords_dict_path=None, serp_rules_path=None):
    """
    分析单个关键词的意图
    
    Args:
        keyword: 要分析的关键词
        keywords_dict_path: 关键词字典YAML文件路径
        serp_rules_path: SERP规则YAML文件路径
        
    Returns:
        意图分析结果字典
    """
    # 初始化分析器
    analyzer = IntentAnalyzerV2(
        keywords_dict_path=keywords_dict_path,
        serp_rules_path=serp_rules_path
    )
    
    # 创建包含单个关键词的DataFrame
    import pandas as pd
    df = pd.DataFrame([{'query': keyword}])
    
    # 分析关键词
    analysis_results = analyzer.analyze_keywords(df, query_col='query')
    
    # 返回第一个结果
    if analysis_results['results']:
        return analysis_results['results'][0]
    else:
        return {
            'query': keyword,
            'intent_primary': '',
            'intent_secondary': '',
            'sub_intent': '',
            'probability': 0,
            'probability_secondary': 0,
            'signals_hit': []
        }