#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于搜索意图的网站自动建设工具 - 内容计划生成器
"""

import os
from typing import Dict, List, Tuple, Set, Optional, Any, Union
from src.website_builder.intent_config import IntentConfigManager

class ContentPlanGenerator:
    """内容计划生成器"""

    def __init__(self, website_structure, intent_summary, analyzer, config=None):
        """
        初始化内容计划生成器
        
        Args:
            website_structure: 网站结构
            intent_summary: 意图摘要
            analyzer: 意图分析器
            config: 配置参数
        """
        self.website_structure = website_structure
        self.intent_summary = intent_summary
        self.analyzer = analyzer
        self.config = config or {}
        
        # 初始化内容计划
        self.content_plan = []
        self.week = 1

    def generate(self) -> List[Dict[str, Any]]:
        """
        生成内容计划
        
        Returns:
            内容计划列表
        """
        # 1. 首页内容
        self._plan_homepage_content()
        
        # 2. 意图页面内容
        self._plan_intent_pages_content()
        
        # 3. 内容页面
        self._plan_content_pages()
        
        # 4. 产品页面
        self._plan_product_pages()
        
        # 5. 分类页面
        self._plan_category_pages()
        
        return self.content_plan

    def _plan_homepage_content(self) -> None:
        """规划首页内容"""
        self.content_plan.append({
            'week': self.week,
            'title': '首页内容',
            'page_url': '/',
            'content_type': 'homepage',
            'intent': 'multiple',
            'priority': 'very_high',
            'word_count': 1000,
            'status': 'planned',
            'sections': [
                {
                    'name': '英雄区',
                    'type': 'hero',
                    'word_count': 200
                },
                {
                    'name': '意图导航',
                    'type': 'intent_nav',
                    'word_count': 100
                },
                {
                    'name': '意图专区',
                    'type': 'intent_sections',
                    'word_count': 700
                }
            ]
        })
        
        self.week += 1

    def _plan_intent_pages_content(self) -> None:
        """规划意图页面内容"""
        for intent, pages in self.website_structure['intent_pages'].items():
            for page in pages:
                intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
                page_type = page['type']
                
                # 根据页面类型确定内容结构
                sections = []
                word_count = 1500 if page_type == 'intent_overview' else 1200
                
                if page_type == 'intent_overview':
                    sections = [
                        {
                            'name': '意图介绍',
                            'type': 'introduction',
                            'word_count': 300
                        },
                        {
                            'name': '常见问题',
                            'type': 'faq',
                            'word_count': 500
                        },
                        {
                            'name': '相关内容',
                            'type': 'related_content',
                            'word_count': 700
                        }
                    ]
                elif page_type == 'sub_intent':
                    sections = [
                        {
                            'name': '子意图介绍',
                            'type': 'introduction',
                            'word_count': 250
                        },
                        {
                            'name': '内容列表',
                            'type': 'content_list',
                            'word_count': 650
                        },
                        {
                            'name': '相关资源',
                            'type': 'resources',
                            'word_count': 300
                        }
                    ]
                elif page_type == 'keyword':
                    sections = [
                        {
                            'name': '关键词介绍',
                            'type': 'introduction',
                            'word_count': 300
                        },
                        {
                            'name': '详细内容',
                            'type': 'detailed_content',
                            'word_count': 900
                        }
                    ]
                
                self.content_plan.append({
                    'week': self.week,
                    'title': page['title'],
                    'page_url': page['url'],
                    'content_type': page_type,
                    'intent': intent,
                    'intent_name': intent_name,
                    'priority': page['seo_priority'],
                    'word_count': word_count,
                    'status': 'planned',
                    'sections': sections
                })
                
                self.week += 1

    def _plan_content_pages(self) -> None:
        """规划内容页面"""
        for page_id, page in self.website_structure['content_pages'].items():
            intent = page['intent']
            keyword = page['keyword']
            
            # 使用配置化的意图信息
            intent_name = self.intent_config.get_intent_name(intent)
            sections = self.intent_config.get_content_sections(intent)
            word_count = self.intent_config.get_word_count(intent)
            priority = self.intent_config.get_seo_priority(intent)
            
            self.content_plan.append({
                'week': self.week,
                'title': page['title'],
                'page_url': page['url'],
                'content_type': 'article',
                'intent': intent,
                'intent_name': intent_name,
                'keyword': keyword,
                'priority': page['seo_priority'],
                'word_count': word_count,
                'status': 'planned',
                'sections': sections
            })
            
            self.week += 1

    def _plan_product_pages(self) -> None:
        """规划产品页面"""
        for page_id, page in self.website_structure['product_pages'].items():
            keyword = page['keyword']
            
            self.content_plan.append({
                'week': self.week,
                'title': page['title'],
                'page_url': page['url'],
                'content_type': 'product',
                'intent': 'E',
                'intent_name': self.analyzer.INTENT_DESCRIPTIONS.get('E', 'E'),
                'keyword': keyword,
                'priority': page['seo_priority'],
                'word_count': 1500,
                'status': 'planned',
                'sections': [
                    {
                        'name': '产品介绍',
                        'type': 'introduction',
                        'word_count': 300
                    },
                    {
                        'name': '产品特点',
                        'type': 'features',
                        'word_count': 400
                    },
                    {
                        'name': '规格参数',
                        'type': 'specifications',
                        'word_count': 300
                    },
                    {
                        'name': '价格信息',
                        'type': 'pricing',
                        'word_count': 200
                    },
                    {
                        'name': '用户评价',
                        'type': 'reviews',
                        'word_count': 300
                    }
                ]
            })
            
            self.week += 1

    def _plan_category_pages(self) -> None:
        """规划分类页面"""
        for category_id, page in self.website_structure['category_pages'].items():
            intent = page['intent']
            intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
            
            self.content_plan.append({
                'week': self.week,
                'title': page['title'],
                'page_url': page['url'],
                'content_type': 'category',
                'intent': intent,
                'intent_name': intent_name,
                'priority': page['seo_priority'],
                'word_count': 1000,
                'status': 'planned',
                'sections': [
                    {
                        'name': '分类介绍',
                        'type': 'introduction',
                        'word_count': 300
                    },
                    {
                        'name': '内容列表',
                        'type': 'content_list',
                        'word_count': 500
                    },
                    {
                        'name': '相关分类',
                        'type': 'related_categories',
                        'word_count': 200
                    }
                ]
            })
            
            self.week += 1