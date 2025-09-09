#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
长尾关键词生成器
基于词根组合生成长尾词，集成AI工具类别词汇库，实现智能词汇过滤
"""

import re
from typing import List, Dict, Set, Any, Optional
from collections import Counter
import pandas as pd
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LongtailGenerator:
    """长尾关键词生成器"""
    
    def __init__(self):
        # AI工具类别词汇库
        self.ai_tool_categories = {
            'image': {
                'tools': ['generator', 'creator', 'maker', 'editor', 'enhancer', 'upscaler', 'converter'],
                'actions': ['create', 'generate', 'edit', 'enhance', 'upscale', 'convert', 'design'],
                'formats': ['png', 'jpg', 'svg', 'vector', 'hd', '4k', 'high resolution']
            },
            'text': {
                'tools': ['writer', 'generator', 'editor', 'translator', 'summarizer', 'paraphraser', 'checker'],
                'actions': ['write', 'generate', 'edit', 'translate', 'summarize', 'paraphrase', 'check'],
                'formats': ['article', 'blog', 'essay', 'content', 'copy', 'script']
            },
            'video': {
                'tools': ['generator', 'editor', 'creator', 'enhancer', 'converter', 'maker'],
                'actions': ['create', 'generate', 'edit', 'enhance', 'convert', 'produce'],
                'formats': ['mp4', 'hd', '4k', 'animation', 'short', 'clip']
            },
            'audio': {
                'tools': ['generator', 'editor', 'transcriber', 'converter', 'enhancer', 'synthesizer'],
                'actions': ['generate', 'edit', 'transcribe', 'convert', 'enhance', 'synthesize'],
                'formats': ['mp3', 'wav', 'voice', 'music', 'sound', 'speech']
            },
            'code': {
                'tools': ['generator', 'assistant', 'reviewer', 'optimizer', 'debugger', 'formatter'],
                'actions': ['generate', 'assist', 'review', 'optimize', 'debug', 'format'],
                'formats': ['python', 'javascript', 'html', 'css', 'api', 'function']
            },
            'design': {
                'tools': ['generator', 'creator', 'assistant', 'optimizer', 'enhancer', 'builder'],
                'actions': ['design', 'create', 'generate', 'optimize', 'enhance', 'build'],
                'formats': ['logo', 'banner', 'poster', 'ui', 'mockup', 'template']
            }
        }
        
        # 意图修饰词
        self.intent_modifiers = {
            'informational': [
                'how to', 'what is', 'guide to', 'tutorial for', 'learn',
                'understand', 'explain', 'introduction to', 'basics of'
            ],
            'commercial': [
                'best', 'top', 'compare', 'review', 'vs', 'alternative to',
                'pricing', 'cost', 'features', 'benefits', 'pros and cons'
            ],
            'transactional': [
                'buy', 'download', 'get', 'try', 'free', 'trial', 'demo',
                'signup', 'register', 'purchase', 'order'
            ],
            'navigational': [
                'official', 'website', 'login', 'dashboard', 'app', 'platform'
            ]
        }
        
        # 用户类型修饰词
        self.user_types = [
            'for beginners', 'for professionals', 'for business', 'for students',
            'for developers', 'for designers', 'for marketers', 'for writers',
            'for small business', 'for enterprise', 'for agencies', 'for freelancers'
        ]
        
        # 技术规格修饰词
        self.tech_specs = [
            'api', 'integration', 'plugin', 'extension', 'mobile app', 'desktop',
            'cloud based', 'open source', 'saas', 'web based', 'browser',
            'no code', 'drag and drop', 'automated', 'ai powered'
        ]
        
        # 质量修饰词
        self.quality_modifiers = [
            'high quality', 'professional', 'advanced', 'simple', 'easy',
            'fast', 'powerful', 'smart', 'intelligent', 'accurate',
            'reliable', 'secure', 'scalable', 'customizable'
        ]
        
        # 停用词
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
    
    def generate_category_based_longtails(self, root_keywords: List[str], 
                                        max_per_root: int = 20) -> Dict[str, List[str]]:
        """
        基于AI工具类别生成长尾关键词
        
        Args:
            root_keywords: 词根关键词列表
            max_per_root: 每个词根最大生成数量
            
        Returns:
            按词根分组的长尾关键词字典
        """
        results = {}
        
        for root in root_keywords:
            longtails = set()
            root_lower = root.lower()
            
            # 识别关键词所属类别
            matched_categories = []
            for category, data in self.ai_tool_categories.items():
                if (category in root_lower or 
                    any(tool in root_lower for tool in data['tools']) or
                    any(action in root_lower for action in data['actions'])):
                    matched_categories.append(category)
            
            # 如果没有匹配到类别，使用通用类别
            if not matched_categories:
                matched_categories = ['image', 'text']  # 默认类别
            
            # 为每个匹配的类别生成长尾词
            for category in matched_categories:
                category_data = self.ai_tool_categories[category]
                
                # 工具类型组合
                for tool in category_data['tools']:
                    if tool not in root_lower:
                        longtails.add(f"{root} {tool}")
                        longtails.add(f"{tool} for {root}")
                
                # 动作组合
                for action in category_data['actions']:
                    longtails.add(f"{action} {root}")
                    longtails.add(f"how to {action} {root}")
                
                # 格式组合
                for format_type in category_data['formats']:
                    longtails.add(f"{root} {format_type}")
                    longtails.add(f"{format_type} {root}")
            
            # 限制数量并转换为列表
            results[root] = list(longtails)[:max_per_root]
        
        return results
    
    def generate_intent_based_longtails(self, root_keywords: List[str],
                                      intent_types: List[str] = None,
                                      max_per_intent: int = 10) -> Dict[str, Dict[str, List[str]]]:
        """
        基于搜索意图生成长尾关键词
        
        Args:
            root_keywords: 词根关键词列表
            intent_types: 意图类型列表，默认为所有类型
            max_per_intent: 每个意图最大生成数量
            
        Returns:
            按词根和意图分组的长尾关键词字典
        """
        if intent_types is None:
            intent_types = list(self.intent_modifiers.keys())
        
        results = {}
        
        for root in root_keywords:
            results[root] = {}
            
            for intent in intent_types:
                longtails = set()
                modifiers = self.intent_modifiers[intent]
                
                for modifier in modifiers:
                    longtails.add(f"{modifier} {root}")
                    if intent == 'informational':
                        longtails.add(f"{modifier} use {root}")
                        longtails.add(f"{modifier} choose {root}")
                    elif intent == 'commercial':
                        longtails.add(f"{modifier} {root} 2024")
                        longtails.add(f"{modifier} {root} tool")
                
                results[root][intent] = list(longtails)[:max_per_intent]
        
        return results
    
    def generate_comprehensive_longtails(self, root_keywords: List[str],
                                       max_total: int = 100) -> Dict[str, Any]:
        """
        综合生成长尾关键词
        
        Args:
            root_keywords: 词根关键词列表
            max_total: 最大总数量
            
        Returns:
            综合长尾关键词结果
        """
        logger.info(f"🚀 开始为 {len(root_keywords)} 个词根生成长尾关键词...")
        
        all_longtails = set()
        results = {
            'root_keywords': root_keywords,
            'category_based': {},
            'intent_based': {},
            'all_longtails': [],
            'statistics': {}
        }
        
        # 1. 基于类别生成
        category_longtails = self.generate_category_based_longtails(root_keywords)
        results['category_based'] = category_longtails
        for longtails in category_longtails.values():
            all_longtails.update(longtails)
        
        # 2. 基于意图生成
        intent_longtails = self.generate_intent_based_longtails(root_keywords)
        results['intent_based'] = intent_longtails
        for root_data in intent_longtails.values():
            for longtails in root_data.values():
                all_longtails.update(longtails)
        
        # 3. 过滤和评分
        all_longtails_list = list(all_longtails)
        scored_longtails = []
        
        for longtail in all_longtails_list:
            if len(longtail) > 10 and len(longtail) < 100:
                score = self._calculate_longtail_score(longtail)
                scored_longtails.append({
                    'keyword': longtail,
                    'score': score,
                    'word_count': len(longtail.split()),
                    'estimated_difficulty': self._estimate_difficulty(longtail),
                    'commercial_potential': self._estimate_commercial_potential(longtail)
                })
        
        # 按评分排序并限制数量
        scored_longtails.sort(key=lambda x: x['score'], reverse=True)
        results['all_longtails'] = scored_longtails[:max_total]
        
        # 生成统计信息
        results['statistics'] = {
            'total_generated': len(all_longtails_list),
            'after_filtering': len(scored_longtails),
            'final_count': len(results['all_longtails']),
            'category_count': sum(len(longtails) for longtails in category_longtails.values()),
            'intent_count': sum(len(longtails) for root_data in intent_longtails.values() 
                              for longtails in root_data.values()),
            'avg_score': sum(item['score'] for item in results['all_longtails']) / len(results['all_longtails']) if results['all_longtails'] else 0,
            'high_score_count': len([item for item in results['all_longtails'] if item['score'] >= 80])
        }
        
        logger.info(f"✅ 长尾关键词生成完成:")
        logger.info(f"   总生成数量: {results['statistics']['total_generated']}")
        logger.info(f"   过滤后数量: {results['statistics']['after_filtering']}")
        logger.info(f"   最终数量: {results['statistics']['final_count']}")
        logger.info(f"   平均评分: {results['statistics']['avg_score']:.1f}")
        logger.info(f"   高分关键词: {results['statistics']['high_score_count']}")
        
        return results
    
    def _calculate_longtail_score(self, longtail: str) -> float:
        """计算长尾关键词评分"""
        score = 50.0  # 基础分数
        longtail_lower = longtail.lower()
        
        # 长度评分（3-6个词最佳）
        word_count = len(longtail.split())
        if 3 <= word_count <= 6:
            score += 20
        elif word_count > 6:
            score -= (word_count - 6) * 3
        
        # AI相关性评分
        ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'smart', 'intelligent']
        for ai_kw in ai_keywords:
            if ai_kw in longtail_lower:
                score += 15
                break
        
        # 工具相关性评分
        tool_keywords = ['tool', 'software', 'app', 'platform', 'generator', 'creator']
        for tool_kw in tool_keywords:
            if tool_kw in longtail_lower:
                score += 10
                break
        
        # 意图明确性评分
        clear_intents = ['how to', 'best', 'free', 'vs', 'alternative', 'review']
        for intent in clear_intents:
            if intent in longtail_lower:
                score += 15
                break
        
        return min(score, 100.0)
    
    def _estimate_difficulty(self, longtail: str) -> str:
        """估算关键词难度"""
        word_count = len(longtail.split())
        longtail_lower = longtail.lower()
        
        # 基于词数的难度
        if word_count >= 5:
            base_difficulty = 'Low'
        elif word_count >= 3:
            base_difficulty = 'Medium'
        else:
            base_difficulty = 'High'
        
        # 基于竞争词的调整
        high_competition = ['best', 'top', 'review', 'vs']
        if any(term in longtail_lower for term in high_competition):
            if base_difficulty == 'Low':
                base_difficulty = 'Medium'
            elif base_difficulty == 'Medium':
                base_difficulty = 'High'
        
        return base_difficulty
    
    def _estimate_commercial_potential(self, longtail: str) -> str:
        """估算商业潜力"""
        longtail_lower = longtail.lower()
        
        high_commercial = ['buy', 'price', 'cost', 'pricing', 'professional', 'business', 'enterprise']
        medium_commercial = ['best', 'top', 'review', 'compare', 'alternative']
        
        if any(term in longtail_lower for term in high_commercial):
            return 'High'
        elif any(term in longtail_lower for term in medium_commercial):
            return 'Medium'
        else:
            return 'Low'


def main():
    """测试长尾关键词生成器"""
    generator = LongtailGenerator()
    
    print("🚀 长尾关键词生成器测试")
    print("=" * 50)
    
    # 测试词根
    root_keywords = ['ai image generator', 'chatgpt alternative', 'video editor']
    
    # 综合生成测试
    results = generator.generate_comprehensive_longtails(root_keywords, max_total=50)
    
    print(f"\n📊 生成统计:")
    stats = results['statistics']
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\n🏆 Top 10 长尾关键词:")
    for i, item in enumerate(results['all_longtails'][:10], 1):
        print(f"  {i}. {item['keyword']} (评分: {item['score']:.1f}, 难度: {item['estimated_difficulty']})")
    
    print(f"\n✅ 长尾关键词生成器测试完成!")


if __name__ == '__main__':
    main()