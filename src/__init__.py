"""
市场需求分析工具集
Market Demand Analysis Toolkit
"""

__version__ = "1.0.0"
__author__ = "Market Analysis Team"
__description__ = "一套完整的市场需求分析工具，包含Google Trends数据采集、关键词评分、搜索意图分析等功能"

from .core.market_analyzer import MarketAnalyzer
from .collectors.trends_collector import TrendsCollector
from .analyzers.keyword_scorer import KeywordScorer
from .analyzers.intent_analyzer import IntentAnalyzer
from .utils.config import DEFAULT_CONFIG

__all__ = [
    'MarketAnalyzer',
    'TrendsCollector', 
    'KeywordScorer',
    'IntentAnalyzer',
    'DEFAULT_CONFIG'
]