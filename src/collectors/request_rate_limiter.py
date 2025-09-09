#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局请求频率控制器
解决Google Trends API的429错误问题
"""

import time
import threading
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RequestRateLimiter:
    """全局请求频率控制器"""
    
    def __init__(self, min_interval: float = 3.0, max_requests_per_minute: int = 15):
        """
        初始化频率控制器
        
        Args:
            min_interval: 最小请求间隔（秒）
            max_requests_per_minute: 每分钟最大请求数
        """
        self.min_interval = min_interval
        self.max_requests_per_minute = max_requests_per_minute
        self.last_request_time = 0.0
        self.request_times = []
        self._lock = threading.RLock()  # 使用可重入锁
        
        logger.info(f"🚦 初始化请求频率控制器: 最小间隔{min_interval}秒, 每分钟最多{max_requests_per_minute}次请求")
    
    def wait_if_needed(self) -> None:
        """如果需要，等待到可以发送下一个请求"""
        with self._lock:
            current_time = time.time()
            
            # 清理超过1分钟的请求记录
            cutoff_time = current_time - 60
            self.request_times = [t for t in self.request_times if t > cutoff_time]
            
            # 检查每分钟请求数限制
            if len(self.request_times) >= self.max_requests_per_minute:
                oldest_request = min(self.request_times)
                wait_time = 60 - (current_time - oldest_request)
                if wait_time > 0:
                    logger.warning(f"⏳ 达到每分钟请求限制，等待 {wait_time:.1f} 秒")
                    time.sleep(wait_time)
                    current_time = time.time()
            
            # 检查最小间隔限制
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                logger.debug(f"⏱️ 等待最小间隔: {wait_time:.1f} 秒")
                time.sleep(wait_time)
                current_time = time.time()
            
            # 记录请求时间
            self.last_request_time = current_time
            self.request_times.append(current_time)
            
            logger.debug(f"📊 当前分钟内请求数: {len(self.request_times)}/{self.max_requests_per_minute}")
    
    def reset(self) -> None:
        """重置频率控制器"""
        with self._lock:
            self.last_request_time = 0.0
            self.request_times.clear()
            logger.info("🔄 请求频率控制器已重置")
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - 60
            recent_requests = [t for t in self.request_times if t > cutoff_time]
            
            return {
                'requests_last_minute': len(recent_requests),
                'max_requests_per_minute': self.max_requests_per_minute,
                'min_interval': self.min_interval,
                'time_since_last_request': current_time - self.last_request_time if self.last_request_time > 0 else None
            }

# 全局单例实例
_global_rate_limiter: Optional[RequestRateLimiter] = None
_limiter_lock = threading.Lock()

def get_global_rate_limiter() -> RequestRateLimiter:
    """获取全局请求频率控制器单例"""
    global _global_rate_limiter
    
    if _global_rate_limiter is None:
        with _limiter_lock:
            if _global_rate_limiter is None:
                _global_rate_limiter = RequestRateLimiter(
                    min_interval=5.0,  # 最小5秒间隔，更保守
                    max_requests_per_minute=8   # 每分钟最多8次请求，非常保守
                )
                logger.info("🆕 创建全局请求频率控制器")
    
    return _global_rate_limiter

def reset_global_rate_limiter() -> None:
    """重置全局请求频率控制器"""
    global _global_rate_limiter
    
    with _limiter_lock:
        if _global_rate_limiter is not None:
            _global_rate_limiter.reset()
            logger.info("♻️ 全局请求频率控制器已重置")

def wait_for_next_request() -> None:
    """等待到可以发送下一个请求的时间"""
    limiter = get_global_rate_limiter()
    limiter.wait_if_needed()

def get_rate_limiter_stats() -> dict:
    """获取频率控制器统计信息"""
    limiter = get_global_rate_limiter()
    return limiter.get_stats()