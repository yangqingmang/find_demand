#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一HTTP请求工具类

功能:
- 封装代理管理器功能
- 提供统一的HTTP请求接口
- 支持重试机制和错误处理
- 自动User-Agent轮换

作者: AI Assistant
创建时间: 2025-01-27
"""

import logging
import os
import time
from typing import Any, Dict, Optional, TYPE_CHECKING, Union
from urllib.parse import urlparse

import requests

try:
    import httpx  # type: ignore
except ImportError:  # pragma: no cover - graceful fallback when httpx missing
    httpx = None

if TYPE_CHECKING:  # pragma: no cover
    from httpx import Response as HTTPXResponse

# 导入代理管理器
try:
    from ..demand_mining.core.proxy_manager import get_proxy_manager
except ImportError:
    get_proxy_manager = None
    logging.warning("代理管理器不可用，将使用直接请求")

try:
    from config.proxy_config_loader import get_proxy_config
except ImportError:
    get_proxy_config = None

logger = logging.getLogger(__name__)

ResponseType = Union[requests.Response, "HTTPXResponse"]


class HttpClient:
    """统一HTTP请求客户端"""
    
    def __init__(self, 
                 use_proxy: bool = True,
                 timeout: Union[int, float, tuple] = 30,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 default_headers: Optional[Dict[str, str]] = None,
                 backend: Optional[str] = None):
        """
        初始化HTTP客户端
        
        Args:
            use_proxy: 是否使用代理
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
            default_headers: 默认请求头
        """
        self.use_proxy = use_proxy
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.default_headers = default_headers or {}
        self.proxy_manager = None
        self.backend = self._resolve_backend(backend)
        self._httpx_client: Optional["httpx.Client"] = None
        logger.debug("HTTP客户端初始化，后端=%s，代理=%s", self.backend, "on" if use_proxy else "off")
        if self.backend == 'httpx':
            self._httpx_client = self._create_httpx_client()
        
        if self.use_proxy and get_proxy_config:
            try:
                proxy_config = get_proxy_config()
                if not proxy_config.enabled:
                    logger.info("代理配置已禁用代理功能，HTTP客户端将改用直连模式")
                    self.use_proxy = False
            except Exception as e:
                logger.warning(f"读取代理配置失败: {e}，HTTP客户端将改用直连模式")
                self.use_proxy = False

        # 初始化代理管理器
        if self.use_proxy and get_proxy_manager:
            try:
                self.proxy_manager = get_proxy_manager()
                logger.info("✅ HTTP客户端：代理管理器已启用")
            except Exception as e:
                logger.warning(f"⚠️ HTTP客户端：代理管理器初始化失败: {e}，将使用直接请求")
                self.use_proxy = False

    def _resolve_backend(self, backend: Optional[str]) -> str:
        """解析HTTP客户端后端实现"""
        candidates = [
            backend,
            os.getenv('FIND_DEMAND_HTTP_BACKEND'),
            'httpx' if httpx is not None else 'requests',
        ]
        for candidate in candidates:
            if not candidate:
                continue
            normalized = candidate.strip().lower()
            if normalized in {'requests', 'httpx'}:
                if normalized == 'httpx' and httpx is None:
                    logger.warning("httpx 未安装，HTTP客户端自动回退至 requests")
                    return 'requests'
                return normalized
            else:
                logger.warning(f"未知的HTTP客户端后端: {candidate}，忽略")
        return 'requests'

    def _build_httpx_timeout(self, timeout: Union[int, float, tuple]) -> "httpx.Timeout":
        """根据配置构造 httpx Timeout 对象"""
        assert httpx is not None  # 静态类型提示
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

    def _create_httpx_client(self) -> Optional["httpx.Client"]:
        """创建 httpx.Client 实例"""
        if httpx is None:
            return None
        try:
            timeout = self._build_httpx_timeout(self.timeout)
            client = httpx.Client(
                http2=True,
                timeout=timeout,
                headers=self.default_headers.copy(),
                trust_env=False,
                follow_redirects=True,
            )
            logger.debug("httpx 客户端已启用 (HTTP/2 支持)")
            return client
        except Exception as exc:
            logger.warning(f"httpx 客户端初始化失败: {exc}，回退至 requests")
            self.backend = 'requests'
            return None

    def _prepare_httpx_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """将 requests 风格参数转换为 httpx 接口"""
        assert httpx is not None
        converted = dict(kwargs)
        timeout = converted.pop('timeout', self.timeout)
        converted['timeout'] = self._build_httpx_timeout(timeout)

        if 'allow_redirects' in converted:
            converted['follow_redirects'] = converted.pop('allow_redirects')

        # httpx使用proxies参数同名，保持兼容即可
        return converted

    def _direct_request_httpx(self, method: str, url: str, **kwargs) -> Optional[ResponseType]:
        """通过 httpx 发送请求"""
        if httpx is None:
            logger.error("未安装 httpx，无法使用 httpx 后端")
            return None

        client = self._httpx_client or self._create_httpx_client()
        if client is None:
            return None
        self._httpx_client = client

        httpx_kwargs = self._prepare_httpx_kwargs(kwargs)
        try:
            response = client.request(method, url, **httpx_kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            logger.error(f"httpx 请求返回错误状态码: {exc.response.status_code} - {exc}")
        except httpx.RequestError as exc:
            logger.error(f"httpx 请求异常: {exc}")
        return None
    
    def request(self, 
                method: str, 
                url: str, 
                headers: Optional[Dict[str, str]] = None,
                params: Optional[Dict[str, Any]] = None,
                data: Optional[Any] = None,
                json: Optional[Dict[str, Any]] = None,
                **kwargs) -> Optional[ResponseType]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE等)
            url: 请求URL
            headers: 请求头
            params: URL参数
            data: 请求体数据
            json: JSON数据
            **kwargs: 其他requests参数
            
        Returns:
            requests.Response对象，失败时返回None
        """
        # 合并请求头
        final_headers = self.default_headers.copy()
        if headers:
            final_headers.update(headers)
        
        # 准备请求参数
        request_kwargs = {
            'headers': final_headers,
            'timeout': kwargs.get('timeout', self.timeout)
        }
        
        if params:
            request_kwargs['params'] = params
        if data:
            request_kwargs['data'] = data
        if json:
            request_kwargs['json'] = json
        
        # 添加其他kwargs
        for key, value in kwargs.items():
            if key not in request_kwargs:
                request_kwargs[key] = value
        
        # 如果启用代理管理器，使用代理发送请求
        if self.use_proxy and self.proxy_manager:
            try:
                response = self.proxy_manager.make_request(
                    url,
                    method,
                    backend=self.backend,
                    **request_kwargs,
                )
                if response:
                    return response
                else:
                    logger.warning("⚠️ 代理请求失败，尝试直接请求")
            except Exception as e:
                logger.warning(f"⚠️ 代理请求异常: {e}，尝试直接请求")
        
        # 直接请求（无代理或代理失败时的回退方案）
        if self.backend == 'httpx':
            return self._direct_request_httpx(method, url, **request_kwargs)
        return self._direct_request_requests(method, url, **request_kwargs)
    
    def _direct_request_requests(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        直接发送HTTP请求（不使用代理）
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: requests参数
            
        Returns:
            Response对象，失败时返回None
        """
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.request(method, url, **kwargs)
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}，{wait_time}秒后重试")
                    time.sleep(wait_time)
                else:
                    logger.error(f"请求最终失败: {e}")
                    return None
        
        return None
    
    def get(self, url: str, **kwargs) -> Optional[ResponseType]:
        """发送GET请求"""
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> Optional[ResponseType]:
        """发送POST请求"""
        return self.request('POST', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> Optional[ResponseType]:
        """发送PUT请求"""
        return self.request('PUT', url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> Optional[ResponseType]:
        """发送DELETE请求"""
        return self.request('DELETE', url, **kwargs)
    
    def patch(self, url: str, **kwargs) -> Optional[ResponseType]:
        """发送PATCH请求"""
        return self.request('PATCH', url, **kwargs)
    
    def head(self, url: str, **kwargs) -> Optional[ResponseType]:
        """发送HEAD请求"""
        return self.request('HEAD', url, **kwargs)
    
    def options(self, url: str, **kwargs) -> Optional[ResponseType]:
        """发送OPTIONS请求"""
        return self.request('OPTIONS', url, **kwargs)
    
    def download_file(self, url: str, file_path: str, **kwargs) -> bool:
        """
        下载文件
        
        Args:
            url: 文件URL
            file_path: 保存路径
            **kwargs: 其他请求参数
            
        Returns:
            下载成功返回True，失败返回False
        """
        try:
            response = self.get(url, stream=True, **kwargs)
            if response:
                with open(file_path, 'wb') as f:
                    if hasattr(response, "iter_content"):
                        iterator = response.iter_content(chunk_size=8192)  # requests
                    else:
                        iterator = response.iter_bytes(chunk_size=8192)  # httpx
                    for chunk in iterator:
                        if chunk:
                            f.write(chunk)
                logger.info(f"文件下载成功: {file_path}")
                return True
            else:
                logger.error(f"文件下载失败: {url}")
                return False
        except Exception as e:
            logger.error(f"文件下载异常: {e}")
            return False
    
    def get_json(self, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        获取JSON数据
        
        Args:
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            JSON数据字典，失败时返回None
        """
        response = self.get(url, **kwargs)
        if response:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"JSON解析失败: {e}")
                return None
        return None
    
    def post_json(self, url: str, data: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        发送JSON数据并获取JSON响应
        
        Args:
            url: 请求URL
            data: 要发送的JSON数据
            **kwargs: 其他请求参数
            
        Returns:
            JSON响应数据，失败时返回None
        """
        response = self.post(url, json=data, **kwargs)
        if response:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"JSON解析失败: {e}")
                return None
        return None
    
    def set_proxy_enabled(self, enabled: bool):
        """启用或停用代理"""
        if enabled and get_proxy_config:
            try:
                proxy_config = get_proxy_config()
                if not proxy_config.enabled:
                    logger.info("代理配置已禁用代理功能，无法开启代理")
                    self.use_proxy = False
                    return
            except Exception as e:
                logger.warning(f"读取代理配置失败: {e}，无法开启代理")
                self.use_proxy = False
                return

        self.use_proxy = enabled
        if enabled and not self.proxy_manager and get_proxy_manager:
            try:
                self.proxy_manager = get_proxy_manager()
                logger.info("✅ 代理管理器已重新启用")
            except Exception as e:
                logger.warning(f"⚠️ 代理管理器重新初始化失败: {e}")
                self.use_proxy = False
        elif not enabled:
            logger.info("已关闭代理模式，后续请求将使用直连")

    def get_proxy_stats(self) -> Optional[Dict[str, Any]]:
        """获取代理统计信息"""
        if self.proxy_manager:
            return self.proxy_manager.get_proxy_stats()
        return None

    def close(self) -> None:
        """关闭底层客户端资源"""
        if self._httpx_client:
            try:
                self._httpx_client.close()
            except Exception:
                pass
            finally:
                self._httpx_client = None


# 全局HTTP客户端实例
_global_http_client = None


def get_http_client(use_proxy: bool = True, **kwargs) -> HttpClient:
    """
    获取全局HTTP客户端实例
    
    Args:
        use_proxy: 是否使用代理
        **kwargs: HttpClient初始化参数
        
    Returns:
        HttpClient实例
    """
    global _global_http_client
    if _global_http_client is None:
        _global_http_client = HttpClient(use_proxy=use_proxy, **kwargs)
    return _global_http_client


def reset_http_client():
    """重置全局HTTP客户端"""
    global _global_http_client
    if _global_http_client:
        try:
            _global_http_client.close()
        except Exception:
            pass
    _global_http_client = None


# 便捷函数
def get(url: str, **kwargs) -> Optional[ResponseType]:
    """便捷GET请求函数"""
    return get_http_client().get(url, **kwargs)


def post(url: str, **kwargs) -> Optional[ResponseType]:
    """便捷POST请求函数"""
    return get_http_client().post(url, **kwargs)


def get_json(url: str, **kwargs) -> Optional[Dict[str, Any]]:
    """便捷获取JSON函数"""
    return get_http_client().get_json(url, **kwargs)


def post_json(url: str, data: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
    """便捷发送JSON函数"""
    return get_http_client().post_json(url, data, **kwargs)


if __name__ == "__main__":
    # 示例用法
    import json
    
    # 创建HTTP客户端
    client = HttpClient(use_proxy=True)
    
    # 测试GET请求
    response = client.get('http://httpbin.org/ip')
    if response:
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    
    # 测试JSON请求
    json_data = client.get_json('http://httpbin.org/json')
    if json_data:
        print(f"JSON数据: {json.dumps(json_data, indent=2)}")
    
    # 获取代理统计
    stats = client.get_proxy_stats()
    if stats:
        print(f"代理统计: {json.dumps(stats, indent=2)}")
