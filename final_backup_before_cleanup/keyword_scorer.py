# 兼容性导入 - 请使用 from src.analyzers.keyword_scorer import KeywordScorer
import warnings
warnings.warn("直接导入 keyword_scorer.py 已弃用，请使用 'from src.analyzers.keyword_scorer import KeywordScorer'", DeprecationWarning)

from src.analyzers.keyword_scorer import KeywordScorer, main

if __name__ == "__main__":
    main()
