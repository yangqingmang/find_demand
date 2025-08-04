# 兼容性导入 - 请使用 main.py 或 from src.core.market_analyzer import MarketAnalyzer
import warnings
warnings.warn("直接导入 market_analyzer.py 已弃用，请使用 'python main.py' 或 'from src.core.market_analyzer import MarketAnalyzer'", DeprecationWarning)

from src.core.market_analyzer import MarketAnalyzer, main

if __name__ == "__main__":
    main()
