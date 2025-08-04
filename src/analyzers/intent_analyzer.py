#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索意图分析工具 - Intent Analyzer
用于判断关键词的搜索意图类型
"""

import pandas as pd
import numpy as np
import os
import argparse
import re
import json
import requests
import time
from datetime import datetime
from collections import Counter

from src.analyzers.serp_analyzer import SerpAnalyzer
from src.utils import (
    INTENT_TYPES, INTENT_KEYWORDS, RECOMMENDED_ACTIONS,
    FileUtils, Logger, ExceptionHandler, DataError
)

class IntentAnalyzer:
    """搜索意图分析类，用于判断关键词的搜索意图"""
    
    def __init__(self, use_serp=False):
        """初始化搜索意图分析器"""
        self.use_serp = use_serp
        self.logger = Logger()
        
        # 如果启用SERP分析，初始化SERP分析器
        if self.use_serp:
            try:
                self.serp_analyzer = SerpAnalyzer()
                self.logger.info("已启用SERP分析功能")
            except Exception as e:
                self.logger.error(f"SERP分析器初始化失败: {e}")
                self.logger.info("将使用基于关键词的分析方法")
                self.use_serp = False
                self.serp_analyzer = None
        else:
            self.serp_analyzer = None
        
        # 正则表达式模式
        self.patterns = {
            intent: re.compile(r'\b(' + '|'.join(words) + r')\b', re.IGNORECASE) 
            for intent, words in INTENT_KEYWORDS.items()
        }
    
    def detect_intent_from_keyword(self, keyword):
        """
        从关键词文本判断搜索意图
        
        参数:
            keyword (str): 关键词文本
            
        返回:
            tuple: (主要意图, 置信度, 次要意图)
        """
        scores = {intent: 0 for intent in self.INTENT_TYPES.keys()}
        
        # 计算每种意图的匹配分数
        for intent, pattern in self.patterns.items():
            matches = pattern.findall(keyword.lower())
            scores[intent] = len(matches)
        
        # 如果没有匹配，默认为信息型
        if sum(scores.values()) == 0:
            return ('I', 0.5, None)
        
        # 找出主要意图和次要意图
        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_intent, primary_score = sorted_intents[0]
        
        # 计算置信度 (0.5-1.0)
        total_score = sum(scores.values())
        confidence = 0.5 + 0.5 * (primary_score / total_score) if total_score > 0 else 0.5
        
        # 次要意图
        secondary_intent = sorted_intents[1][0] if len(sorted_intents) > 1 and sorted_intents[1][1] > 0 else None
        
        return (primary_intent, confidence, secondary_intent)
    
    def detect_intent_from_serp(self, keyword):
        """
        从SERP数据判断搜索意图（真实实现）
        
        参数:
            keyword (str): 关键词
            
        返回:
            tuple: (主要意图, 置信度, 次要意图)
        """
        if not self.use_serp or not self.serp_analyzer:
            # 如果未启用SERP分析，返回默认值
            return ('I', 0.5, None)
        
        try:
            # 使用SERP分析器分析关键词
            result = self.serp_analyzer.analyze_keyword_serp(keyword)
            
            if 'error' in result:
                print(f"SERP分析失败: {result['error']}")
                return ('I', 0.5, None)
            
            return (result['intent'], result['confidence'], result['secondary_intent'])
            
        except Exception as e:
            print(f"SERP分析出错: {e}")
            return ('I', 0.5, None)
    
    def analyze_keywords(self, df, keyword_col='query'):
        """
        分析DataFrame中的关键词意图
        
        参数:
            df (DataFrame): 关键词数据
            keyword_col (str): 关键词列名
            
        返回:
            添加了意图分析结果的DataFrame
        """
        if df.empty:
            print("警告: 输入数据为空")
            return df
            
        if keyword_col not in df.columns:
            print(f"错误: 未找到关键词列 '{keyword_col}'")
            return df
            
        # 创建副本避免修改原始数据
        result_df = df.copy()
        
        # 添加意图分析结果
        result_df['intent'] = ''
        result_df['intent_confidence'] = 0.0
        result_df['secondary_intent'] = ''
        result_df['intent_description'] = ''
        result_df['recommended_action'] = ''
        
        # 分析每个关键词
        for idx, row in result_df.iterrows():
            keyword = str(row[keyword_col])
            
            # 选择分析方法
            if self.use_serp:
                # 使用SERP分析
                print(f"正在分析关键词 ({idx+1}/{len(result_df)}): {keyword}")
                intent, confidence, secondary = self.detect_intent_from_serp(keyword)
                
                # 如果SERP分析失败，回退到关键词分析
                if confidence <= 0.5:
                    keyword_intent, keyword_confidence, keyword_secondary = self.detect_intent_from_keyword(keyword)
                    if keyword_confidence > confidence:
                        intent, confidence, secondary = keyword_intent, keyword_confidence, keyword_secondary
            else:
                # 仅使用关键词文本分析
                intent, confidence, secondary = self.detect_intent_from_keyword(keyword)
            
            # 更新DataFrame
            result_df.at[idx, 'intent'] = intent
            result_df.at[idx, 'intent_confidence'] = round(confidence, 2)
            result_df.at[idx, 'secondary_intent'] = secondary if secondary else ''
            result_df.at[idx, 'intent_description'] = self.INTENT_TYPES[intent]
            result_df.at[idx, 'recommended_action'] = self.get_recommended_action(intent)
        
        return result_df
    
    def get_recommended_action(self, intent):
        """
        根据意图获取推荐行动
        
        参数:
            intent (str): 意图代码
            
        返回:
            str: 推荐行动
        """
        from src.utils import get_recommended_action
        return get_recommended_action(intent)
    
    def generate_intent_summary(self, df):
        """
        生成意图分析摘要
        
        参数:
            df (DataFrame): 带有意图分析结果的DataFrame
            
        返回:
            dict: 意图分析摘要
        """
        if 'intent' not in df.columns:
            return {'error': '数据中没有意图分析结果'}
            
        # 统计各种意图的数量
        intent_counts = df['intent'].value_counts().to_dict()
        
        # 计算百分比
        total = sum(intent_counts.values())
        intent_percentages = {intent: round(count / total * 100, 1) for intent, count in intent_counts.items()}
        
        # 按意图分组的关键词
        intent_keywords = {}
        for intent in self.INTENT_TYPES.keys():
            if intent in intent_counts:
                intent_keywords[intent] = df[df['intent'] == intent]['query'].tolist()
        
        # 高置信度关键词
        high_confidence = df[df['intent_confidence'] >= 0.7]['query'].tolist()
        
        return {
            'total_keywords': total,
            'intent_counts': intent_counts,
            'intent_percentages': intent_percentages,
            'intent_keywords': intent_keywords,
            'high_confidence_keywords': high_confidence,
            'intent_descriptions': self.INTENT_TYPES
        }
    
    def save_results(self, df, summary, output_dir='data', prefix='intent'):
        """
        保存意图分析结果
        
        参数:
            df (DataFrame): 带有意图分析结果的DataFrame
            summary (dict): 意图分析摘要
            output_dir (str): 输出目录
            prefix (str): 文件名前缀
        """
        # 保存主要结果和摘要
        saved_files = FileUtils.save_analysis_results(df, summary, output_dir, prefix)
        self.logger.info(f"已保存意图分析结果到: {saved_files['main_results']}")
        self.logger.info(f"已保存意图分析摘要到: {saved_files['summary']}")
        
        # 按意图分组保存
        for intent, keywords in summary['intent_keywords'].items():
            if keywords:
                intent_df = df[df['intent'] == intent]
                intent_filename = FileUtils.generate_filename(f'{prefix}_{intent}', extension='csv')
                intent_path = FileUtils.save_dataframe(intent_df, output_dir, intent_filename)
                intent_name = INTENT_TYPES.get(intent, intent)
                self.logger.info(f"已保存 {intent} ({intent_name}) 意图关键词到: {intent_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='搜索意图分析工具')
    parser.add_argument('--input', required=True, help='输入CSV文件路径')
    parser.add_argument('--output', default='data', help='输出目录，默认为data')
    parser.add_argument('--keyword-col', default='query', help='关键词列名，默认为query')
    parser.add_argument('--use-serp', action='store_true', help='启用SERP分析（需要Google API配置）')
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入文件 '{args.input}' 不存在")
        return
    
    # 读取输入文件
    try:
        df = pd.read_csv(args.input)
        print(f"已读取 {len(df)} 条关键词数据")
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return
    
    # 创建意图分析器
    analyzer = IntentAnalyzer(use_serp=args.use_serp)
    
    if args.use_serp:
        print("注意: 启用SERP分析将消耗Google API配额，请确保已正确配置API密钥")
        print("分析过程可能需要较长时间，请耐心等待...")
    
    # 分析关键词意图
    result_df = analyzer.analyze_keywords(df, args.keyword_col)
    
    # 生成摘要
    summary = analyzer.generate_intent_summary(result_df)
    
    # 保存结果
    analyzer.save_results(result_df, summary, args.output)
    
    # 打印简要统计
    print("\n意图分布:")
    for intent, count in summary['intent_counts'].items():
        percentage = summary['intent_percentages'][intent]
        print(f"  {intent} ({analyzer.INTENT_TYPES[intent]}): {count} 个关键词 ({percentage}%)")
    
    if args.use_serp:
        print(f"\n已完成SERP增强的意图分析，结果保存到: {args.output}")


if __name__ == "__main__":
    main()