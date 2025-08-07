#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于搜索意图的网站自动建设工具 - 网站结构生成器
"""

import os
from typing import Dict, List, Tuple, Set, Optional, Any, Union

class WebsiteStructureGenerator:
    """网站结构生成器"""

    def __init__(self, intent_data, intent_summary, analyzer, template_manager, config=None):
        """
        初始化网站结构生成器
        
        Args:
            intent_data: 意图数据
            intent_summary: 意图摘要
            analyzer: 意图分析器
            template_manager: 页面模板管理器
            config: 配置参数
        """
        self.intent_data = intent_data
        self.intent_summary = intent_summary
        self.analyzer = analyzer
        self.template_manager = template_manager
        self.config = config or {}
        
        # 初始化网站结构
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

    def generate(self) -> Dict[str, Any]:
        """
        生成网站结构
        
        Returns:
            网站结构字典
        """
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