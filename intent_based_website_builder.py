#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于搜索意图的网站自动建设工具

该工具基于最新的搜索意图分析规则（6主意图×24子意图）自动生成网站结构和内容计划，
针对不同的搜索意图类型设计不同的页面模板和内容策略，以优化SEO效果和用户体验。
"""

import os
import json
import yaml
import pandas as pd
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict

# 导入意图分析器
try:
    from src.analyzers.intent_analyzer_v2 import IntentAnalyzerV2
except ImportError:
    print("警告: 无法导入IntentAnalyzerV2，将使用本地实现")
    # 如果无法导入，使用简化版本
    class IntentAnalyzerV2:
        """简化版意图分析器"""
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


class IntentBasedWebsiteBuilder:
    """基于搜索意图的网站自动建设工具"""
    
    def __init__(self, intent_data_path: str = None, output_dir: str = 'output'):
        """
        初始化网站建设工具
        
        Args:
            intent_data_path: 意图分析数据路径（CSV或JSON）
            output_dir: 输出目录
        """
        self.intent_data_path = intent_data_path
        self.output_dir = output_dir
        self.intent_data = None
        self.intent_summary = None
        self.analyzer = IntentAnalyzerV2()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 页面模板配置
        self.page_templates = self._load_page_templates()
        
        # 内容类型配置
        self.content_types = self._get_content_types()
        
        # SEO配置
        self.seo_config = self._get_seo_config()
        
        # 网站结构
        self.website_structure = {
            'homepage': {},
            'intent_pages': {},
            'content_pages': {},
            'product_pages': {},
            'category_pages': {}
        }
        
        # 内容计划
        self.content_plan = []
        
        # 技术栈配置
        self.tech_stack = self._get_tech_stack()
        
        print("基于搜索意图的网站自动建设工具初始化完成")
    
    def _load_page_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载页面模板配置"""
        return {
            # 信息获取型页面模板
            'I': {
                'layout': 'guide',
                'sections': [
                    {'type': 'hero', 'title': '{keyword} 完全指南', 'description': '了解关于{keyword}的一切'},
                    {'type': 'toc', 'title': '目录'},
                    {'type': 'definition', 'title': '{keyword}是什么?'},
                    {'type': 'steps', 'title': '如何使用{keyword}'},
                    {'type': 'faq', 'title': '常见问题'},
                    {'type': 'related', 'title': '相关资源'}
                ],
                'cta': '深入了解',
                'word_count': 2000,
                'media_ratio': 0.3,  # 30%的内容是媒体（图片、视频）
                'seo_priority': 'high'
            },
            # 导航直达型页面模板
            'N': {
                'layout': 'landing',
                'sections': [
                    {'type': 'hero', 'title': '{keyword} 官方入口', 'description': '快速访问{keyword}'},
                    {'type': 'features', 'title': '主要功能'},
                    {'type': 'cta_block', 'title': '立即访问'},
                    {'type': 'alternatives', 'title': '其他选择'}
                ],
                'cta': '立即访问',
                'word_count': 800,
                'media_ratio': 0.2,
                'seo_priority': 'medium'
            },
            # 商业评估型页面模板
            'C': {
                'layout': 'comparison',
                'sections': [
                    {'type': 'hero', 'title': '{year}年最佳{keyword}推荐', 'description': '全面对比{keyword}'},
                    {'type': 'comparison_table', 'title': '{keyword}对比表'},
                    {'type': 'top_picks', 'title': '编辑推荐'},
                    {'type': 'reviews', 'title': '详细评测'},
                    {'type': 'buying_guide', 'title': '购买指南'},
                    {'type': 'faq', 'title': '常见问题'}
                ],
                'cta': '查看最佳选择',
                'word_count': 3000,
                'media_ratio': 0.25,
                'seo_priority': 'very_high'
            },
            # 交易购买型页面模板
            'E': {
                'layout': 'product',
                'sections': [
                    {'type': 'hero', 'title': '购买{keyword}', 'description': '最优惠的{keyword}价格'},
                    {'type': 'pricing', 'title': '价格方案'},
                    {'type': 'deals', 'title': '限时优惠'},
                    {'type': 'testimonials', 'title': '用户评价'},
                    {'type': 'guarantee', 'title': '购买保障'}
                ],
                'cta': '立即购买',
                'word_count': 1500,
                'media_ratio': 0.3,
                'seo_priority': 'high'
            },
            # 行为后续型页面模板
            'B': {
                'layout': 'support',
                'sections': [
                    {'type': 'hero', 'title': '{keyword}使用指南', 'description': '解决{keyword}使用问题'},
                    {'type': 'troubleshooting', 'title': '常见问题解决'},
                    {'type': 'advanced_tips', 'title': '高级技巧'},
                    {'type': 'community', 'title': '社区支持'},
                    {'type': 'updates', 'title': '最新更新'}
                ],
                'cta': '获取支持',
                'word_count': 2500,
                'media_ratio': 0.4,
                'seo_priority': 'medium'
            },
            # 本地/到店型页面模板
            'L': {
                'layout': 'local',
                'sections': [
                    {'type': 'hero', 'title': '附近的{keyword}', 'description': '找到离您最近的{keyword}'},
                    {'type': 'map', 'title': '位置地图'},
                    {'type': 'locations', 'title': '所有位置'},
                    {'type': 'hours', 'title': '营业时间'},
                    {'type': 'directions', 'title': '到达方式'}
                ],
                'cta': '查看位置',
                'word_count': 1000,
                'media_ratio': 0.5,
                'seo_priority': 'medium'
            }
        }
    
    def _get_content_types(self) -> Dict[str, Dict[str, Any]]:
        """获取内容类型配置"""
        return {
            # 信息获取型内容
            'I': {
                'I1': {  # 定义/概念
                    'formats': ['百科词条', '概念解释', '术语表'],
                    'title_templates': [
                        '什么是{keyword}？完整解释',
                        '{keyword}是什么意思？详细定义',
                        '{keyword}百科：你需要知道的一切'
                    ],
                    'meta_description': '{keyword}的完整定义和解释，了解{keyword}的含义、起源和应用场景。',
                    'content_structure': ['定义', '历史背景', '核心概念', '应用场景', '常见误区', '延伸阅读'],
                    'conversion_strategy': '引导到更深入的教程或相关产品'
                },
                'I2': {  # 原理/源码
                    'formats': ['技术文档', '原理解析', '源码分析'],
                    'title_templates': [
                        '{keyword}工作原理详解',
                        '{keyword}背后的技术：深度解析',
                        '{keyword}源码分析与架构设计'
                    ],
                    'meta_description': '深入解析{keyword}的工作原理、技术架构和源码实现，适合开发者和技术爱好者。',
                    'content_structure': ['技术概述', '架构设计', '核心算法', '源码分析', '性能考量', '实现挑战'],
                    'conversion_strategy': '引导到高级教程或开发者社区'
                },
                'I3': {  # 教程/步骤
                    'formats': ['分步教程', '操作指南', '视频教程'],
                    'title_templates': [
                        '{keyword}教程：从入门到精通',
                        '如何使用{keyword}：完整指南',
                        '{keyword}新手指南：10个简单步骤'
                    ],
                    'meta_description': '学习如何使用{keyword}的详细教程，包含分步指南和实用技巧，适合初学者。',
                    'content_structure': ['准备工作', '基础步骤', '进阶技巧', '常见问题', '实战案例', '下一步学习'],
                    'conversion_strategy': '引导到相关工具或高级课程'
                },
                'I4': {  # 事实求证
                    'formats': ['事实核查', '真相解析', '专家观点'],
                    'title_templates': [
                        '{keyword}是否真的有效？科学解析',
                        '{keyword}的真相：分析与验证',
                        '{keyword}：常见说法的真假分析'
                    ],
                    'meta_description': '深入分析{keyword}的真实情况，基于事实和数据验证常见说法的真伪。',
                    'content_structure': ['常见说法', '事实依据', '专家观点', '研究数据', '结论分析', '延伸阅读'],
                    'conversion_strategy': '建立权威性，引导到相关服务'
                }
            },
            # 导航直达型内容
            'N': {
                'N1': {  # 官方主页
                    'formats': ['官方介绍', '品牌页面', '产品主页'],
                    'title_templates': [
                        '{keyword}官方网站 - 权威入口',
                        '{keyword}官方主页 - 直达链接',
                        '访问{keyword}官方网站 - 安全链接'
                    ],
                    'meta_description': '{keyword}的官方网站入口，获取最新信息、产品介绍和官方支持。',
                    'content_structure': ['品牌介绍', '产品概述', '官方链接', '最新动态', '联系方式'],
                    'conversion_strategy': '直接引导到官方网站或产品'
                },
                'N2': {  # 登录/控制台
                    'formats': ['登录指南', '控制台教程', '账户管理'],
                    'title_templates': [
                        '{keyword}登录入口及使用指南',
                        '如何登录{keyword}控制台 - 详细步骤',
                        '{keyword}账户管理与控制台使用技巧'
                    ],
                    'meta_description': '{keyword}登录入口指南，包含登录步骤、控制台使用技巧和账户管理方法。',
                    'content_structure': ['登录入口', '账户创建', '控制台导航', '常见问题', '安全提示'],
                    'conversion_strategy': '引导到登录页面或账户创建'
                },
                'N3': {  # 下载/安装包
                    'formats': ['下载指南', '安装教程', '版本对比'],
                    'title_templates': [
                        '{keyword}下载：官方最新版本',
                        '如何下载并安装{keyword} - 完整指南',
                        '{keyword}各版本下载与对比'
                    ],
                    'meta_description': '{keyword}的官方下载链接和详细安装指南，包含各版本对比和系统要求。',
                    'content_structure': ['下载链接', '系统要求', '安装步骤', '版本对比', '常见问题'],
                    'conversion_strategy': '引导到下载页面或高级版本'
                }
            },
            # 商业评估型内容
            'C': {
                'C1': {  # 榜单/推荐
                    'formats': ['排行榜', '推荐清单', '编辑精选'],
                    'title_templates': [
                        '{year}年最佳{keyword}推荐：排名前10',
                        '{keyword}排行榜：专家评选与推荐',
                        '最值得使用的{keyword}：完整榜单'
                    ],
                    'meta_description': '{year}年最新{keyword}排行榜，基于专业测评和用户反馈，帮您选择最适合的产品。',
                    'content_structure': ['评选标准', '榜单总览', '详细点评', '价格对比', '如何选择', '常见问题'],
                    'conversion_strategy': '引导到详细评测或购买链接'
                },
                'C2': {  # 对比/评测
                    'formats': ['对比分析', '深度评测', '功能对比表'],
                    'title_templates': [
                        '{keyword}对比：哪个最好？{year}年全面分析',
                        '{keyword1} vs {keyword2}：哪个更值得选择？',
                        '{keyword}深度评测：优缺点全面分析'
                    ],
                    'meta_description': '全面对比各种{keyword}的功能、价格和性能，帮您找到最适合自己需求的选择。',
                    'content_structure': ['对比概述', '功能对比', '性能测试', '价格分析', '适用场景', '最终推荐'],
                    'conversion_strategy': '基于需求引导到最佳选择'
                },
                'C3': {  # 口碑/点评
                    'formats': ['用户评价汇总', '真实使用体验', '长期使用报告'],
                    'title_templates': [
                        '{keyword}用户评价：真实体验分享',
                        '我用{keyword}一年后的真实感受',
                        '{keyword}口碑调查：用户最关心的问题'
                    ],
                    'meta_description': '汇总真实用户对{keyword}的评价和使用体验，揭示产品的真实优缺点和使用感受。',
                    'content_structure': ['评价概述', '优点汇总', '缺点分析', '用户案例', '专家观点', '总体评价'],
                    'conversion_strategy': '基于真实体验建立信任，引导到推荐产品'
                }
            },
            # 交易购买型内容
            'E': {
                'E1': {  # 价格/报价
                    'formats': ['价格指南', '费用分析', '预算规划'],
                    'title_templates': [
                        '{keyword}价格指南：各版本详细对比',
                        '{keyword}要多少钱？完整价格分析',
                        '{keyword}费用明细：从基础版到高级版'
                    ],
                    'meta_description': '{keyword}的详细价格信息，包含各版本费用对比、隐藏成本分析和最佳购买时机。',
                    'content_structure': ['价格总览', '版本对比', '隐藏成本', '性价比分析', '购买建议'],
                    'conversion_strategy': '引导到最佳价格或优惠购买渠道'
                },
                'E2': {  # 优惠/折扣
                    'formats': ['优惠信息', '折扣代码', '促销活动'],
                    'title_templates': [
                        '{keyword}优惠券与折扣码：省钱指南',
                        '{keyword}最新促销活动汇总',
                        '如何以最低价格购买{keyword}'
                    ],
                    'meta_description': '最新{keyword}优惠信息，包含折扣码、促销活动和特别优惠，帮您省钱购买。',
                    'content_structure': ['当前优惠', '折扣码汇总', '会员特价', '季节性促销', '省钱技巧'],
                    'conversion_strategy': '创造紧迫感，引导立即购买'
                },
                'E3': {  # 下单/预订
                    'formats': ['购买指南', '订购流程', '预订教程'],
                    'title_templates': [
                        '如何购买{keyword}：详细步骤指南',
                        '{keyword}订购流程：避开常见陷阱',
                        '{keyword}预订攻略：确保最佳体验'
                    ],
                    'meta_description': '详细指导如何购买或预订{keyword}，包含步骤说明、注意事项和支付方式介绍。',
                    'content_structure': ['准备工作', '购买步骤', '支付选项', '注意事项', '售后服务'],
                    'conversion_strategy': '简化购买流程，减少放弃率'
                }
            },
            # 行为后续型内容
            'B': {
                'B1': {  # 故障/报错
                    'formats': ['故障排除指南', '错误代码解析', '问题解决方案'],
                    'title_templates': [
                        '{keyword}常见问题及解决方法',
                        '{keyword}错误代码大全及修复指南',
                        '解决{keyword}故障的完整指南'
                    ],
                    'meta_description': '全面解析{keyword}常见故障和错误代码，提供详细的排查步骤和解决方案。',
                    'content_structure': ['常见问题', '错误代码', '排查步骤', '解决方案', '预防措施'],
                    'conversion_strategy': '提供高级支持或升级服务'
                },
                'B2': {  # 高级用法
                    'formats': ['高级技巧', '专家指南', '进阶教程'],
                    'title_templates': [
                        '{keyword}高级技巧：提升使用效率',
                        '{keyword}进阶指南：从熟练到精通',
                        '{keyword}专家用法：鲜为人知的功能'
                    ],
                    'meta_description': '探索{keyword}的高级功能和使用技巧，帮助有经验的用户进一步提升效率和体验。',
                    'content_structure': ['基础回顾', '高级功能', '效率技巧', '自定义设置', '案例分享'],
                    'conversion_strategy': '引导到专业版或付费课程'
                },
                'B3': {  # 配置/设置
                    'formats': ['配置指南', '设置教程', '优化方案'],
                    'title_templates': [
                        '{keyword}最佳配置指南：优化性能',
                        '如何正确设置{keyword}：详细教程',
                        '{keyword}设置技巧：提升使用体验'
                    ],
                    'meta_description': '详细指导如何配置和设置{keyword}，包含最佳实践和性能优化建议。',
                    'content_structure': ['基本设置', '高级配置', '性能优化', '安全设置', '常见问题'],
                    'conversion_strategy': '引导到配置服务或高级支持'
                }
            },
            # 本地/到店型内容
            'L': {
                'L1': {  # 附近门店
                    'formats': ['位置指南', '门店列表', '区域地图'],
                    'title_templates': [
                        '附近的{keyword}：完整位置指南',
                        '{location}地区{keyword}门店大全',
                        '如何找到离你最近的{keyword}'
                    ],
                    'meta_description': '查找离您最近的{keyword}位置，包含详细地址、联系方式和服务内容。',
                    'content_structure': ['位置总览', '详细地址', '服务内容', '联系方式', '用户评价'],
                    'conversion_strategy': '引导到地图导航或预约'
                },
                'L2': {  # 预约/路线
                    'formats': ['预约指南', '到店路线', '交通指南'],
                    'title_templates': [
                        '如何预约{keyword}：详细步骤',
                        '前往{keyword}的最佳路线指南',
                        '{keyword}预约系统使用教程'
                    ],
                    'meta_description': '详细指导如何预约{keyword}服务，以及前往各个位置的交通路线和停车信息。',
                    'content_structure': ['预约流程', '准备事项', '交通方式', '停车信息', '到店须知'],
                    'conversion_strategy': '简化预约流程，提高到店率'
                },
                'L3': {  # 开放时间
                    'formats': ['营业时间', '节假日安排', '特殊时段'],
                    'title_templates': [
                        '{keyword}营业时间：完整时间表',
                        '{keyword}节假日开放时间安排',
                        '{keyword}各门店营业时间大全'
                    ],
                    'meta_description': '{keyword}的详细营业时间，包含各分店时间表、节假日安排和特殊时段调整。',
                    'content_structure': ['常规时间', '节假日安排', '特殊时段', '提前预约', '联系方式'],
                    'conversion_strategy': '引导到预约系统或特别活动'
                }
            }
        }
    
    def _get_seo_config(self) -> Dict[str, Any]:
        """获取SEO配置"""
        return {
            'title_patterns': {
                'I': '{keyword} 指南：完整教程与使用方法 ({year})',
                'N': '{keyword} 官方入口 - 安全直达链接',
                'C': '{year}年最佳{keyword}推荐：排名与对比',
                'E': '{keyword}价格与购买指南：如何获得最优惠',
                'B': '{keyword}问题解决与高级使用技巧',
                'L': '附近的{keyword}：位置、时间与预约'
            },
            'meta_description_patterns': {
                'I': '全面了解{keyword}的详细指南，包含使用方法、最佳实践和常见问题解答。',
                'N': '{keyword}的官方入口，安全可靠，直达目标网站，避免钓鱼和欺诈风险。',
                'C': '专业评测{year}年最佳{keyword}，基于实际使用体验和性能测试，帮您做出明智选择。',
                'E': '{keyword}的最新价格信息、购买渠道和折扣优惠，助您以最优惠的价格获取产品。',
                'B': '解决{keyword}使用过程中的常见问题，掌握高级技巧，充分发挥产品潜力。',
                'L': '查找离您最近的{keyword}位置，了解营业时间、预约方式和到店路线。'
            },
            'heading_structure': {
                'h1_pattern': '{main_keyword} - {sub_keyword}',
                'h2_count': {'min': 3, 'max': 7},
                'h3_per_h2': {'min': 2, 'max': 5}
            },
            'content_guidelines': {
                'paragraph_length': {'min': 3, 'max': 5},  # 每段句子数
                'sentence_length': {'min': 10, 'max': 20},  # 每句词数
                'keyword_density': {'min': 0.5, 'max': 2.0},  # 关键词密度百分比
                'readability': 'middle_school'  # 可读性级别
            },
            'schema_markup': {
                'I': 'HowTo',
                'N': 'WebPage',
                'C': 'Review',
                'E': 'Product',
                'B': 'FAQPage',
                'L': 'LocalBusiness'
            },
            'internal_linking': {
                'links_per_page': {'min': 3, 'max': 8},
                'anchor_text_variation': True,
                'link_to_related_intents': True
            }
        }
    
    def _get_tech_stack(self) -> Dict[str, Any]:
        """获取技术栈配置"""
        return {
            'frontend': {
                'framework': 'Next.js',
                'styling': 'Tailwind CSS',
                'features': [
                    'SSR (Server-Side Rendering)',
                    'ISR (Incremental Static Regeneration)',
                    '响应式设计',
                    '暗黑模式',
                    'PWA支持'
                ]
            },
            'backend': {
                'framework': 'Next.js API Routes',
                'database': 'PostgreSQL (Supabase)',
                'cms': 'Contentful',
                'features': [
                    'RESTful API',
                    '内容管理',
                    '用户认证',
                    '搜索功能',
                    '数据分析'
                ]
            },
            'deployment': {
                'hosting': 'Vercel',
                'cdn': 'Cloudflare',
                'monitoring': 'Sentry',
                'analytics': 'Google Analytics 4'
            },
            'seo_tools': {
                'sitemap': 'next-sitemap',
                'meta_tags': 'next-seo',
                'schema': 'schema-dts',
                'analytics': 'GA4 + GTM'
            },
            'performance': {
                'image_optimization': 'next/image',
                'code_splitting': 'Automatic',
                'lazy_loading': 'Enabled',
                'caching': 'SWR + Redis'
            }
        }
    
    def load_intent_data(self) -> bool:
        """
        加载意图分析数据
        
        Returns:
            加载是否成功
        """
        if not self.intent_data_path:
            print("错误: 未指定意图数据路径")
            return False
        
        try:
            # 根据文件扩展名决定加载方式
            if self.intent_data_path.endswith('.csv'):
                self.intent_data = pd.read_csv(self.intent_data_path)
                print(f"已从CSV加载 {len(self.intent_data)} 条意图数据")
            elif self.intent_data_path.endswith('.json'):
                with open(self.intent_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'results' in data:
                        # 如果是IntentAnalyzerV2的输出格式
                        self.intent_data = pd.DataFrame(data['results'])
                        self.intent_summary = data.get('summary', {})
                    else:
                        # 尝试直接加载
                        self.intent_data = pd.DataFrame(data)
                print(f"已从JSON加载 {len(self.intent_data)} 条意图数据")
            else:
                print(f"不支持的文件格式: {self.intent_data_path}")
                return False
            
            # 验证数据格式
            required_columns = ['query', 'intent_primary']
            if not all(col in self.intent_data.columns for col in required_columns):
                print(f"数据格式错误: 缺少必要的列 {required_columns}")
                return False
            
            # 生成意图摘要（如果没有）
            if not self.intent_summary:
                self._generate_intent_summary()
            
            return True
        except Exception as e:
            print(f"加载意图数据失败: {e}")
            return False
    
    def _generate_intent_summary(self) -> None:
        """生成意图摘要"""
        if self.intent_data is None:
            return
        
        # 统计各意图数量
        intent_counts = self.intent_data['intent_primary'].value_counts().to_dict()
        
        # 计算百分比
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
        
        # 创建摘要
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
        
        print(f"已生成意图摘要: {len(intent_counts)} 种意图类型")
    
    def analyze_keywords(self, keywords: List[str]) -> bool:
        """
        分析关键词列表
        
        Args:
            keywords: 关键词列表
            
        Returns:
            分析是否成功
        """
        try:
            # 创建DataFrame
            df = pd.DataFrame({'query': keywords})
            
            # 使用意图分析器
            analysis_results = self.analyzer.analyze_keywords(df, query_col='query')
            
            # 保存结果
            self.intent_data = analysis_results['dataframe']
            self.intent_summary = analysis_results['summary']
            
            # 保存到文件
            timestamp = datetime.now().strftime('%Y-%m-%d')
            output_file = os.path.join(self.output_dir, f'intent_analysis_{timestamp}.json')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'results': analysis_results['results'],
                    'summary': analysis_results['summary']
                }, f, ensure_ascii=False, indent=2)
            
            print(f"已分析 {len(keywords)} 个关键词，结果保存到: {output_file}")
            return True
        except Exception as e:
            print(f"分析关键词失败: {e}")
            return False
    
    def generate_website_structure(self) -> Dict[str, Any]:
        """
        生成网站结构
        
        Returns:
            网站结构字典
        """
        if self.intent_data is None or self.intent_summary is None:
            print("错误: 未加载意图数据")
            return {}
        
        print("正在生成基于搜索意图的网站结构...")
        
        # 获取当前年份
        current_year = datetime.now().year
        
        # 1. 生成首页
        self.website_structure['homepage'] = self._generate_homepage()
        
        # 2. 生成意图页面
        for intent, keywords in self.intent_summary['intent_keywords'].items():
            if not keywords:
                continue
                
            # 只处理主意图（单字符）
            if len(intent) == 1:
                intent_pages = self._generate_intent_pages(intent, keywords, current_year)
                self.website_structure['intent_pages'][intent] = intent_pages
        
        # 3. 生成内容页面
        self._generate_content_pages(current_year)
        
        # 4. 生成产品页面
        self._generate_product_pages()
        
        # 5. 生成分类页面
        self._generate_category_pages(current_year)
        
        print(f"网站结构生成完成，共包含:")
        print(f"- 1 个首页")
        print(f"- {sum(len(pages) for pages in self.website_structure['intent_pages'].values())} 个意图页面")
        print(f"- {len(self.website_structure['content_pages'])} 个内容页面")
        print(f"- {len(self.website_structure['product_pages'])} 个产品页面")
        print(f"- {len(self.website_structure['category_pages'])} 个分类页面")
        
        return self.website_structure
    
    def _generate_homepage(self) -> Dict[str, Any]:
        """生成首页结构"""
        # 获取主要关键词（按意图分布）
        top_keywords = {}
        for intent, keywords in self.intent_summary['intent_keywords'].items():
            if keywords:
                # 每种意图取前3个关键词
                top_keywords[intent] = keywords[:3]
        
        # 确定主要意图（占比最高的前3种）
        main_intents = sorted(
            self.intent_summary['intent_percentages'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        # 生成首页结构
        homepage = {
            'title': '主页 - 基于用户搜索意图优化的内容平台',
            'meta_description': '提供满足各种搜索意图的高质量内容，包括教程、评测、购买指南和问题解决方案。',
            'sections': [
                {
                    'type': 'hero',
                    'title': '找到您需要的一切',
                    'description': '基于真实搜索意图打造的内容平台'
                }
            ],
            'intent_sections': []
        }
        
        # 为主要意图创建专区
        for intent, percentage in main_intents:
            intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
            keywords = self.intent_summary['intent_keywords'].get(intent, [])[:5]
            
            homepage['intent_sections'].append({
                'intent': intent,
                'intent_name': intent_name,
                'title': f"{intent_name}内容",
                'description': self._get_intent_description(intent),
                'featured_keywords': keywords,
                'percentage': percentage
            })
        
        # 添加其他首页部分
        homepage['sections'].extend([
            {
                'type': 'featured',
                'title': '热门内容',
                'items': self._get_top_keywords(5)
            },
            {
                'type': 'categories',
                'title': '内容分类',
                'items': [
                    {'name': self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent), 'intent': intent}
                    for intent, _ in main_intents
                ]
            },
            {
                'type': 'cta',
                'title': '找不到您需要的内容？',
                'description': '告诉我们您的需求，我们将为您创建相关内容',
                'button': '提交需求'
            }
        ])
        
        return homepage
    
    def _get_intent_description(self, intent: str) -> str:
        """获取意图的描述文本"""
        descriptions = {
            'I': '全面的指南和教程，帮助您了解和学习各种主题',
            'N': '直达官方网站、登录入口和下载页面的安全链接',
            'C': '详细的产品评测、对比和推荐，助您做出明智选择',
            'E': '最优惠的价格信息、折扣代码和购买指南',
            'B': '解决使用问题、故障排除和高级使用技巧',
            'L': '查找附近位置、营业时间和到店路线'
        }
        return descriptions.get(intent, '相关内容和资源')
    
    def _get_top_keywords(self, count: int) -> List[Dict[str, str]]:
        """获取热门关键词"""
        if self.intent_data is None or len(self.intent_data) == 0:
            return []
        
        # 如果有概率列，按概率排序
        if 'probability' in self.intent_data.columns:
            top_df = self.intent_data.sort_values('probability', ascending=False).head(count)
        else:
            # 否则随机选择
            top_df = self.intent_data.sample(min(count, len(self.intent_data)))
        
        return [
            {
                'keyword': row['query'],
                'intent': row['intent_primary'],
                'intent_name': self.analyzer.INTENT_DESCRIPTIONS.get(row['intent_primary'], '')
            }
            for _, row in top_df.iterrows()
        ]
    
    def _generate_intent_pages(self, intent: str, keywords: List[str], year: int) -> List[Dict[str, Any]]:
        """
        为特定意图生成页面
        
        Args:
            intent: 意图代码
            keywords: 相关关键词列表
            year: 当前年份
            
        Returns:
            页面列表
        """
        # 获取页面模板
        template = self.page_templates.get(intent, {})
        if not template:
            return []
        
        # 按子意图分组关键词
        sub_intent_keywords = defaultdict(list)
        
        # 遍历关键词，查找子意图
        for keyword in keywords:
            # 在意图数据中查找该关键词
            keyword_data = self.intent_data[self.intent_data['query'] == keyword]
            if not keyword_data.empty and 'sub_intent' in keyword_data.columns:
                sub_intent = keyword_data.iloc[0]['sub_intent']
                if sub_intent and sub_intent.startswith(intent):
                    sub_intent_keywords[sub_intent].append(keyword)
                else:
                    # 如果没有子意图或子意图不匹配，放入主意图组
                    sub_intent_keywords[intent].append(keyword)
            else:
                sub_intent_keywords[intent].append(keyword)
        
        # 生成页面
        pages = []
        
        # 1. 为主意图创建总览页面
        overview_page = self._create_intent_overview_page(intent, keywords, template, year)
        pages.append(overview_page)
        
        # 2. 为每个子意图创建专门页面
        for sub_intent, sub_keywords in sub_intent_keywords.items():
            # 跳过主意图（已经创建了总览页面）
            if sub_intent == intent or not sub_keywords:
                continue
                
            # 创建子意图页面
            sub_page = self._create_sub_intent_page(sub_intent, sub_keywords, template, year)
            pages.append(sub_page)
        
        # 3. 为热门关键词创建专门页面
        top_keywords = sorted(keywords, key=lambda k: len(k))[:5]  # 简单示例：取最短的5个关键词作为热门
        for keyword in top_keywords:
            keyword_page = self._create_keyword_page(keyword, intent, template, year)
            pages.append(keyword_page)
        
        return pages
    
    def _create_intent_overview_page(self, intent: str, keywords: List[str], template: Dict[str, Any], year: int) -> Dict[str, Any]:
        """创建意图总览页面"""
        intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
        
        # 生成标题和描述
        title_pattern = self.seo_config['title_patterns'].get(intent, '{intent_name}内容 - {year}')
        title = title_pattern.format(
            intent_name=intent_name,
            keyword=intent_name,
            year=year
        )
        
        description_pattern = self.seo_config['meta_description_patterns'].get(intent, '')
        description = description_pattern.format(
            intent_name=intent_name,
            keyword=intent_name,
            year=year
        )
        
        # 创建页面结构
        page = {
            'type': 'intent_overview',
            'intent': intent,
            'intent_name': intent_name,
            'url': f'/intent/{intent.lower()}',
            'title': title,
            'meta_description': description,
            'sections': [],
            'keywords': keywords[:20],  # 最多显示20个关键词
            'layout': template.get('layout', 'default'),
            'seo_priority': template.get('seo_priority', 'medium')
        }
        
        # 添加页面部分
        for section in template.get('sections', []):
            section_copy = section.copy()
            section_copy['title'] = section['title'].format(
                keyword=intent_name,
                year=year
            )
            page['sections'].append(section_copy)
        
        return page
    
    def _create_sub_intent_page(self, sub_intent: str, keywords: List[str], template: Dict[str, Any], year: int) -> Dict[str, Any]:
        """创建子意图页面"""
        sub_intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(sub_intent, sub_intent)
        main_intent = sub_intent[0]
        
        # 获取内容类型配置
        content_type = self.content_types.get(main_intent, {}).get(sub_intent, {})
        
        # 选择标题模板
        title_templates = content_type.get('title_templates', ['{sub_intent_name} - {year}年完整指南'])
        title = title_templates[0].format(
            sub_intent_name=sub_intent_name,
            keyword=sub_intent_name,
            year=year
        )
        
        # 生成描述
        description = content_type.get('meta_description', '').format(
            sub_intent_name=sub_intent_name,
            keyword=sub_intent_name,
            year=year
        )
        
        # 创建页面结构
        page = {
            'type': 'sub_intent',
            'intent': main_intent,
            'sub_intent': sub_intent,
            'intent_name': sub_intent_name,
            'url': f'/intent/{sub_intent.lower()}',
            'title': title,
            'meta_description': description,
            'sections': [],
            'keywords': keywords[:20],  # 最多显示20个关键词
            'layout': template.get('layout', 'default'),
            'seo_priority': template.get('seo_priority', 'medium'),
            'content_structure': content_type.get('content_structure', []),
            'conversion_strategy': content_type.get('conversion_strategy', '')
        }
        
        # 添加页面部分
        for section in template.get('sections', []):
            section_copy = section.copy()
            section_copy['title'] = section['title'].format(
                keyword=sub_intent_name,
                year=year
            )
            page['sections'].append(section_copy)
        
        return page
    
    def _create_keyword_page(self, keyword: str, intent: str, template: Dict[str, Any], year: int) -> Dict[str, Any]:
        """创建关键词专题页面"""
        intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
        
        # 查找该关键词的子意图
        sub_intent = ''
        keyword_data = self.intent_data[self.intent_data['query'] == keyword]
        if not keyword_data.empty and 'sub_intent' in keyword_data.columns:
            sub_intent = keyword_data.iloc[0]['sub_intent']
        
        # 获取内容类型配置
        content_type = {}
        if sub_intent and len(sub_intent) > 1:
            main_intent = sub_intent[0]
            content_type = self.content_types.get(main_intent, {}).get(sub_intent, {})
        
        # 选择标题模板
        title_templates = content_type.get('title_templates', ['{keyword} - {year}年完整指南'])
        title = title_templates[0].format(
            keyword=keyword,
            year=year
        )
        
        # 生成描述
        description = content_type.get('meta_description', '关于{keyword}的详细信息和指南').format(
            keyword=keyword,
            year=year
        )
        
        # 创建URL友好的关键词
        url_keyword = keyword.lower().replace(' ', '-').replace('/', '-')
        
        # 创建页面结构
        page = {
            'type': 'keyword',
            'intent': intent,
            'sub_intent': sub_intent,
            'keyword': keyword,
            'url': f'/keyword/{url_keyword}',
            'title': title,
            'meta_description': description,
            'sections': [],
            'layout': template.get('layout', 'default'),
            'seo_priority': 'high',
            'content_structure': content_type.get('content_structure', []),
            'conversion_strategy': content_type.get('conversion_strategy', '')
        }
        
        # 添加页面部分
        for section in template.get('sections', []):
            section_copy = section.copy()
            section_copy['title'] = section['title'].format(
                keyword=keyword,
                year=year
            )
            page['sections'].append(section_copy)
        
        return page
    
    def _generate_content_pages(self, year: int) -> None:
        """生成内容页面"""
        # 按意图类型生成不同的内容页面
        content_pages = {}
        
        # 为每种主要意图创建内容页面
        for intent, keywords in self.intent_summary['intent_keywords'].items():
            # 只处理主意图
            if len(intent) != 1 or not keywords:
                continue
                
            # 获取该意图的内容类型
            intent_content_types = self.content_types.get(intent, {})
            
            # 为每种子意图创建内容
            for sub_intent, content_type in intent_content_types.items():
                # 跳过非子意图
                if not sub_intent.startswith(intent) or len(sub_intent) <= 1:
                    continue
                
                # 为该子意图创建2-3个内容页面
                for i in range(min(3, len(keywords))):
                    if i >= len(keywords):
                        break
                        
                    keyword = keywords[i]
                    
                    # 选择标题模板
                    title_templates = content_type.get('title_templates', ['{keyword} - 指南'])
                    title = title_templates[0].format(
                        keyword=keyword,
                        year=year
                    )
                    
                    # 创建URL友好的标识符
                    page_id = f"{sub_intent.lower()}_{i+1}_{keyword.lower().replace(' ', '_')}"
                    
                    # 创建内容页面
                    content_pages[page_id] = {
                        'type': 'content',
                        'intent': intent,
                        'sub_intent': sub_intent,
                        'keyword': keyword,
                        'title': title,
                        'url': f'/content/{page_id}',
                        'format': content_type.get('formats', ['文章'])[0],
                        'content_structure': content_type.get('content_structure', []),
                        'word_count': self.page_templates.get(intent, {}).get('word_count', 1500),
                        'conversion_strategy': content_type.get('conversion_strategy', '')
                    }
        
        self.website_structure['content_pages'] = content_pages
    
    def _generate_product_pages(self) -> None:
        """生成产品页面"""
        # 查找交易型(E)关键词
        e_keywords = self.intent_summary['intent_keywords'].get('E', [])
        
        # 如果没有交易型关键词，跳过
        if not e_keywords:
            self.website_structure['product_pages'] = {}
            return
        
        # 创建产品页面
        product_pages = {}
        
        # 为前5个交易型关键词创建产品页面
        for i, keyword in enumerate(e_keywords[:5]):
            # 创建URL友好的产品ID
            product_id = f"product_{i+1}_{keyword.lower().replace(' ', '_')}"
            
            # 创建产品页面
            product_pages[product_id] = {
                'type': 'product',
                'keyword': keyword,
                'title': f"{keyword} - 购买指南与最优惠",
                'url': f'/products/{product_id}',
                'sections': [
                    {'type': 'product_info', 'title': f'关于{keyword}'},
                    {'type': 'pricing', 'title': '价格方案'},
                    {'type': 'features', 'title': '主要功能'},
                    {'type': 'reviews', 'title': '用户评价'},
                    {'type': 'cta', 'title': '立即购买'}
                ],
                'seo_priority': 'high'
            }
        
        self.website_structure['product_pages'] = product_pages
    
    def _generate_category_pages(self, year: int) -> None:
        """生成分类页面"""
        # 创建分类页面
        category_pages = {}
        
        # 为每种主要意图创建一个分类页面
        for intent in set(self.intent_data['intent_primary']):
            # 只处理主意图
            if len(intent) != 1:
                continue
                
            intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
            
            # 创建分类页面
            category_pages[intent.lower()] = {
                'type': 'category',
                'intent': intent,
                'title': f"{intent_name}内容 - {year}年精选",
                'url': f'/categories/{intent.lower()}',
                'description': self._get_intent_description(intent),
                'layout': self.page_templates.get(intent, {}).get('layout', 'default'),
                'seo_priority': 'medium'
            }
        
        self.website_structure['category_pages'] = category_pages
    
    def create_content_plan(self) -> List[Dict[str, Any]]:
        """
        创建内容计划
        
        Returns:
            内容计划列表
        """
        if not self.website_structure:
            print("错误: 未生成网站结构")
            return []
        
        print("正在创建基于搜索意图的内容计划...")
        
        # 获取当前日期
        start_date = datetime.now()
        
        # 创建内容计划
        content_plan = []
        
        # 1. 首页内容
        content_plan.append({
            'week': 1,
            'publish_date': start_date.strftime('%Y-%m-%d'),
            'page_type': 'homepage',
            'title': self.website_structure['homepage']['title'],
            'url': '/',
            'priority': 'very_high',
            'word_count': 1000,
            'intent': 'multiple'
        })
        
        # 2. 意图页面内容
        week = 1
        for intent, pages in self.website_structure['intent_pages'].items():
            for page in pages:
                week += 1
                content_plan.append({
                    'week': week,
                    'publish_date': (start_date + timedelta(weeks=week-1)).strftime('%Y-%m-%d'),
                    'page_type': page['type'],
                    'title': page['title'],
                    'url': page['url'],
                    'priority': page['seo_priority'],
                    'word_count': self.page_templates.get(intent, {}).get('word_count', 1500),
                    'intent': intent
                })
        
        # 3. 内容页面
        for page_id, page in self.website_structure['content_pages'].items():
            week += 1
            content_plan.append({
                'week': week,
                'publish_date': (start_date + timedelta(weeks=week-1)).strftime('%Y-%m-%d'),
                'page_type': 'content',
                'title': page['title'],
                'url': page['url'],
                'priority': 'medium',
                'word_count': page['word_count'],
                'intent': page['intent'],
                'sub_intent': page.get('sub_intent', '')
            })
        
        # 4. 产品页面
        for page_id, page in self.website_structure['product_pages'].items():
            week += 1
            content_plan.append({
                'week': week,
                'publish_date': (start_date + timedelta(weeks=week-1)).strftime('%Y-%m-%d'),
                'page_type': 'product',
                'title': page['title'],
                'url': page['url'],
                'priority': 'high',
                'word_count': 2000,
                'intent': 'E'
            })
        
        # 5. 分类页面
        for page_id, page in self.website_structure['category_pages'].items():
            week += 1
            content_plan.append({
                'week': week,
                'publish_date': (start_date + timedelta(weeks=week-1)).strftime('%Y-%m-%d'),
                'page_type': 'category',
                'title': page['title'],
                'url': page['url'],
                'priority': 'medium',
                'word_count': 1000,
                'intent': page['intent']
            })
        
        # 保存内容计划
        self.content_plan = content_plan
        
        # 输出内容计划到文件
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.output_dir, f'content_plan_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(content_plan, f, ensure_ascii=False, indent=2)
        
        print(f"内容计划创建完成，共 {len(content_plan)} 个内容项，已保存到: {output_file}")
        
        return content_plan
    
    def generate_technical_plan(self) -> Dict[str, Any]:
        """
        生成技术实现方案
        
        Returns:
            技术方案字典
        """
        if not self.website_structure:
            print("错误: 未生成网站结构")
            return {}
        
        print("正在生成基于搜索意图的技术实现方案...")
        
        # 获取当前年份
        current_year = datetime.now().year
        
        # 创建技术方案
        tech_plan = {
            'project_name': f'意图驱动内容平台_{current_year}',
            'tech_stack': self.tech_stack,
            'page_templates': {},
            'data_models': [],
            'api_endpoints': [],
            'deployment_steps': []
        }
        
        # 1. 页面模板
        # 为每种意图类型创建页面模板
        for intent, template in self.page_templates.items():

            intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
            
            tech_plan['page_templates'][intent] = {
                'name': f"{intent_name}页面模板",
                'layout': template.get('layout', 'default'),
                'components': [section['type'] for section in template.get('sections', [])],
                'file_path': f'src/templates/{intent.lower()}_template.jsx',
                'data_requirements': [
                    'title',
                    'meta_description',
                    'sections',
                    'keywords',
                    'related_content'
                ]
            }
        
        # 2. 数据模型
        tech_plan['data_models'] = [
            {
                'name': 'Page',
                'fields': [
                    {'name': 'id', 'type': 'uuid', 'primary_key': True},
                    {'name': 'title', 'type': 'string', 'required': True},
                    {'name': 'slug', 'type': 'string', 'required': True, 'unique': True},
                    {'name': 'meta_description', 'type': 'string', 'required': True},
                    {'name': 'content', 'type': 'json', 'required': True},
                    {'name': 'intent_primary', 'type': 'string', 'required': True},
                    {'name': 'intent_secondary', 'type': 'string[]', 'required': False},
                    {'name': 'page_type', 'type': 'string', 'required': True},
                    {'name': 'template', 'type': 'string', 'required': True},
                    {'name': 'seo_priority', 'type': 'string', 'required': True},
                    {'name': 'created_at', 'type': 'timestamp', 'required': True},
                    {'name': 'updated_at', 'type': 'timestamp', 'required': True}
                ]
            },
            {
                'name': 'Keyword',
                'fields': [
                    {'name': 'id', 'type': 'uuid', 'primary_key': True},
                    {'name': 'query', 'type': 'string', 'required': True, 'unique': True},
                    {'name': 'intent_primary', 'type': 'string', 'required': True},
                    {'name': 'sub_intent', 'type': 'string', 'required': False},
                    {'name': 'search_volume', 'type': 'integer', 'required': False},
                    {'name': 'difficulty', 'type': 'float', 'required': False},
                    {'name': 'pages', 'type': 'relation', 'relation': 'Page[]', 'required': False}
                ]
            },
            {
                'name': 'ContentPlan',
                'fields': [
                    {'name': 'id', 'type': 'uuid', 'primary_key': True},
                    {'name': 'title', 'type': 'string', 'required': True},
                    {'name': 'page_id', 'type': 'relation', 'relation': 'Page', 'required': False},
                    {'name': 'publish_date', 'type': 'date', 'required': True},
                    {'name': 'status', 'type': 'string', 'required': True},
                    {'name': 'priority', 'type': 'string', 'required': True},
                    {'name': 'word_count', 'type': 'integer', 'required': True},
                    {'name': 'intent', 'type': 'string', 'required': True},
                    {'name': 'assigned_to', 'type': 'string', 'required': False}
                ]
            }
        ]
        
        # 3. API端点
        tech_plan['api_endpoints'] = [
            {
                'path': '/api/pages',
                'methods': ['GET', 'POST'],
                'description': '获取或创建页面',
                'parameters': {
                    'GET': ['intent', 'page_type', 'limit', 'offset'],
                    'POST': ['title', 'content', 'intent_primary', 'page_type', 'template']
                }
            },
            {
                'path': '/api/pages/:id',
                'methods': ['GET', 'PUT', 'DELETE'],
                'description': '获取、更新或删除特定页面',
                'parameters': {
                    'PUT': ['title', 'content', 'meta_description', 'seo_priority']
                }
            },
            {
                'path': '/api/keywords',
                'methods': ['GET', 'POST'],
                'description': '获取或添加关键词',
                'parameters': {
                    'GET': ['intent', 'limit', 'offset'],
                    'POST': ['query', 'intent_primary', 'sub_intent']
                }
            },
            {
                'path': '/api/content-plan',
                'methods': ['GET', 'POST'],
                'description': '获取或创建内容计划',
                'parameters': {
                    'GET': ['status', 'priority', 'limit', 'offset'],
                    'POST': ['title', 'publish_date', 'priority', 'intent', 'word_count']
                }
            }
        ]
        
        # 4. 部署步骤
        tech_plan['deployment_steps'] = [
            {
                'step': 1,
                'name': '初始化项目',
                'command': 'npx create-next-app@latest intent-based-website --typescript --tailwind --eslint',
                'description': '使用Next.js创建项目基础结构'
            },
            {
                'step': 2,
                'name': '安装依赖',
                'command': 'npm install @supabase/supabase-js contentful swr react-hook-form next-seo schema-dts',
                'description': '安装必要的依赖包'
            },
            {
                'step': 3,
                'name': '设置数据库',
                'command': 'npx supabase init',
                'description': '初始化Supabase项目并创建数据表'
            },
            {
                'step': 4,
                'name': '创建页面模板',
                'description': '根据意图类型创建不同的页面模板'
            },
            {
                'step': 5,
                'name': '实现API路由',
                'description': '创建Next.js API路由处理数据请求'
            },
            {
                'step': 6,
                'name': '部署到Vercel',
                'command': 'vercel deploy',
                'description': '将项目部署到Vercel平台'
            }
        ]
        
        # 5. 文件结构
        tech_plan['file_structure'] = {
            'src': {
                'pages': {
                    'index.tsx': '首页',
                    'intent': {
                        '[intent].tsx': '意图页面',
                        '[subIntent].tsx': '子意图页面'
                    },
                    'keyword': {
                        '[keyword].tsx': '关键词页面'
                    },
                    'content': {
                        '[id].tsx': '内容页面'
                    },
                    'products': {
                        '[id].tsx': '产品页面'
                    },
                    'categories': {
                        '[category].tsx': '分类页面'
                    },
                    'api': {
                        'pages.ts': '页面API',
                        'keywords.ts': '关键词API',
                        'content-plan.ts': '内容计划API'
                    }
                },
                'components': {
                    'layout': {
                        'Layout.tsx': '主布局组件',
                        'Header.tsx': '头部组件',
                        'Footer.tsx': '底部组件',
                        'Sidebar.tsx': '侧边栏组件'
                    },
                    'sections': {
                        'Hero.tsx': '英雄区组件',
                        'ContentBlock.tsx': '内容块组件',
                        'FeatureList.tsx': '特性列表组件',
                        'Comparison.tsx': '对比表组件',
                        'FAQ.tsx': '常见问题组件',
                        'CTABlock.tsx': '号召性用语组件'
                    },
                    'ui': {
                        'Button.tsx': '按钮组件',
                        'Card.tsx': '卡片组件',
                        'Table.tsx': '表格组件',
                        'Modal.tsx': '模态框组件'
                    }
                },
                'templates': {
                    'guide.tsx': '指南模板',
                    'landing.tsx': '落地页模板',
                    'comparison.tsx': '对比页模板',
                    'product.tsx': '产品页模板',
                    'support.tsx': '支持页模板',
                    'local.tsx': '本地页模板'
                },
                'lib': {
                    'supabase.ts': 'Supabase客户端',
                    'contentful.ts': 'Contentful客户端',
                    'seo.ts': 'SEO工具函数',
                    'intent.ts': '意图分析工具'
                },
                'styles': {
                    'globals.css': '全局样式',
                    'components.css': '组件样式'
                }
            },
            'public': {
                'images': '图片资源',
                'icons': '图标资源'
            }
        }
        
        # 保存技术方案
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.output_dir, f'technical_plan_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tech_plan, f, ensure_ascii=False, indent=2)
        
        print(f"技术实现方案生成完成，已保存到: {output_file}")
        
        return tech_plan
    
    def create_seo_strategy(self) -> Dict[str, Any]:
        """
        创建SEO策略
        
        Returns:
            SEO策略字典
        """
        if not self.website_structure or not self.intent_summary:
            print("错误: 未生成网站结构或意图摘要")
            return {}
        
        print("正在创建基于搜索意图的SEO策略...")
        
        # 获取当前年份
        current_year = datetime.now().year
        
        # 创建SEO策略
        seo_strategy = {
            'site_structure': {
                'homepage': '/',
                'intent_pages': {},
                'content_pages': {},
                'product_pages': {},
                'category_pages': {}
            },
            'title_templates': self.seo_config['title_patterns'],
            'meta_description_templates': self.seo_config['meta_description_patterns'],
            'heading_structure': self.seo_config['heading_structure'],
            'schema_markup': self.seo_config['schema_markup'],
            'internal_linking': self.seo_config['internal_linking'],
            'intent_specific_strategies': {},
            'priority_pages': [],
            'content_guidelines': self.seo_config['content_guidelines'],
            'technical_seo': {
                'sitemap': True,
                'robots_txt': True,
                'canonical_urls': True,
                'hreflang': False,
                'mobile_friendly': True,
                'page_speed': {
                    'image_optimization': True,
                    'code_minification': True,
                    'browser_caching': True,
                    'lazy_loading': True
                },
                'structured_data': True
            }
        }
        
        # 1. 网站结构
        # 添加意图页面到网站结构
        for intent, pages in self.website_structure['intent_pages'].items():
            seo_strategy['site_structure']['intent_pages'][intent] = [
                page['url'] for page in pages
            ]
        
        # 2. 意图特定策略
        # 为每种主要意图创建特定的SEO策略
        for intent in set(self.intent_data['intent_primary']):
            # 只处理主意图
            if len(intent) != 1:
                continue
                
            intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
            
            # 获取该意图的关键词
            keywords = self.intent_summary['intent_keywords'].get(intent, [])
            
            # 创建意图特定策略
            seo_strategy['intent_specific_strategies'][intent] = {
                'intent_name': intent_name,
                'title_pattern': self.seo_config['title_patterns'].get(intent, '{keyword} - {year}'),
                'meta_description': self.seo_config['meta_description_patterns'].get(intent, ''),
                'schema_type': self.seo_config['schema_markup'].get(intent, 'WebPage'),
                'content_focus': self._get_intent_content_focus(intent),
                'keyword_strategy': self._get_intent_keyword_strategy(intent),
                'top_keywords': keywords[:10] if keywords else [],
                'competitor_analysis': self._get_intent_competitor_analysis(intent),
                'conversion_strategy': self._get_intent_conversion_strategy(intent)
            }
        
        # 3. 优先级页面
        # 根据SEO优先级排序页面
        priority_pages = []
        
        # 添加首页
        priority_pages.append({
            'url': '/',
            'title': self.website_structure['homepage']['title'],
            'priority': 'very_high',
            'intent': 'multiple'
        })
        
        # 添加意图页面
        for intent, pages in self.website_structure['intent_pages'].items():
            for page in pages:
                priority_pages.append({
                    'url': page['url'],
                    'title': page['title'],
                    'priority': page['seo_priority'],
                    'intent': intent
                })
        
        # 添加内容页面
        for page_id, page in self.website_structure['content_pages'].items():
            priority_pages.append({
                'url': page['url'],
                'title': page['title'],
                'priority': 'medium',
                'intent': page['intent']
            })
        
        # 添加产品页面
        for page_id, page in self.website_structure['product_pages'].items():
            priority_pages.append({
                'url': page['url'],
                'title': page['title'],
                'priority': 'high',
                'intent': 'E'
            })
        
        # 按优先级排序
        priority_map = {
            'very_high': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }
        
        priority_pages.sort(key=lambda x: priority_map.get(x['priority'], 0), reverse=True)
        
        # 添加到策略
        seo_strategy['priority_pages'] = priority_pages[:20]  # 只保留前20个高优先级页面
        
        # 4. 内部链接策略
        seo_strategy['internal_linking_plan'] = self._generate_internal_linking_plan()
        
        # 保存SEO策略
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.output_dir, f'seo_strategy_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(seo_strategy, f, ensure_ascii=False, indent=2)
        
        print(f"SEO策略创建完成，已保存到: {output_file}")
        
        return seo_strategy
    
    def _get_intent_content_focus(self, intent: str) -> List[str]:
        """获取意图内容重点"""
        content_focus = {
            'I': ['详细解释', '步骤指南', '示例代码', '常见问题', '相关资源'],
            'N': ['官方链接', '安全提示', '功能概述', '使用场景', '替代选择'],
            'C': ['对比表格', '优缺点分析', '专家评测', '用户评价', '最佳推荐'],
            'E': ['价格信息', '折扣优惠', '购买流程', '售后保障', '用户评价'],
            'B': ['问题解决', '高级技巧', '常见错误', '配置指南', '更新信息'],
            'L': ['位置地图', '营业时间', '联系方式', '到店路线', '用户评价']
        }
        return content_focus.get(intent, ['详细内容', '用户价值', '相关资源'])
    
    def _get_intent_keyword_strategy(self, intent: str) -> Dict[str, Any]:
        """获取意图关键词策略"""
        strategies = {
            'I': {
                'primary_patterns': ['什么是{keyword}', '{keyword}教程', '{keyword}指南', '如何使用{keyword}'],
                'secondary_patterns': ['{keyword}例子', '{keyword}原理', '{keyword}vs', '{keyword}常见问题'],
                'keyword_density': {'title': 1, 'h1': 1, 'h2': 2, 'body': '1-2%'},
                'long_tail_focus': True
            },
            'N': {
                'primary_patterns': ['{keyword}官网', '{keyword}登录', '{keyword}下载', '{keyword}入口'],
                'secondary_patterns': ['{keyword}安全', '{keyword}官方', '{keyword}最新版', '{keyword}app'],
                'keyword_density': {'title': 1, 'h1': 1, 'h2': 1, 'body': '0.5-1%'},
                'long_tail_focus': False
            },
            'C': {
                'primary_patterns': ['{keyword}推荐', '{keyword}排行榜', '{keyword}对比', '{keyword}评测'],
                'secondary_patterns': ['{keyword}哪个好', '{keyword}性价比', '{keyword}测评', '最好的{keyword}'],
                'keyword_density': {'title': 1, 'h1': 1, 'h2': 3, 'body': '1-2%'},
                'long_tail_focus': True
            },
            'E': {
                'primary_patterns': ['{keyword}价格', '{keyword}优惠', '{keyword}购买', '{keyword}多少钱'],
                'secondary_patterns': ['{keyword}折扣', '{keyword}促销', '{keyword}特价', '{keyword}团购'],
                'keyword_density': {'title': 1, 'h1': 1, 'h2': 2, 'body': '1-2%'},
                'long_tail_focus': True
            },
            'B': {
                'primary_patterns': ['{keyword}问题', '{keyword}故障', '{keyword}设置', '{keyword}使用技巧'],
                'secondary_patterns': ['{keyword}报错', '{keyword}解决方法', '{keyword}配置', '{keyword}高级用法'],
                'keyword_density': {'title': 1, 'h1': 1, 'h2': 3, 'body': '1-2%'},
                'long_tail_focus': True
            },
            'L': {
                'primary_patterns': ['{keyword}地址', '{keyword}位置', '{keyword}营业时间', '{keyword}预约'],
                'secondary_patterns': ['{keyword}附近', '{keyword}怎么去', '{keyword}电话', '{keyword}地图'],
                'keyword_density': {'title': 1, 'h1': 1, 'h2': 2, 'body': '1-2%'},
                'long_tail_focus': True
            }
        }
        return strategies.get(intent, {
            'primary_patterns': ['{keyword}', '关于{keyword}', '{keyword}详情'],
            'secondary_patterns': ['{keyword}介绍', '{keyword}信息', '{keyword}内容'],
            'keyword_density': {'title': 1, 'h1': 1, 'h2': 2, 'body': '1-2%'},
            'long_tail_focus': True
        })
    
    def _get_intent_competitor_analysis(self, intent: str) -> Dict[str, Any]:
        """获取意图竞争对手分析策略"""
        analysis = {
            'I': {
                'competitor_types': ['教育网站', '博客', '文档网站', '问答平台'],
                'differentiation': '提供更详细、更结构化的教程和指南',
                'content_gap': '实际案例和应用场景'
            },
            'N': {
                'competitor_types': ['官方网站', '导航站', '下载站'],
                'differentiation': '提供更安全、更直接的官方入口',
                'content_gap': '安全提示和使用建议'
            },
            'C': {
                'competitor_types': ['评测网站', '电商平台', '专业媒体'],
                'differentiation': '提供更客观、更全面的对比和评测',
                'content_gap': '详细的参数对比和使用场景分析'
            },
            'E': {
                'competitor_types': ['电商平台', '优惠券网站', '价格对比网站'],
                'differentiation': '提供更全面的价格信息和购买建议',
                'content_gap': '隐藏成本和长期价值分析'
            },
            'B': {
                'competitor_types': ['官方支持网站', '论坛', '问答平台'],
                'differentiation': '提供更系统、更易懂的问题解决方案',
                'content_gap': '常见问题的根本原因分析'
            },
            'L': {
                'competitor_types': ['地图应用', '本地目录网站', '商家官网'],
                'differentiation': '提供更详细的位置信息和到店指南',
                'content_gap': '用户实际到店体验分享'
            }
        }
        return analysis.get(intent, {
            'competitor_types': ['综合网站', '专业网站', '社交媒体'],
            'differentiation': '提供更有针对性的内容',
            'content_gap': '用户实际需求分析'
        })
    
    def _get_intent_conversion_strategy(self, intent: str) -> Dict[str, Any]:
        """获取意图转化策略"""
        strategies = {
            'I': {
                'primary_cta': '深入学习',
                'secondary_cta': '下载资源',
                'conversion_goals': ['课程注册', '电子书下载', '订阅通讯'],
                'user_journey': ['了解概念', '学习基础', '掌握技能', '应用实践']
            },
            'N': {
                'primary_cta': '安全访问',
                'secondary_cta': '了解更多',
                'conversion_goals': ['官网跳转', '应用下载', '账户注册'],
                'user_journey': ['寻找入口', '确认安全性', '访问官网', '完成目标']
            },
            'C': {
                'primary_cta': '查看详情',
                'secondary_cta': '对比全部',
                'conversion_goals': ['产品详情查看', '对比工具使用', '购买链接点击'],
                'user_journey': ['浏览选项', '对比功能', '阅读评测', '做出决策']
            },
            'E': {
                'primary_cta': '立即购买',
                'secondary_cta': '查看优惠',
                'conversion_goals': ['加入购物车', '完成购买', '优惠券使用'],
                'user_journey': ['了解产品', '比较价格', '查找优惠', '完成购买']
            },
            'B': {
                'primary_cta': '解决问题',
                'secondary_cta': '获取支持',
                'conversion_goals': ['问题解决', '支持服务购买', '社区参与'],
                'user_journey': ['发现问题', '寻找解决方案', '应用解决方法', '问题解决']
            },
            'L': {
                'primary_cta': '查看位置',
                'secondary_cta': '立即预约',
                'conversion_goals': ['地图查看', '路线规划', '预约完成'],
                'user_journey': ['查找位置', '了解服务', '规划路线', '到店体验']
            }
        }
        return strategies.get(intent, {
            'primary_cta': '了解更多',
            'secondary_cta': '立即行动',
            'conversion_goals': ['内容阅读', '互动参与', '转化行动'],
            'user_journey': ['发现内容', '了解详情', '评估价值', '采取行动']
        })
    
    def _generate_internal_linking_plan(self) -> Dict[str, Any]:
        """生成内部链接计划"""
        # 创建内部链接计划
        linking_plan = {
            'homepage_links': [],
            'intent_page_links': {},
            'content_page_links': {},
            'cross_intent_links': []
        }
        
        # 1. 首页链接
        # 首页链接到各个意图页面
        for intent in self.website_structure['intent_pages'].keys():
            intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
            linking_plan['homepage_links'].append({
                'from': '/',
                'to': f'/intent/{intent.lower()}',
                'anchor_text': f'{intent_name}内容',
                'context': '意图导航区域'
            })
        
        # 2. 意图页面链接
        # 每个意图页面链接到其子意图页面和关键词页面
        for intent, pages in self.website_structure['intent_pages'].items():
            linking_plan['intent_page_links'][intent] = []
            
            # 获取意图总览页面
            overview_page = next((p for p in pages if p['type'] == 'intent_overview'), None)
            if not overview_page:
                continue
                
            # 链接到子意图页面
            sub_intent_pages = [p for p in pages if p['type'] == 'sub_intent']
            for sub_page in sub_intent_pages:
                linking_plan['intent_page_links'][intent].append({
                    'from': overview_page['url'],
                    'to': sub_page['url'],
                    'anchor_text': sub_page['intent_name'],
                    'context': '子意图导航区域'
                })
            
            # 链接到关键词页面
            keyword_pages = [p for p in pages if p['type'] == 'keyword']
            for keyword_page in keyword_pages:
                linking_plan['intent_page_links'][intent].append({
                    'from': overview_page['url'],
                    'to': keyword_page['url'],
                    'anchor_text': keyword_page['keyword'],
                    'context': '热门关键词区域'
                })
        
        # 3. 内容页面链接
        # 每个内容页面链接到相关内容页面
        for page_id, page in self.website_structure['content_pages'].items():
            intent = page['intent']
            sub_intent = page.get('sub_intent', '')
            
            # 查找同一子意图的其他内容页面
            related_pages = [
                p for pid, p in self.website_structure['content_pages'].items()
                if pid != page_id and p.get('sub_intent', '') == sub_intent
            ]
            
            linking_plan['content_page_links'][page_id] = []
            
            # 添加相关内容链接
            for related_page in related_pages[:3]:  # 最多添加3个相关链接
                linking_plan['content_page_links'][page_id].append({
                    'from': page['url'],
                    'to': related_page['url'],
                    'anchor_text': related_page['keyword'],
                    'context': '相关内容区域'
                })
        
        # 4. 跨意图链接
        # 创建不同意图之间的链接
        intent_pairs = [
            ('I', 'C'),  # 信息获取 -> 商业评估
            ('C', 'E'),  # 商业评估 -> 交易购买
            ('I', 'B'),  # 信息获取 -> 行为后续
            ('N', 'E'),  # 导航直达 -> 交易购买
            ('B', 'I')   # 行为后续 -> 信息获取
        ]
        
        for intent1, intent2 in intent_pairs:
            # 获取两种意图的页面
            pages1 = self.website_structure['intent_pages'].get(intent1, [])
            pages2 = self.website_structure['intent_pages'].get(intent2, [])
            
            if not pages1 or not pages2:
                continue
                
            # 为每个意图选择一个代表页面
            page1 = next((p for p in pages1 if p['type'] == 'intent_overview'), None)
            page2 = next((p for p in pages2 if p['type'] == 'intent_overview'), None)
            
            if not page1 or not page2:
                continue
                
            # 创建跨意图链接
            linking_plan['cross_intent_links'].append({
                'from': page1['url'],
                'to': page2['url'],
                'anchor_text': page2['intent_name'],
                'context': '相关意图区域'
            })
        
        return linking_plan
    
    def generate_complete_plan(self) -> Dict[str, Any]:
        """
        生成完整的网站建设计划
        
        Returns:
            完整计划字典
        """
        if not self.intent_data:
            print("错误: 未加载意图数据")
            return {}
        
        print("正在生成基于搜索意图的完整网站建设计划...")
        
        # 1. 生成网站结构
        self.generate_website_structure()
        
        # 2. 创建内容计划
        content_plan = self.create_content_plan()
        
        # 3. 生成技术实现方案
        tech_plan = self.generate_technical_plan()
        
        # 4. 创建SEO策略
        seo_strategy = self.create_seo_strategy()
        
        # 创建完整计划
        timestamp = datetime.now().strftime('%Y-%m-%d')
        complete_plan = {
            'project_name': f'基于搜索意图的网站_{timestamp}',
            'generated_date': timestamp,
            'summary': {
                'total_pages': (
                    1 +  # 首页
                    sum(len(pages) for pages in self.website_structure['intent_pages'].values()) +
                    len(self.website_structure['content_pages']) +
                    len(self.website_structure['product_pages']) +
                    len(self.website_structure['category_pages'])
                ),
                'intent_distribution': self.intent_summary['intent_percentages'],
                'content_plan_weeks': len(content_plan),
                'priority_pages': len(seo_strategy['priority_pages'])
            },
            'website_structure': self.website_structure,
            'content_plan': content_plan,
            'tech_plan': tech_plan,
            'seo_strategy': seo_strategy,
            'implementation_timeline': self._generate_implementation_timeline(content_plan)
        }
        
        # 保存完整计划
        output_file = os.path.join(self.output_dir, f'complete_plan_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(complete_plan, f, ensure_ascii=False, indent=2)
        
        print(f"完整网站建设计划生成完成，已保存到: {output_file}")
        
        return complete_plan
    
    def _generate_implementation_timeline(self, content_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成实施时间线"""
        # 创建实施时间线
        timeline = {
            'phases': [
                {
                    'phase': 1,
                    'name': '规划与设计',
                    'duration': '2周',
                    'tasks': [
                        {'task': '确定网站结构', 'duration': '3天'},
                        {'task': '设计页面模板', 'duration': '5天'},
                        {'task': '创建内容计划', 'duration': '2天'},
                        {'task': '制定SEO策略', 'duration': '2天'},
                        {'task': '技术栈选择', 'duration': '2天'}
                    ]
                },
                {
                    'phase': 2,
                    'name': '技术实现',
                    'duration': '4周',
                    'tasks': [
                        {'task': '搭建项目框架', 'duration': '1周'},
                        {'task': '实现页面模板', 'duration': '1周'},
                        {'task': '开发API接口', 'duration': '1周'},
                        {'task': '集成数据库', 'duration': '3天'},
                        {'task': '实现SEO功能', 'duration': '3天'}
                    ]
                },
                {
                    'phase': 3,
                    'name': '内容创建',
                    'duration': f'{len(content_plan) // 5}周',
                    'tasks': [
                        {'task': '首页内容', 'duration': '1周'},
                        {'task': '意图页面内容', 'duration': '2周'},
                        {'task': '内容页面创建', 'duration': f'{len(content_plan) // 10}周'},
                        {'task': '产品页面创建', 'duration': '2周'},
                        {'task': '内容优化与审核', 'duration': '2周'}
                    ]
                },
                {
                    'phase': 4,
                    'name': '测试与部署',
                    'duration': '2周',
                    'tasks': [
                        {'task': '功能测试', 'duration': '3天'},
                        {'task': '性能优化', 'duration': '3天'},
                        {'task': 'SEO检查', 'duration': '2天'},
                        {'task': '部署准备', 'duration': '2天'},
                        {'task': '上线部署', 'duration': '2天'}
                    ]
                },
                {
                    'phase': 5,
                    'name': '监控与优化',
                    'duration': '持续',
                    'tasks': [
                        {'task': '流量监控', 'duration': '持续'},
                        {'task': '用户行为分析', 'duration': '持续'},
                        {'task': '内容更新', 'duration': '持续'},
                        {'task': 'SEO优化', 'duration': '持续'},
                        {'task': '性能监控', 'duration': '持续'}
                    ]
                }
            ],
            'milestones': [
                {'name': '网站结构确定', 'date': '第2周末'},
                {'name': '技术框架搭建完成', 'date': '第6周末'},
                {'name': '首批内容上线', 'date': '第10周末'},
                {'name': '全站内容完成', 'date': f'第{10 + len(content_plan) // 5}周末'},
                {'name': '网站正式上线', 'date': f'第{12 + len(content_plan) // 5}周末'}
            ],
            'resources': {
                'development': {
                    'frontend_developer': 2,
                    'backend_developer': 1,
                    'designer': 1
                },
                'content': {
                    'content_writer': 2,
                    'seo_specialist': 1,
                    'editor': 1
                },
                'management': {
                    'project_manager': 1,
                    'product_owner': 1
                }
            }
        }
        
        return timeline


def main():
    """主函数"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='基于搜索意图的网站自动建设工具')
    
    # 添加命令行参数
    parser.add_argument('--input', '-i', type=str, help='输入文件路径（CSV或JSON）')
    parser.add_argument('--output', '-o', type=str, default='output', help='输出目录路径')
    parser.add_argument('--keywords', '-k', type=str, help='关键词列表文件（每行一个关键词）')
    parser.add_argument('--action', '-a', type=str, choices=['analyze', 'structure', 'content', 'tech', 'seo', 'all'], 
                        default='all', help='执行的操作')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 检查必要参数
    if not args.input and not args.keywords:
        parser.error("必须提供输入文件(--input)或关键词列表文件(--keywords)")
    
    # 创建网站建设工具实例
    builder = IntentBasedWebsiteBuilder(
        intent_data_path=args.input,
        output_dir=args.output
    )
    
    # 根据操作类型执行相应功能
    if args.keywords:
        # 从文件加载关键词
        try:
            with open(args.keywords, 'r', encoding='utf-8') as f:
                keywords = [line.strip() for line in f if line.strip()]
            
            print(f"已从文件加载 {len(keywords)} 个关键词")
            
            # 分析关键词
            builder.analyze_keywords(keywords)
        except Exception as e:
            print(f"加载或分析关键词失败: {e}")
            return
    else:
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
    
    if args.action == 'tech' or args.action == 'all':
        # 生成技术实现方案
        builder.generate_technical_plan()
    
    if args.action == 'seo' or args.action == 'all':
        # 创建SEO策略
        builder.create_seo_strategy()
    
    if args.action == 'all':
        # 生成完整计划
        builder.generate_complete_plan()
    
    print("操作完成")


if __name__ == "__main__":
    main()
        
        # 1. 页面模板
        # 为每种意图类型创建页面模板
        for intent, template in self.page_templates.items():

            intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
            
            tech_plan['page_templates'][intent] = {
                'name': f"{intent_name}页面模板",
                'layout': template.get('layout', 'default'),
                'components': [section['type'] for section in template.get('sections', [])],
                'file_path': f'src/templates/{intent.lower()}_template.jsx',
                'data_requirements': [
                    'title',
                    'meta_description',
                    'sections',
                    'keywords',
                    'related_content'
                ]
            }
        
        # 2. 数据模型
        tech_plan['data_models'] = [
            {
                'name': 'Page',
                'fields': [
                    {'name': 'id', 'type': 'uuid', 'primary_key': True},
                    {'name': 'title', 'type': 'string', 'required': True},
                    {'name': 'slug', 'type': 'string', 'required': True, 'unique': True},
                    {'name': 'meta_description', 'type': 'string', 'required': True},
                    {'name': 'content', 'type': 'json', 'required': True},
                    {'name': 'intent_primary', 'type': 'string', 'required': True},
                    {'name': 'intent_secondary', 'type': 'string[]', 'required': False},
                    {'name': 'page_type', 'type': 'string', 'required': True},
                    {'name': 'template', 'type': 'string', 'required': True},
                    {'name': 'seo_priority', 'type': 'string', 'required': True},
                    {'name': 'created_at', 'type': 'timestamp', 'required': True},
                    {'name': 'updated_at', 'type': 'timestamp', 'required': True}
                ]
            },
            {
                'name': 'Keyword',
                'fields': [
                    {'name': 'id', 'type': 'uuid', 'primary_key': True},
                    {'name': 'query', 'type': 'string', 'required': True, 'unique': True},
                    {'name': 'intent_primary', 'type': 'string', 'required': True},
                    {'name': 'sub_intent', 'type': 'string', 'required': False},
                    {'name': 'search_volume', 'type': 'integer', 'required': False},
                    {'name': 'difficulty', 'type': 'float', 'required': False},
                    {'name': 'pages', 'type': 'relation', 'relation': 'Page[]', 'required': False}
                ]
            },
            {
                'name': 'ContentPlan',
                'fields': [
                    {'name': 'id', 'type': 'uuid', 'primary_key': True},
                    {'name': 'title', 'type': 'string', 'required': True},
                    {'name': 'page_id', 'type': 'relation', 'relation': 'Page', 'required': False},
                    {'name': 'publish_date', 'type': 'date', 'required': True},
                    {'name': 'status', 'type': 'string', 'required': True},
                    {'name': 'priority', 'type': 'string', 'required': True},
                    {'name': 'word_count', 'type': 'integer', 'required': True},
                    {'name': 'intent', 'type': 'string', 'required': True},
                    {'name': 'assigned_to', 'type': 'string', 'required': False}
                ]
            }
        ]
        
        # 3. API端点
        tech_plan['api_endpoints'] = [
            {
                'path': '/api/pages',
                'methods': ['GET', 'POST'],
                'description': '获取或创建页面',
                'parameters': {
                    'GET': ['intent', 'page_type', 'limit', 'offset'],
                    'POST': ['title', 'content', 'intent_primary', 'page_type', 'template']
                }
            },
            {
                'path': '/api/pages/:id',
                'methods': ['GET', 'PUT', 'DELETE'],
                'description': '获取、更新或删除特定页面',
                'parameters': {
                    'PUT': ['title', 'content', 'meta_description', 'seo_priority']
                }
            },
            {
                'path': '/api/keywords',
                'methods': ['GET', 'POST'],
                'description': '获取或添加关键词',
                'parameters': {
                    'GET': ['intent', 'limit', 'offset'],
                    'POST': ['query', 'intent_primary', 'sub_intent']
                }
            },
            {
                'path': '/api/content-plan',
                'methods': ['GET', 'POST'],
                'description': '获取或创建内容计划',
                'parameters': {
                    'GET': ['status', 'priority', 'limit', 'offset'],
                    'POST': ['title', 'publish_date', 'priority', 'intent', 'word_count']
                }
            }
        ]
        
        # 4. 部署步骤
        tech_plan['deployment_steps'] = [
            {
                'step': 1,
                'name': '初始化项目',
                'command': 'npx create-next-app@latest intent-based-website --typescript --tailwind --eslint',
                'description': '使用Next.js创建项目基础结构'
            },
            {
                'step': 2,
                'name': '安装依赖',
                'command': 'npm install @supabase/supabase-js contentful swr react-hook-form next-seo schema-dts',
                'description': '安装必要的依赖包'
            },
            {
                'step': 3,
                'name': '设置数据库',
                'command': 'npx supabase init',
                'description': '初始化Supabase项目并创建数据表'
            },
            {
                'step': 4,
                'name': '创建页面模板',
                'description': '根据意图类型创建不同的页面模板'
            },
            {
                'step': 5,
                'name': '实现API路由',
                'description': '创建Next.js API路由处理数据请求'
            },
            {
                'step': 6,
                'name': '部署到Vercel',
                'command': 'vercel deploy',
                'description': '将项目部署到Vercel平台'
            }
        ]
        
        # 5. 文件结构
        tech_plan['file_structure'] = {
            'src': {
                'pages': {
                    'index.tsx': '首页',
                    'intent': {
                        '[intent].tsx': '意图页面',
                        '[subIntent].tsx': '子意图页面'
                    },
                    'keyword': {
                        '[keyword].tsx': '关键词页面'
                    },
                    'content': {
                        '[id].tsx': '内容页面'
                    },
                    'products': {
                        '[id].tsx': '产品页面'
                    },
                    'categories': {
                        '[category].tsx': '分类页面'
                    },
                    'api': {
                        'pages.ts': '页面API',
                        'keywords.ts': '关键词API',
                        'content-plan.ts': '内容计划API'
                    }
                },
                'components': {
                    'layout': {
                        'Layout.tsx': '主布局组件',
                        'Header.tsx': '头部组件',
                        'Footer.tsx': '底部组件',
                        'Sidebar.tsx': '侧边栏组件'
                    },
                    'sections': {
                        'Hero.tsx': '英雄区组件',
                        'ContentBlock.tsx': '内容块组件',
                        'FeatureList.tsx': '特性列表组件',
                        'Comparison.tsx': '对比表组件',
                        'FAQ.tsx': '常见问题组件',
                        'CTABlock.tsx': '号召性用语组件'
                    },
                    'ui': {
                        'Button.tsx': '按钮组件',
                        'Card.tsx': '卡片组件',
                        'Table.tsx': '表格组件',
                        'Modal.tsx': '模态框组件'
                    }
                },
                'templates': {
                    'guide.tsx': '指南模板',
                    'landing.tsx': '落地页模板',
                    'comparison.tsx': '对比页模板',
                    'product.tsx': '产品页模板',
                    'support.tsx': '支持页模板',
                    'local.tsx': '本地页模板'
                },
                'lib': {
                    'supabase.ts': 'Supabase客户端',
                    'contentful.ts': 'Contentful客户端',
                    'seo.ts': 'SEO工具函数',
                    'intent.ts': '意图分析工具'
                },
                'styles': {
                    'globals.css': '全局样式',
                    'components.css': '组件样式'
                }
            },
            'public': {
                'images': '图片资源',
                'icons': '图标资源'
            }
        }
        
        # 保存技术方案
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.output_dir, f'technical_plan_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tech_plan, f, ensure_ascii=False, indent=2)
        
        print(f"技术实现方案生成完成，已保存到: {output_file}")
        
        return tech_plan
    
    def create_seo_strategy(self) -> Dict[str, Any]:
        """
        创建SEO策略
        
        Returns:
            SEO策略字典
        """
        if not self.website_structure or not self.intent_summary:
            print("错误: 未生成网站结构或意图摘要")
            return {}
        
        print("正在创建基于搜索意图的SEO策略...")
        
        # 获取当前年份
        current_year = datetime.now().year
        
        # 创建SEO策略
        seo_strategy = {
            'site_structure': {
                'homepage': '/',
                'intent_pages': {},
                'content_pages': {},
                'product_pages': {},
                'category_pages': {}
            },
            'title_templates': self.seo_config['title_patterns'],
            'meta_description_templates': self.seo_config['meta_description_patterns'],
            'heading_structure': self.seo_config['heading_structure'],
            'schema_markup': self.seo_config['schema_markup'],
            'internal_linking': self.seo_config['internal_linking'],
            'intent_specific_strategies': {},
            'priority_pages': [],
            'content_guidelines': self.seo_config['content_guidelines'],
            'technical_seo': {
                'sitemap': True,
                'robots_txt': True,
                'canonical_urls': True,
                'hreflang': False,
                'mobile_friendly': True,
                'page_speed': {
                    'image_optimization': True,
                    'code_minification': True,
                    'browser_caching': True,
                    'lazy_loading': True
                },
                'structured_data': True
            }
        }
        
        # 1. 网站结构
        # 添加意图页面到网站结构
        for intent, pages in self.website_structure['intent_pages'].items():
            seo_strategy['site_structure']['intent_pages'][intent] = [
                page['url'] for page in pages
            ]
        
        # 2. 意图特定策略
        # 为每种主要意图创建特定的SEO策略
        for intent in set(self.intent_data['intent_primary']):
            # 只处理主意图
            if len(intent) != 1:
                continue
                
            intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
            
            # 获取该意图的关键词
            keywords = self.intent_summary['intent_keywords'].get(intent, [])
            
            # 创建意图特定策略
            seo_strategy['intent_specific_strategies'][intent] = {
                'intent_name': intent_name,
                'title_pattern': self.seo_config['title_patterns'].get(intent, '{keyword} - {year}'),
                'meta_description': self.seo_config['meta_description_patterns'].get(intent, ''),
                'schema_type': self.seo_config['schema_markup'].get(intent, 'WebPage'),
                'content_focus': self._get_intent_content_focus(intent),
                'keyword_strategy': self._get_intent_keyword_strategy(intent),
                'top_keywords': keywords[:10] if keywords else [],
                'competitor_analysis': self._get_intent_competitor_analysis(intent),
                'conversion_strategy': self._get_intent_conversion_strategy(intent)
            }
        
        # 3. 优先级页面
        # 根据SEO优先级排序页面
        priority_pages = []
        
        # 添加首页
        priority_pages.append({
            'url': '/',
            'title': self.website_structure['homepage']['title'],
            'priority': 'very_high',
            'intent': 'multiple'
        })
        
        # 添加意图页面
        for intent, pages in self.website_structure['intent_pages'].items():
            for page in pages:
                priority_pages.append({
                    'url': page['url'],
                    'title': page['title'],
                    'priority': page['seo_priority'],
                    'intent': intent
                })
        
        # 添加内容页面
        for page_id, page in self.website_structure['content_pages'].items():
            priority_pages.append({
                'url': page['url'],
                'title': page['title'],
                'priority': 'medium',
                'intent': page['intent']
            })
        
        # 添加产品页面
        for page_id, page in self.website_structure['product_pages'].items():
            priority_pages.append({
                'url': page['url'],
                'title': page['title'],
                'priority': 'high',
                'intent': 'E'
            })
        
        # 按优先级排序
        priority_map = {
            'very_high': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }
        
        priority_pages.sort(key=lambda x: priority_map.get(x['priority'], 0), reverse=True)
        
        # 添加到策略
        seo_strategy['priority_pages'] = priority_pages[:20]  # 只保留前20个高优先级页面
        
        # 4. 内部链接策略
        seo_strategy['internal_linking_plan'] = self._generate_internal_linking_plan()
        
        # 保存SEO策略
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.output_dir, f'seo_strategy_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(seo_strategy, f, ensure_ascii=False, indent=2)
        
        print(f"SEO策略创建完成，已保存到: {output_file}")
        
        return seo_strategy
    
    def _get_intent_content_focus(self, intent: str) -> List[str]:
        """获取意图内容重点"""
        content_focus = {
            'I': ['详细解释', '步骤指南', '示例代码', '常见问题', '相关资源'],
            'N': ['官方链接', '安全提示', '功能概述', '使用场景', '替代选择'],
            'C': ['对比表格', '优缺点分析', '专家评测', '用户评价', '最佳推荐'],
            'E': ['价格信息', '折扣优惠', '购买流程', '售后保障', '用户评价'],
            'B': ['问题解决', '高级技巧', '常见错误', '配置指南', '更新信息'],
            'L': ['位置地图', '营业时间', '联系方式', '到店路线', '用户评价']
        }
        return content_focus.get(intent, ['详细内容', '用户价值', '相关资源'])
    
    def _get_intent_keyword_strategy(self, intent: str) -> Dict[str, Any]:
        """获取意图关键词策略"""
        strategies = {
            'I': {
                'primary_patterns': ['什么是{keyword}', '{keyword}教程', '{keyword}指南', '如何使用{keyword}'],
                'secondary_patterns': ['{keyword}例子', '{keyword}原理', '{keyword}vs', '{keyword}常见问题'],
                'keyword_density': {'title': 1, 'h1': 1, 'h2': 2, 'body': '1-2%'},
                'long_tail_focus': True
            },
            'N': {
                'primary_patterns': ['{keyword}官网', '{keyword}登录', '{keyword}下载', '{keyword}入口'],
                'secondary_patterns': ['{keyword}安全', '{keyword}官方', '{keyword}最新版', '{keyword}app'],
                'keyword_density': {'title': 1, 'h1': 1, 'h2': 1, 'body': '0.5-1%'},
                'long_tail_focus': False
            },
            'C': {
                'primary_patterns': ['{keyword}推荐', '{keyword}排行榜', '{keyword}对比', '{keyword}评测'],
                'secondary_patterns': ['{keyword}哪个好', '{keyword}性价比', '{keyword}测评', '最好的{keyword}'],
                'keyword_density': {'title': 1, 'h1': 1, 'h2': 3, 'body': '1-2%'},
                'long_tail_focus': True
            },
            'E': {
                'primary_patterns': ['{keyword}价格', '{keyword}优惠', '{keyword}购买', '{keyword}多少钱'],
                'secondary_patterns': ['{keyword}折扣', '{keyword}促销', '{keyword}特价', '{keyword}团购'],
                'keyword_density': {'title': 1, 'h1': 1, 'h2': 2, 'body': '1-2%'},
                'long_tail_focus': True
            },
            'B': {
                'primary_patterns': ['{keyword}问题', '{keyword}故障', '{keyword}设置', '{keyword}使用技巧'],
                'secondary_patterns': ['{keyword}报错', '{keyword}解决方法', '{keyword}配置', '{keyword}高级用法'],
                'keyword_density': {'title': 1, 'h1': 1, 'h2': 3, 'body': '1-2%'},
                'long_tail_focus': True
            },
            'L': {
                'primary_patterns': ['{keyword}地址', '{keyword}位置', '{keyword}营业时间', '{keyword}预约'],
                'secondary_patterns': ['{keyword}附近', '{keyword}怎么去', '{keyword}电话', '{keyword}地图'],
                'keyword_density': {'title': 1, 'h1': 1, 'h2': 2, 'body': '1-2%'},
                'long_tail_focus': True
            }
        }
        return strategies.get(intent, {
            'primary_patterns': ['{keyword}', '关于{keyword}', '{keyword}详情'],
            'secondary_patterns': ['{keyword}介绍', '{keyword}信息', '{keyword}内容'],
            'keyword_density': {'title': 1, 'h1': 1, 'h2': 2, 'body': '1-2%'},
            'long_tail_focus': True
        })
    
    def _get_intent_competitor_analysis(self, intent: str) -> Dict[str, Any]:
        """获取意图竞争对手分析策略"""
        analysis = {
            'I': {
                'competitor_types': ['教育网站', '博客', '文档网站', '问答平台'],
                'differentiation': '提供更详细、更结构化的教程和指南',
                'content_gap': '实际案例和应用场景'
            },
            'N': {
                'competitor_types': ['官方网站', '导航站', '下载站'],
                'differentiation': '提供更安全、更直接的官方入口',
                'content_gap': '安全提示和使用建议'
            },
            'C': {
                'competitor_types': ['评测网站', '电商平台', '专业媒体'],
                'differentiation': '提供更客观、更全面的对比和评测',
                'content_gap': '详细的参数对比和使用场景分析'
            },
            'E': {
                'competitor_types': ['电商平台', '优惠券网站', '价格对比网站'],
                'differentiation': '提供更全面的价格信息和购买建议',
                'content_gap': '隐藏成本和长期价值分析'
            },
            'B': {
                'competitor_types': ['官方支持网站', '论坛', '问答平台'],
                'differentiation': '提供更系统、更易懂的问题解决方案',
                'content_gap': '常见问题的根本原因分析'
            },
            'L': {
                'competitor_types': ['地图应用', '本地目录网站', '商家官网'],
                'differentiation': '提供更详细的位置信息和到店指南',
                'content_gap': '用户实际到店体验分享'
            }
        }
        return analysis.get(intent, {
            'competitor_types': ['综合网站', '专业网站', '社交媒体'],
            'differentiation': '提供更有针对性的内容',
            'content_gap': '用户实际需求分析'
        })
    
    def _get_intent_conversion_strategy(self, intent: str) -> Dict[str, Any]:
        """获取意图转化策略"""
        strategies = {
            'I': {
                'primary_cta': '深入学习',
                'secondary_cta': '下载资源',
                'conversion_goals': ['课程注册', '电子书下载', '订阅通讯'],
                'user_journey': ['了解概念', '学习基础', '掌握技能', '应用实践']
            },
            'N': {
                'primary_cta': '安全访问',
                'secondary_cta': '了解更多',
                'conversion_goals': ['官网跳转', '应用下载', '账户注册'],
                'user_journey': ['寻找入口', '确认安全性', '访问官网', '完成目标']
            },
            'C': {
                'primary_cta': '查看详情',
                'secondary_cta': '对比全部',
                'conversion_goals': ['产品详情查看', '对比工具使用', '购买链接点击'],
                'user_journey': ['浏览选项', '对比功能', '阅读评测', '做出决策']
            },
            'E': {
                'primary_cta': '立即购买',
                'secondary_cta': '查看优惠',
                'conversion_goals': ['加入购物车', '完成购买', '优惠券使用'],
                'user_journey': ['了解产品', '比较价格', '查找优惠', '完成购买']
            },
            'B': {
                'primary_cta': '解决问题',
                'secondary_cta': '获取支持',
                'conversion_goals': ['问题解决', '支持服务购买', '社区参与'],
                'user_journey': ['发现问题', '寻找解决方案', '应用解决方法', '问题解决']
            },
            'L': {
                'primary_cta': '查看位置',
                'secondary_cta': '立即预约',
                'conversion_goals': ['地图查看', '路线规划', '预约完成'],
                'user_journey': ['查找位置', '了解服务', '规划路线', '到店体验']
            }
        }
        return strategies.get(intent, {
            'primary_cta': '了解更多',
            'secondary_cta': '立即行动',
            'conversion_goals': ['内容阅读', '互动参与', '转化行动'],
            'user_journey': ['发现内容', '了解详情', '评估价值', '采取行动']
        })
    
    def _generate_internal_linking_plan(self) -> Dict[str, Any]:
        """生成内部链接计划"""
        # 创建内部链接计划
        linking_plan = {
            'homepage_links': [],
            'intent_page_links': {},
            'content_page_links': {},
            'cross_intent_links': []
        }
        
        # 1. 首页链接
        # 首页链接到各个意图页面
        for intent in self.website_structure['intent_pages'].keys():
            intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
            linking_plan['homepage_links'].append({
                'from': '/',
                'to': f'/intent/{intent.lower()}',
                'anchor_text': f'{intent_name}内容',
                'context': '意图导航区域'
            })
        
        # 2. 意图页面链接
        # 每个意图页面链接到其子意图页面和关键词页面
        for intent, pages in self.website_structure['intent_pages'].items():
            linking_plan['intent_page_links'][intent] = []
            
            # 获取意图总览页面
            overview_page = next((p for p in pages if p['type'] == 'intent_overview'), None)
            if not overview_page:
                continue
                
            # 链接到子意图页面
            sub_intent_pages = [p for p in pages if p['type'] == 'sub_intent']
            for sub_page in sub_intent_pages:
                linking_plan['intent_page_links'][intent].append({
                    'from': overview_page['url'],
                    'to': sub_page['url'],
                    'anchor_text': sub_page['intent_name'],
                    'context': '子意图导航区域'
                })
            
            # 链接到关键词页面
            keyword_pages = [p for p in pages if p['type'] == 'keyword']
            for keyword_page in keyword_pages:
                linking_plan['intent_page_links'][intent].append({
                    'from': overview_page['url'],
                    'to': keyword_page['url'],
                    'anchor_text': keyword_page['keyword'],
                    'context': '热门关键词区域'
                })
        
        # 3. 内容页面链接
        # 每个内容页面链接到相关内容页面
        for page_id, page in self.website_structure['content_pages'].items():
            intent = page['intent']
            sub_intent = page.get('sub_intent', '')
            
            # 查找同一子意图的其他内容页面
            related_pages = [
                p for pid, p in self.website_structure['content_pages'].items()
                if pid != page_id and p.get('sub_intent', '') == sub_intent
            ]
            
            linking_plan['content_page_links'][page_id] = []
            
            # 添加相关内容链接
            for related_page in related_pages[:3]:  # 最多添加3个相关链接
                linking_plan['content_page_links'][page_id].append({
                    'from': page['url'],
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于搜索意图的网站自动建设工具

该工具基于最新的搜索意图分析规则（6主意图×24子意图）自动生成网站结构和内容计划，
针对不同的搜索意图类型设计不同的页面模板和内容策略，以优化SEO效果和用户体验。
"""

import os
import json
import yaml
import pandas as pd
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict

# 导入意图分析器
try:
    from src.analyzers.intent_analyzer_v2 import IntentAnalyzerV2
except ImportError:
    print("警告: 无法导入IntentAnalyzerV2，将使用本地实现")
    # 如果无法导入，使用简化版本
    class IntentAnalyzerV2:
        """简化版意图分析器"""
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


class IntentBasedWebsiteBuilder:
    """基于搜索意图的网站自动建设工具"""
    
    def __init__(self, intent_data_path: str = None, output_dir: str = 'output'):
        """
        初始化网站建设工具
        
        Args:
            intent_data_path: 意图分析数据路径（CSV或JSON）
            output_dir: 输出目录
        """
        self.intent_data_path = intent_data_path
        self.output_dir = output_dir
        self.intent_data = None
        self.intent_summary = None
        self.analyzer = IntentAnalyzerV2()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 页面模板配置
        self.page_templates = self._load_page_templates()
        
        # 内容类型配置
        self.content_types = self._get_content_types()
        
        # SEO配置
        self.seo_config = self._get_seo_config()
        
        # 网站结构
        self.website_structure = {
            'homepage': {},
            'intent_pages': {},
            'content_pages': {},
            'product_pages': {},
            'category_pages': {}
        }
        
        # 内容计划
        self.content_plan = []
        
        # 技术栈配置
        self.tech_stack = self._get_tech_stack()
        
        print("基于搜索意图的网站自动建设工具初始化完成")
    
    def _load_page_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载页面模板配置"""
        return {
            # 信息获取型页面模板
            'I': {
                'layout': 'guide',
                'sections': [
                    {'type': 'hero', 'title': '{keyword} 完全指南', 'description': '了解关于{keyword}的一切'},
                    {'type': 'toc', 'title': '目录'},
                    {'type': 'definition', 'title': '{keyword}是什么?'},
                    {'type': 'steps', 'title': '如何使用{keyword}'},
                    {'type': 'faq', 'title': '常见问题'},
                    {'type': 'related', 'title': '相关资源'}
                ],
                'cta': '深入了解',
                'word_count': 2000,
                'media_ratio': 0.3,  # 30%的内容是媒体（图片、视频）
                'seo_priority': 'high'
            },
            # 导航直达型页面模板
            'N': {
                'layout': 'landing',
                'sections': [
                    {'type': 'hero', 'title': '{keyword} 官方入口', 'description': '快速访问{keyword}'},
                    {'type': 'features', 'title': '主要功能'},
                    {'type': 'cta_block', 'title': '立即访问'},
                    {'type': 'alternatives', 'title': '其他选择'}
                ],
                'cta': '立即访问',
                'word_count': 800,
                'media_ratio': 0.2,
                'seo_priority': 'medium'
            },
            # 商业评估型页面模板
            'C': {
                'layout': 'comparison',
                'sections': [
                    {'type': 'hero', 'title': '{year}年最佳{keyword}推荐', 'description': '全面对比{keyword}'},
                    {'type': 'comparison_table', 'title': '{keyword}对比表'},
                    {'type': 'top_picks', 'title': '编辑推荐'},
                    {'type': 'reviews', 'title': '详细评测'},
                    {'type': 'buying_guide', 'title': '购买指南'},
                    {'type': 'faq', 'title': '常见问题'}
                ],
                'cta': '查看最佳选择',
                'word_count': 3000,
                'media_ratio': 0.25,
                'seo_priority': 'very_high'
            },
            # 交易购买型页面模板
            'E': {
                'layout': 'product',
                'sections': [
                    {'type': 'hero', 'title': '购买{keyword}', 'description': '最优惠的{keyword}价格'},
                    {'type': 'pricing', 'title': '价格方案'},
                    {'type': 'deals', 'title': '限时优惠'},
                    {'type': 'testimonials', 'title': '用户评价'},
                    {'type': 'guarantee', 'title': '购买保障'}
                ],
                'cta': '立即购买',
                'word_count': 1500,
                'media_ratio': 0.3,
                'seo_priority': 'high'
            },
            # 行为后续型页面模板
            'B': {
                'layout': 'support',
                'sections': [
                    {'type': 'hero', 'title': '{keyword}使用指南', 'description': '解决{keyword}使用问题'},
                    {'type': 'troubleshooting', 'title': '常见问题解决'},
                    {'type': 'advanced_tips', 'title': '高级技巧'},
                    {'type': 'community', 'title': '社区支持'},
                    {'type': 'updates', 'title': '最新更新'}
                ],
                'cta': '获取支持',
                'word_count': 2500,
                'media_ratio': 0.4,
                'seo_priority': 'medium'
            },
            # 本地/到店型页面模板
            'L': {
                'layout': 'local',
                'sections': [
                    {'type': 'hero', 'title': '附近的{keyword}', 'description': '找到离您最近的{keyword}'},
                    {'type': 'map', 'title': '位置地图'},
                    {'type': 'locations', 'title': '所有位置'},
                    {'type': 'hours', 'title': '营业时间'},
                    {'type': 'directions', 'title': '到达方式'}
                ],
                'cta': '查看位置',
                'word_count': 1000,
                'media_ratio': 0.5,
                'seo_priority': 'medium'
            }
        }
    
    def _get_content_types(self) -> Dict[str, Dict[str, Any]]:
        """获取内容类型配置"""
        return {
            # 信息获取型内容
            'I': {
                'I1': {  # 定义/概念
                    'formats': ['百科词条', '概念解释', '术语表'],
                    'title_templates': [
                        '什么是{keyword}？完整解释',
                        '{keyword}是什么意思？详细定义',
                        '{keyword}百科：你需要知道的一切'
                    ],
                    'meta_description': '{keyword}的完整定义和解释，了解{keyword}的含义、起源和应用场景。',
                    'content_structure': ['定义', '历史背景', '核心概念', '应用场景', '常见误区', '延伸阅读'],
                    'conversion_strategy': '引导到更深入的教程或相关产品'
                },
                'I2': {  # 原理/源码
                    'formats': ['技术文档', '原理解析', '源码分析'],
                    'title_templates': [
                        '{keyword}工作原理详解',
                        '{keyword}背后的技术：深度解析',
                        '{keyword}源码分析与架构设计'
                    ],
                    'meta_description': '深入解析{keyword}的工作原理、技术架构和源码实现，适合开发者和技术爱好者。',
                    'content_structure': ['技术概述', '架构设计', '核心算法', '源码分析', '性能考量', '实现挑战'],
                    'conversion_strategy': '引导到高级教程或开发者社区'
                },
                'I3': {  # 教程/步骤
                    'formats': ['分步教程', '操作指南', '视频教程'],
                    'title_templates': [
                        '{keyword}教程：从入门到精通',
                        '如何使用{keyword}：完整指南',
                        '{keyword}新手指南：10个简单步骤'
                    ],
                    'meta_description': '学习如何使用{keyword}的详细教程，包含分步指南和实用技巧，适合初学者。',
                    'content_structure': ['准备工作', '基础步骤', '进阶技巧', '常见问题', '实战案例', '下一步学习'],
                    'conversion_strategy': '引导到相关工具或高级课程'
                },
                'I4': {  # 事实求证
                    'formats': ['事实核查', '真相解析', '专家观点'],
                    'title_templates': [
                        '{keyword}是否真的有效？科学解析',
                        '{keyword}的真相：分析与验证',
                        '{keyword}：常见说法的真假分析'
                    ],
                    'meta_description': '深入分析{keyword}的真实情况，基于事实和数据验证常见说法的真伪。',
                    'content_structure': ['常见说法', '事实依据', '专家观点', '研究数据', '结论分析', '延伸阅读'],
                    'conversion_strategy': '建立权威性，引导到相关服务'
                }
            },
            # 导航直达型内容
            'N': {
                'N1': {  # 官方主页
                    'formats': ['官方介绍', '品牌页面', '产品主页'],
                    'title_templates': [
                        '{keyword}官方网站 - 权威入口',
                        '{keyword}官方主页 - 直达链接',
                        '访问{keyword}官方网站 - 安全链接'
                    ],
                    'meta_description': '{keyword}的官方网站入口，获取最新信息、产品介绍和官方支持。',
                    'content_structure': ['品牌介绍', '产品概述', '官方链接', '最新动态', '联系方式'],
                    'conversion_strategy': '直接引导到官方网站或产品'
                },
                'N2': {  # 登录/控制台
                    'formats': ['登录指南', '控制台教程', '账户管理'],
                    'title_templates': [
                        '{keyword}登录入口及使用指南',
                        '如何登录{keyword}控制台 - 详细步骤',
                        '{keyword}账户管理与控制台使用技巧'
                    ],
                    'meta_description': '{keyword}登录入口指南，包含登录步骤、控制台使用技巧和账户管理方法。',
                    'content_structure': ['登录入口', '账户创建', '控制台导航', '常见问题', '安全提示'],
                    'conversion_strategy': '引导到登录页面或账户创建'
                },
                'N3': {  # 下载/安装包
                    'formats': ['下载指南', '安装教程', '版本对比'],
                    'title_templates': [
                        '{keyword}下载：官方最新版本',
                        '如何下载并安装{keyword} - 完整指南',
                        '{keyword}各版本下载与对比'
                    ],
                    'meta_description': '{keyword}的官方下载链接和详细安装指南，包含各版本对比和系统要求。',
                    'content_structure': ['下载链接', '系统要求', '安装步骤', '版本对比', '常见问题'],
                    'conversion_strategy': '引导到下载页面或高级版本'
                }
            },
            # 商业评估型内容
            'C': {
                'C1': {  # 榜单/推荐
                    'formats': ['排行榜', '推荐清单', '编辑精选'],
                    'title_templates': [
                        '{year}年最佳{keyword}推荐：排名前10',
                        '{keyword}排行榜：专家评选与推荐',
                        '最值得使用的{keyword}：完整榜单'
                    ],
                    'meta_description': '{year}年最新{keyword}排行榜，基于专业测评和用户反馈，帮您选择最适合的产品。',
                    'content_structure': ['评选标准', '榜单总览', '详细点评', '价格对比', '如何选择', '常见问题'],
                    'conversion_strategy': '引导到详细评测或购买链接'
                },
                'C2': {  # 对比/评测
                    'formats': ['对比分析', '深度评测', '功能对比表'],
                    'title_templates': [
                        '{keyword}对比：哪个最好？{year}年全面分析',
                        '{keyword1} vs {keyword2}：哪个更值得选择？',
                        '{keyword}深度评测：优缺点全面分析'
                    ],
                    'meta_description': '全面对比各种{keyword}的功能、价格和性能，帮您找到最适合自己需求的选择。',
                    'content_structure': ['对比概述', '功能对比', '性能测试', '价格分析', '适用场景', '最终推荐'],
                    'conversion_strategy': '基于需求引导到最佳选择'
                },
                'C3': {  # 口碑/点评
                    'formats': ['用户评价汇总', '真实使用体验', '长期使用报告'],
                    'title_templates': [
                        '{keyword}用户评价：真实体验分享',
                        '我用{keyword}一年后的真实感受',
                        '{keyword}口碑调查：用户最关心的问题'
                    ],
                    'meta_description': '汇总真实用户对{keyword}的评价和使用体验，揭示产品的真实优缺点和使用感受。',
                    'content_structure': ['评价概述', '优点汇总', '缺点分析', '用户案例', '专家观点', '总体评价'],
                    'conversion_strategy': '基于真实体验建立信任，引导到推荐产品'
                }
            },
            # 交易购买型内容
            'E': {
                'E1': {  # 价格/报价
                    'formats': ['价格指南', '费用分析', '预算规划'],
                    'title_templates': [
                        '{keyword}价格指南：各版本详细对比',
                        '{keyword}要多少钱？完整价格分析',
                        '{keyword}费用明细：从基础版到高级版'
                    ],
                    'meta_description': '{keyword}的详细价格信息，包含各版本费用对比、隐藏成本分析和最佳购买时机。',
                    'content_structure': ['价格总览', '版本对比', '隐藏成本', '性价比分析', '购买建议'],
                    'conversion_strategy': '引导到最佳价格或优惠购买渠道'
                },
                'E2': {  # 优惠/折扣
                    'formats': ['优惠信息', '折扣代码', '促销活动'],
                    'title_templates': [
                        '{keyword}优惠券与折扣码：省钱指南',
                        '{keyword}最新促销活动汇总',
                        '如何以最低价格购买{keyword}'
                    ],
                    'meta_description': '最新{keyword}优惠信息，包含折扣码、促销活动和特别优惠，帮您省钱购买。',
                    'content_structure': ['当前优惠', '折扣码汇总', '会员特价', '季节性促销', '省钱技巧'],
                    'conversion_strategy': '创造紧迫感，引导立即购买'
                },
                'E3': {  # 下单/预订
                    'formats': ['购买指南', '订购流程', '预订教程'],
                    'title_templates': [
                        '如何购买{keyword}：详细步骤指南',
                        '{keyword}订购流程：避开常见陷阱',
                        '{keyword}预订攻略：确保最佳体验'
                    ],
                    'meta_description': '详细指导如何购买或预订{keyword}，包含步骤说明、注意事项和支付方式介绍。',
                    'content_structure': ['准备工作', '购买步骤', '支付选项', '注意事项', '售后服务'],
                    'conversion_strategy': '简化购买流程，减少放弃率'
                }
            },
            # 行为后续型内容
            'B': {
                'B1': {  # 故障/报错
                    'formats': ['故障排除指南', '错误代码解析', '问题解决方案'],
                    'title_templates': [
                        '{keyword}常见问题及解决方法',
                        '{keyword}错误代码大全及修复指南',
                        '解决{keyword}故障的完整指南'
                    ],
                    'meta_description': '全面解析{keyword}常见故障和错误代码，提供详细的排查步骤和解决方案。',
                    'content_structure': ['常见问题', '错误代码', '排查步骤', '解决方案', '预防措施'],
                    'conversion_strategy': '提供高级支持或升级服务'
                },
                'B2': {  # 高级用法
                    'formats': ['高级技巧', '专家指南', '进阶教程'],
                    'title_templates': [
                        '{keyword}高级技巧：提升使用效率',
                        '{keyword}进阶指南：从熟练到精通',
                        '{keyword}专家用法：鲜为人知的功能'
                    ],
                    'meta_description': '探索{keyword}的高级功能和使用技巧，帮助有经验的用户进一步提升效率和体验。',
                    'content_structure': ['基础回顾', '高级功能', '效率技巧', '自定义设置', '案例分享'],
                    'conversion_strategy': '引导到专业版或付费课程'
                },
                'B3': {  # 配置/设置
                    'formats': ['配置指南', '设置教程', '优化方案'],
                    'title_templates': [
                        '{keyword}最佳配置指南：优化性能',
                        '如何正确设置{keyword}：详细教程',
                        '{keyword}设置技巧：提升使用体验'
                    ],
                    'meta_description': '详细指导如何配置和设置{keyword}，包含最佳实践和性能优化建议。',
                    'content_structure': ['基本设置', '高级配置', '性能优化', '安全设置', '常见问题'],
                    'conversion_strategy': '引导到配置服务或高级支持'
                }
            },
            # 本地/到店型内容
            'L': {
                'L1': {  # 附近门店
                    'formats': ['位置指南', '门店列表', '区域地图'],
                    'title_templates': [
                        '附近的{keyword}：完整位置指南',
                        '{location}地区{keyword}门店大全',
                        '如何找到离你最近的{keyword}'
                    ],
                    'meta_description': '查找离您最近的{keyword}位置，包含详细地址、联系方式和服务内容。',
                    'content_structure': ['位置总览', '详细地址', '服务内容', '联系方式', '用户评价'],
                    'conversion_strategy': '引导到地图导航或预约'
                },
                'L2': {  # 预约/路线
                    'formats': ['预约指南', '到店路线', '交通指南'],
                    'title_templates': [
                        '如何预约{keyword}：详细步骤',
                        '前往{keyword}的最佳路线指南',
                        '{keyword}预约系统使用教程'
                    ],
                    'meta_description': '详细指导如何预约{keyword}服务，以及前往各个位置的交通路线和停车信息。',
                    'content_structure': ['预约流程', '准备事项', '交通方式', '停车信息', '到店须知'],
                    'conversion_strategy': '简化预约流程，提高到店率'
                },
                'L3': {  # 开放时间
                    'formats': ['营业时间', '节假日安排', '特殊时段'],
                    'title_templates': [
                        '{keyword}营业时间：完整时间表',
                        '{keyword}节假日开放时间安排',
                        '{keyword}各门店营业时间大全'
                    ],
                    'meta_description': '{keyword}的详细营业时间，包含各分店时间表、节假日安排和特殊时段调整。',
                    'content_structure': ['常规时间', '节假日安排', '特殊时段', '提前预约', '联系方式'],
                    'conversion_strategy': '引导到预约系统或特别活动'
                }
            }
        }
    
    def _get_seo_config(self) -> Dict[str, Any]:
        """获取SEO配置"""
        return {
            'title_patterns': {
                'I': '{keyword} 指南：完整教程与使用方法 ({year})',
                'N': '{keyword} 官方入口 - 安全直达链接',
                'C': '{year}年最佳{keyword}推荐：排名与对比',
                'E': '{keyword}价格与购买指南：如何获得最优惠',
                'B': '{keyword}问题解决与高级使用技巧',
                'L': '附近的{keyword}：位置、时间与预约'
            },
            'meta_description_patterns': {
                'I': '全面了解{keyword}的详细指南，包含使用方法、最佳实践和常见问题解答。',
                'N': '{keyword}的官方入口，安全可靠，直达目标网站，避免钓鱼和欺诈风险。',
                'C': '专业评测{year}年最佳{keyword}，基于实际使用体验和性能测试，帮您做出明智选择。',
                'E': '{keyword}的最新价格信息、购买渠道和折扣优惠，助您以最优惠的价格获取产品。',
                'B': '解决{keyword}使用过程中的常见问题，掌握高级技巧，充分发挥产品潜力。',
                'L': '查找离您最近的{keyword}位置，了解营业时间、预约方式和到店路线。'
            },
            'heading_structure': {
                'h1_pattern': '{main_keyword} - {sub_keyword}',
                'h2_count': {'min': 3, 'max': 7},
                'h3_per_h2': {'min': 2, 'max': 5}
            },
            'content_guidelines': {
                'paragraph_length': {'min': 3, 'max': 5},  # 每段句子数
                'sentence_length': {'min': 10, 'max': 20},  # 每句词数
                'keyword_density': {'min': 0.5, 'max': 2.0},  # 关键词密度百分比
                'readability': 'middle_school'  # 可读性级别
            },
            'schema_markup': {
                'I': 'HowTo',
                'N': 'WebPage',
                'C': 'Review',
                'E': 'Product',
                'B': 'FAQPage',
                'L': 'LocalBusiness'
            },
            'internal_linking': {
                'links_per_page': {'min': 3, 'max': 8},
                'anchor_text_variation': True,
                'link_to_related_intents': True
            }
        }
    
    def _get_tech_stack(self) -> Dict[str, Any]:
        """获取技术栈配置"""
        return {
            'frontend': {
                'framework': 'Next.js',
                'styling': 'Tailwind CSS',
                'features': [
                    'SSR (Server-Side Rendering)',
                    'ISR (Incremental Static Regeneration)',
                    '响应式设计',
                    '暗黑模式',
                    'PWA支持'
                ]
            },
            'backend': {
                'framework': 'Next.js API Routes',
                'database': 'PostgreSQL (Supabase)',
                'cms': 'Contentful',
                'features': [
                    'RESTful API',
                    '内容管理',
                    '用户认证',
                    '搜索功能',
                    '数据分析'
                ]
            },
            'deployment': {
                'hosting': 'Vercel',
                'cdn': 'Cloudflare',
                'monitoring': 'Sentry',
                'analytics': 'Google Analytics 4'
            },
            'seo_tools': {
                'sitemap': 'next-sitemap',
                'meta_tags': 'next-seo',
                'schema': 'schema-dts',
                'analytics': 'GA4 + GTM'
            },
            'performance': {
                'image_optimization': 'next/image',
                'code_splitting': 'Automatic',
                'lazy_loading': 'Enabled',
                'caching': 'SWR + Redis'
            }
        }
    
    def load_intent_data(self) -> bool:
        """
        加载意图分析数据
        
        Returns:
            加载是否成功
        """
        if not self.intent_data_path:
            print("错误: 未指定意图数据路径")
            return False
        
        try:
            # 根据文件扩展名决定加载方式
            if self.intent_data_path.endswith('.csv'):
                self.intent_data = pd.read_csv(self.intent_data_path)
                print(f"已从CSV加载 {len(self.intent_data)} 条意图数据")
            elif self.intent_data_path.endswith('.json'):
                with open(self.intent_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'results' in data:
                        # 如果是IntentAnalyzerV2的输出格式
                        self.intent_data = pd.DataFrame(data['results'])
                        self.intent_summary = data.get('summary', {})
                    else:
                        # 尝试直接加载
                        self.intent_data = pd.DataFrame(data)
                print(f"已从JSON加载 {len(self.intent_data)} 条意图数据")
            else:
                print(f"不支持的文件格式: {self.intent_data_path}")
                return False
            
            # 验证数据格式
            required_columns = ['query', 'intent_primary']
            if not all(col in self.intent_data.columns for col in required_columns):
                print(f"数据格式错误: 缺少必要的列 {required_columns}")
                return False
            
            # 生成意图摘要（如果没有）
            if not self.intent_summary:
                self._generate_intent_summary()
            
            return True
        except Exception as e:
            print(f"加载意图数据失败: {e}")
            return False
    
    def _generate_intent_summary(self) -> None:
        """生成意图摘要"""
        if self.intent_data is None:
            return
        
        # 统计各意图数量
        intent_counts = self.intent_data['intent_primary'].value_counts().to_dict()
        
        # 计算百分比
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
        
        # 创建摘要
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
        
        print(f"已生成意图摘要: {len(intent_counts)} 种意图类型")
    
    def analyze_keywords(self, keywords: List[str]) -> bool:
        """
        分析关键词列表
        
        Args:
            keywords: 关键词列表
            
        Returns:
            分析是否成功
        """
        try:
            # 创建DataFrame
            df = pd.DataFrame({'query': keywords})
            
            # 使用意图分析器
            analysis_results = self.analyzer.analyze_keywords(df, query_col='query')
            
            # 保存结果
            self.intent_data = analysis_results['dataframe']
            self.intent_summary = analysis_results['summary']
            
            # 保存到文件
            timestamp = datetime.now().strftime('%Y-%m-%d')
            output_file = os.path.join(self.output_dir, f'intent_analysis_{timestamp}.json')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'results': analysis_results['results'],
                    'summary': analysis_results['summary']
                }, f, ensure_ascii=False, indent=2)
            
            print(f"已分析 {len(keywords)} 个关键词，结果保存到: {output_file}")
            return True
        except Exception as e:
            print(f"分析关键词失败: {e}")
            return False
    
    def generate_website_structure(self) -> Dict[str, Any]:
        """
        生成网站结构
        
        Returns:
            网站结构字典
        """
        if self.intent_data is None or self.intent_summary is None:
            print("错误: 未加载意图数据")
            return {}
        
        print("正在生成基于搜索意图的网站结构...")
        
        # 获取当前年份
        current_year = datetime.now().year
        
        # 1. 生成首页
        self.website_structure['homepage'] = self._generate_homepage()
        
        # 2. 生成意图页面
        for intent, keywords in self.intent_summary['intent_keywords'].items():
            if not keywords:
                continue
                
            # 只处理主意图（单字符）
            if len(intent) == 1:
                intent_pages = self._generate_intent_pages(intent, keywords, current_year)
                self.website_structure['intent_pages'][intent] = intent_pages
        
        # 3. 生成内容页面
        self._generate_content_pages(current_year)
        
        # 4. 生成产品页面
        self._generate_product_pages()
        
        # 5. 生成分类页面
        self._generate_category_pages(current_year)
        
        print(f"网站结构生成完成，共包含:")
        print(f"- 1 个首页")
        print(f"- {sum(len(pages) for pages in self.website_structure['intent_pages'].values())} 个意图页面")
        print(f"- {len(self.website_structure['content_pages'])} 个内容页面")
        print(f"- {len(self.website_structure['product_pages'])} 个产品页面")
        print(f"- {len(self.website_structure['category_pages'])} 个分类页面")
        
        return self.website_structure
    
    def _generate_homepage(self) -> Dict[str, Any]:
        """生成首页结构"""
        # 获取主要关键词（按意图分布）
        top_keywords = {}
        for intent, keywords in self.intent_summary['intent_keywords'].items():
            if keywords:
                # 每种意图取前3个关键词
                top_keywords[intent] = keywords[:3]
        
        # 确定主要意图（占比最高的前3种）
        main_intents = sorted(
            self.intent_summary['intent_percentages'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        # 生成首页结构
        homepage = {
            'title': '主页 - 基于用户搜索意图优化的内容平台',
            'meta_description': '提供满足各种搜索意图的高质量内容，包括教程、评测、购买指南和问题解决方案。',
            'sections': [
                {
                    'type': 'hero',
                    'title': '找到您需要的一切',
                    'description': '基于真实搜索意图打造的内容平台'
                }
            ],
            'intent_sections': []
        }
        
        # 为主要意图创建专区
        for intent, percentage in main_intents:
            intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
            keywords = self.intent_summary['intent_keywords'].get(intent, [])[:5]
            
            homepage['intent_sections'].append({
                'intent': intent,
                'intent_name': intent_name,
                'title': f"{intent_name}内容",
                'description': self._get_intent_description(intent),
                'featured_keywords': keywords,
                'percentage': percentage
            })
        
        # 添加其他首页部分
        homepage['sections'].extend([
            {
                'type': 'featured',
                'title': '热门内容',
                'items': self._get_top_keywords(5)
            },
            {
                'type': 'categories',
                'title': '内容分类',
                'items': [
                    {'name': self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent), 'intent': intent}
                    for intent, _ in main_intents
                ]
            },
            {
                'type': 'cta',
                'title': '找不到您需要的内容？',
                'description': '告诉我们您的需求，我们将为您创建相关内容',
                'button': '提交需求'
            }
        ])
        
        return homepage
    
    def _get_intent_description(self, intent: str) -> str:
        """获取意图的描述文本"""
        descriptions = {
            'I': '全面的指南和教程，帮助您了解和学习各种主题',
            'N': '直达官方网站、登录入口和下载页面的安全链接',
            'C': '详细的产品评测、对比和推荐，助您做出明智选择',
            'E': '最优惠的价格信息、折扣代码和购买指南',
            'B': '解决使用问题、故障排除和高级使用技巧',
            'L': '查找附近位置、营业时间和到店路线'
        }
        return descriptions.get(intent, '相关内容和资源')
    
    def _get_top_keywords(self, count: int) -> List[Dict[str, str]]:
        """获取热门关键词"""
        if self.intent_data is None or len(self.intent_data) == 0:
            return []
        
        # 如果有概率列，按概率排序
        if 'probability' in self.intent_data.columns:
            top_df = self.intent_data.sort_values('probability', ascending=False).head(count)
        else:
            # 否则随机选择
            top_df = self.intent_data.sample(min(count, len(self.intent_data)))
        
        return [
            {
                'keyword': row['query'],
                'intent': row['intent_primary'],
                'intent_name': self.analyzer.INTENT_DESCRIPTIONS.get(row['intent_primary'], '')
            }
            for _, row in top_df.iterrows()
        ]
    
    def _generate_intent_pages(self, intent: str, keywords: List[str], year: int) -> List[Dict[str, Any]]:
        """
        为特定意图生成页面
        
        Args:
            intent: 意图代码
            keywords: 相关关键词列表
            year: 当前年份
            
        Returns:
            页面列表
        """
        # 获取页面模板
        template = self.page_templates.get(intent, {})
        if not template:
            return []
        
        # 按子意图分组关键词
        sub_intent_keywords = defaultdict(list)
        
        # 遍历关键词，查找子意图
        for keyword in keywords:
            # 在意图数据中查找该关键词
            keyword_data = self.intent_data[self.intent_data['query'] == keyword]
            if not keyword_data.empty and 'sub_intent' in keyword_data.columns:
                sub_intent = keyword_data.iloc[0]['sub_intent']
                if sub_intent and sub_intent.startswith(intent):
                    sub_intent_keywords[sub_intent].append(keyword)
                else:
                    # 如果没有子意图或子意图不匹配，放入主意图组
                    sub_intent_keywords[intent].append(keyword)
            else:
                sub_intent_keywords[intent].append(keyword)
        
        # 生成页面
        pages = []
        
        # 1. 为主意图创建总览页面
        overview_page = self._create_intent_overview_page(intent, keywords, template, year)
        pages.append(overview_page)
        
        # 2. 为每个子意图创建专门页面
        for sub_intent, sub_keywords in sub_intent_keywords.items():
            # 跳过主意图（已经创建了总览页面）
            if sub_intent == intent or not sub_keywords:
                continue
                
            # 创建子意图页面
            sub_page = self._create_sub_intent_page(sub_intent, sub_keywords, template, year)
            pages.append(sub_page)
        
        # 3. 为热门关键词创建专门页面
        top_keywords = sorted(keywords, key=lambda k: len(k))[:5]  # 简单示例：取最短的5个关键词作为热门
        for keyword in top_keywords:
            keyword_page = self._create_keyword_page(keyword, intent, template, year)
            pages.append(keyword_page)
        
        return pages
    
    def _create_intent_overview_page(self, intent: str, keywords: List[str], template: Dict[str, Any], year: int) -> Dict[str, Any]:
        """创建意图总览页面"""
        intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
        
        # 生成标题和描述
        title_pattern = self.seo_config['title_patterns'].get(intent, '{intent_name}内容 - {year}')
        title = title_pattern.format(
            intent_name=intent_name,
            keyword=intent_name,
            year=year
        )
        
        description_pattern = self.seo_config['meta_description_patterns'].get(intent, '')
        description = description_pattern.format(
            intent_name=intent_name,
            keyword=intent_name,
            year=year
        )
        
        # 创建页面结构
        page = {
            'type': 'intent_overview',
            'intent': intent,
            'intent_name': intent_name,
            'url': f'/intent/{intent.lower()}',
            'title': title,
            'meta_description': description,
            'sections': [],
            'keywords': keywords[:20],  # 最多显示20个关键词
            'layout': template.get('layout', 'default'),
            'seo_priority': template.get('seo_priority', 'medium')
        }
        
        # 添加页面部分
        for section in template.get('sections', []):
            section_copy = section.copy()
            section_copy['title'] = section['title'].format(
                keyword=intent_name,
                year=year
            )
            page['sections'].append(section_copy)
        
        return page
    
    def _create_sub_intent_page(self, sub_intent: str, keywords: List[str], template: Dict[str, Any], year: int) -> Dict[str, Any]:
        """创建子意图页面"""
        sub_intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(sub_intent, sub_intent)
        main_intent = sub_intent[0]
        
        # 获取内容类型配置
        content_type = self.content_types.get(main_intent, {}).get(sub_intent, {})
        
        # 选择标题模板
        title_templates = content_type.get('title_templates', ['{sub_intent_name} - {year}年完整指南'])
        title = title_templates[0].format(
            sub_intent_name=sub_intent_name,
            keyword=sub_intent_name,
            year=year
        )
        
        # 生成描述
        description = content_type.get('meta_description', '').format(
            sub_intent_name=sub_intent_name,
            keyword=sub_intent_name,
            year=year
        )
        
        # 创建页面结构
        page = {
            'type': 'sub_intent',
            'intent': main_intent,
            'sub_intent': sub_intent,
            'intent_name': sub_intent_name,
            'url': f'/intent/{sub_intent.lower()}',
            'title': title,
            'meta_description': description,
            'sections': [],
            'keywords': keywords[:20],  # 最多显示20个关键词
            'layout': template.get('layout', 'default'),
            'seo_priority': template.get('seo_priority', 'medium'),
            'content_structure': content_type.get('content_structure', []),
            'conversion_strategy': content_type.get('conversion_strategy', '')
        }
        
        # 添加页面部分
        for section in template.get('sections', []):
            section_copy = section.copy()
            section_copy['title'] = section['title'].format(
                keyword=sub_intent_name,
                year=year
            )
            page['sections'].append(section_copy)
        
        return page
    
    def _create_keyword_page(self, keyword: str, intent: str, template: Dict[str, Any], year: int) -> Dict[str, Any]:
        """创建关键词专题页面"""
        intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
        
        # 查找该关键词的子意图
        sub_intent = ''
        keyword_data = self.intent_data[self.intent_data['query'] == keyword]
        if not keyword_data.empty and 'sub_intent' in keyword_data.columns:
            sub_intent = keyword_data.iloc[0]['sub_intent']
        
        # 获取内容类型配置
        content_type = {}
        if sub_intent and len(sub_intent) > 1:
            main_intent = sub_intent[0]
            content_type = self.content_types.get(main_intent, {}).get(sub_intent, {})
        
        # 选择标题模板
        title_templates = content_type.get('title_templates', ['{keyword} - {year}年完整指南'])
        title = title_templates[0].format(
            keyword=keyword,
            year=year
        )
        
        # 生成描述
        description = content_type.get('meta_description', '关于{keyword}的详细信息和指南').format(
            keyword=keyword,
            year=year
        )
        
        # 创建URL友好的关键词
        url_keyword = keyword.lower().replace(' ', '-').replace('/', '-')
        
        # 创建页面结构
        page = {
            'type': 'keyword',
            'intent': intent,
            'sub_intent': sub_intent,
            'keyword': keyword,
            'url': f'/keyword/{url_keyword}',
            'title': title,
            'meta_description': description,
            'sections': [],
            'layout': template.get('layout', 'default'),
            'seo_priority': 'high',
            'content_structure': content_type.get('content_structure', []),
            'conversion_strategy': content_type.get('conversion_strategy', '')
        }
        
        # 添加页面部分
        for section in template.get('sections', []):
            section_copy = section.copy()
            section_copy['title'] = section['title'].format(
                keyword=keyword,
                year=year
            )
            page['sections'].append(section_copy)
        
        return page
    
    def _generate_content_pages(self, year: int) -> None:
        """生成内容页面"""
        # 按意图类型生成不同的内容页面
        content_pages = {}
        
        # 为每种主要意图创建内容页面
        for intent, keywords in self.intent_summary['intent_keywords'].items():
            # 只处理主意图
            if len(intent) != 1 or not keywords:
                continue
                
            # 获取该意图的内容类型
            intent_content_types = self.content_types.get(intent, {})
            
            # 为每种子意图创建内容
            for sub_intent, content_type in intent_content_types.items():
                # 跳过非子意图
                if not sub_intent.startswith(intent) or len(sub_intent) <= 1:
                    continue
                
                # 为该子意图创建2-3个内容页面
                for i in range(min(3, len(keywords))):
                    if i >= len(keywords):
                        break
                        
                    keyword = keywords[i]
                    
                    # 选择标题模板
                    title_templates = content_type.get('title_templates', ['{keyword} - 指南'])
                    title = title_templates[0].format(
                        keyword=keyword,
                        year=year
                    )
                    
                    # 创建URL友好的标识符
                    page_id = f"{sub_intent.lower()}_{i+1}_{keyword.lower().replace(' ', '_')}"
                    
                    # 创建内容页面
                    content_pages[page_id] = {
                        'type': 'content',
                        'intent': intent,
                        'sub_intent': sub_intent,
                        'keyword': keyword,
                        'title': title,
                        'url': f'/content/{page_id}',
                        'format': content_type.get('formats', ['文章'])[0],
                        'content_structure': content_type.get('content_structure', []),
                        'word_count': self.page_templates.get(intent, {}).get('word_count', 1500),
                        'conversion_strategy': content_type.get('conversion_strategy', '')
                    }
        
        self.website_structure['content_pages'] = content_pages
    
    def _generate_product_pages(self) -> None:
        """生成产品页面"""
        # 查找交易型(E)关键词
        e_keywords = self.intent_summary['intent_keywords'].get('E', [])
        
        # 如果没有交易型关键词，跳过
        if not e_keywords:
            self.website_structure['product_pages'] = {}
            return
        
        # 创建产品页面
        product_pages = {}
        
        # 为前5个交易型关键词创建产品页面
        for i, keyword in enumerate(e_keywords[:5]):
            # 创建URL友好的产品ID
            product_id = f"product_{i+1}_{keyword.lower().replace(' ', '_')}"
            
            # 创建产品页面
            product_pages[product_id] = {
                'type': 'product',
                'keyword': keyword,
                'title': f"{keyword} - 购买指南与最优惠",
                'url': f'/products/{product_id}',
                'sections': [
                    {'type': 'product_info', 'title': f'关于{keyword}'},
                    {'type': 'pricing', 'title': '价格方案'},
                    {'type': 'features', 'title': '主要功能'},
                    {'type': 'reviews', 'title': '用户评价'},
                    {'type': 'cta', 'title': '立即购买'}
                ],
                'seo_priority': 'high'
            }
        
        self.website_structure['product_pages'] = product_pages
    
    def _generate_category_pages(self, year: int) -> None:
        """生成分类页面"""
        # 创建分类页面
        category_pages = {}
        
        # 为每种主要意图创建一个分类页面
        for intent in set(self.intent_data['intent_primary']):
            # 只处理主意图
            if len(intent) != 1:
                continue
                
            intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
            
            # 创建分类页面
            category_pages[intent.lower()] = {
                'type': 'category',
                'intent': intent,
                'title': f"{intent_name}内容 - {year}年精选",
                'url': f'/categories/{intent.lower()}',
                'description': self._get_intent_description(intent),
                'layout': self.page_templates.get(intent, {}).get('layout', 'default'),
                'seo_priority': 'medium'
            }
        
        self.website_structure['category_pages'] = category_pages
    
    def create_content_plan(self) -> List[Dict[str, Any]]:
        """
        创建内容计划
        
        Returns:
            内容计划列表
        """
        if not self.website_structure:
            print("错误: 未生成网站结构")
            return []
        
        print("正在创建基于搜索意图的内容计划...")
        
        # 获取当前日期
        start_date = datetime.now()
        
        # 创建内容计划
        content_plan = []
        
        # 1. 首页内容
        content_plan.append({
            'week': 1,
            'publish_date': start_date.strftime('%Y-%m-%d'),
            'page_type': 'homepage',
            'title': self.website_structure['homepage']['title'],
            'url': '/',
            'priority': 'very_high',
            'word_count': 1000,
            'intent': 'multiple'
        })
        
        # 2. 意图页面内容
        week = 1
        for intent, pages in self.website_structure['intent_pages'].items():
            for page in pages:
                week += 1
                content_plan.append({
                    'week': week,
                    'publish_date': (start_date + timedelta(weeks=week-1)).strftime('%Y-%m-%d'),
                    'page_type': page['type'],
                    'title': page['title'],
                    'url': page['url'],
                    'priority': page['seo_priority'],
                    'word_count': self.page_templates.get(intent, {}).get('word_count', 1500),
                    'intent': intent
                })
        
        # 3. 内容页面
        for page_id, page in self.website_structure['content_pages'].items():
            week += 1
            content_plan.append({
                'week': week,
                'publish_date': (start_date + timedelta(weeks=week-1)).strftime('%Y-%m-%d'),
                'page_type': 'content',
                'title': page['title'],
                'url': page['url'],
                'priority': 'medium',
                'word_count': page['word_count'],
                'intent': page['intent'],
                'sub_intent': page.get('sub_intent', '')
            })
        
        # 4. 产品页面
        for page_id, page in self.website_structure['product_pages'].items():
            week += 1
            content_plan.append({
                'week': week,
                'publish_date': (start_date + timedelta(weeks=week-1)).strftime('%Y-%m-%d'),
                'page_type': 'product',
                'title': page['title'],
                'url': page['url'],
                'priority': 'high',
                'word_count': 2000,
                'intent': 'E'
            })
        
        # 5. 分类页面
        for page_id, page in self.website_structure['category_pages'].items():
            week += 1
            content_plan.append({
                'week': week,
                'publish_date': (start_date + timedelta(weeks=week-1)).strftime('%Y-%m-%d'),
                'page_type': 'category',
                'title': page['title'],
                'url': page['url'],
                'priority': 'medium',
                'word_count': 1000,
                'intent': page['intent']
            })
        
        # 保存内容计划
        self.content_plan = content_plan
        
        # 输出内容计划到文件
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.output_dir, f'content_plan_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(content_plan, f, ensure_ascii=False, indent=2)
        
        print(f"内容计划创建完成，共 {len(content_plan)} 个内容项，已保存到: {output_file}")
        
        return content_plan
    
    def generate_technical_plan(self) -> Dict[str, Any]:
        """
        生成技术实现方案
        
        Returns:
            技术方案字典
        """
        if not self.website_structure:
            print("错误: 未生成网站结构")
            return {}
        
        print("正在生成基于搜索意图的技术实现方案...")
        
        # 获取当前年份
        current_year = datetime.now().year
        
        # 创建技术方案
        tech_plan = {
            'project_name': f'意图驱动内容平台_{current_year}',
            'tech_stack': self.tech_stack,
            'page_templates': {},
            'data_models': [],
            'api_endpoints': [],
            'deployment_steps': []
        }
        
        # 1. 页面模板
        # 为每种意图类型创建页面模板
        for intent, template in self.page_templates.items():

            intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
            
            tech_plan['page_templates'][intent] = {
                'name': f"{intent_name}页面模板",
                'layout': template.get('layout', 'default'),
                'components': [section['type'] for section in template.get('sections', [])],
                'file_path': f'src/templates/{intent.lower()}_template.jsx',
                'data_requirements': [
                    'title',
                    'meta_description',
                    'sections',
                    'keywords',
                    'related_content'
                ]
            }
        
        # 2. 数据模型
        tech_plan['data_models'] = [
            {
                'name': 'Page',
                'fields': [
                    {'name': 'id', 'type': 'uuid', 'primary_key': True},
                    {'name': 'title', 'type': 'string', 'required': True},
                    {'name': 'slug', 'type': 'string', 'required': True, 'unique': True},
                    {'name': 'meta_description', 'type': 'string', 'required': True},
                    {'name': 'content', 'type': 'json', 'required': True},
                    {'name': 'intent_primary', 'type': 'string', 'required': True},
                    {'name': 'intent_secondary', 'type': 'string[]', 'required': False},
                    {'name': 'page_type', 'type': 'string', 'required': True},
                    {'name': 'template', 'type': 'string', 'required': True},
                    {'name': 'seo_priority', 'type': 'string', 'required': True},
                    {'name': 'created_at', 'type': 'timestamp', 'required': True},
                    {'name': 'updated_at', 'type': 'timestamp', 'required': True}
                ]
            },
            {
                'name': 'Keyword',
                'fields': [
                    {'name': 'id', 'type': 'uuid', 'primary_key': True},
                    {'name': 'query', 'type': 'string', 'required': True, 'unique': True},
                    {'name': 'intent_primary', 'type': 'string', 'required': True},
                    {'name': 'sub_intent', 'type': 'string', 'required': False},
                    {'name': 'search_volume', 'type': 'integer', 'required': False},
                    {'name': 'difficulty', 'type': 'float', 'required': False},
                    {'name': 'pages', 'type': 'relation', 'relation': 'Page[]', 'required': False}
                ]
            },
            {
                'name': 'ContentPlan',
                'fields': [
                    {'name': 'id', 'type': 'uuid', 'primary_key': True},
                    {'name': 'title', 'type': 'string', 'required': True},
                    {'name': 'page_id', 'type': 'relation', 'relation': 'Page', 'required': False},
                    {'name': 'publish_date', 'type': 'date', 'required': True},
                    {'name': 'status', 'type': 'string', 'required': True},
                    {'name': 'priority', 'type': 'string', 'required': True},
                    {'name': 'word_count', 'type': 'integer', 'required': True},
                    {'name': 'intent', 'type': 'string', 'required': True},
                    {'name': 'assigned_to', 'type': 'string', 'required': False}
                ]
            }
        ]
        
        # 3. API端点
        tech_plan['api_endpoints'] = [
            {
                'path': '/api/pages',
                'methods': ['GET', 'POST'],
                'description': '获取或创建页面',
                'parameters': {
                    'GET': ['intent', 'page_type', 'limit', 'offset'],
                    'POST': ['title', 'content', 'intent_primary', 'page_type', 'template']
                }
            },
            {
                'path': '/api/pages/:id',
                'methods': ['GET', 'PUT', 'DELETE'],
                'description': '获取、更新或删除特定页面',
                'parameters': {
                    'PUT': ['title', 'content', 'meta_description', 'seo_priority']
                }
            },
            {
                'path': '/api/keywords',
                'methods': ['GET', 'POST'],
                'description': '获取或添加关键词',
                'parameters': {
                    'GET': ['intent', 'limit', 'offset'],
                    'POST': ['query', 'intent_primary', 'sub_intent']
                }
            },
            {
                'path': '/api/content-plan',
                'methods': ['GET', 'POST'],
                'description': '获取或创建内容计划',
                'parameters': {
                    'GET': ['status', 'priority', 'limit', 'offset'],
                    'POST': ['title', 'publish_date', 'priority', 'intent', 'word_count']
                }
            }
        ]
        
        # 4. 部署步骤
        tech_plan['deployment_steps'] = [
            {
                'step': 1,
                'name': '初始化项目',
                'command': 'npx create-next-app@latest intent-based-website --typescript --tailwind --eslint',
                'description': '使用Next.js创建项目基础结构'
            },
            {
                'step': 2,
                'name': '安装依赖',
                'command': 'npm install @supabase/supabase-js contentful swr react-hook-form next-seo schema-dts',
                'description': '安装必要的依赖包'
            },
            {
                'step': 3,
                'name': '设置数据库',
                'command': 'npx supabase init',
                'description': '初始化Supabase项目并创建数据表'
            },
            {
                'step': 4,
                'name': '创建页面模板',
                'description': '根据意图类型创建不同的页面模板'
            },
            {
                'step': 5,
                'name': '实现API路由',
                'description': '创建Next.js API路由处理数据请求'
            },
            {
                'step': 6,
                'name': '部署到Vercel',
                'command': 'vercel deploy',
                'description': '将项目部署到Vercel平台'
            }
        ]
        
        # 5. 文件结构
        tech_plan['file_structure'] = {
            'src': {
                'pages': {
                    'index.tsx': '首页',
                    'intent': {
                        '[intent].tsx': '意图页面',
                        '[subIntent].tsx': '子意图页面'
                    },
                    'keyword': {
                        '[keyword].tsx': '关键词页面'
                    },
                    'content': {
                        '[id].tsx': '内容页面'
                    },
                    'products': {
                        '[id].tsx': '产品页面'
                    },
                    'categories': {
                        '[category].tsx': '分类页面'
                    },
                    'api': {
                        'pages.ts': '页面API',
                        'keywords.ts': '关键词API',
                        'content-plan.ts': '内容计划API'
                    }
                },
                'components': {
                    'layout': {
                        'Layout.tsx': '主布局组件',
                        'Header.tsx': '头部组件',
                        'Footer.tsx': '底部组件',
                        'Sidebar.tsx': '侧边栏组件'
                    },
                    'sections': {
                        'Hero.tsx': '英雄区组件',
                        'ContentBlock.tsx': '内容块组件',
                        'FeatureList.tsx': '特性列表组件',
                        'Comparison.tsx': '对比表组件',
                        'FAQ.tsx': '常见问题组件',
                        'CTABlock.tsx': '号召性用语组件'
                    },
                    'ui': {
                        'Button.tsx': '按钮组件',
                        'Card.tsx': '卡片组件',
                        'Table.tsx': '表格组件',
                        'Modal.tsx': '模态框组件'
                    }
                },
                'templates': {
                    'guide.tsx': '指南模板',
                    'landing.tsx': '落地页模板',
                    'comparison.tsx': '对比页模板',
                    'product.tsx': '产品页模板',
                    'support.tsx': '支持页模板',
                    'local.tsx': '本地页模板'
                },
                'lib': {
                    'supabase.ts': 'Supabase客户端',
                    'contentful.ts': 'Contentful客户端',
                    'seo.ts': 'SEO工具函数',
                    'intent.ts': '意图分析工具'
                },
                'styles': {
                    'globals.css': '全局样式',
                    'components.css': '组件样式'
                }
            },
            'public': {
                'images': '图片资源',
                'icons': '图标资源'
            }
        }
        
        # 保存技术方案
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.output_dir, f'technical_plan_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tech_plan, f, ensure_ascii=False, indent=2)
        
        print(f"技术实现方案生成完成，已保存到: {output_file}")
        
        return tech_plan
    
    def create_content_plan(self) -> List[Dict[str, Any]]:
        """
        创建内容计划
        
        Returns:
            内容计划列表
        """
        if not self.website_structure:
            print("错误: 未生成网站结构")
            return []
        
        print("正在创建基于搜索意图的内容计划...")
        
        # 获取当前日期
        start_date = datetime.now()
        
        # 创建内容计划
        content_plan = []
        
        # 1. 首页内容
        content_plan.append({
            'week': 1,
            'publish_date': start_date.strftime('%Y-%m-%d'),
            'page_type': 'homepage',
            'title': self.website_structure['homepage']['title'],
            'url': '/',
            'priority': 'very_high',
            'word_count': 1000,
            'intent': 'multiple'
        })
        
        # 2. 意图页面内容
        week = 1
        for intent, pages in self.website_structure['intent_pages'].items():
            for page in pages:
                week += 1
                content_plan.append({
                    'week': week,
                    'publish_date': (start_date + timedelta(weeks=week-1)).strftime('%Y-%m-%d'),
                    'page_type': page['type'],
                    'title': page['title'],
                    'url': page['url'],
                    'priority': page['seo_priority'],
                    'word_count': self.page_templates.get(intent, {}).get('word_count', 1500),
                    'intent': intent
                })
        
        # 3. 内容页面
        for page_id, page in self.website_structure['content_pages'].items():
            week += 1
            content_plan.append({
                'week': week,
                'publish_date': (start_date + timedelta(weeks=week-1)).strftime('%Y-%m-%d'),
                'page_type': 'content',
                'title': page['title'],
                'url': page['url'],
                'priority': 'medium',
                'word_count': page['word_count'],
                'intent': page['intent'],
                'sub_intent': page.get('sub_intent', '')
            })
        
        # 4. 产品页面
        for page_id, page in self.website_structure['product_pages'].items():
            week += 1
            content_plan.append({
                'week': week,
                'publish_date': (start_date + timedelta(weeks=week-1)).strftime('%Y-%m-%d'),
                'page_type': 'product',
                'title': page['title'],
                'url': page['url'],
                'priority': 'high',
                'word_count': 2000,
                'intent': 'E'
            })
        
        # 5. 分类页面
        for page_id, page in self.website_structure['category_pages'].items():
            week += 1
            content_plan.append({
                'week': week,
                'publish_date': (start_date + timedelta(weeks=week-1)).strftime('%Y-%m-%d'),
                'page_type': 'category',
                'title': page['title'],
                'url': page['url'],
                'priority': 'medium',
                'word_count': 1000,
                'intent': page['intent']
            })
        
        # 保存内容计划
        self.content_plan = content_plan
        
        # 输出内容计划到文件
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.output_dir, f'content_plan_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(content_plan, f, ensure_ascii=False, indent=2)
        
        print(f"内容计划创建完成，共 {len(content_plan)} 个内容项，已保存到: {output_file}")
        
        return content_plan
    
    def generate_technical_plan(self) -> Dict[str, Any]:
        """
        生成技术实现方案
        
        Returns:
            技术方案字典
        """
        if not self.website_structure:
            print("错误: 未生成网站结构")
            return {}
        
        print("正在生成基于搜索意图的技术实现方案...")
        
        # 获取当前年份
        current_year = datetime.now().year
        
        # 创建技术方案
        tech_plan = {
            'project_name': f'意图驱动内容平台_{current_year}',
            'tech_stack': self.tech_stack,
            'page_templates': {},
            'data_models': [],
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于搜索意图的网站自动建设工具

该工具基于最新的搜索意图分析规则（6主意图×24子意图）自动生成网站结构和内容计划，
针对不同的搜索意图类型设计不同的页面模板和内容策略，以优化SEO效果和用户体验。
"""

import os
import json
import yaml
import pandas as pd
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict

# 导入意图分析器
try:
    from src.analyzers.intent_analyzer_v2 import IntentAnalyzerV2
except ImportError:
    print("警告: 无法导入IntentAnalyzerV2，将使用本地实现")
    # 如果无法导入，使用简化版本
    class IntentAnalyzerV2:
        """简化版意图分析器"""
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


class IntentBasedWebsiteBuilder:
    """基于搜索意图的网站自动建设工具"""
    
    def __init__(self, intent_data_path: str = None, output_dir: str = 'output'):
        """
        初始化网站建设工具
        
        Args:
            intent_data_path: 意图分析数据路径（CSV或JSON）
            output_dir: 输出目录
        """
        self.intent_data_path = intent_data_path
        self.output_dir = output_dir
        self.intent_data = None
        self.intent_summary = None
        self.analyzer = IntentAnalyzerV2()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 页面模板配置
        self.page_templates = self._load_page_templates()
        
        # 内容类型配置
        self.content_types = self._get_content_types()
        
        # SEO配置
        self.seo_config = self._get_seo_config()
        
        # 网站结构
        self.website_structure = {
            'homepage': {},
            'intent_pages': {},
            'content_pages': {},
            'product_pages': {},
            'category_pages': {}
        }
        
        # 内容计划
        self.content_plan = []
        
        # 技术栈配置
        self.tech_stack = self._get_tech_stack()
        
        print("基于搜索意图的网站自动建设工具初始化完成")
    
    def _load_page_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载页面模板配置"""
        return {
            # 信息获取型页面模板
            'I': {
                'layout': 'guide',
                'sections': [
                    {'type': 'hero', 'title': '{keyword} 完全指南', 'description': '了解关于{keyword}的一切'},
                    {'type': 'toc', 'title': '目录'},
                    {'type': 'definition', 'title': '{keyword}是什么?'},
                    {'type': 'steps', 'title': '如何使用{keyword}'},
                    {'type': 'faq', 'title': '常见问题'},
                    {'type': 'related', 'title': '相关资源'}
                ],
                'cta': '深入了解',
                'word_count': 2000,
                'media_ratio': 0.3,  # 30%的内容是媒体（图片、视频）
                'seo_priority': 'high'
            },
            # 导航直达型页面模板
            'N': {
                'layout': 'landing',
                'sections': [
                    {'type': 'hero', 'title': '{keyword} 官方入口', 'description': '快速访问{keyword}'},
                    {'type': 'features', 'title': '主要功能'},
                    {'type': 'cta_block', 'title': '立即访问'},
                    {'type': 'alternatives', 'title': '其他选择'}
                ],
                'cta': '立即访问',
                'word_count': 800,
                'media_ratio': 0.2,
                'seo_priority': 'medium'
            },
            # 商业评估型页面模板
            'C': {
                'layout': 'comparison',
                'sections': [
                    {'type': 'hero', 'title': '{year}年最佳{keyword}推荐', 'description': '全面对比{keyword}'},
                    {'type': 'comparison_table', 'title': '{keyword}对比表'},
                    {'type': 'top_picks', 'title': '编辑推荐'},
                    {'type': 'reviews', 'title': '详细评测'},
                    {'type': 'buying_guide', 'title': '购买指南'},
                    {'type': 'faq', 'title': '常见问题'}
                ],
                'cta': '查看最佳选择',
                'word_count': 3000,
                'media_ratio': 0.25,
                'seo_priority': 'very_high'
            },
            # 交易购买型页面模板
            'E': {
                'layout': 'product',
                'sections': [
                    {'type': 'hero', 'title': '购买{keyword}', 'description': '最优惠的{keyword}价格'},
                    {'type': 'pricing', 'title': '价格方案'},
                    {'type': 'deals', 'title': '限时优惠'},
                    {'type': 'testimonials', 'title': '用户评价'},
                    {'type': 'guarantee', 'title': '购买保障'}
                ],
                'cta': '立即购买',
                'word_count': 1500,
                'media_ratio': 0.3,
                'seo_priority': 'high'
            },
            # 行为后续型页面模板
            'B': {
                'layout': 'support',
                'sections': [
                    {'type': 'hero', 'title': '{keyword}使用指南', 'description': '解决{keyword}使用问题'},
                    {'type': 'troubleshooting', 'title': '常见问题解决'},
                    {'type': 'advanced_tips', 'title': '高级技巧'},
                    {'type': 'community', 'title': '社区支持'},
                    {'type': 'updates', 'title': '最新更新'}
                ],
                'cta': '获取支持',
                'word_count': 2500,
                'media_ratio': 0.4,
                'seo_priority': 'medium'
            },
            # 本地/到店型页面模板
            'L': {
                'layout': 'local',
                'sections': [
                    {'type': 'hero', 'title': '附近的{keyword}', 'description': '找到离您最近的{keyword}'},
                    {'type': 'map', 'title': '位置地图'},
                    {'type': 'locations', 'title': '所有位置'},
                    {'type': 'hours', 'title': '营业时间'},
                    {'type': 'directions', 'title': '到达方式'}
                ],
                'cta': '查看位置',
                'word_count': 1000,
                'media_ratio': 0.5,
                'seo_priority': 'medium'
            }
        }
    
    def _get_content_types(self) -> Dict[str, Dict[str, Any]]:
        """获取内容类型配置"""
        return {
            # 信息获取型内容
            'I': {
                'I1': {  # 定义/概念
                    'formats': ['百科词条', '概念解释', '术语表'],
                    'title_templates': [
                        '什么是{keyword}？完整解释',
                        '{keyword}是什么意思？详细定义',
                        '{keyword}百科：你需要知道的一切'
                    ],
                    'meta_description': '{keyword}的完整定义和解释，了解{keyword}的含义、起源和应用场景。',
                    'content_structure': ['定义', '历史背景', '核心概念', '应用场景', '常见误区', '延伸阅读'],
                    'conversion_strategy': '引导到更深入的教程或相关产品'
                },
                'I2': {  # 原理/源码
                    'formats': ['技术文档', '原理解析', '源码分析'],
                    'title_templates': [
                        '{keyword}工作原理详解',
                        '{keyword}背后的技术：深度解析',
                        '{keyword}源码分析与架构设计'
                    ],
                    'meta_description': '深入解析{keyword}的工作原理、技术架构和源码实现，适合开发者和技术爱好者。',
                    'content_structure': ['技术概述', '架构设计', '核心算法', '源码分析', '性能考量', '实现挑战'],
                    'conversion_strategy': '引导到高级教程或开发者社区'
                },
                'I3': {  # 教程/步骤
                    'formats': ['分步教程', '操作指南', '视频教程'],
                    'title_templates': [
                        '{keyword}教程：从入门到精通',
                        '如何使用{keyword}：完整指南',
                        '{keyword}新手指南：10个简单步骤'
                    ],
                    'meta_description': '学习如何使用{keyword}的详细教程，包含分步指南和实用技巧，适合初学者。',
                    'content_structure': ['准备工作', '基础步骤', '进阶技巧', '常见问题', '实战案例', '下一步学习'],
                    'conversion_strategy': '引导到相关工具或高级课程'
                },
                'I4': {  # 事实求证
                    'formats': ['事实核查', '真相解析', '专家观点'],
                    'title_templates': [
                        '{keyword}是否真的有效？科学解析',
                        '{keyword}的真相：分析与验证',
                        '{keyword}：常见说法的真假分析'
                    ],
                    'meta_description': '深入分析{keyword}的真实情况，基于事实和数据验证常见说法的真伪。',
                    'content_structure': ['常见说法', '事实依据', '专家观点', '研究数据', '结论分析', '延伸阅读'],
                    'conversion_strategy': '建立权威性，引导到相关服务'
                }
            },
            # 导航直达型内容
            'N': {
                'N1': {  # 官方主页
                    'formats': ['官方介绍', '品牌页面', '产品主页'],
                    'title_templates': [
                        '{keyword}官方网站 - 权威入口',
                        '{keyword}官方主页 - 直达链接',
                        '访问{keyword}官方网站 - 安全链接'
                    ],
                    'meta_description': '{keyword}的官方网站入口，获取最新信息、产品介绍和官方支持。',
                    'content_structure': ['品牌介绍', '产品概述', '官方链接', '最新动态', '联系方式'],
                    'conversion_strategy': '直接引导到官方网站或产品'
                },
                'N2': {  # 登录/控制台
                    'formats': ['登录指南', '控制台教程', '账户管理'],
                    'title_templates': [
                        '{keyword}登录入口及使用指南',
                        '如何登录{keyword}控制台 - 详细步骤',
                        '{keyword}账户管理与控制台使用技巧'
                    ],
                    'meta_description': '{keyword}登录入口指南，包含登录步骤、控制台使用技巧和账户管理方法。',
                    'content_structure': ['登录入口', '账户创建', '控制台导航', '常见问题', '安全提示'],
                    'conversion_strategy': '引导到登录页面或账户创建'
                },
                'N3': {  # 下载/安装包
                    'formats': ['下载指南', '安装教程', '版本对比'],
                    'title_templates': [
                        '{keyword}下载：官方最新版本',
                        '如何下载并安装{keyword} - 完整指南',
                        '{keyword}各版本下载与对比'
                    ],
                    'meta_description': '{keyword}的官方下载链接和详细安装指南，包含各版本对比和系统要求。',
                    'content_structure': ['下载链接', '系统要求', '安装步骤', '版本对比', '常见问题'],
                    'conversion_strategy': '引导到下载页面或高级版本'
                }
            },
            # 商业评估型内容
            'C': {
                'C1': {  # 榜单/推荐
                    'formats': ['排行榜', '推荐清单', '编辑精选'],
                    'title_templates': [
                        '{year}年最佳{keyword}推荐：排名前10',
                        '{keyword}排行榜：专家评选与推荐',
                        '最值得使用的{keyword}：完整榜单'
                    ],
                    'meta_description': '{year}年最新{keyword}排行榜，基于专业测评和用户反馈，帮您选择最适合的产品。',
                    'content_structure': ['评选标准', '榜单总览', '详细点评', '价格对比', '如何选择', '常见问题'],
                    'conversion_strategy': '引导到详细评测或购买链接'
                },
                'C2': {  # 对比/评测
                    'formats': ['对比分析', '深度评测', '功能对比表'],
                    'title_templates': [
                        '{keyword}对比：哪个最好？{year}年全面分析',
                        '{keyword1} vs {keyword2}：哪个更值得选择？',
                        '{keyword}深度评测：优缺点全面分析'
                    ],
                    'meta_description': '全面对比各种{keyword}的功能、价格和性能，帮您找到最适合自己需求的选择。',
                    'content_structure': ['对比概述', '功能对比', '性能测试', '价格分析', '适用场景', '最终推荐'],
                    'conversion_strategy': '基于需求引导到最佳选择'
                },
                'C3': {  # 口碑/点评
                    'formats': ['用户评价汇总', '真实使用体验', '长期使用报告'],
                    'title_templates': [
                        '{keyword}用户评价：真实体验分享',
                        '我用{keyword}一年后的真实感受',
                        '{keyword}口碑调查：用户最关心的问题'
                    ],
                    'meta_description': '汇总真实用户对{keyword}的评价和使用体验，揭示产品的真实优缺点和使用感受。',
                    'content_structure': ['评价概述', '优点汇总', '缺点分析', '用户案例', '专家观点', '总体评价'],
                    'conversion_strategy': '基于真实体验建立信任，引导到推荐产品'
                }
            },
            # 交易购买型内容
            'E': {
                'E1': {  # 价格/报价
                    'formats': ['价格指南', '费用分析', '预算规划'],
                    'title_templates': [
                        '{keyword}价格指南：各版本详细对比',
                        '{keyword}要多少钱？完整价格分析',
                        '{keyword}费用明细：从基础版到高级版'
                    ],
                    'meta_description': '{keyword}的详细价格信息，包含各版本费用对比、隐藏成本分析和最佳购买时机。',
                    'content_structure': ['价格总览', '版本对比', '隐藏成本', '性价比分析', '购买建议'],
                    'conversion_strategy': '引导到最佳价格或优惠购买渠道'
                },
                'E2': {  # 优惠/折扣
                    'formats': ['优惠信息', '折扣代码', '促销活动'],
                    'title_templates': [
                        '{keyword}优惠券与折扣码：省钱指南',
                        '{keyword}最新促销活动汇总',
                        '如何以最低价格购买{keyword}'
                    ],
                    'meta_description': '最新{keyword}优惠信息，包含折扣码、促销活动和特别优惠，帮您省钱购买。',
                    'content_structure': ['当前优惠', '折扣码汇总', '会员特价', '季节性促销', '省钱技巧'],
                    'conversion_strategy': '创造紧迫感，引导立即购买'
                },
                'E3': {  # 下单/预订
                    'formats': ['购买指南', '订购流程', '预订教程'],
                    'title_templates': [
                        '如何购买{keyword}：详细步骤指南',
                        '{keyword}订购流程：避开常见陷阱',
                        '{keyword}预订攻略：确保最佳体验'
                    ],
                    'meta_description': '详细指导如何购买或预订{keyword}，包含步骤说明、注意事项和支付方式介绍。',
                    'content_structure': ['准备工作', '购买步骤', '支付选项', '注意事项', '售后服务'],
                    'conversion_strategy': '简化购买流程，减少放弃率'
                }
            },
            # 行为后续型内容
            'B': {
                'B1': {  # 故障/报错
                    'formats': ['故障排除指南', '错误代码解析', '问题解决方案'],
                    'title_templates': [
                        '{keyword}常见问题及解决方法',
                        '{keyword}错误代码大全及修复指南',
                        '解决{keyword}故障的完整指南'
                    ],
                    'meta_description': '全面解析{keyword}常见故障和错误代码，提供详细的排查步骤和解决方案。',
                    'content_structure': ['常见问题', '错误代码', '排查步骤', '解决方案', '预防措施'],
                    'conversion_strategy': '提供高级支持或升级服务'
                },
                'B2': {  # 高级用法
                    'formats': ['高级技巧', '专家指南', '进阶教程'],
                    'title_templates': [
                        '{keyword}高级技巧：提升使用效率',
                        '{keyword}进阶指南：从熟练到精通',
                        '{keyword}专家用法：鲜为人知的功能'
                    ],
                    'meta_description': '探索{keyword}的高级功能和使用技巧，帮助有经验的用户进一步提升效率和体验。',
                    'content_structure': ['基础回顾', '高级功能', '效率技巧', '自定义设置', '案例分享'],
                    'conversion_strategy': '引导到专业版或付费课程'
                },
                'B3': {  # 配置/设置
                    'formats': ['配置指南', '设置教程', '优化方案'],
                    'title_templates': [
                        '{keyword}最佳配置指南：优化性能',
                        '如何正确设置{keyword}：详细教程',
                        '{keyword}设置技巧：提升使用体验'
                    ],
                    'meta_description': '详细指导如何配置和设置{keyword}，包含最佳实践和性能优化建议。',
                    'content_structure': ['基本设置', '高级配置', '性能优化', '安全设置', '常见问题'],
                    'conversion_strategy': '引导到配置服务或高级支持'
                }
            },
            # 本地/到店型内容
            'L': {
                'L1': {  # 附近门店
                    'formats': ['位置指南', '门店列表', '区域地图'],
                    'title_templates': [
                        '附近的{keyword}：完整位置指南',
                        '{location}地区{keyword}门店大全',
                        '如何找到离你最近的{keyword}'
                    ],
                    'meta_description': '查找离您最近的{keyword}位置，包含详细地址、联系方式和服务内容。',
                    'content_structure': ['位置总览', '详细地址', '服务内容', '联系方式', '用户评价'],
                    'conversion_strategy': '引导到地图导航或预约'
                },
                'L2': {  # 预约/路线
                    'formats': ['预约指南', '到店路线', '交通指南'],
                    'title_templates': [
                        '如何预约{keyword}：详细步骤',
                        '前往{keyword}的最佳路线指南',
                        '{keyword}预约系统使用教程'
                    ],
                    'meta_description': '详细指导如何预约{keyword}服务，以及前往各个位置的交通路线和停车信息。',
                    'content_structure': ['预约流程', '准备事项', '交通方式', '停车信息', '到店须知'],
                    'conversion_strategy': '简化预约流程，提高到店率'
                },
                'L3': {  # 开放时间
                    'formats': ['营业时间', '节假日安排', '特殊时段'],
                    'title_templates': [
                        '{keyword}营业时间：完整时间表',
                        '{keyword}节假日开放时间安排',
                        '{keyword}各门店营业时间大全'
                    ],
                    'meta_description': '{keyword}的详细营业时间，包含各分店时间表、节假日安排和特殊时段调整。',
                    'content_structure': ['常规时间', '节假日安排', '特殊时段', '提前预约', '联系方式'],
                    'conversion_strategy': '引导到预约系统或特别活动'
                }
            }
        }
    
    def _get_seo_config(self) -> Dict[str, Any]:
        """获取SEO配置"""
        return {
            'title_patterns': {
                'I': '{keyword} 指南：完整教程与使用方法 ({year})',
                'N': '{keyword} 官方入口 - 安全直达链接',
                'C': '{year}年最佳{keyword}推荐：排名与对比',
                'E': '{keyword}价格与购买指南：如何获得最优惠',
                'B': '{keyword}问题解决与高级使用技巧',
                'L': '附近的{keyword}：位置、时间与预约'
            },
            'meta_description_patterns': {
                'I': '全面了解{keyword}的详细指南，包含使用方法、最佳实践和常见问题解答。',
                'N': '{keyword}的官方入口，安全可靠，直达目标网站，避免钓鱼和欺诈风险。',
                'C': '专业评测{year}年最佳{keyword}，基于实际使用体验和性能测试，帮您做出明智选择。',
                'E': '{keyword}的最新价格信息、购买渠道和折扣优惠，助您以最优惠的价格获取产品。',
                'B': '解决{keyword}使用过程中的常见问题，掌握高级技巧，充分发挥产品潜力。',
                'L': '查找离您最近的{keyword}位置，了解营业时间、预约方式和到店路线。'
            },
            'heading_structure': {
                'h1_pattern': '{main_keyword} - {sub_keyword}',
                'h2_count': {'min': 3, 'max': 7},
                'h3_per_h2': {'min': 2, 'max': 5}
            },
            'content_guidelines': {
                'paragraph_length': {'min': 3, 'max': 5},  # 每段句子数
                'sentence_length': {'min': 10, 'max': 20},  # 每句词数
                'keyword_density': {'min': 0.5, 'max': 2.0},  # 关键词密度百分比
                'readability': 'middle_school'  # 可读性级别
            },
            'schema_markup': {
                'I': 'HowTo',
                'N': 'WebPage',
                'C': 'Review',
                'E': 'Product',
                'B': 'FAQPage',
                'L': 'LocalBusiness'
            },
            'internal_linking': {
                'links_per_page': {'min': 3, 'max': 8},
                'anchor_text_variation': True,
                'link_to_related_intents': True
            }
        }
    
    def _get_tech_stack(self) -> Dict[str, Any]:
        """获取技术栈配置"""
        return {
            'frontend': {
                'framework': 'Next.js',
                'styling': 'Tailwind CSS',
                'features': [
                    'SSR (Server-Side Rendering)',
                    'ISR (Incremental Static Regeneration)',
                    '响应式设计',
                    '暗黑模式',
                    'PWA支持'
                ]
            },
            'backend': {
                'framework': 'Next.js API Routes',
                'database': 'PostgreSQL (Supabase)',
                'cms': 'Contentful',
                'features': [
                    'RESTful API',
                    '内容管理',
                    '用户认证',
                    '搜索功能',
                    '数据分析'
                ]
            },
            'deployment': {
                'hosting': 'Vercel',
                'cdn': 'Cloudflare',
                'monitoring': 'Sentry',
                'analytics': 'Google Analytics 4'
            },
            'seo_tools': {
                'sitemap': 'next-sitemap',
                'meta_tags': 'next-seo',
                'schema': 'schema-dts',
                'analytics': 'GA4 + GTM'
            },
            'performance': {
                'image_optimization': 'next/image',
                'code_splitting': 'Automatic',
                'lazy_loading': 'Enabled',
                'caching': 'SWR + Redis'
            }
        }
    
    def load_intent_data(self) -> bool:
        """
        加载意图分析数据
        
        Returns:
            加载是否成功
        """
        if not self.intent_data_path:
            print("错误: 未指定意图数据路径")
            return False
        
        try:
            # 根据文件扩展名决定加载方式
            if self.intent_data_path.endswith('.csv'):
                self.intent_data = pd.read_csv(self.intent_data_path)
                print(f"已从CSV加载 {len(self.intent_data)}