"""
关键词评分分析器
提供多维度的关键词评分功能，包括PRAY评分、商业价值评分等
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re
import math

from .base_analyzer import BaseAnalyzer
from ..config import DemandMiningConfig

logger = logging.getLogger(__name__)

@dataclass
class KeywordScore:
    """关键词评分结果"""
    keyword: str
    pray_score: float
    commercial_score: float
    trend_score: float
    competition_score: float
    intent_depth_score: float  # 新增意图深度评分
    total_score: float
    details: Dict[str, Any]

class KeywordScorer(BaseAnalyzer):
    """关键词评分分析器"""
    
    def __init__(self, config: Optional[DemandMiningConfig] = None):
        super().__init__(config)
        self._load_scoring_config()
    
    def _load_scoring_config(self):
        """加载评分配置"""
        try:
            self.scoring_config = self.config.get_config().get('keyword_scoring', {})
            self.pray_weights = self.scoring_config.get('pray_weights', {
                'potential': 0.3, 'reach': 0.25, 'authority': 0.25, 'yield': 0.2
            })
            self.commercial_indicators = self.scoring_config.get('commercial_indicators', {
                'buy_keywords': ['buy', 'purchase', 'order', 'shop', 'price', 'cost', 'cheap', 'discount'],
                'service_keywords': ['service', 'company', 'professional', 'expert', 'consultant'],
                'comparison_keywords': ['vs', 'versus', 'compare', 'best', 'top', 'review']
            })
        except Exception as e:
            logger.warning(f"加载评分配置失败，使用默认配置: {e}")
            self._set_default_config()
    
    def _set_default_config(self):
        """设置默认配置"""
        self.pray_weights = {'potential': 0.3, 'reach': 0.25, 'authority': 0.25, 'yield': 0.2}
        self.commercial_indicators = {
            'buy_keywords': ['buy', 'purchase', 'order', 'shop', 'price', 'cost'],
            'service_keywords': ['service', 'company', 'professional', 'expert'],
            'comparison_keywords': ['vs', 'versus', 'compare', 'best', 'top', 'review']
        }
    
    def score_keywords(self, keywords: List[str], **kwargs) -> List[KeywordScore]:
        """批量评分关键词"""
        if not keywords:
            return []
        
        results = []
        for keyword in keywords:
            try:
                score = self.score_single_keyword(keyword, **kwargs)
                results.append(score)
            except Exception as e:
                logger.error(f"评分关键词 '{keyword}' 失败: {e}")
                results.append(self._create_default_score(keyword))
        
        return sorted(results, key=lambda x: x.total_score, reverse=True)
    
    def score_single_keyword(self, keyword: str, **kwargs) -> KeywordScore:
        """单个关键词评分"""
        if not keyword or not keyword.strip():
            return self._create_default_score(keyword)
        
        keyword = keyword.strip().lower()
        
        # 计算各项评分
        pray_score = self._calculate_pray_score(keyword, **kwargs)
        commercial_score = self._calculate_commercial_score(keyword)
        trend_score = self._calculate_trend_score(keyword, **kwargs)
        competition_score = self._calculate_competition_score(keyword, **kwargs)
        
        # 计算意图深度评分
        intent_depth_score = self._calculate_intent_depth_score(keyword)
        
        # 计算总分 (包含意图深度)
        total_score = self._calculate_total_score(
            pray_score, commercial_score, trend_score, competition_score, intent_depth_score
        )
        
        return KeywordScore(
            keyword=keyword,
            pray_score=pray_score,
            commercial_score=commercial_score,
            trend_score=trend_score,
            competition_score=competition_score,
            intent_depth_score=intent_depth_score,
            total_score=total_score,
            details={
                'length': len(keyword),
                'word_count': len(keyword.split()),
                'has_numbers': bool(re.search(r'\d', keyword)),
                'has_special_chars': bool(re.search(r'[^\w\s]', keyword)),
                'intent_type': self._get_intent_type(keyword),
                'conversion_potential': self._get_conversion_potential(intent_depth_score)
            }
        )
    
    def _calculate_pray_score(self, keyword: str, **kwargs) -> float:
        """计算PRAY评分"""
        try:
            # Potential (潜力)
            potential = self._calculate_potential(keyword, kwargs.get('search_volume', 0))
            
            # Reach (覆盖面)
            reach = self._calculate_reach(keyword, kwargs.get('related_keywords', []))
            
            # Authority (权威性)
            authority = self._calculate_authority(keyword, kwargs.get('domain_authority', 0))
            
            # Yield (收益)
            yield_score = self._calculate_yield(keyword, kwargs.get('cpc', 0))
            
            # 加权计算
            pray_score = (
                potential * self.pray_weights['potential'] +
                reach * self.pray_weights['reach'] +
                authority * self.pray_weights['authority'] +
                yield_score * self.pray_weights['yield']
            )
            
            return min(max(pray_score, 0), 100)
        except Exception as e:
            logger.error(f"计算PRAY评分失败: {e}")
            return 50.0
    
    def _calculate_potential(self, keyword: str, search_volume: int) -> float:
        """计算潜力评分"""
        if search_volume <= 0:
            return self._estimate_potential_by_keyword(keyword)
        
        # 基于搜索量的潜力评分
        if search_volume >= 10000:
            return 90.0
        elif search_volume >= 1000:
            return 70.0 + (search_volume - 1000) / 9000 * 20
        elif search_volume >= 100:
            return 50.0 + (search_volume - 100) / 900 * 20
        else:
            return 30.0 + search_volume / 100 * 20
    
    def _estimate_potential_by_keyword(self, keyword: str) -> float:
        """基于关键词特征估算潜力"""
        score = 50.0
        
        # 长度因子
        length = len(keyword)
        if 5 <= length <= 15:
            score += 10
        elif length > 20:
            score -= 10
        
        # 词数因子
        word_count = len(keyword.split())
        if 2 <= word_count <= 4:
            score += 5
        elif word_count > 6:
            score -= 5
        
        return min(max(score, 0), 100)
    
    def _calculate_reach(self, keyword: str, related_keywords: List[str]) -> float:
        """计算覆盖面评分"""
        base_score = 50.0
        
        # 相关关键词数量
        related_count = len(related_keywords)
        if related_count > 0:
            base_score += min(related_count * 2, 30)
        
        # 关键词通用性
        common_words = ['how', 'what', 'why', 'when', 'where', 'best', 'top', 'guide']
        if any(word in keyword for word in common_words):
            base_score += 10
        
        return min(max(base_score, 0), 100)
    
    def _calculate_authority(self, keyword: str, domain_authority: float) -> float:
        """计算权威性评分"""
        if domain_authority > 0:
            return min(domain_authority, 100)
        
        # 基于关键词特征估算权威性
        score = 50.0
        
        # 品牌词或专业术语
        if any(indicator in keyword for indicator in ['official', 'professional', 'expert', 'certified']):
            score += 20
        
        return min(max(score, 0), 100)
    
    def _calculate_yield(self, keyword: str, cpc: float) -> float:
        """计算收益评分"""
        if cpc > 0:
            # CPC越高，收益潜力越大
            if cpc >= 5.0:
                return 90.0
            elif cpc >= 2.0:
                return 70.0 + (cpc - 2.0) / 3.0 * 20
            elif cpc >= 0.5:
                return 50.0 + (cpc - 0.5) / 1.5 * 20
            else:
                return 30.0 + cpc / 0.5 * 20
        
        return self._estimate_yield_by_keyword(keyword)
    
    def _estimate_yield_by_keyword(self, keyword: str) -> float:
        """基于关键词特征估算收益"""
        score = 50.0
        
        # 商业意图关键词
        commercial_words = self.commercial_indicators['buy_keywords']
        if any(word in keyword for word in commercial_words):
            score += 20
        
        return min(max(score, 0), 100)
    
    def _calculate_commercial_score(self, keyword: str) -> float:
        """计算商业价值评分"""
        score = 0.0
        
        # 购买意图
        buy_words = self.commercial_indicators['buy_keywords']
        buy_matches = sum(1 for word in buy_words if word in keyword)
        score += buy_matches * 15
        
        # 服务意图
        service_words = self.commercial_indicators['service_keywords']
        service_matches = sum(1 for word in service_words if word in keyword)
        score += service_matches * 10
        
        # 比较意图
        comparison_words = self.commercial_indicators['comparison_keywords']
        comparison_matches = sum(1 for word in comparison_words if word in keyword)
        score += comparison_matches * 12
        
        return min(score, 100)
    
    def _calculate_new_word_score(self, keyword: str, **kwargs) -> float:
        """计算新词评分"""
        try:
            # 检查是否有新词检测结果
            new_word_data = kwargs.get('new_word_data', {})
            if new_word_data:
                return new_word_data.get('new_word_score', 0.0)
            
            # 基于关键词特征估算新词分数
            score = 0.0
            
            # 新兴技术词汇
            emerging_tech = ['ai', 'gpt', 'llm', 'blockchain', 'web3', 'defi', 'nft', 
                           'metaverse', 'quantum', 'edge computing', 'iot', 'ar', 'vr']
            if any(tech in keyword.lower() for tech in emerging_tech):
                score += 30
            
            # 年份相关（2023, 2024等表示新趋势）
            import re
            if re.search(r'202[3-9]', keyword):
                score += 20
            
            # 新词特征词汇
            new_indicators = ['new', 'latest', 'emerging', 'trending', 'next-gen', 'future']
            if any(indicator in keyword.lower() for indicator in new_indicators):
                score += 25
            
            # 组合词（多个技术概念组合通常是新词）
            word_count = len(keyword.split())
            if word_count >= 3:
                score += 15
            
            return min(score, 100.0)
        except Exception as e:
            logger.error(f"计算新词评分失败: {e}")
            return 0.0
    
    def _calculate_niche_vertical_score(self, keyword: str) -> float:
        """计算垂直细分领域评分"""
        try:
            score = 0.0
            keyword_lower = keyword.lower()
            
            # 高价值垂直领域
            high_value_verticals = {
                'fintech': ['blockchain', 'defi', 'crypto', 'nft', 'web3', 'dao', 'trading', 'fintech'],
                'healthtech': ['telemedicine', 'digital health', 'wearable', 'biotech', 'medtech'],
                'edtech': ['online learning', 'e-learning', 'mooc', 'lms', 'edtech'],
                'saas': ['crm', 'erp', 'automation', 'workflow', 'api', 'saas'],
                'ai_tools': ['ai tool', 'gpt', 'chatbot', 'machine learning', 'neural network'],
                'emerging_tech': ['quantum', 'ar', 'vr', 'iot', 'edge computing', '5g']
            }
            
            # 检查垂直领域匹配
            for vertical, keywords_list in high_value_verticals.items():
                if any(kw in keyword_lower for kw in keywords_list):
                    if vertical == 'emerging_tech':
                        score += 40  # 新兴技术最高分
                    elif vertical in ['fintech', 'ai_tools']:
                        score += 35  # 金融科技和AI工具高分
                    elif vertical in ['healthtech', 'saas']:
                        score += 30  # 健康科技和SaaS中高分
                    else:
                        score += 25  # 其他垂直领域中等分
                    break
            
            # 专业术语加分
            professional_terms = ['api', 'sdk', 'framework', 'platform', 'solution', 'enterprise']
            if any(term in keyword_lower for term in professional_terms):
                score += 15
            
            # B2B相关加分
            b2b_indicators = ['business', 'enterprise', 'corporate', 'professional', 'commercial']
            if any(indicator in keyword_lower for indicator in b2b_indicators):
                score += 10
            
            # 长尾关键词（通常竞争度较低）
            word_count = len(keyword.split())
            if word_count >= 4:
                score += 15
            elif word_count == 3:
                score += 10
            
            return min(score, 100.0)
        except Exception as e:
            logger.error(f"计算垂直细分评分失败: {e}")
            return 0.0
    
    def _calculate_trend_score(self, keyword: str, **kwargs) -> float:
        """计算趋势评分"""
        trend_data = kwargs.get('trend_data', {})
        if not trend_data:
            return 50.0
        
        try:
            # 获取趋势值
            current_trend = trend_data.get('current', 50)
            trend_direction = trend_data.get('direction', 'stable')
            
            score = current_trend
            
            # 趋势方向调整
            if trend_direction == 'rising':
                score += 10
            elif trend_direction == 'falling':
                score -= 10
            
            return min(max(score, 0), 100)
        except Exception:
            return 50.0
    
    def _calculate_competition_score(self, keyword: str, **kwargs) -> float:
        """计算竞争度评分（分数越高表示竞争越小，机会越大）"""
        competition_level = kwargs.get('competition', 'medium')
        
        competition_scores = {
            'low': 80.0,
            'medium': 50.0,
            'high': 20.0
        }
        
        return competition_scores.get(competition_level, 50.0)
    
    def _calculate_total_score(self, pray: float, commercial: float, 
                             trend: float, competition: float, **kwargs) -> float:
        """计算总评分 (优化版本 - 加入新词和垂直细分权重)"""
        # 获取新词和垂直细分评分
        new_word_score = self._calculate_new_word_score(kwargs.get('keyword', ''), **kwargs)
        niche_score = self._calculate_niche_vertical_score(kwargs.get('keyword', ''))
        
        # 权重配置 (与config.py保持一致)
        weights = {
            'pray': 0.35,              # 降低PRAY权重
            'commercial': 0.25,        # 降低商业权重
            'trend': 0.12,            # 降低趋势权重
            'competition': 0.08,       # 降低竞争权重
            'new_word': 0.12,         # 新词权重
            'niche_vertical': 0.08    # 垂直细分权重
        }
        
        total = (
            pray * weights['pray'] +
            commercial * weights['commercial'] +
            trend * weights['trend'] +
            competition * weights['competition'] +
            new_word_score * weights['new_word'] +
            niche_score * weights['niche_vertical']
        )
        
        return min(max(total, 0), 100)
    
    def _create_default_score(self, keyword: str) -> KeywordScore:
        """创建默认评分"""
        return KeywordScore(
            keyword=keyword,
            pray_score=50.0,
            commercial_score=30.0,
            trend_score=50.0,
            competition_score=50.0,
            total_score=45.0,
            details={'error': 'Failed to calculate score'}
        )
    
    def get_top_keywords(self, keywords: List[str], top_n: int = 10, **kwargs) -> List[KeywordScore]:
        """获取评分最高的关键词"""
        if not keywords:
            return []
        
        scores = self.score_keywords(keywords, **kwargs)
        return scores[:min(top_n, len(scores))]
    
    def filter_by_score(self, keywords: List[str], min_score: float = 60.0, **kwargs) -> List[KeywordScore]:
        """按评分过滤关键词"""
        if not keywords:
            return []
        
        scores = self.score_keywords(keywords, **kwargs)
        return [score for score in scores if score.total_score >= min_score]
    
    def export_scores(self, scores: List[KeywordScore], format: str = 'dict') -> Any:
        """导出评分结果"""
        if format == 'dict':
            return [
                {
                    'keyword': score.keyword,
                    'pray_score': score.pray_score,
                    'commercial_score': score.commercial_score,
                    'trend_score': score.trend_score,
                    'competition_score': score.competition_score,
                    'total_score': score.total_score,
                    'details': score.details
                }
                for score in scores
            ]
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow([
                'Keyword', 'PRAY Score', 'Commercial Score', 
                'Trend Score', 'Competition Score', 'Total Score'
            ])
            
            # 写入数据
            for score in scores:
                writer.writerow([
                    score.keyword, score.pray_score, score.commercial_score,
                    score.trend_score, score.competition_score, score.total_score
                ])
            
            return output.getvalue()
        else:
            return scores
    
    def _calculate_new_word_score(self, keyword: str, **kwargs) -> float:
        """计算新词评分"""
        try:
            # 检查是否有新词检测结果
            new_word_data = kwargs.get('new_word_data', {})
            if new_word_data:
                return new_word_data.get('new_word_score', 0.0)
            
            # 基于关键词特征估算新词分数
            score = 0.0
            
            # 新兴技术词汇
            emerging_tech = ['ai', 'gpt', 'llm', 'blockchain', 'web3', 'defi', 'nft', 
                           'metaverse', 'quantum', 'edge computing', 'iot', 'ar', 'vr']
            if any(tech in keyword.lower() for tech in emerging_tech):
                score += 30
            
            # 年份相关（2023, 2024等表示新趋势）
            import re
            if re.search(r'202[3-9]', keyword):
                score += 20
            
            # 新词特征词汇
            new_indicators = ['new', 'latest', 'emerging', 'trending', 'next-gen', 'future']
            if any(indicator in keyword.lower() for indicator in new_indicators):
                score += 25
            
            # 组合词（多个技术概念组合通常是新词）
            word_count = len(keyword.split())
            if word_count >= 3:
                score += 15
            
            return min(score, 100.0)
        except Exception as e:
            logger.error(f"计算新词评分失败: {e}")
            return 0.0
    
    def _calculate_niche_vertical_score(self, keyword: str) -> float:
        """计算垂直细分领域评分"""
        try:
            score = 0.0
            keyword_lower = keyword.lower()
            
            # 高价值垂直领域
            high_value_verticals = {
                'fintech': ['blockchain', 'defi', 'crypto', 'nft', 'web3', 'dao', 'trading', 'fintech'],
                'healthtech': ['telemedicine', 'digital health', 'wearable', 'biotech', 'medtech'],
                'edtech': ['online learning', 'e-learning', 'mooc', 'lms', 'edtech'],
                'saas': ['crm', 'erp', 'automation', 'workflow', 'api', 'saas'],
                'ai_tools': ['ai tool', 'gpt', 'chatbot', 'machine learning', 'neural network'],
                'emerging_tech': ['quantum', 'ar', 'vr', 'iot', 'edge computing', '5g']
            }
            
            # 检查垂直领域匹配
            for vertical, keywords_list in high_value_verticals.items():
                if any(kw in keyword_lower for kw in keywords_list):
                    if vertical == 'emerging_tech':
                        score += 40  # 新兴技术最高分
                    elif vertical in ['fintech', 'ai_tools']:
                        score += 35  # 金融科技和AI工具高分
                    elif vertical in ['healthtech', 'saas']:
                        score += 30  # 健康科技和SaaS中高分
                    else:
                        score += 25  # 其他垂直领域中等分
                    break
            
            # 专业术语加分
            professional_terms = ['api', 'sdk', 'framework', 'platform', 'solution', 'enterprise']
            if any(term in keyword_lower for term in professional_terms):
                score += 15
            
            # B2B相关加分
            b2b_indicators = ['business', 'enterprise', 'corporate', 'professional', 'commercial']
            if any(indicator in keyword_lower for indicator in b2b_indicators):
                score += 10
            
            # 长尾关键词（通常竞争度较低）
            word_count = len(keyword.split())
            if word_count >= 4:
                score += 15
            elif word_count == 3:
                score += 10
            
            return min(score, 100.0)
        except Exception as e:
            logger.error(f"计算垂直细分评分失败: {e}")
            return 0.0