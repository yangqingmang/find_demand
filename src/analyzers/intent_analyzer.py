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

class IntentAnalyzer:
    """搜索意图分析类，用于判断关键词的搜索意图"""
    
    # 意图类型定义
    INTENT_TYPES = {
        'I': 'Informational', # 信息型
        'N': 'Navigational',  # 导航型
        'C': 'Commercial',    # 商业型
        'E': 'Transactional', # 交易型
        'B': 'Behavioral'     # 行为型
    }
    
    def __init__(self):
        """初始化搜索意图分析器"""
        # 意图关键词词典
        self.intent_keywords = {
            'I': [
                'what', 'how', 'why', 'when', 'where', 'who', 'which', 
                'guide', 'tutorial', 'learn', 'example', 'explain', 'meaning',
                '什么', '如何', '为什么', '怎么', '教程', '学习', '示例', '解释', '意思'
            ],
            'N': [
                'login', 'signin', 'download', 'official', 'website', 'app', 'install',
                'account', 'dashboard', 'home', 'page', 'site', 'portal',
                '登录', '下载', '官网', '官方', '应用', '安装', '账号', '主页'
            ],
            'C': [
                'best', 'top', 'review', 'compare', 'vs', 'versus', 'alternative',
                'comparison', 'difference', 'better', 'pricing', 'features', 'pros', 'cons',
                '最佳', '评测', '对比', '比较', '替代', '区别', '价格', '功能', '优点', '缺点'
            ],
            'E': [
                'buy', 'purchase', 'order', 'coupon', 'discount', 'deal', 'price',
                'cheap', 'free', 'trial', 'subscription', 'template', 'download',
                '购买', '订购', '优惠', '折扣', '价格', '便宜', '免费', '试用', '订阅', '模板'
            ],
            'B': [
                'error', 'fix', 'issue', 'problem', 'bug', 'not working', 'help',
                'support', 'troubleshoot', 'update', 'upgrade', 'integration', 'api',
                '错误', '修复', '问题', '故障', '不工作', '帮助', '支持', '故障排除', '更新', '升级', '集成'
            ]
        }
        
        # 正则表达式模式
        self.patterns = {
            intent: re.compile(r'\b(' + '|'.join(words) + r')\b', re.IGNORECASE) 
            for intent, words in self.intent_keywords.items()
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
    
    def detect_intent_from_serp(self, serp_data):
        """
        从SERP数据判断搜索意图（模拟实现）
        
        参数:
            serp_data (dict): SERP数据
            
        返回:
            tuple: (主要意图, 置信度, 次要意图)
        """
        # 注意：这是一个模拟实现，实际使用需要替换为真实的SERP分析
        
        # 模拟SERP特征
        features = {
            'ads_count': serp_data.get('ads_count', 0),
            'has_paa': serp_data.get('has_paa', False),
            'has_featured_snippet': serp_data.get('has_featured_snippet', False),
            'has_shopping': serp_data.get('has_shopping', False),
            'has_video': serp_data.get('has_video', False),
            'title_keywords': serp_data.get('title_keywords', [])
        }
        
        # 基于SERP特征的意图判断规则
        if features['ads_count'] >= 3 or features['has_shopping']:
            return ('E', 0.8, 'C')
        elif features['has_featured_snippet'] or features['has_paa']:
            return ('I', 0.7, None)
        elif any(kw in features['title_keywords'] for kw in ['best', 'top', 'review', 'vs']):
            return ('C', 0.75, 'I')
        else:
            return ('I', 0.6, None)  # 默认为信息型
    
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
            
            # 从关键词文本判断意图
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
        actions = {
            'I': '创建教程、指南或信息图表',
            'N': '优化登录/下载页面，提高加载速度',
            'C': '创建对比页面或评测内容',
            'E': '优化购买流程，添加促销信息',
            'B': '提供故障排除指南或支持文档'
        }
        
        return actions.get(intent, '创建综合内容')
    
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
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取当前日期作为文件名一部分
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 保存CSV
        file_path = os.path.join(output_dir, f'{prefix}_{date_str}.csv')
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"已保存意图分析结果到: {file_path}")
        
        # 保存摘要为JSON
        summary_path = os.path.join(output_dir, f'{prefix}_summary_{date_str}.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"已保存意图分析摘要到: {summary_path}")
        
        # 按意图分组保存
        for intent, keywords in summary['intent_keywords'].items():
            if keywords:
                intent_df = df[df['intent'] == intent]
                intent_path = os.path.join(output_dir, f'{prefix}_{intent}_{date_str}.csv')
                intent_df.to_csv(intent_path, index=False, encoding='utf-8-sig')
                print(f"已保存 {intent} ({self.INTENT_TYPES[intent]}) 意图关键词到: {intent_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='搜索意图分析工具')
    parser.add_argument('--input', required=True, help='输入CSV文件路径')
    parser.add_argument('--output', default='data', help='输出目录，默认为data')
    parser.add_argument('--keyword-col', default='query', help='关键词列名，默认为query')
    
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
    analyzer = IntentAnalyzer()
    
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


if __name__ == "__main__":
    main()