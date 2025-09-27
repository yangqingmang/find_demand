"""Rate limiter configuration constants used across collectors."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitSettings:
    min_interval: float = 3.0
    max_requests_per_minute: int = 15
    max_requests_per_hour: int = 180
    max_requests_per_day: int = 1500
    max_min_interval: float = 30.0
    throttle_cooldown: float = 300.0


DEFAULT_RATE_LIMIT_SETTINGS = RateLimitSettings()

