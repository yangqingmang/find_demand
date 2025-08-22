#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竞争对手分析器 - Competitor Analyzer
用于分析关键词的竞争对手情况和竞争强度
"""

import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import re
import time
from urllib.parse import urlparse, urljoin
import hashlib

from .base_analyzer import BaseAnalyzer

try:
    from src.utils import Logger, FileUtils, ExceptionHandler
    from src.demand_mining.analyzers.serp_analyzer import SerpAnalyzer
except ImportError:
    class Logger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    class FileUtils:
        @staticmethod
        def generate_filename(prefix, extension='csv'):
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"{prefix}_{timestamp}.{extension}"
        
        @staticmethod
        def save_dataframe(df, output_dir, filename):
            import os
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, filename)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            return file_path


class CompetitorAnalyzer(BaseAnalyzer):
    """竞争对手分析器，用于评估关键词的竞争强度和竞争对手情况"""
    
    def __init__(self, serp_weight=0.4, domain_weight=0.3, content_weight=0.2, backlink_weight=0.1):
        """
        初始化竞争对手分析器
        
        参数:
            serp_weight (float): SERP结果权重
            domain_weight (float): 域名权威度权重
            content_weight (float): 内容质量权重
            backlink_weight (float): 反向链接权重
        """
        super().__init__()
        self.serp_weight = serp_weight
        self.domain_weight = domain_weight
        self.content_weight = content_weight
        self.backlink_weight = backlink_weight
        
        # 验证权重总和
        total_weight = serp_weight + domain_weight + content_weight + backlink_weight
        if abs(total_weight - 1.0) > 0.001:
            self.logger.warning(f"权重总和 ({total_weight}) 不等于1，已自动归一化")
            self.serp_weight /= total_weight
            self.domain_weight /= total_weight
            self.content_weight /= total_weight
            self.backlink_weight /= total_weight
        
        # 初始化SERP分析器
        try:
            self.serp_analyzer = SerpAnalyzer()
        except:
            self.serp_analyzer = None
            self.logger.warning("SERP分析器初始化失败")
        
        # 竞争强度等级定义
        self.competition_grades = {
            'A': {'min_score': 80, 'description': '极高竞争 - 顶级竞争对手'},
            'B': {'min_score': 60, 'description': '高竞争 - 强势竞争对手'},
            'C': {'min_score': 40, 'description': '中等竞争 - 一般竞争对手'},
            'D': {'min_score': 20, 'description': '低竞争 - 弱势竞争对手'},
            'F': {'min_score': 0, 'description': '无竞争 - 蓝海机会'}
        }
        
        # 知名域名权威度数据库
        self.domain_authority_db = {
            # 搜索引擎和大型平台
            'google.com': 100, 'youtube.com': 98, 'facebook.com': 97,
            'wikipedia.org': 96, 'twitter.com': 95, 'instagram.com': 94,
            'linkedin.com': 93, 'reddit.com': 92, 'pinterest.com': 90,
            
            # 技术和AI相关权威网站
            'github.com': 95, 'stackoverflow.com': 94, 'medium.com': 88,
            'openai.com': 85, 'huggingface.co': 82, 'arxiv.org': 90,
            'tensorflow.org': 88, 'pytorch.org': 87,
            
            # 新闻和媒体
            'cnn.com': 92, 'bbc.com': 94, 'nytimes.com': 93,
            'techcrunch.com': 89, 'wired.com': 87, 'theverge.com': 86,
            
            # 电商平台
            'amazon.com': 96, 'ebay.com': 90, 'shopify.com': 85,
            
            # 教育平台
            'coursera.org': 88, 'udemy.com': 85, 'edx.org': 87,
            'khanacademy.org': 86,
            
            # 工具和软件
            'adobe.com': 90, 'microsoft.com': 95, 'apple.com': 96,
            'canva.com': 82, 'figma.com': 80
        }
    
    def analyze(self, data, keyword_col='query', **kwargs):
        """
        实现基础分析器的抽象方法
        
        参数:
            data: 关键词数据DataFrame
            keyword_col: 关键词列名
            **kwargs: 其他参数
            
        返回:
            添加了竞争对手分析结果的DataFrame
        """
        return self.analyze_competitors(data, keyword_col)
    
    def get_domain_authority(self, domain: str) -> int:
        """
        获取域名权威度评分
        
        参数:
            domain (str): 域名
            
        返回:
            int: 权威度评分 (0-100)
        """
        # 清理域名
        domain = domain.lower().replace('www.', '').strip('/')
        
        # 查找已知域名
        if domain in self.domain_authority_db:
            return self.domain_authority_db[domain]
        
        # 基于域名特征估算权威度
        authority_score = 30  # 基础分数
        
        # 域名长度影响（短域名通常权威度更高）
        if len(domain) <= 10:
            authority_score += 10
        elif len(domain) <= 15:
            authority_score += 5
        
        # 顶级域名影响
        if domain.endswith('.com'):
            authority_score += 15
        elif domain.endswith('.org'):
            authority_score += 12
        elif domain.endswith('.edu'):
            authority_score += 20
        elif domain.endswith('.gov'):
            authority_score += 25
        elif domain.endswith('.io'):
            authority_score += 8
        
        # 子域名影响
        if domain.count('.') > 1:
            authority_score -= 10
        
        # 特殊关键词影响
        high_authority_keywords = ['ai', 'tech', 'news', 'blog', 'wiki', 'docs']
        for keyword in high_authority_keywords:
            if keyword in domain:
                authority_score += 5
                break
        
        return min(100, max(10, authority_score))
    
    def analyze_serp_competition(self, keyword: str) -> Dict:
        """
        分析SERP竞争情况
        
        参数:
            keyword (str): 关键词
            
        返回:
            dict: SERP竞争分析结果
        """
        if self.serp_analyzer:
            try:
                # 使用真实SERP数据
                serp_data = self.serp_analyzer.search_google(keyword, num_results=10)
                
                if serp_data and 'items' in serp_data:
                    competitors = []
                    total_authority = 0
                    
                    for i, item in enumerate(serp_data['items'][:10]):
                        domain = urlparse(item['link']).netloc
                        authority = self.get_domain_authority(domain)
                        
                        competitor = {
                            'rank': i + 1,
                            'domain': domain,
                            'title': item.get('title', ''),
                            'url': item['link'],
                            'authority': authority
                        }
                        competitors.append(competitor)
                        total_authority += authority
                    
                    avg_authority = total_authority / len(competitors) if competitors else 0
                    
                    # 计算竞争强度
                    competition_score = min(100, avg_authority * 0.8 + len(competitors) * 2)
                    
                    return {
                        'serp_score': competition_score,
                        'avg_domain_authority': avg_authority,
                        'total_results': len(competitors),
                        'top_competitors': competitors[:5],
                        'competition_level': self._get_competition_level(competition_score)
                    }
            except Exception as e:
                self.logger.warning(f"SERP分析失败: {e}")
        
        # 无法获取数据
        return {}
    
        keyword_lower = keyword.lower()
        
        # 基于关键词特征分析竞争强度
        if any(term in keyword_lower for term in ['ai', 'chatgpt', 'openai']):
            # AI相关关键词竞争激烈
            base_score = np.random.uniform(70, 95)
            competitors = [
                {'rank': 1, 'domain': 'openai.com', 'authority': 85},
                {'rank': 2, 'domain': 'github.com', 'authority': 95},
                {'rank': 3, 'domain': 'medium.com', 'authority': 88},
                {'rank': 4, 'domain': 'techcrunch.com', 'authority': 89},
                {'rank': 5, 'domain': 'huggingface.co', 'authority': 82}
            ]
        elif any(term in keyword_lower for term in ['free', 'tool', 'generator']):
            # 工具类关键词中等竞争
            base_score = np.random.uniform(50, 75)
            competitors = [
                {'rank': 1, 'domain': 'canva.com', 'authority': 82},
                {'rank': 2, 'domain': 'github.com', 'authority': 95},
                {'rank': 3, 'domain': 'medium.com', 'authority': 88},
                {'rank': 4, 'domain': 'stackoverflow.com', 'authority': 94},
                {'rank': 5, 'domain': 'reddit.com', 'authority': 92}
            ]
        elif any(term in keyword_lower for term in ['tutorial', 'how to', 'guide']):
            # 教程类关键词竞争适中
            base_score = np.random.uniform(40, 70)
            competitors = [
                {'rank': 1, 'domain': 'youtube.com', 'authority': 98},
                {'rank': 2, 'domain': 'medium.com', 'authority': 88},
                {'rank': 3, 'domain': 'stackoverflow.com', 'authority': 94},
                {'rank': 4, 'domain': 'github.com', 'authority': 95},
                {'rank': 5, 'domain': 'coursera.org', 'authority': 88}
            ]
        else:
            # 其他关键词
            base_score = np.random.uniform(30, 60)
            competitors = [
                {'rank': 1, 'domain': 'wikipedia.org', 'authority': 96},
                {'rank': 2, 'domain': 'medium.com', 'authority': 88},
                {'rank': 3, 'domain': 'reddit.com', 'authority': 92},
                {'rank': 4, 'domain': 'github.com', 'authority': 95},
                {'rank': 5, 'domain': 'stackoverflow.com', 'authority': 94}
            ]
        
        avg_authority = np.mean([comp['authority'] for comp in competitors])
        
        return {
            'serp_score': round(base_score, 1),
            'avg_domain_authority': round(avg_authority, 1),
            'total_results': 10,
            'top_competitors': competitors,
            'competition_level': self._get_competition_level(base_score)
        }
    
    def analyze_content_competition(self, keyword: str) -> Dict:
        """
        分析内容竞争情况
        
        参数:
            keyword (str): 关键词
            
        返回:
            dict: 内容竞争分析结果
        """
        keyword_lower = keyword.lower()
        
        # 基于关键词特征分析内容竞争
        content_score = 50  # 基础分数
        
        # 技术类关键词内容竞争激烈
        if any(term in keyword_lower for term in ['ai', 'machine learning', 'deep learning', 'python']):
            content_score += 20
            content_quality = 'high'
            content_depth = 'comprehensive'
        
        # 工具类关键词内容竞争中等
        elif any(term in keyword_lower for term in ['tool', 'generator', 'converter']):
            content_score += 10
            content_quality = 'medium'
            content_depth = 'moderate'
        
        # 教程类关键词内容丰富
        elif any(term in keyword_lower for term in ['tutorial', 'how to', 'guide']):
            content_score += 15
            content_quality = 'high'
            content_depth = 'detailed'
        
        # 商业类关键词内容竞争激烈
        elif any(term in keyword_lower for term in ['buy', 'price', 'cost', 'review']):
            content_score += 25
            content_quality = 'high'
            content_depth = 'comprehensive'
        
        else:
            content_quality = 'medium'
            content_depth = 'basic'
        
        # 添加随机变化
        content_score += np.random.uniform(-10, 10)
        content_score = max(10, min(100, content_score))
        
        return {
            'content_score': round(content_score, 1),
            'content_quality': content_quality,
            'content_depth': content_depth,
            'estimated_word_count': np.random.randint(800, 3000),
            'multimedia_usage': np.random.choice(['low', 'medium', 'high'], p=[0.3, 0.5, 0.2])
        }
    
    def analyze_backlink_competition(self, keyword: str) -> Dict:
        """
        分析反向链接竞争情况
        
        参数:
            keyword (str): 关键词
            
        返回:
            dict: 反向链接竞争分析结果
        """
        keyword_lower = keyword.lower()
        
        # 基于关键词特征估算反向链接竞争
        if any(term in keyword_lower for term in ['ai', 'chatgpt', 'openai']):
            # AI相关关键词反向链接多
            backlink_score = np.random.uniform(70, 95)
            avg_backlinks = np.random.randint(1000, 10000)
            link_quality = 'high'
        elif any(term in keyword_lower for term in ['tool', 'free', 'generator']):
            # 工具类关键词反向链接中等
            backlink_score = np.random.uniform(40, 70)
            avg_backlinks = np.random.randint(100, 1000)
            link_quality = 'medium'
        elif any(term in keyword_lower for term in ['tutorial', 'guide']):
            # 教程类关键词反向链接较少
            backlink_score = np.random.uniform(30, 60)
            avg_backlinks = np.random.randint(50, 500)
            link_quality = 'medium'
        else:
            # 其他关键词
            backlink_score = np.random.uniform(20, 50)
            avg_backlinks = np.random.randint(10, 200)
            link_quality = 'low'
        
        return {
            'backlink_score': round(backlink_score, 1),
            'avg_backlinks': avg_backlinks,
            'link_quality': link_quality,
            'referring_domains': np.random.randint(avg_backlinks // 10, avg_backlinks // 5)
        }
    
    def _get_competition_level(self, score: float) -> str:
        """
        根据评分获取竞争等级
        
        参数:
            score (float): 竞争评分
            
        返回:
            str: 竞争等级
        """
        for grade, info in self.competition_grades.items():
            if score >= info['min_score']:
                return grade
        return 'F'
    
    def calculate_competition_score(self, serp_data: Dict, content_data: Dict, backlink_data: Dict) -> float:
        """
        计算综合竞争评分
        
        参数:
            serp_data: SERP竞争数据
            content_data: 内容竞争数据
            backlink_data: 反向链接竞争数据
            
        返回:
            float: 综合竞争评分 (0-100)
        """
        competition_score = (
            self.serp_weight * serp_data['serp_score'] +
            self.domain_weight * serp_data['avg_domain_authority'] +
            self.content_weight * content_data['content_score'] +
            self.backlink_weight * backlink_data['backlink_score']
        )
        
        return round(competition_score, 1)
    
    def analyze_competitor_gaps(self, keyword: str, competitors: List[Dict]) -> Dict:
        """
        分析竞争对手的内容空白和机会
        
        参数:
            keyword (str): 关键词
            competitors (List[Dict]): 竞争对手列表
            
        返回:
            dict: 竞争空白分析结果
        """
        # 分析竞争对手的弱点和机会
        gaps = {
            'content_gaps': [],
            'technical_gaps': [],
            'user_experience_gaps': [],
            'opportunity_score': 0
        }
        
        # 基于关键词类型分析潜在机会
        keyword_lower = keyword.lower()
        
        if 'tutorial' in keyword_lower or 'how to' in keyword_lower:
            gaps['content_gaps'].extend([
                '缺少视频教程',
                '缺少实际案例',
                '缺少步骤图解'
            ])
            gaps['opportunity_score'] += 20
        
        if 'tool' in keyword_lower or 'generator' in keyword_lower:
            gaps['technical_gaps'].extend([
                '缺少在线工具',
                '缺少API接口',
                '缺少移动端适配'
            ])
            gaps['opportunity_score'] += 25
        
        if 'ai' in keyword_lower:
            gaps['content_gaps'].extend([
                '缺少最新AI发展动态',
                '缺少实际应用案例',
                '缺少技术对比分析'
            ])
            gaps['opportunity_score'] += 30
        
        # 用户体验方面的通用机会
        gaps['user_experience_gaps'].extend([
            '页面加载速度优化',
            '移动端体验改进',
            '搜索功能增强'
        ])
        gaps['opportunity_score'] += 15
        
        # 根据竞争对手数量调整机会评分
        if len(competitors) < 5:
            gaps['opportunity_score'] += 20
        elif len(competitors) > 8:
            gaps['opportunity_score'] -= 10
        
        gaps['opportunity_score'] = max(0, min(100, gaps['opportunity_score']))
        
        return gaps
    
    def analyze_competitors(self, df: pd.DataFrame, keyword_col: str = 'query') -> pd.DataFrame:
        """
        分析DataFrame中关键词的竞争对手情况
        
        参数:
            df (DataFrame): 关键词数据
            keyword_col (str): 关键词列名
            
        返回:
            添加了竞争对手分析结果的DataFrame
        """
        if not self.validate_input(df, [keyword_col]):
            return df
        
        self.log_analysis_start("竞争对手分析", f"，共 {len(df)} 个关键词")
        
        # 创建副本避免修改原始数据
        result_df = df.copy()
        
        # 初始化结果列
        result_columns = [
            'competition_score', 'competition_grade', 'competition_description',
            'serp_competition_score', 'avg_domain_authority', 'top_competitor_domain',
            'content_competition_score', 'content_quality', 'content_depth',
            'backlink_competition_score', 'avg_backlinks', 'link_quality',
            'opportunity_score', 'content_gaps', 'recommended_strategy'
        ]
        
        for col in result_columns:
            result_df[col] = None
        
        # 分析每个关键词
        for idx, row in result_df.iterrows():
            keyword = str(row[keyword_col])
            
            try:
                # 分析SERP竞争
                serp_data = self.analyze_serp_competition(keyword)
                
                # 分析内容竞争
                content_data = self.analyze_content_competition(keyword)
                
                # 分析反向链接竞争
                backlink_data = self.analyze_backlink_competition(keyword)
                
                # 计算综合竞争评分
                competition_score = self.calculate_competition_score(serp_data, content_data, backlink_data)
                
                # 获取等级和描述
                grade = self._get_competition_level(competition_score)
                description = self.competition_grades[grade]['description']
                
                # 分析竞争空白
                gaps_data = self.analyze_competitor_gaps(keyword, serp_data['top_competitors'])
                
                # 生成推荐策略
                strategy = self._generate_strategy(competition_score, gaps_data, keyword)
                
                # 更新DataFrame
                result_df.at[idx, 'competition_score'] = float(competition_score)
                result_df.at[idx, 'competition_grade'] = grade
                result_df.at[idx, 'competition_description'] = description
                
                # SERP数据
                result_df.at[idx, 'serp_competition_score'] = float(serp_data['serp_score'])
                result_df.at[idx, 'avg_domain_authority'] = float(serp_data['avg_domain_authority'])
                result_df.at[idx, 'top_competitor_domain'] = serp_data['top_competitors'][0]['domain'] if serp_data['top_competitors'] else ''
                
                # 内容数据
                result_df.at[idx, 'content_competition_score'] = float(content_data['content_score'])
                result_df.at[idx, 'content_quality'] = content_data['content_quality']
                result_df.at[idx, 'content_depth'] = content_data['content_depth']
                
                # 反向链接数据
                result_df.at[idx, 'backlink_competition_score'] = float(backlink_data['backlink_score'])
                result_df.at[idx, 'avg_backlinks'] = int(backlink_data['avg_backlinks'])
                result_df.at[idx, 'link_quality'] = backlink_data['link_quality']
                
                # 机会分析
                result_df.at[idx, 'opportunity_score'] = float(gaps_data['opportunity_score'])
                result_df.at[idx, 'content_gaps'] = '; '.join(gaps_data['content_gaps'][:3])  # 只保存前3个
                result_df.at[idx, 'recommended_strategy'] = strategy
                
                if (idx + 1) % 10 == 0:
                    self.logger.info(f"已分析 {idx + 1}/{len(df)} 个关键词")
                    
            except Exception as e:
                self.logger.error(f"分析关键词 '{keyword}' 时出错: {e}")
                # 设置默认值
                result_df.at[idx, 'competition_score'] = 50.0
                result_df.at[idx, 'competition_grade'] = 'C'
                result_df.at[idx, 'competition_description'] = '中等竞争'
                result_df.at[idx, 'opportunity_score'] = 50.0
                result_df.at[idx, 'recommended_strategy'] = '需要进一步分析'
        
        # 确保数值列的数据类型正确
        numeric_columns = ['competition_score', 'serp_competition_score', 'avg_domain_authority',
                          'content_competition_score', 'backlink_competition_score', 'opportunity_score']
        
        for col in numeric_columns:
            if col in result_df.columns:
                result_df[col] = pd.to_numeric(result_df[col], errors='coerce')
        
        # 确保整数列的数据类型正确
        if 'avg_backlinks' in result_df.columns:
            result_df['avg_backlinks'] = pd.to_numeric(result_df['avg_backlinks'], errors='coerce').fillna(0).astype(int)
        
        self.log_analysis_complete("竞争对手分析", len(result_df))
        return result_df
    
    def _generate_strategy(self, competition_score: float, gaps_data: Dict, keyword: str) -> str:
        """
        生成推荐策略
        
        参数:
            competition_score (float): 竞争评分
            gaps_data (Dict): 竞争空白数据
            keyword (str): 关键词
            
        返回:
            str: 推荐策略
        """
        strategies = []
        
        if competition_score < 40:
            strategies.append("低竞争机会，建议快速进入")
        elif competition_score < 60:
            strategies.append("中等竞争，需要差异化内容")
        else:
            strategies.append("高竞争，需要长期SEO策略")
        
        # 基于机会评分添加策略
        if gaps_data['opportunity_score'] > 70:
            strategies.append("存在明显内容空白，机会较大")
        elif gaps_data['opportunity_score'] > 50:
            strategies.append("有一定优化空间")
        
        # 基于关键词类型添加策略
        keyword_lower = keyword.lower()
        if 'tutorial' in keyword_lower:
            strategies.append("重点制作高质量教程内容")
        elif 'tool' in keyword_lower:
            strategies.append("考虑开发实用工具")
        elif 'ai' in keyword_lower:
            strategies.append("保持技术前沿性")
        
        return '; '.join(strategies[:3])  # 最多返回3个策略
    
    def generate_competitor_summary(self, df: pd.DataFrame) -> Dict:
        """
        生成竞争对手分析摘要
        
        参数:
            df (DataFrame): 带有竞争对手分析结果的DataFrame
            
        返回:
            dict: 竞争对手分析摘要
        """
        if 'competition_score' not in df.columns:
            return {'error': '数据中没有竞争对手分析结果'}
        
        # 等级分布
        grade_counts = df['competition_grade'].value_counts().to_dict()
        
        # 竞争强度统计
        avg_competition = df['competition_score'].mean()
        high_competition = df[df['competition_grade'].isin(['A', 'B'])]
        low_competition = df[df['competition_grade'].isin(['D', 'F'])]
        
        # 机会分析
        high_opportunity = df[df['opportunity_score'] >= 70]
        
        # 顶级竞争对手统计
        top_competitors = df['top_competitor_domain'].value_counts().head(10).to_dict()
        
        return {
            'total_keywords': len(df),
            'average_competition_score': round(avg_competition, 1),
            'grade_distribution': grade_counts,
            'high_competition_keywords': high_competition['query'].tolist() if 'query' in df.columns else [],
            'low_competition_keywords': low_competition['query'].tolist() if 'query' in df.columns else [],
            'high_opportunity_keywords': high_opportunity['query'].tolist() if 'query' in df.columns else [],
            'top_competitor_domains': top_competitors,
            'average_domain_authority': round(df['avg_domain_authority'].mean(), 1),
            'average_opportunity_score': round(df['opportunity_score'].mean(), 1)
        }
    
    def save_results(self, df: pd.DataFrame, output_dir: str = 'data', prefix: str = 'competitor_analysis'):
        """
        保存竞争对手分析结果
        
        参数:
            df (DataFrame): 分析结果DataFrame
            output_dir (str): 输出目录
            prefix (str): 文件名前缀
        """
        # 保存主要结果
        filename = FileUtils.generate_filename(prefix, extension='csv')
        file_path = FileUtils.save_dataframe(df, output_dir, filename)
        self.logger.info(f"已保存竞争对手分析结果到: {file_path}")
        
        # 保存低竞争关键词
        low_competition_df = df[df['competition_grade'].isin(['D', 'F'])].sort_values('opportunity_score', ascending=False)
        if not low_competition_df.empty:
            low_filename = FileUtils.generate_filename(f'{prefix}_low_competition', extension='csv')
            low_path = FileUtils.save_dataframe(low_competition_df, output_dir, low_filename)
            self.logger.info(f"已保存低竞争关键词 ({len(low_competition_df)}个) 到: {low_path}")
        
        # 保存高机会关键词
        high_opportunity_df = df[df['opportunity_score'] >= 70].sort_values('opportunity_score', ascending=False)
        if not high_opportunity_df.empty:
            opportunity_filename = FileUtils.generate_filename(f'{prefix}_high_opportunity', extension='csv')
            opportunity_path = FileUtils.save_dataframe(high_opportunity_df, output_dir, opportunity_filename)
            self.logger.info(f"已保存高机会关键词 ({len(high_opportunity_df)}个) 到: {opportunity_path}")


def main():
    """主函数"""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='竞争对手分析工具')
    parser.add_argument('--input', required=True, help='输入CSV文件路径')
    parser.add_argument('--output', default='data', help='输出目录，默认为data')
    parser.add_argument('--keyword-col', default='query', help='关键词列名，默认为query')
    parser.add_argument('--serp-weight', type=float, default=0.4, help='SERP权重，默认0.4')
    parser.add_argument('--domain-weight', type=float, default=0.3, help='域名权威度权重，默认0.3')
    parser.add_argument('--content-weight', type=float, default=0.2, help='内容质量权重，默认0.2')
    parser.add_argument('--backlink-weight', type=float, default=0.1, help='反向链接权重，默认0.1')
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"错误: 输入文件 '{args.input}' 不存在")
        return
    
    # 读取数据
    try:
        df = pd.read_csv(args.input)
        print(f"已读取 {len(df)} 条关键词数据")
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return
    
    # 创建分析器
    analyzer = CompetitorAnalyzer(
        serp_weight=args.serp_weight,
        domain_weight=args.domain_weight,
        content_weight=args.content_weight,
        backlink_weight=args.backlink_weight
    )
    
    # 分析竞争对手
    result_df = analyzer.analyze_competitors(df, args.keyword_col)
    
    # 生成摘要
    summary = analyzer.generate_competitor_summary(result_df)
    
    # 保存结果
    analyzer.save_results(result_df, args.output)
    
    # 显示摘要
    print("\n=== 竞争对手分析摘要 ===")
    print(f"总关键词数: {summary['total_keywords']}")
    print(f"平均竞争评分: {summary['average_competition_score']}")
    print(f"平均域名权威度: {summary['average_domain_authority']}")
    print(f"平均机会评分: {summary['average_opportunity_score']}")
    print(f"低竞争关键词数: {len(summary['low_competition_keywords'])}")
    print(f"高机会关键词数: {len(summary['high_opportunity_keywords'])}")
    
    if summary['top_competitor_domains']:
        print(f"\n主要竞争对手:")
        for domain, count in list(summary['top_competitor_domains'].items())[:5]:
            print(f"  {domain}: {count} 次")


if __name__ == "__main__":
    main()
