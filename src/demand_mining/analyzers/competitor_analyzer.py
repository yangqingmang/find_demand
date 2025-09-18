#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""竞争对手分析器 - 用于分析关键词的竞争对手情况和竞争强度"""

import pandas as pd
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
        raise RuntimeError("竞争对手数据源未配置，无法提供模拟数据")
    
    def analyze_serp_competition(self, keyword: str) -> Dict:
        """分析SERP竞争情况"""
        if not self.serp_analyzer:
            raise RuntimeError("SERP 分析器未启用，无法执行竞争对手分析")

        try:
            serp_result = self.serp_analyzer.analyze_serp_structure(keyword)
        except Exception as exc:
            raise RuntimeError(f"获取关键词 '{keyword}' 的 SERP 结构失败: {exc}") from exc

        if not serp_result or 'competitors' not in serp_result:
            raise RuntimeError(f"SERP 分析未返回竞争对手信息: {keyword}")

        competitors = []
        for comp in serp_result['competitors'][:10]:
            competitors.append({
                'domain': comp['domain'],
                'url': comp['url'],
                'title': comp['title'],
                'position': comp['position'],
                'domain_authority': comp['domain_authority'],
                'competitor_type': comp['competitor_type']
            })

        competition_score = min(100, serp_result['difficulty_score'] * 100)

        return {
            'keyword': keyword,
            'competitors': competitors,
            'competition_score': competition_score,
            'competition_level': serp_result['competition_level'],
            'serp_features': serp_result['structure']
        }
    
    def analyze_content_competition(self, keyword: str) -> Dict:
        """分析内容竞争情况"""
        raise RuntimeError("内容竞争分析需要接入真实内容质量数据，目前未实现")
    
    def analyze_backlink_competition(self, keyword: str) -> Dict:
        """分析反向链接竞争情况"""
        raise RuntimeError("反向链接竞争分析需要接入真实外链数据，目前未实现")
    
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
        raise RuntimeError("竞品内容差距分析需要真实竞品语料，目前未实现")
    
    def analyze_competitors(self, df: pd.DataFrame, keyword_col: str = 'query') -> pd.DataFrame:
        """分析DataFrame中关键词的竞争对手情况"""
        if not self.validate_input(df, [keyword_col]):
            return df

        raise RuntimeError("竞争对手分析功能需要接入真实 SERP/SEO 数据，目前未实现")

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

