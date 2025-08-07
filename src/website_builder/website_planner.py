#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI工具网站架构规划工具
基于关键词分析结果生成详细的网站建设计划
"""

import json
import pandas as pd
from datetime import datetime, timedelta
import os

class WebsitePlanner:
    def __init__(self):
        self.site_structure = {}
        self.monetization_strategy = {}
        self.seo_strategy = {}
        
    def load_clustering_data(self):
        """加载聚类分析数据"""
        try:
            # 查找最新的聚类文件
            clustering_files = [f for f in os.listdir('data/ai_tools_analysis/') 
                              if f.startswith('keyword_clustering_')]
            if not clustering_files:
                print("未找到聚类分析文件，请先运行 keyword_clustering.py")
                return None
                
            latest_file = sorted(clustering_files)[-1]
            file_path = f'data/ai_tools_analysis/{latest_file}'
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载聚类数据失败: {e}")
            return None
    
    def generate_monetization_strategy(self, clustering_data):
        """生成变现策略"""
        monetization_plan = {
            'affiliate_marketing': {
                'description': '推广AI工具获得佣金',
                'target_categories': ['chatbot', 'image_generation', 'writing_tools', 'coding_tools'],
                'estimated_revenue_per_month': 5000,
                'implementation_priority': 'high',
                'action_items': [
                    '申请主要AI工具的联盟计划',
                    '创建详细的工具评测内容',
                    '设置转化跟踪系统'
                ]
            },
            'display_ads': {
                'description': 'Google AdSense和其他广告网络',
                'estimated_revenue_per_month': 2000,
                'implementation_priority': 'medium',
                'requirements': '月访问量达到10万+'
            },
            'sponsored_content': {
                'description': '赞助文章和工具推荐',
                'estimated_revenue_per_month': 3000,
                'implementation_priority': 'medium',
                'requirements': '建立品牌影响力'
            },
            'premium_content': {
                'description': '付费会员和高级内容',
                'estimated_revenue_per_month': 1500,
                'implementation_priority': 'low',
                'requirements': '积累足够用户基础'
            }
        }
        
        return monetization_plan
    
    def create_seo_strategy(self, clustering_data):
        """创建SEO策略"""
        website_structure = clustering_data.get('website_structure', {})
        
        seo_strategy = {
            'technical_seo': {
                'site_speed': '页面加载时间 < 3秒',
                'mobile_optimization': '响应式设计，移动端友好',
                'ssl_certificate': 'HTTPS加密',
                'sitemap': '自动生成XML站点地图',
                'robots_txt': '优化爬虫抓取规则'
            },
            'content_seo': {
                'keyword_density': '主关键词密度2-3%',
                'internal_linking': '相关文章互相链接',
                'meta_optimization': '标题和描述包含目标关键词',
                'structured_data': '使用Schema.org标记',
                'content_freshness': '定期更新内容'
            },
            'off_page_seo': {
                'backlink_building': '获取高质量外链',
                'social_signals': '社交媒体分享',
                'guest_posting': '在相关网站发布客座文章',
                'directory_submission': '提交到相关目录'
            }
        }
        
        return seo_strategy
    
    def generate_content_calendar(self, clustering_data):
        """生成内容发布日历"""
        content_calendar = clustering_data.get('content_calendar', [])
        
        # 扩展内容日历，添加更多细节
        enhanced_calendar = []
        start_date = datetime.now()
        
        for i, content in enumerate(content_calendar[:12]):  # 前12周
            publish_date = start_date + timedelta(weeks=i)
            
            enhanced_content = {
                'week': i + 1,
                'publish_date': publish_date.strftime('%Y-%m-%d'),
                'category': content['category'],
                'content_type': content['content_type'],
                'page_title': content['page_title'],
                'target_keywords': content['target_keywords'],
                'estimated_traffic': content['estimated_traffic'],
                'priority_score': content['priority_score'],
                'url_slug': content['url_slug'],
                'word_count': self.estimate_word_count(content['content_type']),
                'content_outline': self.generate_content_outline(content),
                'monetization_focus': self.get_monetization_focus(content['category'])
            }
            
            enhanced_calendar.append(enhanced_content)
        
        return enhanced_calendar
    
    def estimate_word_count(self, content_type):
        """估算内容字数"""
        word_counts = {
            'review': 2500,
            'tutorial': 3000,
            'best': 3500,
            'comparison': 2000,
            'guide': 2800,
            'general': 2000
        }
        return word_counts.get(content_type, 2000)
    
    def generate_content_outline(self, content):
        """生成内容大纲"""
        content_type = content['content_type']
        category = content['category']
        
        outlines = {
            'review': [
                '工具简介和背景',
                '主要功能特点',
                '使用体验评测',
                '优缺点分析',
                '价格和套餐',
                '与竞品对比',
                '适用人群推荐',
                '总结和评分'
            ],
            'best': [
                '行业概述',
                '评选标准',
                '工具排名列表',
                '详细功能对比',
                '价格对比分析',
                '使用场景推荐',
                '选择建议',
                '未来趋势'
            ],
            'tutorial': [
                '工具介绍',
                '准备工作',
                '步骤详解',
                '实际案例',
                '常见问题',
                '进阶技巧',
                '相关工具推荐',
                '总结'
            ]
        }
        
        return outlines.get(content_type, ['介绍', '主要内容', '实例', '总结'])
    
    def get_monetization_focus(self, category):
        """获取变现重点"""
        monetization_map = {
            'chatbot': 'affiliate_links',
            'image_generation': 'affiliate_links',
            'writing_tools': 'affiliate_links',
            'coding_tools': 'affiliate_links',
            'video_tools': 'sponsored_content',
            'audio_ai': 'display_ads',
            'business_automation': 'affiliate_links',
            'research_tools': 'premium_content'
        }
        
        return monetization_map.get(category, 'display_ads')
    
    def create_technical_requirements(self):
        """创建技术需求文档"""
        tech_requirements = {
            'frontend': {
                'framework': 'Next.js (React)',
                'styling': 'Tailwind CSS',
                'components': 'Headless UI',
                'features': [
                    '响应式设计',
                    '搜索功能',
                    '分类筛选',
                    '工具对比功能',
                    '用户评分系统',
                    '社交分享按钮'
                ]
            },
            'backend': {
                'framework': 'Node.js + Express',
                'database': 'PostgreSQL',
                'cms': 'Strapi或自建',
                'features': [
                    'RESTful API',
                    '内容管理',
                    '用户管理',
                    '分析统计',
                    '邮件订阅',
                    'SEO优化'
                ]
            },
            'hosting': {
                'platform': 'Vercel或Netlify',
                'cdn': 'Cloudflare',
                'database_hosting': 'Supabase或Railway',
                'monitoring': 'Google Analytics + Search Console'
            },
            'third_party_integrations': [
                'Google AdSense',
                'Amazon Associates',
                'Mailchimp',
                'Disqus评论系统',
                'Hotjar用户行为分析'
            ]
        }
        
        return tech_requirements
    
    def generate_launch_timeline(self):
        """生成发布时间线"""
        timeline = [
            {
                'phase': '准备阶段',
                'duration': '2周',
                'tasks': [
                    '域名注册和服务器配置',
                    '设计系统和UI组件开发',
                    '基础架构搭建',
                    '内容管理系统设置'
                ]
            },
            {
                'phase': '开发阶段',
                'duration': '4周',
                'tasks': [
                    '核心功能开发',
                    '工具数据库建设',
                    '搜索和筛选功能',
                    '用户交互功能'
                ]
            },
            {
                'phase': '内容创建',
                'duration': '3周',
                'tasks': [
                    '首批20个工具评测',
                    '分类页面内容',
                    '关于页面和政策页面',
                    'SEO优化'
                ]
            },
            {
                'phase': '测试和优化',
                'duration': '1周',
                'tasks': [
                    '功能测试',
                    '性能优化',
                    '移动端适配',
                    '最终检查'
                ]
            },
            {
                'phase': '正式发布',
                'duration': '1周',
                'tasks': [
                    '域名解析',
                    '搜索引擎提交',
                    '社交媒体宣传',
                    '监控和反馈收集'
                ]
            }
        ]
        
        return timeline
    
    def run_planning(self):
        """执行完整的网站规划"""
        print("开始网站架构规划...")
        
        # 加载聚类数据
        clustering_data = self.load_clustering_data()
        if not clustering_data:
            return
        
        # 生成各种策略
        monetization_strategy = self.generate_monetization_strategy(clustering_data)
        seo_strategy = self.create_seo_strategy(clustering_data)
        content_calendar = self.generate_content_calendar(clustering_data)
        tech_requirements = self.create_technical_requirements()
        launch_timeline = self.generate_launch_timeline()
        
        # 创建完整的网站规划文档
        website_plan = {
            'project_overview': {
                'name': 'AI工具导航网站',
                'description': '专业的AI工具评测和推荐平台',
                'target_audience': '企业用户、开发者、内容创作者',
                'primary_goal': '通过高质量内容获取流量并实现变现',
                'estimated_launch_date': (datetime.now() + timedelta(weeks=11)).strftime('%Y-%m-%d')
            },
            'keyword_analysis_summary': {
                'total_keywords': clustering_data.get('total_keywords', 0),
                'categories_found': clustering_data.get('categories_found', 0),
                'high_value_keywords': len([kw for kw in clustering_data.get('categorized_keywords', {}).values() 
                                          for intent_group in kw.values() 
                                          for keyword in intent_group if keyword.get('score', 0) >= 50])
            },
            'website_structure': clustering_data.get('website_structure', {}),
            'monetization_strategy': monetization_strategy,
            'seo_strategy': seo_strategy,
            'content_calendar': content_calendar,
            'technical_requirements': tech_requirements,
            'launch_timeline': launch_timeline,
            'success_metrics': {
                'month_1': {'visitors': 5000, 'revenue': 500},
                'month_3': {'visitors': 25000, 'revenue': 2500},
                'month_6': {'visitors': 100000, 'revenue': 8000},
                'month_12': {'visitors': 300000, 'revenue': 15000}
            }
        }
        
        # 保存规划文档
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = f'data/ai_tools_analysis/website_plan_{timestamp}.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(website_plan, f, ensure_ascii=False, indent=2)
        
        # 生成执行清单
        self.generate_action_checklist(website_plan, timestamp)
        
        print(f"\n网站规划完成！")
        print(f"详细规划文档: {output_file}")
        print(f"预计发布时间: {website_plan['project_overview']['estimated_launch_date']}")
        
        # 显示关键信息
        print(f"\n=== 项目概览 ===")
        print(f"目标关键词: {website_plan['keyword_analysis_summary']['total_keywords']} 个")
        print(f"内容类别: {website_plan['keyword_analysis_summary']['categories_found']} 个")
        print(f"高价值关键词: {website_plan['keyword_analysis_summary']['high_value_keywords']} 个")
        
        print(f"\n=== 变现预期 ===")
        for strategy, details in monetization_strategy.items():
            if 'estimated_revenue_per_month' in details:
                print(f"{strategy}: ${details['estimated_revenue_per_month']}/月")
        
        print(f"\n=== 下一步行动 ===")
        print("1. 审查网站规划文档")
        print("2. 选择技术栈和开发工具")
        print("3. 开始域名注册和服务器配置")
        print("4. 创建项目开发计划")
        
        return website_plan
    
    def generate_action_checklist(self, website_plan, timestamp):
        """生成行动清单"""
        checklist_items = []
        
        # 技术准备清单
        checklist_items.extend([
            {'category': '技术准备', 'task': '注册域名', 'priority': 'high', 'estimated_hours': 1},
            {'category': '技术准备', 'task': '选择托管服务', 'priority': 'high', 'estimated_hours': 2},
            {'category': '技术准备', 'task': '设置开发环境', 'priority': 'high', 'estimated_hours': 4},
            {'category': '技术准备', 'task': '配置数据库', 'priority': 'high', 'estimated_hours': 3}
        ])
        
        # 设计和开发清单
        checklist_items.extend([
            {'category': '设计开发', 'task': '创建网站设计稿', 'priority': 'high', 'estimated_hours': 16},
            {'category': '设计开发', 'task': '开发核心功能', 'priority': 'high', 'estimated_hours': 40},
            {'category': '设计开发', 'task': '实现搜索功能', 'priority': 'medium', 'estimated_hours': 12},
            {'category': '设计开发', 'task': '添加用户交互', 'priority': 'medium', 'estimated_hours': 8}
        ])
        
        # 内容创建清单
        for content in website_plan['content_calendar'][:5]:
            checklist_items.append({
                'category': '内容创建',
                'task': f"创建: {content['page_title']}",
                'priority': 'high' if content['priority_score'] > 45 else 'medium',
                'estimated_hours': content['word_count'] // 200  # 估算写作时间
            })
        
        # SEO优化清单
        checklist_items.extend([
            {'category': 'SEO优化', 'task': '设置Google Analytics', 'priority': 'high', 'estimated_hours': 1},
            {'category': 'SEO优化', 'task': '提交Google Search Console', 'priority': 'high', 'estimated_hours': 1},
            {'category': 'SEO优化', 'task': '创建XML站点地图', 'priority': 'medium', 'estimated_hours': 2},
            {'category': 'SEO优化', 'task': '优化页面加载速度', 'priority': 'medium', 'estimated_hours': 6}
        ])
        
        # 变现准备清单
        checklist_items.extend([
            {'category': '变现准备', 'task': '申请Google AdSense', 'priority': 'medium', 'estimated_hours': 2},
            {'category': '变现准备', 'task': '注册联盟营销计划', 'priority': 'high', 'estimated_hours': 4},
            {'category': '变现准备', 'task': '设置转化跟踪', 'priority': 'medium', 'estimated_hours': 3}
        ])
        
        # 保存清单
        checklist_df = pd.DataFrame(checklist_items)
        checklist_file = f'data/ai_tools_analysis/action_checklist_{timestamp}.csv'
        checklist_df.to_csv(checklist_file, index=False, encoding='utf-8')
        
        print(f"行动清单已保存: {checklist_file}")
        
        # 显示优先任务
        high_priority_tasks = checklist_df[checklist_df['priority'] == 'high']
        total_hours = high_priority_tasks['estimated_hours'].sum()
        
        print(f"\n=== 高优先级任务 ({len(high_priority_tasks)} 项，预计 {total_hours} 小时) ===")
        for _, task in high_priority_tasks.head(8).iterrows():
            print(f"• {task['task']} ({task['estimated_hours']}h)")

if __name__ == "__main__":
    planner = WebsitePlanner()
    planner.run_planning()