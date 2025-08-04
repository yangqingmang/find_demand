# 兼容性导入 - 请使用 from src.utils.config import *
import warnings
warnings.warn("直接导入 config.py 已弃用，请使用 'from src.utils.config import *'", DeprecationWarning)

from src.utils.config import *
