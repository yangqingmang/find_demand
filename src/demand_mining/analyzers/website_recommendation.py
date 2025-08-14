#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建站建议模块 - Website Recommendation
基于搜索意图分析结果提供具体的建站建议
"""

import pandas as pd
import re
from typing import Dict, List, Any, Tuple
from collections import Counter

from .base_analyzer import BaseAnalyzer
from src.utils import Logger

class WebsiteRecommendationEngine(BaseAnalyzer):
    """建站建议引擎，基于搜索意图提供建站建议"""
    
    def __init__(self):
        """初始化建站建议引擎"""
        super().__init__()
        
        # 网站类型定义
        self.website_types = {
            'I': {
                'primary_types': ['博客站', '知识库', '教程站', '百科站'],
                'secondary_types': ['问答社区', '学习平台', '资源导航'],
                'monetization': ['广告收入', '付费内容', '会员订阅', '知识付费']
            },
            'N': {
                'primary_types': ['官方网站', '品牌站', '产品主页', '下载站'],
                'secondary_types': ['登录门户', '应用商店', '软件分发'],
                'monetization': ['产品销售', '服务收费', '授权许可', '企业服务']
            },
            'C': {
                'primary_types': ['评测站', '对比站', '导购站', '榜单站'],
                'secondary_types': ['测评博客', '选购指南', '产品库'],
                'monetization': ['联盟营销', '广告收入', '付费评测', '导购佣金']
            },
            'E': {
                'primary_types': ['电商站', '工具站', '服务站', '下载站'],
                'secondary_types': ['在线商城', 'SaaS平台', '数字产品'],
                'monetization': ['产品销售', '订阅收费', '按次付费', '增值服务']
            },
            'B': {
                'primary_types': ['支持站', '文档站', '社区站', '工具站'],
                'secondary_types': ['帮助中心', '开发者社区', '故障排除'],
                'monetization': ['技术支持', '咨询服务', '培训收费', '工具订阅']
            },
            'L': {
                'primary_types': ['本地服务站', '门店官网', '预约平台', '地图服务'],
                'secondary_types': ['O2O平台', '本地导航', '服务预订'],
                'monetization': ['服务收费', '预约佣金', '广告收入', '会员费']
            }
        }
        
        # AI工具站细分类型
        self.ai_tool_categories = {
            'chatbot': {
                'name': 'AI对话工具',
                'examples': ['ChatGPT', 'Claude', 'Bard'],
                'features': ['对话界面', '多轮对话', '角色扮演', 'API集成'],
                'domain_suggestions': ['chat', 'talk', 'ai', 'bot', 'assistant']
            },
            'image_generation': {
                'name': 'AI图像生成',
                'examples': ['Midjourney', 'DALL-E', 'Stable Diffusion'],
                'features': ['图像生成', '风格转换', '图像编辑', '批量处理'],
                'domain_suggestions': ['image', 'art', 'generate', 'create', 'design']
            },
            'writing_tools': {
                'name': 'AI写作工具',
                'examples': ['Jasper', 'Copy.ai', 'Writesonic'],
                'features': ['文本生成', '内容优化', '多语言支持', '模板库'],
                'domain_suggestions': ['write', 'content', 'copy', 'text', 'writer']
            },
            'video_tools': {
                'name': 'AI视频工具',
                'examples': ['Runway', 'Pika', 'Synthesia'],
                'features': ['视频生成', '视频编辑', '语音合成', '字幕生成'],
                'domain_suggestions': ['video', 'movie', 'film', 'create', 'studio']
            },
            'audio_tools': {
                'name': 'AI音频工具',
                'examples': ['ElevenLabs', 'Murf', 'Speechify'],
                'features': ['语音合成', '音频编辑', '音乐生成', '语音克隆'],
                'domain_suggestions': ['voice', 'audio', 'speech', 'sound', 'music']
            },
            'coding_tools': {
                'name': 'AI编程工具',
                'examples': ['GitHub Copilot', 'Codeium', 'Tabnine'],
                'features': ['代码生成', '代码补全', '错误检测', '代码优化'],
                'domain_suggestions': ['code', 'dev', 'program', 'coding', 'developer']
            },
            'business_tools': {
                'name': 'AI商业工具',
                'examples': ['Zapier AI', 'Notion AI', 'Salesforce AI'],
                'features': ['自动化', '数据分析', '客户服务', '流程优化'],
                'domain_suggestions': ['business', 'auto', 'smart', 'pro', 'enterprise']
            },
            'research_tools': {
                'name': 'AI研究工具',
                'examples': ['Perplexity', 'Semantic Scholar', 'Elicit'],
                'features': ['文献检索', '数据分析', '知识图谱', '智能摘要'],
                'domain_suggestions': ['research', 'scholar', 'study', 'analysis', 'insight']
            }
        }
        
        # 域名建议规则
        self.domain_rules = {
            'prefixes': ['ai', 'smart', 'auto', 'quick', 'easy', 'best', 'top', 'pro', 'super'],
            'suffixes': ['tool', 'tools', 'app', 'hub', 'lab', 'studio', 'ai', 'bot', 'gen', 'maker'],
            'extensions': ['.com', '.ai', '.io', '.app', '.tools', '.tech', '.digital'],
            'avoid_words': ['free', 'cheap', 'download', 'crack', 'hack']
        }
    
    def analyze(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        实现基础分析器的抽象方法
        
        参数:
            data: 包含意图分析结果的DataFrame
            **kwargs: 其他参数
            
        返回:
            添加了建站建议的DataFrame
        """
        return self.generate_website_recommendations(data, **kwargs)
    
    def generate_website_recommendations(self, df: pd.DataFrame, 
                                       keyword_col: str = 'query',
                                       intent_col: str = 'intent') -> pd.DataFrame:
        """
        为关键词生成建站建议
        
        参数:
            df: 包含关键词和意图的DataFrame
            keyword_col: 关键词列名
            intent_col: 意图列名
            
        返回:
            添加了建站建议的DataFrame
        """
        if not self.validate_input(df):
            return df
        
        self.log_analysis_start("建站建议生成", f"，共 {len(df)} 个关键词")
        
        result_df = df.copy()
        
        # 为每个关键词生成建站建议
        recommendations = []
        for idx, row in result_df.iterrows():
            keyword = row.get(keyword_col, '')
            intent = row.get(intent_col, 'I')
            
            recommendation = self._generate_single_recommendation(keyword, intent)
            recommendations.append(recommendation)
        
        # 添加建议列
        result_df['website_type'] = [r['website_type'] for r in recommendations]
        result_df['ai_tool_category'] = [r['ai_tool_category'] for r in recommendations]
        result_df['monetization_strategy'] = [r['monetization_strategy'] for r in recommendations]
        result_df['domain_suggestions'] = [r['domain_suggestions'] for r in recommendations]
        result_df['content_strategy'] = [r['content_strategy'] for r in recommendations]
        result_df['technical_requirements'] = [r['technical_requirements'] for r in recommendations]
        result_df['competition_analysis'] = [r['competition_analysis'] for r in recommendations]
        result_df['development_priority'] = [r['development_priority'] for r in recommendations]
        
        self.log_analysis_complete("建站建议生成", len(result_df))
        return result_df
    
    def _generate_single_recommendation(self, keyword: str, intent: str) -> Dict[str, Any]:
        """
        为单个关键词生成建站建议
        
        参数:
            keyword: 关键词
            intent: 搜索意图
            
        返回:
            建站建议字典
        """
        keyword_lower = keyword.lower()
        
        # 检测AI工具类别
        ai_category = self._detect_ai_tool_category(keyword_lower)
        
        # 基础网站类型建议
        website_type = self._recommend_website_type(intent, keyword_lower, ai_category)
        
        # 变现策略
        monetization = self._recommend_monetization_strategy(intent, ai_category)
        
        # 域名建议
        domain_suggestions = self._generate_domain_suggestions(keyword_lower, ai_category)
        
        # 内容策略
        content_strategy = self._recommend_content_strategy(intent, keyword_lower, ai_category)
        
        # 技术要求
        technical_requirements = self._recommend_technical_requirements(intent, ai_category)
        
        # 竞争分析
        competition_analysis = self._analyze_competition_level(keyword_lower, intent)
        
        # 开发优先级
        development_priority = self._assess_development_priority(intent, ai_category, keyword_lower)
        
        return {
            'website_type': website_type,
            'ai_tool_category': ai_category,
            'monetization_strategy': monetization,
            'domain_suggestions': domain_suggestions,
            'content_strategy': content_strategy,
            'technical_requirements': technical_requirements,
            'competition_analysis': competition_analysis,
            'development_priority': development_priority
        }
    
    def _detect_ai_tool_category(self, keyword: str) -> str:
        """
        检测AI工具类别
        
        参数:
            keyword: 关键词（小写）
            
        返回:
            AI工具类别
        """
        # 检查关键词中是否包含特定的AI工具类型
        for category, info in self.ai_tool_categories.items():
            # 检查类别名称
            if any(word in keyword for word in info['domain_suggestions']):
                return info['name']
            
            # 检查示例产品名称
            for example in info['examples']:
                if example.lower().replace(' ', '') in keyword.replace(' ', ''):
                    return info['name']
        
        # 通用AI工具检测
        ai_indicators = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'gpt', 'bot', 'assistant']
        if any(indicator in keyword for indicator in ai_indicators):
            return 'AI通用工具'
        
        return '非AI工具'
    
    def _recommend_website_type(self, intent: str, keyword: str, ai_category: str) -> str:
        """
        推荐网站类型
        
        参数:
            intent: 搜索意图
            keyword: 关键词
            ai_category: AI工具类别
            
        返回:
            推荐的网站类型
        """
        base_types = self.website_types.get(intent, {}).get('primary_types', ['通用网站'])
        
        # 如果是AI工具，优先推荐工具站
        if ai_category != '非AI工具':
            if intent == 'E':  # 交易型
                return 'AI工具站 (SaaS平台)'
            elif intent == 'C':  # 商业型
                return 'AI工具评测站'
            elif intent == 'I':  # 信息型
                return 'AI工具教程站'
            elif intent == 'B':  # 行为型
                return 'AI工具支持站'
            else:
                return 'AI工具导航站'
        
        # 根据关键词特征调整
        if any(word in keyword for word in ['tool', 'generator', 'maker', 'creator']):
            return '在线工具站'
        elif any(word in keyword for word in ['game', 'play', 'fun']):
            return '游戏娱乐站'
        elif any(word in keyword for word in ['course', 'learn', 'tutorial']):
            return '在线教育站'
        
        return base_types[0] if base_types else '通用网站'
    
    def _recommend_monetization_strategy(self, intent: str, ai_category: str) -> List[str]:
        """
        推荐变现策略
        
        参数:
            intent: 搜索意图
            ai_category: AI工具类别
            
        返回:
            变现策略列表
        """
        base_strategies = self.website_types.get(intent, {}).get('monetization', ['广告收入'])
        
        # AI工具特殊变现策略
        if ai_category != '非AI工具':
            ai_strategies = [
                'Freemium模式 (免费+付费功能)',
                'API调用收费',
                '按使用量计费',
                '订阅制 (月费/年费)',
                '企业版授权'
            ]
            return ai_strategies[:3]  # 返回前3个策略
        
        return base_strategies[:3]
    
    def _generate_domain_suggestions(self, keyword: str, ai_category: str) -> List[str]:
        """
        生成域名建议
        
        参数:
            keyword: 关键词
            ai_category: AI工具类别
            
        返回:
            域名建议列表
        """
        suggestions = []
        
        # 提取关键词核心部分
        core_words = self._extract_core_words(keyword)
        
        # 生成域名组合
        for core in core_words[:2]:  # 最多取2个核心词
            # 直接使用核心词
            for ext in self.domain_rules['extensions'][:3]:
                suggestions.append(f"{core}{ext}")
            
            # 添加前缀
            for prefix in self.domain_rules['prefixes'][:3]:
                suggestions.append(f"{prefix}{core}.com")
            
            # 添加后缀
            for suffix in self.domain_rules['suffixes'][:3]:
                suggestions.append(f"{core}{suffix}.com")
        
        # AI工具特殊域名
        if ai_category != '非AI工具':
            ai_domains = [
                f"{core_words[0]}ai.com",
                f"ai{core_words[0]}.io",
                f"{core_words[0]}.ai"
            ]
            suggestions.extend(ai_domains)
        
        # 去重并限制数量
        unique_suggestions = list(dict.fromkeys(suggestions))  # 保持顺序去重
        return unique_suggestions[:8]  # 最多返回8个建议
    
    def _extract_core_words(self, keyword: str) -> List[str]:
        """
        提取关键词的核心词汇
        
        参数:
            keyword: 关键词
            
        返回:
            核心词汇列表
        """
        # 移除常见停用词
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                     'best', 'top', 'how', 'what', 'why', 'when', 'where', 'free', 'online'}
        
        # 分词并清理
        words = re.findall(r'\b[a-zA-Z]+\b', keyword.lower())
        core_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        return core_words[:3]  # 最多返回3个核心词
    
    def _recommend_content_strategy(self, intent: str, keyword: str, ai_category: str) -> List[str]:
        """
        推荐内容策略
        
        参数:
            intent: 搜索意图
            keyword: 关键词
            ai_category: AI工具类别
            
        返回:
            内容策略列表
        """
        strategies = []
        
        # 基于意图的内容策略
        intent_strategies = {
            'I': ['教程文章', '操作指南', 'FAQ页面', '视频教程', '案例研究'],
            'N': ['产品介绍页', '功能展示', '下载页面', '用户手册', '快速开始'],
            'C': ['产品对比', '评测报告', '用户评价', '功能对比表', '价格对比'],
            'E': ['产品页面', '定价页面', '免费试用', '购买流程', '客户案例'],
            'B': ['帮助文档', '故障排除', '社区论坛', '技术支持', 'API文档'],
            'L': ['门店信息', '服务介绍', '预约系统', '联系方式', '地图导航']
        }
        
        strategies.extend(intent_strategies.get(intent, ['通用内容'])[:3])
        
        # AI工具特殊内容策略
        if ai_category != '非AI工具':
            ai_strategies = [
                'AI工具使用教程',
                '提示词(Prompt)模板',
                '最佳实践案例',
                'AI技术解析',
                '行业应用场景'
            ]
            strategies.extend(ai_strategies[:2])
        
        return strategies[:5]
    
    def _recommend_technical_requirements(self, intent: str, ai_category: str) -> List[str]:
        """
        推荐技术要求
        
        参数:
            intent: 搜索意图
            ai_category: AI工具类别
            
        返回:
            技术要求列表
        """
        requirements = []
        
        # 基础技术要求
        base_requirements = {
            'I': ['响应式设计', 'SEO优化', '内容管理系统', '搜索功能'],
            'N': ['快速加载', '移动适配', '用户认证', '下载管理'],
            'C': ['对比功能', '评分系统', '用户评论', '数据可视化'],
            'E': ['支付系统', '用户账户', '订单管理', '安全防护'],
            'B': ['知识库', '搜索功能', '用户社区', '工单系统'],
            'L': ['地图集成', '位置服务', '预约系统', '移动优先']
        }
        
        requirements.extend(base_requirements.get(intent, ['基础网站功能'])[:3])
        
        # AI工具特殊技术要求
        if ai_category != '非AI工具':
            ai_requirements = [
                'AI API集成',
                '实时处理能力',
                '大文件处理',
                '用户使用量统计',
                '模型版本管理'
            ]
            requirements.extend(ai_requirements[:2])
        
        return requirements[:5]
    
    def _analyze_competition_level(self, keyword: str, intent: str) -> Dict[str, Any]:
        """
        分析竞争程度
        
        参数:
            keyword: 关键词
            intent: 搜索意图
            
        返回:
            竞争分析结果
        """
        # 基于关键词特征估算竞争程度
        competition_indicators = {
            'high': ['best', 'top', 'review', 'vs', 'compare', 'free', 'download'],
            'medium': ['how', 'tutorial', 'guide', 'tool', 'generator'],
            'low': ['specific brand names', 'long tail keywords']
        }
        
        # 计算竞争程度
        high_count = sum(1 for word in competition_indicators['high'] if word in keyword)
        medium_count = sum(1 for word in competition_indicators['medium'] if word in keyword)
        
        if high_count >= 2:
            level = '高'
            advice = '需要强大的SEO策略和独特价值主张'
        elif high_count >= 1 or medium_count >= 2:
            level = '中'
            advice = '可通过长尾关键词和细分市场切入'
        else:
            level = '低'
            advice = '机会较好，可快速建立市场地位'
        
        return {
            'level': level,
            'advice': advice,
            'strategy': self._get_competition_strategy(level)
        }
    
    def _get_competition_strategy(self, level: str) -> List[str]:
        """
        获取竞争策略
        
        参数:
            level: 竞争程度
            
        返回:
            竞争策略列表
        """
        strategies = {
            '高': [
                '差异化定位',
                '垂直细分市场',
                '独特功能开发',
                '品牌建设投入',
                '用户体验优化'
            ],
            '中': [
                '长尾关键词优化',
                '内容营销',
                '社交媒体推广',
                '合作伙伴关系',
                '用户口碑建设'
            ],
            '低': [
                '快速市场进入',
                'SEO基础优化',
                '内容规模化',
                '用户获取',
                '市场教育'
            ]
        }
        
        return strategies.get(level, ['通用策略'])[:3]
    
    def _assess_development_priority(self, intent: str, ai_category: str, keyword: str) -> Dict[str, Any]:
        """
        评估开发优先级
        
        参数:
            intent: 搜索意图
            ai_category: AI工具类别
            keyword: 关键词
            
        返回:
            开发优先级评估
        """
        # 基础优先级评分
        priority_scores = {
            'E': 90,  # 交易型最高优先级
            'C': 80,  # 商业型次之
            'I': 70,  # 信息型中等
            'B': 60,  # 行为型较低
            'N': 50,  # 导航型最低
            'L': 75   # 本地型较高
        }
        
        base_score = priority_scores.get(intent, 60)
        
        # AI工具加分
        if ai_category != '非AI工具':
            base_score += 15
        
        # 关键词热度加分
        hot_keywords = ['ai', 'chatgpt', 'generator', 'free', 'online', 'tool']
        keyword_bonus = sum(5 for word in hot_keywords if word in keyword.lower())
        
        final_score = min(100, base_score + keyword_bonus)
        
        # 确定优先级等级
        if final_score >= 85:
            priority = '高'
            timeline = '1-2个月'
        elif final_score >= 70:
            priority = '中'
            timeline = '3-4个月'
        else:
            priority = '低'
            timeline = '6个月以上'
        
        return {
            'score': final_score,
            'level': priority,
            'timeline': timeline,
            'reasoning': self._get_priority_reasoning(intent, ai_category, final_score)
        }
    
    def _get_priority_reasoning(self, intent: str, ai_category: str, score: int) -> str:
        """
        获取优先级评估理由
        
        参数:
            intent: 搜索意图
            ai_category: AI工具类别
            score: 优先级评分
            
        返回:
            评估理由
        """
        reasons = []
        
        # 意图相关理由
        intent_reasons = {
            'E': '交易型意图，变现潜力高',
            'C': '商业型意图，适合联盟营销',
            'I': '信息型意图，流量获取相对容易',
            'B': '行为型意图，用户粘性较高',
            'N': '导航型意图，需要品牌建设',
            'L': '本地型意图，竞争相对较小'
        }
        
        reasons.append(intent_reasons.get(intent, '通用意图'))
        
        # AI工具相关理由
        if ai_category != '非AI工具':
            reasons.append('AI工具市场热度高，用户需求旺盛')
        
        # 评分相关理由
        if score >= 85:
            reasons.append('综合评分高，建议优先开发')
        elif score >= 70:
            reasons.append('评分中等，可作为第二批开发项目')
        else:
            reasons.append('评分较低，建议后期考虑')
        
        return '; '.join(reasons)
    
    def generate_summary_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        生成建站建议摘要报告
        
        参数:
            df: 包含建站建议的DataFrame
            
        返回:
            摘要报告
        """
        if df.empty:
            return {'error': '没有数据可分析'}
        
        # 统计网站类型分布
        website_type_dist = df['website_type'].value_counts().to_dict()
        
        # 统计AI工具类别分布
        ai_category_dist = df['ai_tool_category'].value_counts().to_dict()
        
        # 统计开发优先级分布
        priority_dist = df['development_priority'].apply(
            lambda x: x.get('level', '未知') if isinstance(x, dict) else '未知'
        ).value_counts().to_dict()
        
        # 推荐的高优先级项目
        high_priority_projects = df[
            df['development_priority'].apply(
                lambda x: x.get('level', '') == '高' if isinstance(x, dict) else False
            )
        ][['query', 'website_type', 'ai_tool_category']].to_dict('records')
        
        # 域名建议汇总
        all_domains = []
        for domains in df['domain_suggestions']:
            if isinstance(domains, list):
                all_domains.extend(domains)
        
        popular_domains = Counter(all_domains).most_common(10)
        
        return {
            'total_keywords': len(df),
            'website_type_distribution': website_type_dist,
            'ai_category_distribution': ai_category_dist,
            'priority_distribution': priority_dist,
            'high_priority_projects': high_priority_projects[:5],  # 前5个高优先级项目
            'popular_domain_suggestions': dict(popular_domains),
            'recommendations': {
                'immediate_action': self._get_immediate_recommendations(df),
                'market_opportunities': self._identify_market_opportunities(df),
                'technical_focus': self._recommend_technical_focus(df)
            }
        }
    
    def _get_immediate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """
        获取立即行动建议
        
        参数:
            df: 数据DataFrame
            
        返回:
            立即行动建议列表
        """
        recommendations = []
        
        # 检查高优先级项目
        high_priority_count = sum(
            1 for x in df['development_priority'] 
            if isinstance(x, dict) and x.get('level') == '高'
        )
        
        if high_priority_count > 0:
            recommendations.append(f"发现 {high_priority_count} 个高优先级项目，建议立即启动开发")
        
        # 检查AI工具机会
        ai_tools_count = sum(1 for x in df['ai_tool_category'] if x != '非AI工具')
        if ai_tools_count > len(df) * 0.5:
            recommendations.append("AI工具需求占比较高，建议重点关注AI工具站开发")
        
        # 检查交易型关键词
        transactional_count = sum(1 for x in df['intent'] if x == 'E')
        if transactional_count > 0:
            recommendations.append(f"发现 {transactional_count} 个交易型关键词，变现潜力较高")
        
        return recommendations[:3]
    
    def _identify_market_opportunities(self, df: pd.DataFrame) -> List[str]:
        """
        识别市场机会
        
        参数:
            df: 数据DataFrame
            
        返回:
            市场机会列表
        """
        opportunities = []
        
        # 分析竞争程度
        low_competition_count = sum(
            1 for x in df['competition_analysis'] 
            if isinstance(x, dict) and x.get('level') == '低'
        )
        
        if low_competition_count > 0:
            opportunities.append(f"发现 {low_competition_count} 个低竞争关键词，市场进入机会较好")
        
        # 分析AI工具类别机会
        ai_categories = [x for x in df['ai_tool_category'] if x != '非AI工具']
        if ai_categories:
            top_category = Counter(ai_categories).most_common(1)[0]
            opportunities.append(f"{top_category[0]} 需求最高，建议优先布局")
        
        return opportunities[:3]
    
    def _recommend_technical_focus(self, df: pd.DataFrame) -> List[str]:
        """
        推荐技术重点
        
        参数:
            df: 数据DataFrame
            
        返回:
            技术重点建议列表
        """
        focus_areas = []
        
        # 统计技术要求
        all_requirements = []
        for reqs in df['technical_requirements']:
            if isinstance(reqs, list):
                all_requirements.extend(reqs)
        
        top_requirements = Counter(all_requirements).most_common(3)
        
        for req, count in top_requirements:
            focus_areas.append(f"{req} (需求频次: {count})")
        
        return focus_areas