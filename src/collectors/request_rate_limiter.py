#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局请求频率控制器
解决Google Trends API的429错误问题
"""

import time
import threading
import logging
import math
from collections import deque
from typing import Optional, Deque, Dict

logger = logging.getLogger(__name__)


class RequestRateLimiter:
    """全局请求频率控制器，支持多时间窗口和节流恢复"""

    def __init__(
        self,
        min_interval: float = 3.0,
        max_requests_per_minute: int = 15,
        max_requests_per_hour: Optional[int] = 120,
        max_requests_per_day: Optional[int] = 1200,
        max_min_interval: float = 30.0,
        throttle_cooldown: float = 300.0,
    ) -> None:
        """初始化频率控制器"""
        self.base_min_interval = float(min_interval)
        self.min_interval = float(min_interval)
        self.max_min_interval = max(float(max_min_interval), self.base_min_interval)
        self.throttle_cooldown = max(float(throttle_cooldown), 60.0)

        self.max_requests_per_minute = max(int(max_requests_per_minute), 1)
        self.max_requests_per_hour = int(max_requests_per_hour) if max_requests_per_hour else None
        self.max_requests_per_day = int(max_requests_per_day) if max_requests_per_day else None

        self.last_request_time = 0.0
        self._throttle_until = 0.0
        self._last_throttle_time = 0.0

        self._minute_window: Deque[float] = deque()
        self._hour_window: Deque[float] = deque()
        self._day_window: Deque[float] = deque()
        self._warning_marks: Dict[str, float] = {'minute': 0.0, 'hour': 0.0, 'day': 0.0}

        self._lock = threading.RLock()

        logger.info(
            "🚦 初始化请求频率控制器: 最小间隔%.1f秒, 每分钟最多%d次请求" % (self.min_interval, self.max_requests_per_minute)
        )

    def wait_if_needed(self) -> None:
        """如果需要，等待到可以发送下一个请求"""
        with self._lock:
            while True:
                now = time.time()
                self._maybe_decay(now)

                waits = []
                waits.append(
                    self._compute_window_wait(
                        self._minute_window,
                        60.0,
                        self.max_requests_per_minute,
                        'minute',
                        now,
                        allow_sleep=True,
                    )
                )
                waits.append(
                    self._compute_window_wait(
                        self._hour_window,
                        3600.0,
                        self.max_requests_per_hour,
                        'hour',
                        now,
                        allow_sleep=False,
                    )
                )
                waits.append(
                    self._compute_window_wait(
                        self._day_window,
                        86400.0,
                        self.max_requests_per_day,
                        'day',
                        now,
                        allow_sleep=False,
                    )
                )

                if self._throttle_until > now:
                    waits.append(self._throttle_until - now)

                if self.last_request_time > 0:
                    min_gap = self.min_interval - (now - self.last_request_time)
                    if min_gap > 0:
                        waits.append(min_gap)

                waits = [w for w in waits if w and w > 0]
                if waits:
                    wait_time = max(waits)
                    logger.debug("⏳ 等待 %.1f 秒以满足限流策略", wait_time)
                    time.sleep(wait_time)
                    continue

                timestamp = time.time()

                self.last_request_time = timestamp
                for window in (self._minute_window, self._hour_window, self._day_window):
                    window.append(timestamp)
                break

    def reset(self) -> None:
        """重置频率控制器"""
        with self._lock:
            self.last_request_time = 0.0
            self._minute_window.clear()
            self._hour_window.clear()
            self._day_window.clear()
            self._throttle_until = 0.0
            self._last_throttle_time = 0.0
            self.min_interval = self.base_min_interval
            logger.info("🔄 请求频率控制器已重置")

    def register_throttle(self, severity: str = 'medium') -> float:
        """记录一次节流事件并返回建议等待时间"""
        severity_key = (severity or 'medium').lower()
        multiplier_map = {'low': 1.3, 'medium': 1.6, 'high': 2.2}
        cooldown_map = {'low': 12.0, 'medium': 25.0, 'high': 45.0}
        multiplier = multiplier_map.get(severity_key, multiplier_map['medium'])
        cooldown = cooldown_map.get(severity_key, cooldown_map['medium'])

        with self._lock:
            now = time.time()
            self.min_interval = min(
                self.max_min_interval,
                max(self.base_min_interval, self.min_interval * multiplier),
            )
            self._last_throttle_time = now

            penalty = min(max(self.min_interval * multiplier, cooldown), self.max_min_interval * 2)
            self._throttle_until = max(self._throttle_until, now + penalty)

            logger.warning(
                "⚠️ 收到%s级节流信号，最小间隔调整为 %.1f 秒，额外冷却 %.1f 秒",
                severity_key,
                self.min_interval,
                penalty,
            )
            return penalty

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            now = time.time()
            stats = {
                'requests_last_minute': len(self._minute_window),
                'max_requests_per_minute': self.max_requests_per_minute,
                'requests_last_hour': len(self._hour_window),
                'max_requests_per_hour': self.max_requests_per_hour,
                'requests_last_day': len(self._day_window),
                'max_requests_per_day': self.max_requests_per_day,
                'min_interval': self.min_interval,
                'base_min_interval': self.base_min_interval,
                'throttle_cooldown_remaining': max(0.0, self._throttle_until - now),
                'time_since_last_request': now - self.last_request_time if self.last_request_time else None,
            }
            return stats

    def _compute_window_wait(
        self,
        window: Deque[float],
        span_seconds: float,
        limit: Optional[int],
        label: str,
        now: float,
        allow_sleep: bool,
    ) -> float:
        while window and window[0] <= now - span_seconds:
            window.popleft()

        if not limit:
            return 0.0

        usage = len(window)
        self._emit_usage_warning(label, usage, limit, now)

        if usage < limit:
            return 0.0

        if not window:
            return 0.0

        next_reset = window[0] + span_seconds
        remaining = max(0.0, next_reset - now)

        if allow_sleep:
            return remaining

        friendly = {'hour': '每小时', 'day': '每日'}.get(label, label)
        raise RuntimeError(
            f"已达到{friendly}请求上限({limit})，请等待 {math.ceil(remaining / 60)} 分钟后再试"
        )

    def _emit_usage_warning(self, label: str, usage: int, limit: int, now: float) -> None:
        if limit <= 0:
            return

        ratio = usage / limit
        if ratio < 0.8:
            return

        last_mark = self._warning_marks.get(label, 0.0)
        if now - last_mark < 60:
            return

        friendly = {'minute': '每分钟', 'hour': '每小时', 'day': '每日'}.get(label, label)
        logger.warning("⚠️ %s请求已使用 %.0f%% (%d/%d)", friendly, ratio * 100, usage, limit)
        self._warning_marks[label] = now

    def _maybe_decay(self, now: float) -> None:
        if self.min_interval <= self.base_min_interval:
            return

        if now - self._last_throttle_time < self.throttle_cooldown:
            return

        new_interval = max(self.base_min_interval, self.min_interval * 0.7)
        if abs(new_interval - self.base_min_interval) < 0.5:
            new_interval = self.base_min_interval

        if new_interval != self.min_interval:
            logger.info("✅ 节流冷却结束，最小间隔回落至 %.1f 秒", new_interval)
        self.min_interval = new_interval

        if self.min_interval == self.base_min_interval:
            self._throttle_until = max(self._throttle_until, now + self.base_min_interval)


_global_rate_limiter: Optional[RequestRateLimiter] = None
_limiter_lock = threading.Lock()


def get_global_rate_limiter() -> RequestRateLimiter:
    """获取全局请求频率控制器单例"""
    global _global_rate_limiter

    if _global_rate_limiter is None:
        with _limiter_lock:
            if _global_rate_limiter is None:
                _global_rate_limiter = RequestRateLimiter(
                    min_interval=5.0,
                    max_requests_per_minute=8,
                    max_requests_per_hour=60,
                    max_requests_per_day=400,
                    max_min_interval=45.0,
                    throttle_cooldown=420.0,
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


def register_rate_limit_event(severity: str = 'medium') -> float:
    """记录节流事件并返回建议等待时长"""
    limiter = get_global_rate_limiter()
    return limiter.register_throttle(severity)
