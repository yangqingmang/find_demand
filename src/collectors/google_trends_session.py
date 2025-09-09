#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Google Trends Session 管理模块"""

import requests
import json
import os
import logging
from typing import Dict, Optional

# 导入代理管理器
try:
    from ..demand_mining.core.proxy_manager import get_proxy_manager
except ImportError:
    # 如果导入失败，使用None
    get_proxy_manager = None
    logging.warning("代理管理器不可用，将使用直接请求")

logger = logging.getLogger(__name__)

class GoogleTrendsSession:
    """Google Trends Session 管理类"""
    
    def __init__(self, timeout: tuple = (20, 30), use_proxy: bool = True):
        self.timeout = timeout
        self.session = None
        self.headers = self._load_headers()
        self.initialized = False
        self.use_proxy = use_proxy
        self.proxy_manager = None
        
        # 初始化代理管理器
        if self.use_proxy and get_proxy_manager:
            try:
                self.proxy_manager = get_proxy_manager()
                logger.info("✅ 代理管理器已启用")
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
    
    def get_session(self) -> requests.Session:
        """获取已初始化的session"""
        if self.session is None:
            self._create_session()
        
        if not self.initialized:
            self._init_session()
            
        return self.session
    
    def _create_session(self) -> None:
        """创建新的session"""
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        logger.debug("创建新的Google Trends session")
    
    def _init_session(self) -> None:
        """初始化会话，获取必要的cookies"""
        try:
            logger.info("🔧 正在初始化Google Trends会话...")
            
            # 添加延迟避免429错误
            import time
            time.sleep(2)
            
            # 先访问主页获取cookies
            main_page_url = 'https://trends.google.com/'
            response = self.session.get(main_page_url, timeout=self.timeout)
            
            if response.status_code == 200:
                self.initialized = True
                logger.info("✅ Google Trends会话初始化成功")
            elif response.status_code == 429:
                logger.error("❌ 遇到429错误，会话初始化失败")
                self.initialized = False
            else:
                logger.warning(f"⚠️ 主页访问失败，状态码: {response.status_code}")
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

def get_global_session() -> GoogleTrendsSession:
    """获取全局session实例"""
    global _global_session
    if _global_session is None:
        _global_session = GoogleTrendsSession()
    return _global_session

def reset_global_session() -> None:
    """重置全局session"""
    global _global_session
    if _global_session:
        _global_session.reset_session()
    else:
        _global_session = GoogleTrendsSession()