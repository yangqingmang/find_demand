#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用网站建设方案生成器 (原AI工具网站建设方案生成器升级版)
基于任何关键词分析结果，自动生成对应主题的网站建设计划
"""

import json
import pandas as pd
from datetime import datetime, timedelta
import os
import glob

class AIWebsiteBuilder:
    def __init__(self):
        self.comprehensive_data = None
        self.keyword_theme = None
        self.website_type = None
        
    def find_latest_analysis_report(self):
        """查找最新的关键词分析报告"""
        # 从当前目录向上查找
        possible_paths = [
            "src/demand_mining/reports",
            "../demand_mining/reports",
            "../../src/demand_mining/reports"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pattern = os.path.join(path, "keyword_analysis_*.json")
                report_files = glob.glob(pattern)
                if report_files:
                    # 按时间戳排序，获取最新的
                    report_files.sort(reverse=True)
                    return report_files[0]
        return None
        
    def load_comprehensive_data(self):
        """加载综合分析数据 - 支持多种数据源"""
        # 1. 首先尝试加载原始AI工具数据
        try:
            with open('data/ai_tools_analysis/comprehensive_report_2025-08-05.json', 'r', encoding='utf-8') as f:
                self.comprehensive_data = json.load(f)
                self.keyword_theme = "ai tools"
                self.website_type = "ai"
                print("✅ 加载AI工具分析数据")
                return True
        except Exception as e:
            print(f"原始AI数据不存在: {e}")
            
        # 2. 尝试加载最新的关键词分析报告
        latest_report = self.find_latest_analysis_report()
        if latest_report:
            try:
                with open(latest_report, 'r', encoding='utf-8') as f:
                    keyword_data = json.load(f)
                
                # 转换为适合的格式
                self.comprehensive_data = self.convert_keyword_data_to_ai_format(keyword_data)
                
                # 提取主题关键词
                if 'keywords' in keyword_data and keyword_data['keywords']:
                    self.keyword_theme = keyword_data['keywords'][0]['keyword']
                    self.website_type = self.analyze_keyword_theme()
                    print(f"✅ 基于关键词分析报告: {os.path.basename(latest_report)}")
                    print(f"🎯 检测到主题: {self.keyword_theme} (类型: {self.website_type})")
                    return True
            except Exception as e2:
                print(f"加载关键词分析报告失败: {e2}")
        
        # 3. 使用默认配置
        print("使用默认AI工具配置...")
        self.comprehensive_data = self.get_default_ai_data()
        self.keyword_theme = "ai tools"
        self.website_type = "ai"
        return True
    
    def analyze_keyword_theme(self):
        """分析关键词主题，确定网站类型"""
        if not self.keyword_theme:
            return "ai"
            
        keyword_lower = self.keyword_theme.lower()
        
        # 定义主题映射
        theme_mapping = {
            'ai': ['ai', 'artificial intelligence', 'machine learning', 'chatgpt', 'openai'],
            'weather': ['hurricane', 'tornado', 'weather', 'storm', 'climate'],
            'health': ['health', 'medical', 'fitness', 'wellness', 'nutrition'],
            'finance': ['finance', 'investment', 'crypto', 'bitcoin', 'trading'],
            'tech': ['technology', 'software', 'programming', 'coding', 'development'],
            'travel': ['travel', 'vacation', 'hotel', 'flight', 'tourism'],
            'food': ['food', 'recipe', 'cooking', 'restaurant', 'cuisine'],
            'education': ['education', 'learning', 'course', 'tutorial', 'study'],
            'business': ['business', 'marketing', 'startup', 'entrepreneur', 'sales'],
            'entertainment': ['movie', 'music', 'game', 'entertainment', 'celebrity']
        }
        
        # 匹配主题
        for theme, keywords in theme_mapping.items():
            if any(kw in keyword_lower for kw in keywords):
                return theme
                
        return "ai"  # 默认为AI主题
    
    def convert_keyword_data_to_ai_format(self, keyword_data):
        """将关键词数据转换为AI工具分析格式"""
        keywords = keyword_data.get('keywords', [])
        
        converted_data = {
            '关键指标': {
                '总关键词数': len(keywords),
                '高分关键词数': len([k for k in keywords if k.get('综合评分', 0) > 70]),
                '平均搜索量': sum(k.get('搜索量估算', 0) for k in keywords) // max(len(keywords), 1)
            },
            'Top20高价值关键词': []
        }
        
        # 提取高价值关键词
        sorted_keywords = sorted(keywords, key=lambda x: x.get('综合评分', 0), reverse=True)
        for kw in sorted_keywords[:20]:
            converted_data['Top20高价值关键词'].append({
                'query': kw.get('keyword', ''),
                'score': kw.get('综合评分', 0),
                'search_volume': kw.get('搜索量估算', 0),
                'intent': kw.get('intent', {}).get('primary_intent', 'I')
            })
        
        return converted_data
    
    def get_default_ai_data(self):
        """获取默认AI工具数据"""
        return {
            '关键指标': {
                '总关键词数': 100,
                '高分关键词数': 25,
                '平均搜索量': 5000
            },
            'Top20高价值关键词': [
                {'query': 'chatgpt', 'score': 95},
                {'query': 'midjourney', 'score': 92},
                {'query': 'claude ai', 'score': 88},
                {'query': 'stable diffusion', 'score': 85},
                {'query': 'github copilot', 'score': 82}
            ]
        }
    
    def generate_website_concept_by_theme(self, theme):
        """根据主题生成网站概念"""
        concepts = {
            'ai': {
                'name': 'AI工具导航中心',
                'description': '最全面的人工智能工具评测和推荐平台',
                'target_audience': '开发者、企业用户、AI爱好者',
                'value_proposition': '发现最新最好用的AI工具，提供专业评测和使用指南'
            },
            'weather': {
                'name': '天气预警信息中心',
                'description': '实时天气追踪、预报和安全指南平台',
                'target_audience': '沿海居民、应急管理人员、天气爱好者',
                'value_proposition': '提供最及时、最专业的天气信息和安全指导'
            },
            'health': {
                'name': '健康生活指南',
                'description': '专业健康资讯和生活方式建议平台',
                'target_audience': '健康关注者、患者、医疗专业人士',
                'value_proposition': '提供科学可靠的健康信息和个性化建议'
            },
            'finance': {
                'name': '投资理财助手',
                'description': '专业投资分析和理财建议平台',
                'target_audience': '投资者、理财规划师、金融从业者',
                'value_proposition': '提供专业的投资分析和个性化理财方案'
            },
            'tech': {
                'name': '科技资讯中心',
                'description': '最新科技动态和产品评测平台',
                'target_audience': '科技爱好者、开发者、产品经理',
                'value_proposition': '第一时间获取科技资讯和深度产品分析'
            }
        }
        
        # 如果没有匹配的主题，使用通用模板
        if theme not in concepts:
            concepts[theme] = {
                'name': f'{self.keyword_theme.title()} 信息中心',
                'description': f'专业的{self.keyword_theme}相关信息和资源平台',
                'target_audience': f'{self.keyword_theme}相关用户群体',
                'value_proposition': f'提供最全面的{self.keyword_theme}信息和专业指导'
            }
        
        return concepts[theme]
    
    def analyze_keyword_categories(self):
        """分析关键词类别 - 根据主题自适应"""
        if not self.comprehensive_data:
            return {}
        
        # 根据网站类型生成不同的分类
        if self.website_type == 'ai':
            return self.get_ai_categories()
        elif self.website_type == 'weather':
            return self.get_weather_categories()
        elif self.website_type == 'health':
            return self.get_health_categories()
        elif self.website_type == 'finance':
            return self.get_finance_categories()
        else:
            return self.get_general_categories()
    
    def get_ai_categories(self):
        """AI主题分类"""
        return {
            'conversational_ai': {
                'name': '对话AI工具',
                'keywords': ['chatgpt', 'claude', 'bard', 'gemini', 'chatbot', 'ai assistant'],
                'priority': 'high',
                'estimated_traffic': 15000
            },
            'image_generation': {
                'name': '图像生成工具',
                'keywords': ['midjourney', 'dall-e', 'stable diffusion', 'ai image generator'],
                'priority': 'high',
                'estimated_traffic': 12000
            },
            'writing_tools': {
                'name': '写作AI工具',
                'keywords': ['jasper ai', 'copy ai', 'writesonic', 'grammarly'],
                'priority': 'high',
                'estimated_traffic': 10000
            },
            'coding_tools': {
                'name': '编程AI工具',
                'keywords': ['github copilot', 'codeium', 'tabnine', 'ai coding assistant'],
                'priority': 'high',
                'estimated_traffic': 9000
            }
        }
    
    def get_weather_categories(self):
        """天气主题分类"""
        return {
            'tracking': {
                'name': '实时追踪',
                'keywords': ['hurricane tracker', 'storm tracker', 'weather radar'],
                'priority': 'high',
                'estimated_traffic': 8000
            },
            'safety': {
                'name': '安全指南',
                'keywords': ['hurricane safety', 'storm preparedness', 'evacuation guide'],
                'priority': 'high',
                'estimated_traffic': 6000
            },
            'forecasting': {
                'name': '天气预报',
                'keywords': ['hurricane forecast', 'weather prediction', 'storm warning'],
                'priority': 'medium',
                'estimated_traffic': 7000
            },
            'history': {
                'name': '历史数据',
                'keywords': ['hurricane history', 'storm archive', 'weather records'],
                'priority': 'medium',
                'estimated_traffic': 4000
            }
        }
    
    def get_health_categories(self):
        """健康主题分类"""
        return {
            'nutrition': {
                'name': '营养健康',
                'keywords': ['healthy diet', 'nutrition guide', 'meal planning'],
                'priority': 'high',
                'estimated_traffic': 10000
            },
            'fitness': {
                'name': '运动健身',
                'keywords': ['workout routine', 'fitness tips', 'exercise guide'],
                'priority': 'high',
                'estimated_traffic': 8000
            },
            'mental_health': {
                'name': '心理健康',
                'keywords': ['mental wellness', 'stress management', 'mindfulness'],
                'priority': 'medium',
                'estimated_traffic': 6000
            }
        }
    
    def get_finance_categories(self):
        """金融主题分类"""
        return {
            'investment': {
                'name': '投资理财',
                'keywords': ['investment guide', 'stock analysis', 'portfolio management'],
                'priority': 'high',
                'estimated_traffic': 12000
            },
            'crypto': {
                'name': '加密货币',
                'keywords': ['bitcoin', 'cryptocurrency', 'crypto trading'],
                'priority': 'high',
                'estimated_traffic': 10000
            },
            'personal_finance': {
                'name': '个人理财',
                'keywords': ['budgeting', 'saving money', 'financial planning'],
                'priority': 'medium',
                'estimated_traffic': 8000
            }
        }
    
    def get_general_categories(self):
        """通用分类"""
        return {
            'information': {
                'name': '信息资讯',
                'keywords': [f'{self.keyword_theme} news', f'{self.keyword_theme} guide'],
                'priority': 'high',
                'estimated_traffic': 8000
            },
            'guides': {
                'name': '指南教程',
                'keywords': [f'how to {self.keyword_theme}', f'{self.keyword_theme} tutorial'],
                'priority': 'medium',
                'estimated_traffic': 6000
            },
            'reviews': {
                'name': '评测对比',
                'keywords': [f'{self.keyword_theme} review', f'best {self.keyword_theme}'],
                'priority': 'medium',
                'estimated_traffic': 5000
            }
        }
    
    def generate_website_structure(self, categories):
        """生成网站结构"""
        website_concept = self.generate_website_concept_by_theme(self.website_type)
        
        structure = {
            'homepage': {
                'title': f'{website_concept["name"]} - {website_concept["description"]}',
                'description': website_concept['description'],
                'target_keywords': [self.keyword_theme, f'{self.keyword_theme} guide', f'best {self.keyword_theme}'],
                'sections': [
                    f'热门{website_concept["name"]}推荐',
                    '分类导航',
                    '最新动态',
                    '用户评价排行',
                    '精选推荐'
                ]
            },
            'categories': {},
            'content_pages': {}
        }
        
        # 为每个类别创建页面
        for cat_id, cat_info in categories.items():
            structure['categories'][cat_id] = {
                'title': f'{cat_info["name"]}完整指南 - 2025年最新',
                'url': f'/{cat_id.replace("_", "-")}',
                'description': f'专业的{cat_info["name"]}信息，包括详细分析和使用建议',
                'target_keywords': cat_info['keywords'][:5],
                'priority': cat_info['priority'],
                'estimated_traffic': cat_info['estimated_traffic']
            }
        
        return structure
    
    def create_content_strategy(self, structure):
        """创建内容策略"""
        content_calendar = []
        start_date = datetime.now()
        
        # 根据主题生成不同的内容策略
        if self.website_type == 'ai':
            priority_topics = ['ChatGPT', 'Claude', 'Midjourney', 'DALL-E', 'GitHub Copilot']
        elif self.website_type == 'weather':
            priority_topics = ['飓风追踪指南', '风暴安全准备', '天气预报解读', '历史飓风分析', '应急响应计划']
        elif self.website_type == 'health':
            priority_topics = ['健康饮食指南', '运动健身计划', '心理健康管理', '疾病预防知识', '健康生活方式']
        elif self.website_type == 'finance':
            priority_topics = ['投资基础知识', '股票分析方法', '加密货币指南', '理财规划策略', '风险管理技巧']
        else:
            priority_topics = [f'{self.keyword_theme}基础指南', f'{self.keyword_theme}进阶技巧', f'{self.keyword_theme}最佳实践', f'{self.keyword_theme}案例分析', f'{self.keyword_theme}趋势预测']
        
        for i, topic in enumerate(priority_topics):
            content_calendar.append({
                'week': i + 1,
                'publish_date': (start_date + timedelta(weeks=i)).strftime('%Y-%m-%d'),
                'content_type': 'guide_article',
                'title': topic,
                'target_keywords': [topic.lower(), f'{self.keyword_theme} {topic.lower()}'],
                'estimated_words': 2000 + (i * 200),
                'priority': 'high',
                'monetization': 'affiliate_links + display_ads'
            })
        
        return content_calendar
    
    def generate_technical_plan(self):
        """生成技术实施计划"""
        base_plan = {
            'architecture': {
                'frontend': {
                    'framework': 'Next.js 14 (App Router)',
                    'styling': 'Tailwind CSS + Shadcn/ui',
                    'state_management': 'Zustand'
                },
                'backend': {
                    'framework': 'Next.js API Routes',
                    'database': 'PostgreSQL (Supabase)',
                    'auth': 'NextAuth.js'
                },
                'hosting': {
                    'platform': 'Vercel',
                    'cdn': 'Vercel Edge Network',
                    'database': 'Supabase'
                }
            }
        }
        
        # 根据主题添加特殊需求
        if self.website_type == 'weather':
            base_plan['integrations'] = {
                'weather_apis': ['OpenWeatherMap', 'WeatherAPI'],
                'mapping': 'Leaflet.js',
                'real_time': 'WebSocket connections'
            }
        elif self.website_type == 'ai':
            base_plan['integrations'] = {
                'ai_apis': ['OpenAI API', 'Anthropic API'],
                'analytics': 'Google Analytics 4',
                'affiliate_tracking': 'Custom tracking system'
            }
        elif self.website_type == 'finance':
            base_plan['integrations'] = {
                'financial_apis': ['Alpha Vantage', 'Yahoo Finance'],
                'charts': 'Chart.js',
                'real_time_data': 'WebSocket for live prices'
            }
        
        return base_plan
    
    def create_monetization_plan(self):
        """创建变现计划"""
        # 根据主题定制变现策略
        if self.website_type == 'ai':
            return {
                'primary': 'affiliate_marketing',
                'revenue_streams': {
                    'affiliate_commissions': '$2000-5000/月',
                    'display_advertising': '$800-2000/月',
                    'sponsored_reviews': '$500-1500/月'
                }
            }
        elif self.website_type == 'weather':
            return {
                'primary': 'display_advertising',
                'revenue_streams': {
                    'display_advertising': '$1500-3000/月',
                    'emergency_supplies_affiliate': '$500-1200/月',
                    'premium_alerts': '$300-800/月'
                }
            }
        elif self.website_type == 'health':
            return {
                'primary': 'affiliate_marketing',
                'revenue_streams': {
                    'health_products_affiliate': '$1800-4000/月',
                    'display_advertising': '$1000-2500/月',
                    'consultation_referrals': '$600-1500/月'
                }
            }
        else:
            return {
                'primary': 'display_advertising',
                'revenue_streams': {
                    'display_advertising': '$800-2000/月',
                    'affiliate_commissions': '$400-1000/月'
                }
            }
    
    def create_theme_directory(self):
        """创建主题专用目录"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 清理主题名称，用于文件夹命名
        clean_theme = self.keyword_theme.lower().replace(' ', '_').replace('-', '_')
        clean_theme = ''.join(c for c in clean_theme if c.isalnum() or c == '_')
        
        # 创建主题目录名
        theme_dir = f"generated_websites/{self.website_type}_{clean_theme}_{timestamp}"
        
        # 创建目录
        os.makedirs(theme_dir, exist_ok=True)
        
        return theme_dir
    
    def backup_existing_website(self):
        """备份现有的 generated_website 目录"""
        if os.path.exists('generated_website'):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = f"generated_websites/backup_{timestamp}"
            
            os.makedirs('generated_websites', exist_ok=True)
            
            import shutil
            shutil.move('generated_website', backup_dir)
            print(f"📦 已备份现有网站到: {backup_dir}")
            return backup_dir
        return None

    def generate_complete_plan(self):
        """生成完整的网站建设计划"""
        print("🚀 启动通用网站建设方案生成器...")
        
        if not self.load_comprehensive_data():
            print("无法加载基础数据")
            return
        
        # 备份现有网站（如果存在）
        backup_path = self.backup_existing_website()
        
        # 创建主题专用目录
        theme_dir = self.create_theme_directory()
        
        # 生成网站概念
        website_concept = self.generate_website_concept_by_theme(self.website_type)
        
        # 分析关键词类别
        categories = self.analyze_keyword_categories()
        
        # 生成网站结构
        website_structure = self.generate_website_structure(categories)
        
        # 创建内容策略
        content_strategy = self.create_content_strategy(website_structure)
        
        # 生成技术计划
        technical_plan = self.generate_technical_plan()
        
        # 创建变现计划
        monetization_plan = self.create_monetization_plan()
        
        # 汇总完整计划
        complete_plan = {
            'project_info': {
                'theme': self.website_type,
                'main_keyword': self.keyword_theme,
                'website_name': website_concept['name'],
                'description': website_concept['description'],
                'target_audience': website_concept['target_audience'],
                'value_proposition': website_concept['value_proposition'],
                'estimated_launch_date': (datetime.now() + timedelta(weeks=4)).strftime('%Y-%m-%d'),
                'theme_directory': theme_dir
            },
            'market_analysis': {
                'total_keywords_analyzed': self.comprehensive_data['关键指标']['总关键词数'],
                'high_value_keywords': self.comprehensive_data['关键指标']['高分关键词数'],
                'average_search_volume': self.comprehensive_data['关键指标']['平均搜索量'],
                'market_opportunity': f'基于{self.keyword_theme}的利基市场，具有良好的SEO机会'
            },
            'website_structure': website_structure,
            'content_strategy': {
                'content_calendar': content_strategy
            },
            'technical_implementation': technical_plan,
            'monetization_strategy': monetization_plan,
            'success_metrics': {
                'month_1': {'visitors': 1500, 'revenue': 200, 'articles': 8},
                'month_3': {'visitors': 8000, 'revenue': 800, 'articles': 20},
                'month_6': {'visitors': 25000, 'revenue': 2500, 'articles': 35},
                'month_12': {'visitors': 80000, 'revenue': 8000, 'articles': 60}
            }
        }
        
        # 保存计划到主题目录
        plan_file = os.path.join(theme_dir, 'website_plan.json')
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(complete_plan, f, ensure_ascii=False, indent=2)
        
        # 创建项目信息文件
        project_info = {
            'project_name': website_concept['name'],
            'theme': self.website_type,
            'main_keyword': self.keyword_theme,
            'created_at': datetime.now().isoformat(),
            'directory': theme_dir,
            'status': 'plan_generated'
        }
        
        info_file = os.path.join(theme_dir, 'project_info.json')
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(project_info, f, ensure_ascii=False, indent=2)
        
        # 创建 README 文件
        readme_content = f"""# {website_concept['name']}

## 项目信息
- **主题**: {self.website_type}
- **关键词**: {self.keyword_theme}
- **创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **目标受众**: {website_concept['target_audience']}

## 项目描述
{website_concept['description']}

## 价值主张
{website_concept['value_proposition']}

## 文件说明
- `website_plan.json` - 完整的网站建设计划
- `project_info.json` - 项目基本信息
- `website_source/` - 网站源代码（生成后）

## 下一步行动
1. 运行网站生成器创建实际网站文件
2. 选择并注册域名
3. 设置开发环境
4. 开始网站开发
5. 准备首批内容

## 技术栈
- 前端: {technical_plan['architecture']['frontend']['framework']}
- 后端: {technical_plan['architecture']['backend']['framework']}
- 数据库: {technical_plan['architecture']['backend']['database']}
- 托管: {technical_plan['architecture']['hosting']['platform']}
"""
        
        readme_file = os.path.join(theme_dir, 'README.md')
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # 更新项目索引
        self.update_project_index(theme_dir, project_info)
        
        # 显示结果
        print(f"\n🎉 {website_concept['name']} 建设方案已生成！")
        print(f"📁 项目目录: {theme_dir}")
        print(f"📄 详细计划: {plan_file}")
        print(f"🎯 主题关键词: {self.keyword_theme}")
        print(f"🏷️ 网站类型: {self.website_type}")
        print(f"🚀 预计发布时间: {complete_plan['project_info']['estimated_launch_date']}")
        
        if backup_path:
            print(f"📦 原网站已备份到: {backup_path}")
        
        print(f"\n📊 市场分析摘要:")
        print(f"   • 分析关键词总数: {complete_plan['market_analysis']['total_keywords_analyzed']}")
        print(f"   • 高价值关键词: {complete_plan['market_analysis']['high_value_keywords']}")
        print(f"   • 平均搜索量: {complete_plan['market_analysis']['average_search_volume']}")
        
        print(f"\n💰 收入预期:")
        for period, metrics in complete_plan['success_metrics'].items():
            print(f"   • {period}: {metrics['visitors']:,} 访客, ${metrics['revenue']:,} 收入")
        
        print(f"\n🏗️ 技术栈:")
        tech = complete_plan['technical_implementation']
        print(f"   • 前端: {tech['architecture']['frontend']['framework']}")
        print(f"   • 后端: {tech['architecture']['backend']['framework']}")
        print(f"   • 数据库: {tech['architecture']['backend']['database']}")
        print(f"   • 托管: {tech['architecture']['hosting']['platform']}")
        
        print(f"\n🎯 下一步行动:")
        print("   1. 运行网站生成器创建实际网站文件")
        print("   2. 选择并注册域名")
        print("   3. 设置开发环境")
        print("   4. 开始网站开发")
        print("   5. 准备首批内容")
        
        return complete_plan, theme_dir
    
    def update_project_index(self, theme_dir, project_info):
        """更新项目索引"""
        index_file = 'generated_websites/projects_index.json'
        
        # 读取现有索引
        projects_index = []
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    projects_index = json.load(f)
            except:
                projects_index = []
        
        # 添加新项目
        projects_index.append(project_info)
        
        # 按创建时间排序（最新的在前）
        projects_index.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # 保存索引
        os.makedirs('generated_websites', exist_ok=True)
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(projects_index, f, ensure_ascii=False, indent=2)
        
        print(f"📝 已更新项目索引: {index_file}")
    
    def list_projects(self):
        """列出所有项目"""
        index_file = 'generated_websites/projects_index.json'
        
        if not os.path.exists(index_file):
            print("📭 暂无项目")
            return []
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                projects = json.load(f)
            
            print(f"\n📋 项目列表 (共 {len(projects)} 个项目):")
            print("=" * 80)
            
            for i, project in enumerate(projects, 1):
                print(f"{i}. {project['project_name']}")
                print(f"   主题: {project['theme']} | 关键词: {project['main_keyword']}")
                print(f"   创建时间: {project['created_at'][:19].replace('T', ' ')}")
                print(f"   目录: {project['directory']}")
                print(f"   状态: {project.get('status', 'unknown')}")
                print("-" * 80)
            
            return projects
            
        except Exception as e:
            print(f"❌ 读取项目索引失败: {e}")
            return []

if __name__ == "__main__":
    builder = AIWebsiteBuilder()
    builder.generate_complete_plan()