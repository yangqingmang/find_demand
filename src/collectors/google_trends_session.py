#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Google Trends Session 管理模块"""

import json
import logging
import os
import threading
import time
from http.cookiejar import MozillaCookieJar
from typing import Dict, Optional

import requests

# 导入代理管理器
try:
    from ..demand_mining.core.proxy_manager import get_proxy_manager
except ImportError:
    # 如果导入失败，使用None
    get_proxy_manager = None
    logging.warning("代理管理器不可用，将使用直接请求")

logger = logging.getLogger(__name__)

from .request_rate_limiter import wait_for_next_request, register_rate_limit_event

class GoogleTrendsSession:
    """Google Trends Session 管理类"""
    
    def __init__(self, timeout: tuple = (20, 30), use_proxy: bool = True):
        self.timeout = timeout
        self.session = None
        self.headers = self._load_headers()
        self.initialized = False
        self.use_proxy = use_proxy
        self.proxy_manager = None
        self._cookie_lock = threading.Lock()

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
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://trends.google.com/',
                'Origin': 'https://trends.google.com',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Connection': 'keep-alive',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"'
            }

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
    
    def get_session(self) -> requests.Session:
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
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._apply_cookies_to_session()
        logger.debug("创建新的Google Trends session")

    def _apply_cookies_to_session(self) -> None:
        """将持久化cookie写入session"""
        if not self.session:
            return
        with self._cookie_lock:
            for cookie in list(self.cookie_jar):
                try:
                    self.session.cookies.set_cookie(cookie)
                except Exception as cookie_error:
                    logger.debug(f"写入cookie失败，已忽略: {cookie_error}")

    def _persist_session_cookies(self) -> None:
        """将当前session cookie持久化到磁盘"""
        if not self.session:
            return

        with self._cookie_lock:
            jar = MozillaCookieJar(self.cookie_path)
            for cookie in self.session.cookies:
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
    
    def _init_session(self) -> None:
        """初始化会话，获取必要的cookies"""
        try:
            logger.info("🔧 正在初始化Google Trends会话...")

            bootstrap_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Sec-Ch-Ua': '"Not?A_Brand";v="8", "Chromium";v="141", "Google Chrome";v="141"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"'
            }

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

            response = self.session.get(main_page_url, headers=bootstrap_headers, timeout=self.timeout)
            self._persist_session_cookies()

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

                response = self.session.get(main_page_url, headers=bootstrap_headers, timeout=self.timeout)
                self._persist_session_cookies()

            if response.status_code != 200:
                penalty = register_rate_limit_event('high')
                if penalty:
                    logger.error("❌ 主页访问失败，状态码: %s，建议等待 %.1f 秒", response.status_code, penalty)
                else:
                    logger.error(f"❌ 主页访问失败，状态码: {response.status_code}")
                self.initialized = False
                return

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

            trends_response = self.session.get(trends_page_url, headers=bootstrap_headers, timeout=self.timeout)
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

                trends_response = self.session.get(trends_page_url, headers=bootstrap_headers, timeout=self.timeout)
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
            if self.session:
                self.session.close()
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
        if self.session:
            self.session.headers.update(new_headers)
    
    def make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """发送请求的统一接口"""
        # 检查会话是否已成功初始化
        if not self.initialized:
            raise Exception("Google Trends会话初始化失败，无法发送请求。请检查网络连接或稍后重试。")
        
        # 如果启用代理管理器，使用代理发送请求
        if self.use_proxy and self.proxy_manager:
            try:
                # 合并headers
                if 'headers' not in kwargs:
                    kwargs['headers'] = {}
                kwargs['headers'].update(self.headers)
                
                # 设置默认超时
                if 'timeout' not in kwargs:
                    kwargs['timeout'] = self.timeout
                
                # 使用代理管理器发送请求
                response = self.proxy_manager.make_request(url, method, **kwargs)
                if response:
                    if self.session and response.cookies:
                        try:
                            self.session.cookies.update(response.cookies)
                        except Exception as cookie_error:
                            logger.debug(f"代理响应cookie合并失败: {cookie_error}")
                    self._persist_session_cookies()
                    return response
                else:
                    logger.warning("⚠️ 代理请求失败，尝试直接请求")
                    # 如果代理请求失败，回退到直接请求
                    
            except Exception as e:
                logger.warning(f"⚠️ 代理请求异常: {e}，尝试直接请求")
        
        # 直接请求（无代理或代理失败时的回退方案）
        session = self.get_session()
        
        # 设置默认超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
            
        # 发送请求
        response = session.request(method, url, **kwargs)
        self._persist_session_cookies()
        return response
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """GET请求"""
        return self.make_request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """POST请求"""
        return self.make_request('POST', url, **kwargs)
    
    def close(self) -> None:
        """关闭session"""
        try:
            if self.session:
                self.session.close()
                self.session = None
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
