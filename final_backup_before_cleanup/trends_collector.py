# 兼容性导入 - 请使用 from src.collectors.trends_collector import TrendsCollector
import warnings
warnings.warn("直接导入 trends_collector.py 已弃用，请使用 'from src.collectors.trends_collector import TrendsCollector'", DeprecationWarning)

from src.collectors.trends_collector import TrendsCollector, main

if __name__ == "__main__":
    main()
