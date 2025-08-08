"""
需求挖掘分析工具集
整合六大需求挖掘方法的智能分析系统
"""

__version__ = "2.0.0"
__author__ = "Demand Mining Team"
__description__ = "整合六大需求挖掘方法的完整分析系统，专注于出海AI工具需求发现"

# 只导入确实存在的模块，避免导入错误
try:
    from .demand_mining.demand_mining_main import DemandMiningManager
    __all__ = ['DemandMiningManager']
except ImportError:
    # 如果导入失败，提供空的__all__
    __all__ = []

# 保持向后兼容性，但使用try-except避免错误
try:
    from .core.market_analyzer import MarketAnalyzer
    __all__.append('MarketAnalyzer')
except ImportError:
    pass

try:
    from .collectors.trends_collector import TrendsCollector
    __all__.append('TrendsCollector')
except ImportError:
    pass
