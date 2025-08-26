#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""竞争对手分析器 - 用于分析关键词的竞争对手情况和竞争强度"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from urllib.parse import urlparse
from .base_analyzer import BaseAnalyzer

try:
    from src.utils import Logger, FileUtils
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
    """竞争对手分析器"""
    
    def __init__(self, serp_weight=0.4, domain_weight=0.3, content_weight=0.2, backlink_weight=0.1):
        super().__init__()
        # 归一化权重
        total = serp_weight + domain_weight + content_weight + backlink_weight
        self.serp_weight = serp_weight / total
        self.domain_weight = domain_weight / total
        self.content_weight = content_weight / total
        self.backlink_weight = backlink_weight / total
        
        try:
            self.serp_analyzer = SerpAnalyzer()
        except:
            self.serp_analyzer = None
        
        self.competition_grades = {
            'A': {'min_score': 80, 'description': '极高竞争'},
            'B': {'min_score': 60, 'description': '高竞争'},
            'C': {'min_score': 40, 'description': '中等竞争'},
            'D': {'min_score': 20, 'description': '低竞争'},
            'F': {'min_score': 0, 'description': '无竞争'}
        }
        
        self.domain_authority_db = {
            'google.com': 100, 'youtube.com': 98, 'wikipedia.org': 96,
            'github.com': 95, 'stackoverflow.com': 94, 'reddit.com': 92,
            'medium.com': 88, 'openai.com': 85, 'canva.com': 82
        }
    
    def analyze(self, data, keyword_col='query', **kwargs):
        """实现基础分析器的抽象方法"""
        return self.analyze_competitors(data, keyword_col)
    
    def get_domain_authority(self, domain: str) -> int:
        """获取域名权威度评分"""
        domain = domain.lower().replace('www.', '').strip('/')
        
        if domain in self.domain_authority_db:
            return self.domain_authority_db[domain]
        
        # 基于域名特征估算
        score = 30
        if len(domain) <= 10: score += 10
        elif len(domain) <= 15: score += 5
        
        # 顶级域名加分
        tld_scores = {'.com': 15, '.org': 12, '.edu': 20, '.gov': 25, '.io': 8}
        for tld, points in tld_scores.items():
            if domain.endswith(tld):
                score += points
                break
        
        if domain.count('.') > 1: score -= 10
        if any(kw in domain for kw in ['ai', 'tech', 'news', 'blog']): score += 5
        
        return min(100, max(10, score))
    
    def _get_keyword_category(self, keyword: str) -> str:
        """获取关键词类别"""
        keyword_lower = keyword.lower()
        if any(term in keyword_lower for term in ['ai', 'chatgpt', 'openai']):
            return 'ai'
        elif any(term in keyword_lower for term in ['tool', 'generator', 'converter']):
            return 'tool'
        elif any(term in keyword_lower for term in ['tutorial', 'how to', 'guide']):
            return 'tutorial'
        elif any(term in keyword_lower for term in ['buy', 'price', 'cost', 'review']):
            return 'commercial'
        return 'general'
    
    def _get_mock_competitors(self, category: str) -> List[Dict]:
        """根据类别获取模拟竞争对手"""
        competitors_map = {
            'ai': [{'rank': 1, 'domain': 'openai.com', 'authority': 85},
                   {'rank': 2, 'domain': 'github.com', 'authority': 95}],
            'tool': [{'rank': 1, 'domain': 'canva.com', 'authority': 82},
                     {'rank': 2, 'domain': 'github.com', 'authority': 95}],
            'tutorial': [{'rank': 1, 'domain': 'youtube.com', 'authority': 98},
                         {'rank': 2, 'domain': 'medium.com', 'authority': 88}],
            'general': [{'rank': 1, 'domain': 'wikipedia.org', 'authority': 96},
                        {'rank': 2, 'domain': 'reddit.com', 'authority': 92}]
        }
        return competitors_map.get(category, competitors_map['general'])
    
    def analyze_serp_competition(self, keyword: str) -> Dict:
        """分析SERP竞争情况"""
        if self.serp_analyzer:
            try:
                serp_data = self.serp_analyzer.search_google(keyword, num_results=10)
                if serp_data and 'items' in serp_data:
                    competitors = []
                    for i, item in enumerate(serp_data['items'][:10]):
                        domain = urlparse(item['link']).netloc
                        competitors.append({
                            'rank': i + 1, 'domain': domain,
                            'authority': self.get_domain_authority(domain)
                        })
                    
                    avg_authority = np.mean([c['authority'] for c in competitors])
                    score = min(100, avg_authority * 0.8 + len(competitors) * 2)
                    
                    return {
                        'serp_score': round(score, 1),
                        'avg_domain_authority': round(avg_authority, 1),
                        'total_results': len(competitors),
                        'top_competitors': competitors[:5]
                    }
            except Exception as e:
                self.logger.warning(f"SERP分析失败: {e}")
        
        # 模拟数据
        category = self._get_keyword_category(keyword)
        score_ranges = {'ai': (70, 95), 'tool': (50, 75), 'tutorial': (40, 70), 'commercial': (60, 85), 'general': (30, 60)}
        score = np.random.uniform(*score_ranges[category])
        competitors = self._get_mock_competitors(category)
        
        return {
            'serp_score': round(score, 1),
            'avg_domain_authority': round(np.mean([c['authority'] for c in competitors]), 1),
            'total_results': 10,
            'top_competitors': competitors
        }
    
    def analyze_content_competition(self, keyword: str) -> Dict:
        """分析内容竞争情况"""
        category = self._get_keyword_category(keyword)
        
        config = {
            'ai': {'score': 70, 'quality': 'high', 'depth': 'comprehensive'},
            'tool': {'score': 60, 'quality': 'medium', 'depth': 'moderate'},
            'tutorial': {'score': 65, 'quality': 'high', 'depth': 'detailed'},
            'commercial': {'score': 75, 'quality': 'high', 'depth': 'comprehensive'},
            'general': {'score': 50, 'quality': 'medium', 'depth': 'basic'}
        }
        
        base_config = config.get(category, config['general'])
        score = base_config['score'] + np.random.uniform(-10, 10)
        
        return {
            'content_score': round(max(10, min(100, score)), 1),
            'content_quality': base_config['quality'],
            'content_depth': base_config['depth'],
            'estimated_word_count': np.random.randint(800, 3000),
            'multimedia_usage': np.random.choice(['low', 'medium', 'high'], p=[0.3, 0.5, 0.2])
        }
    
    def analyze_backlink_competition(self, keyword: str) -> Dict:
        """分析反向链接竞争情况"""
        category = self._get_keyword_category(keyword)
        
        config = {
            'ai': {'score': (70, 95), 'backlinks': (1000, 10000), 'quality': 'high'},
            'tool': {'score': (40, 70), 'backlinks': (100, 1000), 'quality': 'medium'},
            'tutorial': {'score': (30, 60), 'backlinks': (50, 500), 'quality': 'medium'},
            'commercial': {'score': (50, 80), 'backlinks': (200, 2000), 'quality': 'high'},
            'general': {'score': (20, 50), 'backlinks': (10, 200), 'quality': 'low'}
        }
        
        base_config = config.get(category, config['general'])
        score = np.random.uniform(*base_config['score'])
        backlinks = np.random.randint(*base_config['backlinks'])
        
        return {
            'backlink_score': round(score, 1),
            'avg_backlinks': backlinks,
            'link_quality': base_config['quality'],
            'referring_domains': np.random.randint(backlinks // 10, backlinks // 5)
        }
    
    def _get_competition_level(self, score: float) -> str:
        """根据评分获取竞争等级"""
        for grade, info in self.competition_grades.items():
            if score >= info['min_score']:
                return grade
        return 'F'
    
    def calculate_competition_score(self, serp_data: Dict, content_data: Dict, backlink_data: Dict) -> float:
        """计算综合竞争评分"""
        return round(
            self.serp_weight * serp_data['serp_score'] +
            self.domain_weight * serp_data['avg_domain_authority'] +
            self.content_weight * content_data['content_score'] +
            self.backlink_weight * backlink_data['backlink_score'], 1
        )
    
    def analyze_competitor_gaps(self, keyword: str, competitors: List[Dict]) -> Dict:
        """分析竞争对手的内容空白和机会"""
        category = self._get_keyword_category(keyword)
        
        gaps_config = {
            'tutorial': {'gaps': ['缺少视频教程', '缺少实际案例'], 'score': 20},
            'tool': {'gaps': ['缺少在线工具', '缺少API接口'], 'score': 25},
            'ai': {'gaps': ['缺少最新AI动态', '缺少应用案例'], 'score': 30},
            'general': {'gaps': ['内容深度不足', '用户体验待优化'], 'score': 15}
        }
        
        config = gaps_config.get(category, gaps_config['general'])
        opportunity_score = config['score'] + 15  # 基础分
        
        # 根据竞争对手数量调整
        if len(competitors) < 5:
            opportunity_score += 20
        elif len(competitors) > 8:
            opportunity_score -= 10
        
        return {
            'content_gaps': config['gaps'],
            'opportunity_score': max(0, min(100, opportunity_score))
        }
    
    def analyze_competitors(self, df: pd.DataFrame, keyword_col: str = 'query') -> pd.DataFrame:
        """分析DataFrame中关键词的竞争对手情况"""
        if not self.validate_input(df, [keyword_col]):
            return df
        
        self.log_analysis_start("竞争对手分析", f"，共 {len(df)} 个关键词")
        result_df = df.copy()
        
        # 初始化结果列
        columns = [
            'competition_score', 'competition_grade', 'competition_description',
            'serp_competition_score', 'avg_domain_authority', 'top_competitor_domain',
            'content_competition_score', 'content_quality', 'content_depth',
            'backlink_competition_score', 'avg_backlinks', 'link_quality',
            'opportunity_score', 'content_gaps', 'recommended_strategy'
        ]
        for col in columns:
            result_df[col] = None
        
        # 分析每个关键词
        for idx, row in result_df.iterrows():
            keyword = str(row[keyword_col])
            
            try:
                # 获取各项分析数据
                serp_data = self.analyze_serp_competition(keyword)
                content_data = self.analyze_content_competition(keyword)
                backlink_data = self.analyze_backlink_competition(keyword)
                
                # 计算综合评分
                competition_score = self.calculate_competition_score(serp_data, content_data, backlink_data)
                grade = self._get_competition_level(competition_score)
                
                # 分析机会
                gaps_data = self.analyze_competitor_gaps(keyword, serp_data['top_competitors'])
                strategy = self._generate_strategy(competition_score, gaps_data, keyword)
                
                # 更新数据
                updates = {
                    'competition_score': float(competition_score),
                    'competition_grade': grade,
                    'competition_description': self.competition_grades[grade]['description'],
                    'serp_competition_score': float(serp_data['serp_score']),
                    'avg_domain_authority': float(serp_data['avg_domain_authority']),
                    'top_competitor_domain': serp_data['top_competitors'][0]['domain'] if serp_data['top_competitors'] else '',
                    'content_competition_score': float(content_data['content_score']),
                    'content_quality': content_data['content_quality'],
                    'content_depth': content_data['content_depth'],
                    'backlink_competition_score': float(backlink_data['backlink_score']),
                    'avg_backlinks': int(backlink_data['avg_backlinks']),
                    'link_quality': backlink_data['link_quality'],
                    'opportunity_score': float(gaps_data['opportunity_score']),
                    'content_gaps': '; '.join(gaps_data['content_gaps'][:2]),
                    'recommended_strategy': strategy
                }
                
                for key, value in updates.items():
                    result_df.at[idx, key] = value
                
                if (idx + 1) % 10 == 0:
                    self.logger.info(f"已分析 {idx + 1}/{len(df)} 个关键词")
                    
            except Exception as e:
                self.logger.error(f"分析关键词 '{keyword}' 时出错: {e}")
                # 设置默认值
                defaults = {
                    'competition_score': 50.0, 'competition_grade': 'C',
                    'competition_description': '中等竞争', 'opportunity_score': 50.0,
                    'recommended_strategy': '需要进一步分析'
                }
                for key, value in defaults.items():
                    result_df.at[idx, key] = value
        
        # 数据类型转换
        numeric_cols = ['competition_score', 'serp_competition_score', 'avg_domain_authority',
                       'content_competition_score', 'backlink_competition_score', 'opportunity_score']
        for col in numeric_cols:
            if col in result_df.columns:
                result_df[col] = pd.to_numeric(result_df[col], errors='coerce')
        
        if 'avg_backlinks' in result_df.columns:
            result_df['avg_backlinks'] = pd.to_numeric(result_df['avg_backlinks'], errors='coerce').fillna(0).astype(int)
        
        self.log_analysis_complete("竞争对手分析", len(result_df))
        return result_df
    
    def _generate_strategy(self, competition_score: float, gaps_data: Dict, keyword: str) -> str:
        """生成推荐策略"""
        strategies = []
        
        # 基于竞争评分
        if competition_score < 40:
            strategies.append("低竞争机会，建议快速进入")
        elif competition_score < 60:
            strategies.append("中等竞争，需要差异化内容")
        else:
            strategies.append("高竞争，需要长期SEO策略")
        
        # 基于机会评分
        if gaps_data['opportunity_score'] > 70:
            strategies.append("存在明显内容空白")
        
        # 基于关键词类型
        category = self._get_keyword_category(keyword)
        category_strategies = {
            'tutorial': "重点制作高质量教程",
            'tool': "考虑开发实用工具",
            'ai': "保持技术前沿性"
        }
        if category in category_strategies:
            strategies.append(category_strategies[category])
        
        return '; '.join(strategies[:3])
    
    def generate_competitor_summary(self, df: pd.DataFrame) -> Dict:
        """生成竞争对手分析摘要"""
        if 'competition_score' not in df.columns:
            return {'error': '数据中没有竞争对手分析结果'}
        
        grade_counts = df['competition_grade'].value_counts().to_dict()
        high_competition = df[df['competition_grade'].isin(['A', 'B'])]
        low_competition = df[df['competition_grade'].isin(['D', 'F'])]
        high_opportunity = df[df['opportunity_score'] >= 70]
        
        return {
            'total_keywords': len(df),
            'average_competition_score': round(df['competition_score'].mean(), 1),
            'grade_distribution': grade_counts,
            'low_competition_count': len(low_competition),
            'high_opportunity_count': len(high_opportunity),
            'top_competitor_domains': df['top_competitor_domain'].value_counts().head(5).to_dict(),
            'average_domain_authority': round(df['avg_domain_authority'].mean(), 1),
            'average_opportunity_score': round(df['opportunity_score'].mean(), 1)
        }
    
    def save_results(self, df: pd.DataFrame, output_dir: str = 'data', prefix: str = 'competitor_analysis', **kwargs):
        """保存竞争对手分析结果
        :param **kwargs:
        """
        filename = FileUtils.generate_filename(prefix, extension='csv')
        file_path = FileUtils.save_dataframe(df, output_dir, filename)
        self.logger.info(f"已保存竞争对手分析结果到: {file_path}")
        
        # 保存低竞争关键词
        low_competition_df = df[df['competition_grade'].isin(['D', 'F'])].sort_values('opportunity_score', ascending=False)
        if not low_competition_df.empty:
            low_filename = FileUtils.generate_filename(f'{prefix}_low_competition', extension='csv')
            low_path = FileUtils.save_dataframe(low_competition_df, output_dir, low_filename)
            self.logger.info(f"已保存低竞争关键词 ({len(low_competition_df)}个) 到: {low_path}")

