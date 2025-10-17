#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Google Trends Session 管理模块"""

import json
import logging
import os
import re
import threading
import time
from http.cookiejar import MozillaCookieJar
from typing import Any, Dict, Optional, TYPE_CHECKING, Union
from urllib.parse import urljoin

import requests
from requests.cookies import RequestsCookieJar, create_cookie

try:
    import httpx  # type: ignore
except ImportError:  # pragma: no cover
    httpx = None

try:
    from playwright.sync_api import (
        sync_playwright,  # type: ignore
        TimeoutError as PlaywrightTimeoutError,  # type: ignore
    )
except ImportError:  # pragma: no cover
    sync_playwright = None
    PlaywrightTimeoutError = None

if TYPE_CHECKING:  # pragma: no cover
    from httpx import Response as HTTPXResponse

# 导入代理管理器
try:
    from ..demand_mining.core.proxy_manager import get_proxy_manager
except ImportError:
    # 如果导入失败，使用None
    get_proxy_manager = None
    logging.warning("代理管理器不可用，将使用直接请求")

logger = logging.getLogger(__name__)

ResponseType = Union[requests.Response, "HTTPXResponse", "PlaywrightResponseAdapter"]


class PlaywrightResponseAdapter:
    """适配 Playwright APIResponse 以兼容 requests 接口"""

    def __init__(self, response, cookies: RequestsCookieJar):
        self._response = response
        self.url = response.url
        self.status_code = response.status
        self.headers = response.headers
        self._cookies = cookies
        try:
            self._text = response.text()
        except Exception:
            self._text = ""
        try:
            self._content = response.body()
        except Exception:
            self._content = b""
        self._json_cache: Optional[Any] = None

    @property
    def text(self) -> str:
        return self._text

    @property
    def content(self) -> bytes:
        return self._content

    @property
    def cookies(self) -> RequestsCookieJar:
        return self._cookies

    def json(self) -> Any:
        if self._json_cache is None:
            try:
                self._json_cache = self._response.json()
            except Exception as json_error:
                raise ValueError(f"无法解析 Playwright 响应 JSON: {json_error}")
        return self._json_cache

    def raise_for_status(self) -> None:
        if 400 <= self.status_code:
            raise requests.HTTPError(
                f"{self.status_code} Error for url: {self.url}", response=self
            )

from .request_rate_limiter import wait_for_next_request, register_rate_limit_event

class GoogleTrendsSession:
    """Google Trends Session 管理类"""
    
    def __init__(
        self,
        timeout: tuple = (20, 30),
        use_proxy: bool = True,
        backend: Optional[str] = None,
    ):
        self.timeout = timeout
        self.client_backend = self._resolve_backend(backend)
        self.session: Optional[Any] = None
        self.headers = self._load_headers()
        self.initialized = False
        self.use_proxy = use_proxy
        self.proxy_manager = None
        self._cookie_lock = threading.Lock()
        self._playwright = None
        self._playwright_browser = None
        self._playwright_context = None
        logger.debug(
            "GoogleTrendsSession 初始化，后端=%s，代理=%s",
            self.client_backend,
            "on" if use_proxy else "off",
        )

        if self.client_backend == 'playwright' and self.use_proxy:
            logger.info("Playwright 后端暂未整合代理通道，自动禁用代理模式")
            self.use_proxy = False

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        cookie_dir = os.path.join(project_root, 'output', 'tmp')
        os.makedirs(cookie_dir, exist_ok=True)
        self.cookie_path = os.path.join(cookie_dir, 'google_trends_cookie.txt')
        self.cookie_jar = MozillaCookieJar(self.cookie_path)
        self._load_cookie_jar()
        
        # 初始化代理管理器
        if self.use_proxy and get_proxy_manager:
            try:
                # 检查代理配置是否启用
                import sys
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)
                
                from config.proxy_config_loader import get_proxy_config
                proxy_config = get_proxy_config()
                
                if not proxy_config.enabled:
                    logger.info("ℹ️ 代理在当前环境中被禁用，使用直接请求")
                    self.use_proxy = False
                elif not proxy_config.proxies:
                    logger.warning("⚠️ 代理列表为空，使用直接请求")
                    self.use_proxy = False
                else:
                    self.proxy_manager = get_proxy_manager()
                    logger.info(f"✅ 代理管理器已启用，加载了 {len(proxy_config.proxies)} 个代理")
                    
            except Exception as e:
                logger.warning(f"⚠️ 代理管理器初始化失败: {e}，将使用直接请求")
                self.use_proxy = False
        
    @staticmethod
    def _load_headers() -> Dict[str, str]:
        """加载Google Trends请求头配置"""
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'google_trends_headers.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                headers_config = json.load(f)
                return headers_config['google_trends_headers']
        except Exception as e:
            logger.warning(f"加载headers配置失败，使用默认配置: {e}")
            # 如果加载失败，返回默认headers
            return {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.61 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Referer': 'https://trends.google.com/trends/explore?hl=en-US&tz=360',
                'Origin': 'https://trends.google.com',
                'Connection': 'keep-alive',
                'DNT': '0',
                'TE': 'trailers',
                'Priority': 'u=1, i',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Ch-Ua': '"Not/A)Brand";v="99", "Google Chrome";v="126", "Chromium";v="126"',
                'Sec-Ch-Ua-Full-Version': '"126.0.6478.61"',
                'Sec-Ch-Ua-Full-Version-List': '"Not/A)Brand";v="99.0.0.0", "Google Chrome";v="126.0.6478.61", "Chromium";v="126.0.6478.61"',
                'Sec-Ch-Ua-Reduced': '"Google Chrome";v="126"',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Ch-Ua-Platform-Version': '"15.0.0"',
                'Sec-Ch-Ua-Arch': '"x86"',
                'Sec-Ch-Ua-Bitness': '"64"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Model': '""',
                'Sec-Ch-Ua-Wow64': '?0',
                'Sec-Ch-Ua-Form-Factor': '"Desktop"',
                'Sec-CH-Prefers-Color-Scheme': '"light"',
                'Sec-CH-Prefers-Reduced-Motion': '"no-preference"',
                'Viewport-Width': '1920',
                'Downlink': '10',
                'ECT': '4g',
                'RTT': '50',
                'X-Client-Data': 'CK6/ygEIlLbJAQjBtskBCKmdygEIptzKAQj8tc0BCJrdzgEIk7nOARis7c4B'
            }

    def _resolve_backend(self, backend: Optional[str]) -> str:
        """解析会话使用的HTTP后端"""
        candidates = [
            backend,
            os.getenv('FIND_DEMAND_TRENDS_BACKEND'),
            os.getenv('FIND_DEMAND_HTTP_BACKEND'),
            'playwright' if sync_playwright is not None else None,
            'httpx' if httpx is not None else None,
            'requests',
        ]
        for candidate in candidates:
            if not candidate:
                continue
            normalized = candidate.strip().lower()
            if normalized not in {'requests', 'httpx', 'playwright'}:
                logger.warning(f"未知的HTTP后端配置: {candidate}，忽略")
                continue
            if normalized == 'httpx' and httpx is None:
                logger.warning("httpx 未安装，GoogleTrendsSession 自动回退至 requests")
                return 'requests'
            if normalized == 'playwright' and sync_playwright is None:
                logger.warning("Playwright 未安装，GoogleTrendsSession 自动回退至其他后端")
                continue
            return normalized
        return 'requests'

    def _build_httpx_timeout(self, timeout: Union[int, float, tuple]) -> "httpx.Timeout":
        """构造 httpx Timeout 对象"""
        assert httpx is not None
        if isinstance(timeout, (int, float)):
            return httpx.Timeout(timeout=timeout)
        if isinstance(timeout, tuple):
            if len(timeout) == 2:
                connect, read = timeout
                return httpx.Timeout(
                    connect=connect,
                    read=read,
                    write=read,
                    pool=connect,
                )
            if len(timeout) == 4:
                connect, read, write, pool = timeout
                return httpx.Timeout(
                    connect=connect,
                    read=read,
                    write=write,
                    pool=pool,
                )
        return httpx.Timeout(timeout=30)

    def _prepare_httpx_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """requests 参数转为 httpx 兼容形式"""
        assert httpx is not None
        converted = dict(kwargs)
        timeout = converted.get('timeout', self.timeout)
        converted['timeout'] = self._build_httpx_timeout(timeout)
        if 'allow_redirects' in converted:
            converted['follow_redirects'] = converted.pop('allow_redirects')
        return converted

    def _session_request(self, method: str, url: str, **kwargs) -> ResponseType:
        """统一会话请求入口，兼容 requests 与 httpx"""
        if not self.session:
            raise RuntimeError("会话尚未初始化")

        if self.client_backend == 'playwright':
            return self._playwright_request(method, url, **kwargs)

        if self.client_backend == 'httpx':
            if httpx is None:
                raise RuntimeError("httpx 未安装，无法使用 httpx 后端")
            httpx_kwargs = self._prepare_httpx_kwargs(kwargs)
            return self.session.request(method, url, **httpx_kwargs)

        return self.session.request(method, url, **kwargs)

    def _get_session_cookie_jar(self):
        """获取底层cookie jar"""
        if self.client_backend == 'playwright':
            return self._playwright_cookies_to_jar()

        if not self.session:
            return None
        cookies = getattr(self.session, 'cookies', None)
        if cookies is None:
            return None
        jar = getattr(cookies, 'jar', None)
        return jar if jar is not None else cookies

    def _set_cookie_on_session(self, cookie) -> None:
        """将cookie写入当前会话"""
        if self.client_backend == 'playwright':
            if not self._playwright_context:
                return
            cookie_dict = {
                'name': cookie.name,
                'value': cookie.value,
                'path': cookie.path or '/',
                'domain': cookie.domain or '.trends.google.com',
            }
            if cookie.expires:
                cookie_dict['expires'] = cookie.expires
            try:
                self._playwright_context.add_cookies([cookie_dict])
            except Exception as cookie_error:
                logger.debug(f"Playwright cookie 写入失败: {cookie_error}")
            return

        if not self.session:
            return
        cookies_obj = getattr(self.session, 'cookies', None)
        if cookies_obj is None:
            return
        if hasattr(cookies_obj, 'set_cookie'):
            try:
                cookies_obj.set_cookie(cookie)
                return
            except Exception:
                pass
        try:
            cookies_obj.set(
                cookie.name,
                cookie.value,
                domain=cookie.domain,
                path=cookie.path or '/',
                expires=cookie.expires,
            )
        except Exception as cookie_error:
            logger.debug(f"写入cookie失败，已忽略: {cookie_error}")

    def _iter_session_cookies(self):
        """迭代当前session的cookie对象"""
        jar = self._get_session_cookie_jar()
        if jar is None:
            return []
        try:
            return list(jar)
        except TypeError:
            return []

    def _load_cookie_jar(self) -> None:
        """尝试从磁盘加载已有cookie"""
        if not os.path.exists(self.cookie_path):
            return

        try:
            if os.path.getsize(self.cookie_path) == 0:
                return
        except OSError as os_error:
            logger.debug(f"读取cookie文件失败: {os_error}")
            return

        with self._cookie_lock:
            try:
                self.cookie_jar.load(ignore_discard=True, ignore_expires=True)
                logger.debug("已从磁盘载入 Google Trends cookies")
            except Exception as load_error:
                logger.warning(f"加载cookie失败，将重新生成: {load_error}")
                try:
                    os.remove(self.cookie_path)
                except OSError:
                    pass
                self.cookie_jar = MozillaCookieJar(self.cookie_path)
    
    def get_session(self) -> Any:
        """获取已初始化的session"""
        if self.session is None:
            self._create_session()
        
        if not self.initialized:
            self._init_session()
            if not self.initialized:
                raise RuntimeError("Google Trends会话初始化失败，请在执行任何 API 请求前检查网络或代理配置")

        return self.session
    
    def _create_session(self) -> None:
        """创建新的session"""
        if self.client_backend == 'playwright':
            self._create_playwright_session()
        elif self.client_backend == 'httpx' and httpx is not None:
            try:
                timeout = self._build_httpx_timeout(self.timeout)
                self.session = httpx.Client(
                    http2=True,
                    headers=self.headers.copy(),
                    timeout=timeout,
                    trust_env=False,
                    follow_redirects=True,
                )
                logger.debug("创建新的Google Trends httpx 客户端")
            except Exception as exc:
                logger.warning(f"httpx 客户端创建失败 ({exc})，回退到 requests")
                self.client_backend = 'requests'
                self.session = None

        if self.session is None and self.client_backend != 'playwright':
            self.session = requests.Session()
            logger.debug("创建新的Google Trends requests session")

        if self.client_backend != 'playwright':
            try:
                self.session.headers.update(self.headers)
            except AttributeError:
                pass

        self._apply_cookies_to_session()
        logger.debug("创建新的Google Trends session")

    def _create_playwright_session(self) -> None:
        """创建 Playwright 浏览器上下文并复用其请求能力"""
        if sync_playwright is None:  # pragma: no cover - 运行环境缺少playwright
            raise RuntimeError("Playwright 未安装，无法启用浏览器指纹会话")

        headless_flag = os.getenv('FIND_DEMAND_PLAYWRIGHT_HEADLESS', '1').strip().lower()
        headless = headless_flag not in {'0', 'false', 'no'}

        if self._playwright is None:
            self._playwright = sync_playwright().start()

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
        ]

        if self._playwright_browser is None:
            self._playwright_browser = self._playwright.chromium.launch(
                headless=headless,
                args=launch_args,
            )

        locale = (self.headers.get('Accept-Language') or 'en-US').split(',')[0]
        user_agent = self.headers.get('User-Agent')

        context_kwargs: Dict[str, Any] = {
            'ignore_https_errors': True,
            'locale': locale,
        }
        if user_agent:
            context_kwargs['user_agent'] = user_agent

        if self._playwright_context is not None:
            try:
                self._playwright_context.close()
            except Exception:
                pass

        self._playwright_context = self._playwright_browser.new_context(**context_kwargs)
        self._playwright_context.set_extra_http_headers(self.headers.copy())
        self.session = self._playwright_context.request
        logger.debug("Playwright 请求上下文已创建 (headless=%s)", headless)

    def _playwright_cookies_to_jar(self) -> RequestsCookieJar:
        jar = RequestsCookieJar()
        if not self._playwright_context:
            return jar
        try:
            cookies = self._playwright_context.cookies()
        except Exception as cookie_error:
            logger.debug(f"读取 Playwright cookies 失败: {cookie_error}")
            return jar

        for cookie in cookies:
            try:
                jar.set_cookie(
                    create_cookie(
                        name=cookie.get('name'),
                        value=cookie.get('value'),
                        domain=cookie.get('domain'),
                        path=cookie.get('path', '/'),
                        expires=cookie.get('expires'),
                        secure=cookie.get('secure', False),
                        rest={'HttpOnly': cookie.get('httpOnly', False)},
                    )
                )
            except Exception as cookie_error:
                logger.debug(f"写入 Playwright cookie 至 Jar 失败: {cookie_error}")
        return jar

    def _convert_timeout_to_ms(self, timeout: Union[int, float, tuple]) -> Optional[float]:
        if timeout is None:
            return None
        if isinstance(timeout, (int, float)):
            return max(float(timeout), 0.0) * 1000
        if isinstance(timeout, tuple) and timeout:
            try:
                effective = max(float(value) for value in timeout)
                return max(effective, 0.0) * 1000
            except Exception:
                return None
        return None

    def _playwright_request(self, method: str, url: str, **kwargs) -> PlaywrightResponseAdapter:
        if not self.session or not self._playwright_context:
            raise RuntimeError("Playwright 会话尚未初始化")

        request = self.session
        request_kwargs: Dict[str, Any] = {}

        headers = kwargs.pop('headers', None)
        params = kwargs.pop('params', None)
        data = kwargs.pop('data', None)
        json_payload = kwargs.pop('json', None)
        allow_redirects = kwargs.pop('allow_redirects', True)
        timeout = kwargs.pop('timeout', self.timeout)

        timeout_ms = self._convert_timeout_to_ms(timeout)
        if headers:
            request_kwargs['headers'] = headers
        if params is not None:
            request_kwargs['params'] = params
        if data is not None:
            request_kwargs['data'] = data
        if json_payload is not None:
            request_kwargs['json'] = json_payload
        if timeout_ms is not None:
            request_kwargs['timeout'] = timeout_ms
        if allow_redirects is not None:
            request_kwargs['max_redirects'] = 20 if allow_redirects else 0

        method_lower = method.lower()
        method_callable = getattr(request, method_lower, None)

        try:
            if callable(method_callable):
                response = method_callable(url, **request_kwargs)
            else:
                request_kwargs['method'] = method.upper()
                response = request.fetch(url, **request_kwargs)
        except PlaywrightTimeoutError as timeout_error:
            raise requests.Timeout(f"Playwright 请求超时: {timeout_error}")
        except Exception as playwright_error:
            raise requests.RequestException(f"Playwright 请求异常: {playwright_error}")

        cookies_jar = self._playwright_cookies_to_jar()
        return PlaywrightResponseAdapter(response, cookies_jar)

    def _apply_cookies_to_session(self) -> None:
        """将持久化cookie写入session"""
        if not self.session:
            return
        with self._cookie_lock:
            for cookie in list(self.cookie_jar):
                try:
                    self._set_cookie_on_session(cookie)
                except Exception as cookie_error:
                    logger.debug(f"写入cookie失败，已忽略: {cookie_error}")

    def _persist_session_cookies(self) -> None:
        """将当前session cookie持久化到磁盘"""
        if not self.session:
            return

        with self._cookie_lock:
            jar = MozillaCookieJar(self.cookie_path)
            for cookie in self._iter_session_cookies():
                try:
                    jar.set_cookie(cookie)
                except Exception as cookie_error:
                    logger.debug(f"持久化cookie失败，已忽略: {cookie_error}")
            try:
                jar.save(ignore_discard=True, ignore_expires=True)
                self.cookie_jar = jar
                logger.debug("已刷新 Google Trends cookies 到磁盘")
            except Exception as save_error:
                logger.warning(f"保存cookie失败: {save_error}")

    def _merge_response_cookies(self, response: ResponseType) -> None:
        """将响应中的cookie合并到当前session"""
        if not self.session or not response:
            return
        cookies_obj = getattr(response, 'cookies', None)
        if not cookies_obj:
            return
        source = getattr(cookies_obj, 'jar', None) or cookies_obj
        try:
            for cookie in source:
                self._set_cookie_on_session(cookie)
        except TypeError:
            items = getattr(source, 'items', None)
            if callable(items):
                for name, value in items():
                    try:
                        self.session.cookies.set(name, value)
                    except Exception:
                        pass
        except Exception as cookie_error:
            logger.debug(f"响应cookie合并失败: {cookie_error}")

    def _prefetch_primary_assets(self, main_page_html: str) -> None:
        """模拟浏览器加载首批静态资源，补全指纹"""
        if not main_page_html:
            return

        try:
            script_match = re.search(r'src="(https://[^"]+/_/scs/tt-static/[^"]+\.js)"', main_page_html)
            if not script_match:
                script_match = re.search(r'src="(/_/scs/tt-static/[^"]+\.js)"', main_page_html)

            style_match = re.search(r'href="(https://[^"]+/_/scs/tt-static/[^"]+\.css)"', main_page_html)
            if not style_match:
                style_match = re.search(r'href="(/_/scs/tt-static/[^"]+\.css)"', main_page_html)

            assets = []
            if script_match:
                assets.append(('script', script_match.group(1)))
            if style_match:
                assets.append(('style', style_match.group(1)))

            for asset_type, raw_url in assets[:2]:
                asset_url = urljoin('https://trends.google.com/', raw_url)
                asset_headers = dict(self.headers)
                asset_headers['Referer'] = 'https://trends.google.com/'
                asset_headers['Origin'] = 'https://trends.google.com'
                asset_headers['Priority'] = 'u=2, i' if asset_type == 'script' else 'u=3, i'
                if asset_type == 'script':
                    asset_headers['Accept'] = 'text/javascript, application/javascript;q=0.9, */*;q=0.8'
                    asset_headers['Sec-Fetch-Dest'] = 'script'
                else:
                    asset_headers['Accept'] = 'text/css,*/*;q=0.1'
                    asset_headers['Sec-Fetch-Dest'] = 'style'
                asset_headers['Sec-Fetch-Mode'] = 'no-cors'
                asset_headers['Sec-Fetch-Site'] = 'same-origin' if asset_url.startswith('https://trends.google.com') else 'cross-site'

                try:
                    wait_for_next_request()
                except RuntimeError:
                    pass
                except Exception as limiter_error:
                    logger.debug(f"预取资源等待限流槽位时异常: {limiter_error}")

                try:
                    response = self._session_request('GET', asset_url, headers=asset_headers, timeout=self.timeout)
                    if response.status_code == 200:
                        logger.debug("已预取 Google Trends %s 资源: %s", asset_type, asset_url)
                        if response.cookies:
                            self._persist_session_cookies()
                except Exception as fetch_error:
                    logger.debug("预取资源失败 (%s): %s", asset_url, fetch_error)

        except Exception as parse_error:
            logger.debug(f"预取资源解析失败: {parse_error}")
    
    def _init_session(self) -> None:
        """初始化会话，获取必要的cookies"""
        try:
            logger.info("🔧 正在初始化Google Trends会话...")

            bootstrap_headers = dict(self.headers)
            bootstrap_headers.pop('Origin', None)
            bootstrap_headers['Referer'] = 'https://trends.google.com/'
            bootstrap_headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Priority': 'u=0, i'
            })

            time.sleep(3)

            # 先访问主页获取cookies
            main_page_url = 'https://trends.google.com/'
            try:
                wait_for_next_request()
            except RuntimeError as limiter_error:
                penalty = register_rate_limit_event('medium')
                logger.error("❌ 会话初始化因频控限制被阻止: %s", limiter_error)
                if penalty:
                    logger.info("建议等待 %.1f 秒后重试会话初始化", penalty)
                self.initialized = False
                return

            response = self._session_request('GET', main_page_url, headers=bootstrap_headers, timeout=self.timeout)
            self._persist_session_cookies()
            main_page_html = ''

            if response.status_code == 429:
                logger.warning("⚠️ 首次访问主页遇到429，尝试使用新cookie重试")
                time.sleep(2)
                try:
                    wait_for_next_request()
                except RuntimeError as limiter_error:
                    penalty = register_rate_limit_event('high')
                    logger.error("❌ 重试前被限流: %s", limiter_error)
                    if penalty:
                        logger.info("建议等待 %.1f 秒后重试初始化流程", penalty)
                    self.initialized = False
                    return

                response = self._session_request('GET', main_page_url, headers=bootstrap_headers, timeout=self.timeout)
                self._persist_session_cookies()

            if response.status_code != 200:
                penalty = register_rate_limit_event('high')
                if penalty:
                    logger.error("❌ 主页访问失败，状态码: %s，建议等待 %.1f 秒", response.status_code, penalty)
                else:
                    logger.error(f"❌ 主页访问失败，状态码: {response.status_code}")
                self.initialized = False
                return
            else:
                main_page_html = response.text

            self._prefetch_primary_assets(main_page_html)

            # 再访问一个trends explore页面，确保session完全建立
            time.sleep(2)
            trends_page_url = 'https://trends.google.com/trends/explore?q=automation'

            try:
                wait_for_next_request()
            except RuntimeError as limiter_error:
                penalty = register_rate_limit_event('medium')
                logger.error("❌ 会话初始化后续请求被限流: %s", limiter_error)
                if penalty:
                    logger.info("建议等待 %.1f 秒后重试初始化流程", penalty)
                self.initialized = False
                return

            trends_response = self._session_request('GET', trends_page_url, headers=bootstrap_headers, timeout=self.timeout)
            self._persist_session_cookies()

            if trends_response.status_code == 429:
                logger.warning("⚠️ explore 页面返回429，尝试携带cookie再次访问")
                time.sleep(2)
                try:
                    wait_for_next_request()
                except RuntimeError as limiter_error:
                    penalty = register_rate_limit_event('high')
                    logger.error("❌ explore 重试前被限流: %s", limiter_error)
                    if penalty:
                        logger.info("建议等待 %.1f 秒后重试初始化流程", penalty)
                    self.initialized = False
                    return

                trends_response = self._session_request('GET', trends_page_url, headers=bootstrap_headers, timeout=self.timeout)
                self._persist_session_cookies()

            if trends_response.status_code == 200:
                self.initialized = True
                logger.info("✅ Google Trends会话初始化成功")
            else:
                penalty = register_rate_limit_event('high')
                if penalty:
                    logger.error("❌ explore 页面访问失败，状态码: %s，建议等待 %.1f 秒", trends_response.status_code, penalty)
                else:
                    logger.error(f"❌ explore 页面访问失败，状态码: {trends_response.status_code}")
                self.initialized = False

        except Exception as e:
            logger.error(f"❌ 会话初始化失败: {e}")
            self.initialized = False
    
    def reset_session(self) -> None:
        """重置会话"""
        try:
            self._close_session()
            self._create_session()
            self._init_session()
            if not self.initialized:
                raise RuntimeError("Google Trends会话重置失败，未获得有效会话")
            logger.info("会话已重置")
        except Exception as e:
            logger.error(f"重置会话失败: {e}")
    
    def get_headers(self) -> Dict[str, str]:
        """获取headers"""
        return self.headers.copy()
    
    def update_headers(self, new_headers: Dict[str, str]) -> None:
        """更新headers"""
        self.headers.update(new_headers)
        if self.client_backend == 'playwright' and self._playwright_context:
            try:
                self._playwright_context.set_extra_http_headers(self.headers.copy())
            except Exception as header_error:
                logger.debug(f"Playwright header 更新失败: {header_error}")
        elif self.session:
            try:
                self.session.headers.update(new_headers)
            except Exception as header_error:
                logger.debug(f"会话header更新失败: {header_error}")

    def _close_playwright(self) -> None:
        if self.session:
            try:
                dispose = getattr(self.session, "dispose", None)
                if callable(dispose):
                    dispose()
            except Exception:
                pass
        if self._playwright_context:
            try:
                self._playwright_context.close()
            except Exception:
                pass
            finally:
                self._playwright_context = None
        if self._playwright_browser:
            try:
                self._playwright_browser.close()
            except Exception:
                pass
            finally:
                self._playwright_browser = None
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            finally:
                self._playwright = None
        self.session = None

    def _close_session(self) -> None:
        if self.client_backend == 'playwright':
            self._close_playwright()
            return
        if self.session:
            try:
                self.session.close()
            except Exception:
                pass
        self.session = None

    def _log_request_debug_snapshot(
        self,
        method: str,
        url: str,
        kwargs: Dict[str, Any],
        via_proxy: bool = False,
    ) -> None:
        """输出调试请求快照，协助指纹对比"""
        if not logger.isEnabledFor(logging.DEBUG):
            return

        effective_headers: Dict[str, str] = {}
        if self.session:
            try:
                effective_headers.update(self.session.headers or {})
            except Exception as header_error:
                logger.debug(f"会话默认请求头读取失败: {header_error}")
        else:
            effective_headers.update(self.headers)
        extra_headers = kwargs.get('headers') or {}
        effective_headers.update(extra_headers)

        cookie_dump: Dict[str, str] = {}
        if self.session:
            try:
                cookie_dump = self.session.cookies.get_dict()
            except Exception as cookie_error:
                logger.debug(f"会话 cookie 读取失败: {cookie_error}")

        logger.debug(
            "📡 准备%s请求 %s %s",
            "通过代理发起" if via_proxy else "直接发起",
            method,
            url,
        )
        logger.debug("↳ 请求头: %s", json.dumps(effective_headers, ensure_ascii=False))

        if cookie_dump:
            logger.debug("↳ 会话Cookies: %s", json.dumps(cookie_dump, ensure_ascii=False))

        if kwargs.get('params'):
            logger.debug("↳ Query参数: %s", json.dumps(kwargs['params'], ensure_ascii=False))

        if kwargs.get('data') is not None:
            payload = kwargs['data']
            if isinstance(payload, (bytes, bytearray)):
                logger.debug("↳ 表单/正文: <二进制数据，长度=%s>", len(payload))
            else:
                try:
                    logger.debug("↳ 表单/正文: %s", json.dumps(payload, ensure_ascii=False))
                except (TypeError, ValueError):
                    length_hint = getattr(payload, "__len__", None)
                    logged_length = False
                    if callable(length_hint):
                        try:
                            logger.debug(
                                "↳ 表单/正文: <非JSON可序列化数据，长度=%s>",
                                length_hint(),
                            )
                            logged_length = True
                        except Exception:
                            pass
                    if not logged_length:
                        logger.debug(
                            "↳ 表单/正文: <非JSON可序列化数据，类型=%s>",
                            type(payload).__name__,
                        )
    
    def _clone_request_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """复制请求参数，避免在重试时修改原始引用"""
        cloned = dict(kwargs)
        if 'headers' in cloned and cloned['headers'] is not None:
            cloned['headers'] = dict(cloned['headers'])
        if 'data' in cloned and isinstance(cloned['data'], dict):
            cloned['data'] = dict(cloned['data'])
        if 'params' in cloned and isinstance(cloned['params'], dict):
            cloned['params'] = dict(cloned['params'])
        return cloned

    def _attempt_429_recovery(
        self,
        method: str,
        url: str,
        original_kwargs: Dict[str, Any],
    ) -> Optional[requests.Response]:
        """遇到429时尝试通过重置会话并重试"""
        penalty = register_rate_limit_event('high')
        if penalty:
            logger.warning("⚠️ Google Trends 返回429，重置会话并等待建议 %.1f 秒", penalty)

        try:
            self.reset_session()
        except Exception as reset_error:
            logger.error(f"❌ 重置Google Trends会话失败: {reset_error}")
            return None

        try:
            wait_for_next_request()
        except RuntimeError as limiter_error:
            logger.error("❌ 429恢复过程仍被限流阻止: %s", limiter_error)
            return None
        except Exception as limiter_error:
            logger.warning(f"⚠️ 429恢复等待时发生异常: {limiter_error}")

        retry_kwargs = self._clone_request_kwargs(original_kwargs)
        retry_kwargs.setdefault('timeout', self.timeout)

        return self.make_request(method, url, retry_on_429=False, **retry_kwargs)

    def make_request(
        self,
        method: str,
        url: str,
        retry_on_429: bool = True,
        **kwargs,
    ) -> ResponseType:
        """发送请求的统一接口"""
        # 检查会话是否已成功初始化
        if not self.initialized:
            raise Exception("Google Trends会话初始化失败，无法发送请求。请检查网络连接或稍后重试。")
        
        # 如果启用代理管理器，使用代理发送请求
        if self.use_proxy and self.proxy_manager:
            try:
                request_kwargs = self._clone_request_kwargs(kwargs)
                if 'headers' not in request_kwargs or request_kwargs['headers'] is None:
                    request_kwargs['headers'] = {}
                request_kwargs['headers'].update(self.headers)

                self._log_request_debug_snapshot(method, url, request_kwargs, via_proxy=True)

                if 'timeout' not in request_kwargs:
                    request_kwargs['timeout'] = self.timeout
                
                # 使用代理管理器发送请求
                response = self.proxy_manager.make_request(
                    url,
                    method,
                    backend=self.client_backend,
                    **request_kwargs,
                )
                if response:
                    self._merge_response_cookies(response)
                    self._persist_session_cookies()
                    if response.status_code == 429 and retry_on_429:
                        retry_response = self._attempt_429_recovery(method, url, request_kwargs)
                        if retry_response is not None:
                            return retry_response
                    return response
                else:
                    logger.warning("⚠️ 代理请求失败，尝试直接请求")
                    # 如果代理请求失败，回退到直接请求
                    
            except Exception as e:
                logger.warning(f"⚠️ 代理请求异常: {e}，尝试直接请求")
        
        # 直接请求（无代理或代理失败时的回退方案）
        self.get_session()

        # 设置默认超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout

        self._log_request_debug_snapshot(method, url, kwargs, via_proxy=False)
            
        # 发送请求
        response = self._session_request(method, url, **kwargs)
        self._persist_session_cookies()

        if response.status_code == 429 and retry_on_429:
            retry_response = self._attempt_429_recovery(method, url, kwargs)
            if retry_response is not None:
                return retry_response

        return response
    
    def get(self, url: str, **kwargs) -> ResponseType:
        """GET请求"""
        return self.make_request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> ResponseType:
        """POST请求"""
        return self.make_request('POST', url, **kwargs)
    
    def close(self) -> None:
        """关闭session"""
        try:
            self._close_session()
            self.initialized = False
            logger.debug("Google Trends session已关闭")
        except Exception as e:
            logger.error(f"关闭session失败: {e}")


# 全局session实例
_global_session = None
_session_lock = threading.Lock()

def get_global_session() -> GoogleTrendsSession:
    """获取全局session实例（线程安全）"""
    global _global_session
    
    # 双重检查锁定模式
    if _global_session is None:
        with _session_lock:
            if _global_session is None:
                _global_session = GoogleTrendsSession()
                logger.debug("创建Google Trends会话管理器实例")
    return _global_session

def reset_global_session() -> None:
    """重置全局session（线程安全）"""
    global _global_session
    
    with _session_lock:
        if _global_session:
            _global_session.close()
            _global_session = GoogleTrendsSession()
            logger.info("全局Session已重置")
