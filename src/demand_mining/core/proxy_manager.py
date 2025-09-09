#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理管理器 - 反爬虫机制实现

功能:
- 代理池管理
- 请求频率控制
- User-Agent轮换
- 请求重试机制

作者: AI Assistant
创建时间: 2025-01-27
"""

import time
import random
import requests
import threading
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
from fake_useragent import UserAgent
import logging
from urllib.parse import urlparse

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class ProxyInfo:
    """代理信息数据类"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = 'http'
    success_count: int = 0
    failure_count: int = 0
    last_used: float = 0
    is_active: bool = True
    response_time: float = 0
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0
    
    @property
    def proxy_url(self) -> str:
        """生成代理URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, str]:
        """转换为requests可用的代理字典"""
        proxy_url = self.proxy_url
        return {
            'http': proxy_url,
            'https': proxy_url
        }


class RateLimiter:
    """请求频率控制器"""
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        初始化频率控制器
        
        Args:
            max_requests: 时间窗口内最大请求数
            time_window: 时间窗口大小(秒)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(deque)  # 域名 -> 请求时间队列
        self.lock = threading.Lock()
    
    def can_request(self, domain: str) -> bool:
        """检查是否可以发起请求"""
        with self.lock:
            now = time.time()
            request_times = self.requests[domain]
            
            # 清理过期的请求记录
            while request_times and now - request_times[0] > self.time_window:
                request_times.popleft()
            
            return len(request_times) < self.max_requests
    
    def record_request(self, domain: str):
        """记录请求"""
        with self.lock:
            self.requests[domain].append(time.time())
    
    def wait_time(self, domain: str) -> float:
        """计算需要等待的时间"""
        with self.lock:
            now = time.time()
            request_times = self.requests[domain]
            
            if len(request_times) < self.max_requests:
                return 0
            
            # 计算最早请求过期的时间
            earliest_request = request_times[0]
            wait_time = self.time_window - (now - earliest_request)
            return max(0, wait_time)


class ProxyManager:
    """代理管理器"""
    
    def __init__(self, 
                 proxies: Optional[List[Dict]] = None,
                 max_requests_per_minute: int = 10,
                 request_delay: Tuple[float, float] = (1.0, 3.0),
                 max_retries: int = 3,
                 timeout: int = 10):
        """
        初始化代理管理器
        
        Args:
            proxies: 代理列表，格式: [{'host': 'ip', 'port': port, 'username': '', 'password': ''}]
            max_requests_per_minute: 每分钟最大请求数
            request_delay: 请求延迟范围(秒)
            max_retries: 最大重试次数
            timeout: 请求超时时间(秒)
        """
        self.proxies: List[ProxyInfo] = []
        self.rate_limiter = RateLimiter(max_requests_per_minute, 60)
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.user_agent = UserAgent()
        self.lock = threading.Lock()
        
        # 初始化代理池
        if proxies:
            self._load_proxies(proxies)
        
        logger.info(f"代理管理器初始化完成，加载了 {len(self.proxies)} 个代理")
    
    def _load_proxies(self, proxies: List[Dict]):
        """加载代理列表"""
        for proxy_data in proxies:
            proxy = ProxyInfo(
                host=proxy_data['host'],
                port=proxy_data['port'],
                username=proxy_data.get('username'),
                password=proxy_data.get('password'),
                protocol=proxy_data.get('protocol', 'http')
            )
            self.proxies.append(proxy)
    
    def add_proxy(self, host: str, port: int, 
                  username: Optional[str] = None, 
                  password: Optional[str] = None,
                  protocol: str = 'http'):
        """添加代理"""
        proxy = ProxyInfo(host, port, username, password, protocol)
        with self.lock:
            self.proxies.append(proxy)
        logger.info(f"添加代理: {proxy.proxy_url}")
    
    def remove_proxy(self, host: str, port: int):
        """移除代理"""
        with self.lock:
            self.proxies = [p for p in self.proxies if not (p.host == host and p.port == port)]
        logger.info(f"移除代理: {host}:{port}")
    
    def get_best_proxy(self) -> Optional[ProxyInfo]:
        """获取最佳代理"""
        with self.lock:
            active_proxies = [p for p in self.proxies if p.is_active]
            
            if not active_proxies:
                return None
            
            # 按成功率和响应时间排序
            active_proxies.sort(key=lambda p: (-p.success_rate, p.response_time, p.last_used))
            return active_proxies[0]
    
    def get_random_proxy(self) -> Optional[ProxyInfo]:
        """获取随机代理"""
        with self.lock:
            active_proxies = [p for p in self.proxies if p.is_active]
            return random.choice(active_proxies) if active_proxies else None
    
    def get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        try:
            return self.user_agent.random
        except Exception as e:
            logger.warning(f"获取随机User-Agent失败: {e}，使用默认值")
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    def test_proxy(self, proxy: ProxyInfo, test_url: str = "http://httpbin.org/ip") -> bool:
        """测试代理可用性"""
        try:
            start_time = time.time()
            response = requests.get(
                test_url,
                proxies=proxy.to_dict(),
                timeout=self.timeout,
                headers={'User-Agent': self.get_random_user_agent()}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                proxy.success_count += 1
                proxy.response_time = response_time
                proxy.last_used = time.time()
                logger.debug(f"代理测试成功: {proxy.proxy_url}, 响应时间: {response_time:.2f}s")
                return True
            else:
                proxy.failure_count += 1
                logger.warning(f"代理测试失败: {proxy.proxy_url}, 状态码: {response.status_code}")
                return False
                
        except Exception as e:
            proxy.failure_count += 1
            logger.warning(f"代理测试异常: {proxy.proxy_url}, 错误: {e}")
            return False
    
    def test_all_proxies(self):
        """测试所有代理"""
        logger.info("开始测试所有代理...")
        for proxy in self.proxies:
            is_working = self.test_proxy(proxy)
            proxy.is_active = is_working
        
        active_count = sum(1 for p in self.proxies if p.is_active)
        logger.info(f"代理测试完成，活跃代理数: {active_count}/{len(self.proxies)}")
    
    def make_request(self, url: str, method: str = 'GET', 
                    use_proxy: bool = True, **kwargs) -> Optional[requests.Response]:
        """发起请求"""
        domain = urlparse(url).netloc
        
        # 检查频率限制
        if not self.rate_limiter.can_request(domain):
            wait_time = self.rate_limiter.wait_time(domain)
            logger.info(f"频率限制，等待 {wait_time:.2f} 秒")
            time.sleep(wait_time)
        
        # 随机延迟
        delay = random.uniform(*self.request_delay)
        time.sleep(delay)
        
        # 记录请求
        self.rate_limiter.record_request(domain)
        
        # 准备请求参数
        request_kwargs = {
            'timeout': self.timeout,
            'headers': kwargs.get('headers', {})
        }
        request_kwargs['headers']['User-Agent'] = self.get_random_user_agent()
        request_kwargs.update(kwargs)
        
        # 选择代理
        proxy = None
        if use_proxy and self.proxies:
            proxy = self.get_best_proxy() or self.get_random_proxy()
            if proxy:
                request_kwargs['proxies'] = proxy.to_dict()
        
        # 发起请求
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                if method.upper() == 'GET':
                    response = requests.get(url, **request_kwargs)
                elif method.upper() == 'POST':
                    response = requests.post(url, **request_kwargs)
                else:
                    response = requests.request(method, url, **request_kwargs)
                
                response_time = time.time() - start_time
                
                # 更新代理统计
                if proxy:
                    proxy.success_count += 1
                    proxy.response_time = response_time
                    proxy.last_used = time.time()
                
                logger.debug(f"请求成功: {url}, 状态码: {response.status_code}, 响应时间: {response_time:.2f}s")
                return response
                
            except Exception as e:
                if proxy:
                    proxy.failure_count += 1
                    # 如果失败率过高，暂时禁用代理
                    if proxy.success_rate < 0.5 and proxy.failure_count > 5:
                        proxy.is_active = False
                        logger.warning(f"代理失败率过高，暂时禁用: {proxy.proxy_url}")
                
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.max_retries + 1}): {url}, 错误: {e}")
                
                if attempt < self.max_retries:
                    # 重试时使用不同的代理
                    if use_proxy and self.proxies:
                        proxy = self.get_random_proxy()
                        if proxy:
                            request_kwargs['proxies'] = proxy.to_dict()
                    
                    # 重试延迟
                    retry_delay = random.uniform(2, 5) * (attempt + 1)
                    time.sleep(retry_delay)
        
        logger.error(f"请求最终失败: {url}")
        return None
    
    def get_proxy_stats(self) -> Dict:
        """获取代理统计信息"""
        with self.lock:
            total_proxies = len(self.proxies)
            active_proxies = sum(1 for p in self.proxies if p.is_active)
            
            if not self.proxies:
                return {
                    'total_proxies': 0,
                    'active_proxies': 0,
                    'success_rate': 0,
                    'avg_response_time': 0
                }
            
            total_success = sum(p.success_count for p in self.proxies)
            total_requests = sum(p.success_count + p.failure_count for p in self.proxies)
            success_rate = total_success / total_requests if total_requests > 0 else 0
            
            active_response_times = [p.response_time for p in self.proxies if p.is_active and p.response_time > 0]
            avg_response_time = sum(active_response_times) / len(active_response_times) if active_response_times else 0
            
            return {
                'total_proxies': total_proxies,
                'active_proxies': active_proxies,
                'success_rate': success_rate,
                'avg_response_time': avg_response_time
            }
    
    def cleanup_inactive_proxies(self, min_success_rate: float = 0.3):
        """清理不活跃的代理"""
        with self.lock:
            before_count = len(self.proxies)
            self.proxies = [
                p for p in self.proxies 
                if p.is_active and (p.success_rate >= min_success_rate or p.success_count + p.failure_count < 10)
            ]
            after_count = len(self.proxies)
            
            if before_count != after_count:
                logger.info(f"清理代理完成，移除 {before_count - after_count} 个低质量代理")


# 单例模式的代理管理器
class ProxyManagerSingleton:
    """代理管理器单例"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = ProxyManager(*args, **kwargs)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> ProxyManager:
        """获取单例实例"""
        if not cls._instance:
            cls._instance = ProxyManager()
        return cls._instance


# 便捷函数
def get_proxy_manager() -> ProxyManager:
    """获取代理管理器实例"""
    return ProxyManagerSingleton.get_instance()


if __name__ == "__main__":
    # 示例用法
    import json
    
    # 创建代理管理器
    proxy_manager = ProxyManager(
        max_requests_per_minute=5,
        request_delay=(1, 2)
    )
    
    # 添加一些示例代理（这些是示例，实际使用时需要有效的代理）
    # proxy_manager.add_proxy('127.0.0.1', 8080)
    
    # 测试请求
    response = proxy_manager.make_request('http://httpbin.org/ip', use_proxy=False)
    if response:
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    
    # 获取统计信息
    stats = proxy_manager.get_proxy_stats()
    print(f"代理统计: {json.dumps(stats, indent=2)}")