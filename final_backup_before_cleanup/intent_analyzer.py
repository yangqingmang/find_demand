# 兼容性导入 - 请使用 from src.analyzers.intent_analyzer import IntentAnalyzer
import warnings
warnings.warn("直接导入 intent_analyzer.py 已弃用，请使用 'from src.analyzers.intent_analyzer import IntentAnalyzer'", DeprecationWarning)

from src.analyzers.intent_analyzer import IntentAnalyzer, main

if __name__ == "__main__":
    main()
