
import ssl
import urllib3
from urllib3.util.ssl_ import create_urllib3_context

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 创建自定义SSL上下文
def create_ssl_context():
    ctx = create_urllib3_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

# 应用SSL修复
def apply_ssl_fix():
    """应用SSL修复配置"""
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    # 创建会话
    session = requests.Session()
    
    # 配置重试策略
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    # 创建适配器
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 禁用SSL验证（仅用于解决兼容性问题）
    session.verify = False
    
    return session
