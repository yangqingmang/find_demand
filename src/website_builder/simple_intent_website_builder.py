#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于搜索意图的网站自动建设工具（简化版）
"""

import os
import sys
import json
import csv
import argparse
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional, Any, Union

# 修改导入路径
from src.analyzers.intent_analyzer_v2 import IntentAnalyzerV2

class SimpleIntentWebsiteBuilder:
    """基于搜索意图的网站自动建设工具（简化版）"""

    def __init__(self, intent_data_path: str = None, output_dir: str = "output"):
        """
        初始化网站建设工具
        
        Args:
            intent_data_path: 意图数据文件路径（CSV或JSON）
            output_dir: 输出目录
        """
        # 初始化属性
        self.intent_data_path = intent_data_path
        self.output_dir = output_dir
        self.intent_data = None
        self.intent_summary = None
        self.website_structure = None
        self.content_plan = None
        
        # 创建意图分析器
        self.analyzer = IntentAnalyzerV2()
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"基于搜索意图的网站建设工具初始化完成")

    def load_intent_data(self) -> bool:
        """
        加载意图数据
        
        Returns:
            是否成功加载
        """
        if not self.intent_data_path:
            print("错误: 未提供意图数据文件路径")
            return False
        
        print(f"正在加载意图数据: {self.intent_data_path}")
        
        try:
            # 根据文件扩展名决定加载方式
            ext = os.path.splitext(self.intent_data_path)[1].lower()
            
            if ext == '.csv':
                # 加载CSV文件
                self.intent_data = pd.read_csv(self.intent_data_path)
            elif ext == '.json':
                # 加载JSON文件
                with open(self.intent_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 转换为DataFrame
                if isinstance(data, list):
                    self.intent_data = pd.DataFrame(data)
                else:
                    self.intent_data = pd.DataFrame([data])
            else:
                print(f"错误: 不支持的文件格式: {ext}")
                return False
            
            # 检查必要的列
            required_columns = ['query', 'intent_primary']
            missing_columns = [col for col in required_columns if col not in self.intent_data.columns]
            
            if missing_columns:
                print(f"错误: 数据缺少必要的列: {', '.join(missing_columns)}")
                return False
            
            # 生成意图摘要
            self._generate_intent_summary()
            
            print(f"成功加载意图数据，共 {len(self.intent_data)} 条记录")
            return True
            
        except Exception as e:
            print(f"加载意图数据失败: {e}")
            return False

    def _generate_intent_summary(self) -> None:
        """生成意图摘要"""
        if self.intent_data is None:
            return
        
        # 统计意图数量
        intent_counts = self.intent_data['intent_primary'].value_counts().to_dict()
        
        # 计算意图百分比
        total = len(self.intent_data)
        intent_percentages = {
            intent: round(count / total * 100, 1)
            for intent, count in intent_counts.items()
        }
        
        # 按意图分组关键词
        intent_keywords = {}
        for intent in set(self.intent_data['intent_primary']):
            keywords = self.intent_data[self.intent_data['intent_primary'] == intent]['query'].tolist()
            intent_keywords[intent] = keywords
        
        # 创建意图摘要
        self.intent_summary = {
            'total_keywords': total,
            'intent_counts': intent_counts,
            'intent_percentages': intent_percentages,
            'intent_keywords': intent_keywords,
            'intent_descriptions': {
                intent: self.analyzer.INTENT_DESCRIPTIONS.get(intent, '')
                for intent in intent_counts.keys()
            }
        }

    def generate_website_structure(self) -> Dict[str, Any]:
        """
        生成网站结构
        
        Returns:
            网站结构字典
        """
        if self.intent_data is None or self.intent_data.empty or not self.intent_summary:
            print("错误: 未加载意图数据")
            return {}
        
        print("正在生成基于搜索意图的网站结构...")
        
        # 创建网站结构
        self.website_structure = {
            'homepage': {
                'title': '基于搜索意图的内容平台',
                'url': '/',
                'sections': []
            },
            'intent_pages': {},
            'content_pages': {},
            'product_pages': {},
            'category_pages': {}
        }
        
        # 1. 生成首页结构
        self._generate_homepage_structure()
        
        # 2. 生成意图页面
        self._generate_intent_pages()
        
        # 3. 生成内容页面
        self._generate_content_pages()
        
        # 4. 生成产品页面
        self._generate_product_pages()
        
        # 5. 生成分类页面
        self._generate_category_pages()
        
        # 保存网站结构
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.output_dir, f'website_structure_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.website_structure, f, ensure_ascii=False, indent=2)
        
        print(f"网站结构生成完成，已保存到: {output_file}")
        
        return self.website_structure

    def _generate_homepage_structure(self) -> None:
        """生成首页结构"""
        # 获取主要意图（按百分比排序）
        main_intents = sorted(
            self.intent_summary['intent_percentages'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 添加英雄区
        self.website_structure['homepage']['sections'].append({
            'type': 'hero',
            'title': '基于搜索意图的内容平台',
            'subtitle': '为用户提供精准的内容体验',
            'cta': '开始探索'
        })
        
        # 添加意图导航区
        self.website_structure['homepage']['sections'].append({
            'type': 'intent_nav',
            'title': '按意图浏览',
            'items': [
                {'name': self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent), 'intent': intent}
                for intent, _ in main_intents
            ]
        })
        
        # 为主要意图创建专区
        for intent, percentage in main_intents:
            intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
            
            # 添加意图专区
            self.website_structure['homepage']['sections'].append({
                'type': 'intent_section',
                'intent': intent,
                'title': f'{intent_name}内容',
                'description': f'探索{intent_name}相关的内容',
                'items': []
            })

    def _generate_intent_pages(self) -> None:
        """生成意图页面"""
        # 为每种意图创建页面
        for intent, keywords in self.intent_summary['intent_keywords'].items():
            if not keywords:
                continue
                
            intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
            
            # 确保intent键存在
            if intent not in self.website_structure['intent_pages']:
                self.website_structure['intent_pages'][intent] = []
            
            # 创建意图总览页面
            self.website_structure['intent_pages'][intent].append({
                'title': f'{intent_name}内容总览',
                'url': f'/intent/{intent.lower()}',
                'type': 'intent_overview',
                'intent': intent,
                'intent_name': intent_name,
                'seo_priority': 'high'
            })
            
            # 获取子意图
            sub_intents = set()
            if 'sub_intent' in self.intent_data.columns:
                sub_intents = set(
                    self.intent_data[
                        (self.intent_data['intent_primary'] == intent) & 
                        (self.intent_data['sub_intent'].notna())
                    ]['sub_intent']
                )
            
            # 为每个子意图创建页面
            for sub_intent in sub_intents:
                sub_intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(sub_intent, sub_intent)
                
                self.website_structure['intent_pages'][intent].append({
                    'title': f'{sub_intent_name}内容',
                    'url': f'/intent/{sub_intent.lower()}',
                    'type': 'sub_intent',
                    'intent': intent,
                    'sub_intent': sub_intent,
                    'intent_name': sub_intent_name,
                    'seo_priority': 'medium'
                })
            
            # 为热门关键词创建页面
            top_keywords = {}
            for intent_key, intent_keywords in self.intent_summary['intent_keywords'].items():
                if intent_keywords:
                    top_keywords[intent_key] = intent_keywords[:5]  # 每种意图取前5个关键词
            
            for keyword in top_keywords.get(intent, []):
                self.website_structure['intent_pages'][intent].append({
                    'title': keyword,
                    'url': f'/keyword/{keyword.replace(" ", "-").lower()}',
                    'type': 'keyword',
                    'intent': intent,
                    'keyword': keyword,
                    'seo_priority': 'high'
                })

    def _generate_content_pages(self) -> None:
        """生成内容页面"""
        # 为每种主要意图创建内容页面
        for intent, keywords in self.intent_summary['intent_keywords'].items():
            # 只处理主意图
            if len(intent) != 1:
                continue
                
            # 为每个关键词创建内容页面
            for i, keyword in enumerate(keywords[:10]):  # 每种意图最多取10个关键词
                page_id = f"{intent.lower()}_content_{i+1}"
                
                self.website_structure['content_pages'][page_id] = {
                    'title': keyword,
                    'url': f'/content/{page_id}',
                    'intent': intent,
                    'keyword': keyword,
                    'content_type': 'article',
                    'seo_priority': 'medium'
                }

    def _generate_product_pages(self) -> None:
        """生成产品页面"""
        # 查找交易购买(E)意图的关键词
        e_keywords = self.intent_summary['intent_keywords'].get('E', [])
        
        # 为每个关键词创建产品页面
        for i, keyword in enumerate(e_keywords[:5]):  # 最多取5个关键词
            product_id = f"product_{i+1}"
            
            self.website_structure['product_pages'][product_id] = {
                'title': f"{keyword}产品详情",
                'url': f'/products/{product_id}',
                'intent': 'E',
                'keyword': keyword,
                'product_type': 'digital',
                'seo_priority': 'high'
            }

    def _generate_category_pages(self) -> None:
        """生成分类页面"""
        # 为每种主要意图创建一个分类页面
        for intent in set(self.intent_data['intent_primary']):
            # 只处理主意图
            if len(intent) != 1:
                continue
                
            intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
            category_id = f"category_{intent.lower()}"
            
            self.website_structure['category_pages'][category_id] = {
                'title': f"{intent_name}分类",
                'url': f'/categories/{category_id}',
                'intent': intent,
                'seo_priority': 'medium'
            }

    def create_content_plan(self) -> List[Dict[str, Any]]:
        """
        创建内容计划
        
        Returns:
            内容计划列表
        """
        if not self.website_structure or not self.intent_summary:
            print("错误: 未生成网站结构或意图摘要")
            return []
        
        print("正在创建基于搜索意图的内容计划...")
        
        # 创建内容计划
        content_plan = []
        week = 1
        
        # 1. 首页内容
        content_plan.append({
            'week': week,
            'title': '首页内容',
            'page_url': '/',
            'content_type': 'homepage',
            'intent': 'multiple',
            'priority': 'very_high',
            'word_count': 1000,
            'status': 'planned'
        })
        
        # 2. 意图页面内容
        for intent, pages in self.website_structure['intent_pages'].items():
            for page in pages:
                week += 1
                
                content_plan.append({
                    'week': week,
                    'title': page['title'],
                    'page_url': page['url'],
                    'content_type': page['type'],
                    'intent': intent,
                    'priority': page['seo_priority'],
                    'word_count': 1500 if page['type'] == 'intent_overview' else 1200,
                    'status': 'planned'
                })
        
        # 3. 内容页面
        for page_id, page in self.website_structure['content_pages'].items():
            week += 1
            
            content_plan.append({
                'week': week,
                'title': page['title'],
                'page_url': page['url'],
                'content_type': 'article',
                'intent': page['intent'],
                'priority': 'medium',
                'word_count': 2000,
                'status': 'planned'
            })
        
        # 4. 产品页面
        for page_id, page in self.website_structure['product_pages'].items():
            week += 1
            
            content_plan.append({
                'week': week,
                'title': page['title'],
                'page_url': page['url'],
                'content_type': 'product',
                'intent': 'E',
                'priority': 'high',
                'word_count': 1500,
                'status': 'planned'
            })
        
        # 保存内容计划
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.output_dir, f'content_plan_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(content_plan, f, ensure_ascii=False, indent=2)
        
        print(f"内容计划创建完成，共 {len(content_plan)} 个内容项，已保存到: {output_file}")
        
        self.content_plan = content_plan
        return content_plan


def main():
    """主函数"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='基于搜索意图的网站自动建设工具（简化版）')
    
    # 添加命令行参数
    parser.add_argument('--input', '-i', type=str, help='输入文件路径（CSV或JSON）')
    parser.add_argument('--output', '-o', type=str, default='output', help='输出目录路径')
    parser.add_argument('--action', '-a', type=str, choices=['analyze', 'structure', 'content', 'all'], 
                        default='all', help='执行的操作')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 检查必要参数
    if not args.input:
        parser.error("必须提供输入文件(--input)")
    
    # 创建网站建设工具实例
    builder = SimpleIntentWebsiteBuilder(
        intent_data_path=args.input,
        output_dir=args.output
    )
    
    # 加载意图数据
    if not builder.load_intent_data():
        print("加载意图数据失败，程序退出")
        return
    
    # 执行请求的操作
    if args.action == 'analyze' or args.action == 'all':
        # 已经在前面完成了分析
        pass
    
    if args.action == 'structure' or args.action == 'all':
        # 生成网站结构
        builder.generate_website_structure()
    
    if args.action == 'content' or args.action == 'all':
        # 创建内容计划
        builder.create_content_plan()
    
    print("操作完成")


if __name__ == "__main__":
    main()