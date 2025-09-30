#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台关键词发现工具
整合Reddit、Hacker News、Product Hunt等平台的关键词发现
"""

import asyncio
import json
import random
import re
import time
import hashlib
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional
from urllib.parse import quote, urlparse

import aiohttp
import pandas as pd
from threading import Lock

from src.utils.telemetry import telemetry_manager


_EMBEDDING_MODEL_CACHE: Dict[str, Any] = {}
_EMBEDDING_MODEL_LOCK = Lock()


class _AsyncRateLimiter:
    """Simple per-host async rate limiter using monotonic clocks."""

    def __init__(self, rate_limits: Dict[str, float], default_interval: float) -> None:
        self._rate_limits = {str(host).lower(): float(interval) for host, interval in rate_limits.items()}
        self._default_interval = max(float(default_interval), 0.0)
        self._locks: Dict[str, asyncio.Lock] = {}
        self._last_hit: Dict[str, float] = {}

    def _get_interval(self, host: str) -> float:
        normalized = (host or '').lower()
        interval = self._rate_limits.get(normalized)
        if interval is None:
            interval = self._rate_limits.get('*', self._default_interval)
        return max(float(interval), 0.0)

    async def throttle(self, host: str) -> None:
        interval = self._get_interval(host)
        if interval <= 0:
            return

        key = (host or '*').lower()
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            now = time.monotonic()
            last_time = self._last_hit.get(key, 0.0)
            wait_time = interval - (now - last_time)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                now = time.monotonic()
            self._last_hit[key] = now


class _TTLCache:
    """Disk-backed TTL cache used by keyword discovery."""

    def __init__(
        self,
        cache_dir: Path,
        ttl_seconds: int,
        enabled: bool,
        cache_store: Dict[str, Dict[str, Any]],
        normalizer: Callable[[str], str],
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = max(int(ttl_seconds), 0)
        self.enabled = bool(enabled) and self.ttl_seconds != 0
        self._store = cache_store
        self._normalize = normalizer

    def _namespace_path(self, namespace: str) -> Path:
        path = self.cache_dir / namespace
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get(self, namespace: str, key: str):
        if not self.enabled:
            return None

        now = time.time()
        store = self._store.setdefault(namespace, {})
        entry = store.get(key)
        if entry:
            timestamp = entry.get('timestamp', 0.0)
            if self.ttl_seconds <= 0 or now - timestamp <= self.ttl_seconds:
                return entry.get('payload')
            store.pop(key, None)

        path = self._namespace_path(namespace) / f"{self._normalize(key)}.json"
        if not path.exists():
            return None

        try:
            with path.open('r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception:
            return None

        timestamp = data.get('timestamp', 0.0)
        if self.ttl_seconds > 0 and now - timestamp > self.ttl_seconds:
            try:
                path.unlink()
            except Exception:
                pass
            return None

        payload = data.get('payload')
        store[key] = {'payload': payload, 'timestamp': timestamp or now}
        return payload

    def set(self, namespace: str, key: str, payload: Any) -> None:
        if not self.enabled:
            return

        timestamp = time.time()
        store = self._store.setdefault(namespace, {})
        store[key] = {'payload': payload, 'timestamp': timestamp}

        path = self._namespace_path(namespace) / f"{self._normalize(key)}.json"
        try:
            with path.open('w', encoding='utf-8') as fh:
                json.dump({'timestamp': timestamp, 'payload': payload}, fh, ensure_ascii=False)
        except Exception as exc:
            print(f"⚠️ 缓存写入失败 ({namespace}:{key}): {exc}")

# 添加config目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config'))
from config.config_manager import get_config
from src.pipeline.cleaning.cleaner import standardize_term, is_valid_term, CleaningConfig

class MultiPlatformKeywordDiscovery:
    """多平台关键词发现工具"""
    
    def __init__(self):
        # 加载配置
        self.config = get_config()

        # 基础请求与并发控制
        base_timeout = getattr(self.config, 'DISCOVERY_REQUEST_TIMEOUT', 12) or 12
        base_max_retries = getattr(self.config, 'DISCOVERY_MAX_RETRIES', 3) or 3
        base_backoff = getattr(self.config, 'DISCOVERY_RETRY_BACKOFF', (1, 3))
        base_max_concurrency = getattr(self.config, 'DISCOVERY_MAX_CONCURRENCY', 5) or 5
        base_default_rate_interval = getattr(self.config, 'DISCOVERY_DEFAULT_RATE_INTERVAL', 0.35) or 0.35
        base_cache_dir = getattr(self.config, 'DISCOVERY_CACHE_DIR', 'output/cache/discovery') or 'output/cache/discovery'
        base_cache_enabled = getattr(self.config, 'DISCOVERY_CACHE_ENABLED', True)
        base_cache_ttl = getattr(self.config, 'DISCOVERY_CACHE_TTL', 3600)
        rate_override = getattr(self.config, 'DISCOVERY_RATE_LIMITS', None)

        runtime_cfg = self._load_discovery_runtime_config()
        if isinstance(runtime_cfg, dict):
            base_timeout = runtime_cfg.get('request_timeout', base_timeout)
            base_max_retries = runtime_cfg.get('max_retries', base_max_retries)
            if runtime_cfg.get('retry_backoff') is not None:
                base_backoff = runtime_cfg.get('retry_backoff')
            base_max_concurrency = runtime_cfg.get('max_concurrency', base_max_concurrency)
            base_default_rate_interval = runtime_cfg.get('default_rate_interval', base_default_rate_interval)
            base_cache_dir = runtime_cfg.get('cache_dir', base_cache_dir)
            if 'cache_enabled' in runtime_cfg:
                base_cache_enabled = runtime_cfg.get('cache_enabled')
            base_cache_ttl = runtime_cfg.get('cache_ttl_seconds', base_cache_ttl)
            if runtime_cfg.get('rate_limits') is not None:
                rate_override = runtime_cfg.get('rate_limits')

        embedding_cfg = {}
        if isinstance(runtime_cfg, dict):
            embedding_cfg = runtime_cfg.get('embeddings', {}) or {}
        base_embedding_enabled = getattr(self.config, 'DISCOVERY_EMBEDDINGS_ENABLED', True)
        base_embedding_min_keywords = getattr(self.config, 'DISCOVERY_EMBEDDINGS_MIN_KEYWORDS', 5)
        base_embedding_model = getattr(self.config, 'DISCOVERY_EMBEDDINGS_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        self.embedding_enabled = bool(embedding_cfg.get('enabled', base_embedding_enabled))
        try:
            self.embedding_min_keywords = max(int(embedding_cfg.get('min_keywords', base_embedding_min_keywords)), 1)
        except (TypeError, ValueError):
            try:
                self.embedding_min_keywords = max(int(base_embedding_min_keywords), 1)
            except (TypeError, ValueError):
                self.embedding_min_keywords = 5
        self.embedding_model_name = str(embedding_cfg.get('model_name', base_embedding_model)) or base_embedding_model
        self._embedding_model = None

        self.user_agent = (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko)'
        )

        try:
            self.request_timeout = int(float(base_timeout))
        except (TypeError, ValueError):
            self.request_timeout = 12

        try:
            self.max_retries = max(int(base_max_retries), 1)
        except (TypeError, ValueError):
            self.max_retries = 3

        backoff_cfg = base_backoff
        if isinstance(backoff_cfg, (list, tuple)) and len(backoff_cfg) == 2:
            try:
                self.retry_backoff = (float(backoff_cfg[0]), float(backoff_cfg[1]))
            except (TypeError, ValueError):
                self.retry_backoff = (1.0, 3.0)
        else:
            self.retry_backoff = (1.0, 3.0)

        try:
            self.max_concurrency = max(int(base_max_concurrency), 1)
        except (TypeError, ValueError):
            self.max_concurrency = 5

        try:
            self.default_rate_interval = float(base_default_rate_interval)
        except (TypeError, ValueError):
            self.default_rate_interval = 0.35

        cache_dir_value = str(base_cache_dir)
        self.cache_dir = Path(cache_dir_value)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._cache_enabled = bool(base_cache_enabled)
        try:
            self._cache_ttl = int(base_cache_ttl)
        except (TypeError, ValueError):
            self._cache_ttl = 3600
        if self._cache_ttl <= 0:
            self._cache_enabled = False

        self._cache_store: Dict[str, Dict[str, Any]] = {}
        self._reconfigure_cache_backend()

        self._per_host_rate_limits = self._build_rate_limit_map(rate_override)
        self._rate_limiter = _AsyncRateLimiter(self._per_host_rate_limits, self.default_rate_interval)
        # 平台配置
        self.platforms = {
            'reddit': {
                'base_url': 'https://www.reddit.com',
                'api_url': 'https://www.reddit.com/r/{}/search.json',
                'enabled': True
            },
            'hackernews': {
                'base_url': 'https://hacker-news.firebaseio.com/v0',
                'search_url': 'https://hn.algolia.com/api/v1/search',
                'enabled': True
            },
            'producthunt': {
                'base_url': 'https://api.producthunt.com/v2/api/graphql',
                'enabled': bool(self.config.PRODUCTHUNT_API_TOKEN)
            }
        }

        # 设置ProductHunt认证头
        self.ph_headers = {}
        if self.config.PRODUCTHUNT_API_TOKEN:
            self.ph_headers = {
                'Authorization': f'Bearer {self.config.PRODUCTHUNT_API_TOKEN}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

        filters_cfg = self._load_discovery_filter_config()
        self.brand_filter_config = {
            'enabled': bool(filters_cfg.get('brand_filter_enabled', True)),
            'strict_brand_modifiers': bool(filters_cfg.get('strict_brand_modifiers', False)),
            'min_non_brand_tokens': max(int(filters_cfg.get('min_non_brand_tokens', 1) or 0), 0)
        }
        self.generic_filter_config = {
            'enabled': bool(filters_cfg.get('generic_filter_enabled', True))
        }

        seed_cfg = self._load_discovery_seed_config()
        self.seed_profiles = seed_cfg.get('profiles', {}) if isinstance(seed_cfg.get('profiles'), dict) else {}
        self.default_seed_profile = seed_cfg.get('default_profile') or next(iter(self.seed_profiles.keys()), None)
        self.min_seed_terms = max(int(seed_cfg.get('min_terms', 3) or 0), 1)

        # AI相关subreddit列表
        self.ai_subreddits = [
            'artificial', 'MachineLearning', 'deeplearning', 'ChatGPT',
            'OpenAI', 'artificial_intelligence', 'singularity', 'Futurology',
            'programming', 'webdev', 'entrepreneur', 'SaaS', 'startups'
        ]

        # 关键词提取模式（用于论坛/新闻原始文本）
        self.keyword_patterns = [
            r'\b(?:ai|artificial intelligence|machine learning|deep learning|neural network)\b',
            r'\b(?:tool|software|app|platform|service|solution)\b'
        ]

        self.brand_phrases = {
            'chatgpt', 'openai', 'gpt', 'gpt-4', 'gpt4', 'gpt5', 'claude',
            'midjourney', 'deepseek', 'hix bypass', 'undetectable ai', 'turnitin',
            'copilot'
        }
        self.brand_tokens = {token for phrase in self.brand_phrases for token in phrase.split()}
        self.brand_tokens.update({'chatgpt', 'openai', 'gpt', 'claude', 'midjourney', 'deepseek', 'hix', 'bypass', 'turnitin', 'copilot'})
        self.brand_modifier_tokens = {
            'login', 'logins', 'signup', 'sign', 'account', 'app', 'apps',
            'download', 'downloads', 'premium', 'price', 'prices', 'pricing',
            'cost', 'costs', 'free', 'trial', 'promo', 'discount', 'code',
            'codes', 'coupon', 'review', 'reviews', 'vs', 'versus', 'alternative',
            'alternatives', 'compare', 'comparison', 'checker', 'detector',
            'essay', 'humanizer', 'turnitin', 'unlimited', 'pro', 'plus', 'plan',
            'plans', 'tier', 'tiers', 'lifetime', 'prompt', 'prompts', 'price',
            'pricing'
        }
        self.generic_head_terms = {
            'service', 'services', 'software', 'platform', 'platforms', 'solution',
            'solutions', 'application', 'applications', 'tool', 'tools',
            'machine learning', 'artificial intelligence', 'automation', 'ai',
            'technology', 'technologies', 'gpt'
        }
        self.generic_lead_tokens = {'ai', 'machine', 'software', 'platform', 'service', 'tool', 'technology', 'data'}
        self.generic_tail_tokens = {
            'tool', 'tools', 'software', 'platform', 'platforms', 'service',
            'services', 'application', 'applications', 'app', 'apps', 'solution',
            'solutions', 'system', 'systems', 'suite'
        }
        self.long_tail_tokens = {
            'workflow', 'workflows', 'strategy', 'strategies', 'ideas', 'guide',
            'guides', 'tutorial', 'tutorials', 'template', 'templates', 'checklist',
            'automation', 'process', 'processes', 'plan', 'plans', 'blueprint',
            'blueprints', 'examples', 'case', 'cases', 'study', 'studies', 'use',
            'uses', 'stack', 'stacks', 'integration', 'integrations', 'niche',
            'niches', 'system', 'systems', 'playbook', 'playbooks', 'framework',
            'frameworks', 'marketing', 'seo', 'content', 'workflow', 'roadmap',
            'roadmaps', 'setup', 'automation', 'builders', 'for', 'beginners',
            'advanced', 'agency', 'agencies', 'students', 'writers', 'designers',
            'developers', 'founders', 'startups', 'teams', 'checklists'
        }
        self.question_prefixes = (
            'how to', 'how do', 'how can', 'what is', 'what are', 'why', 'should i',
            'can i', 'is there', 'best way', 'ways to'
        )
        self.max_brand_variations = max(int(filters_cfg.get('max_brand_variations', 8) or 0), 0)
        self.lsh_similarity_threshold = float(filters_cfg.get('lsh_similarity_threshold', 0.9))
        self.cluster_distance_threshold = float(filters_cfg.get('cluster_distance_threshold', 0.2))
        self.lsh_similarity_threshold = min(max(self.lsh_similarity_threshold, 0.5), 0.98)
        self.cluster_distance_threshold = min(max(self.cluster_distance_threshold, 0.05), 0.5)
        self._cleaning_config = CleaningConfig()
        self._brand_filter_notice_shown = False
        self._generic_filter_notice_shown = False
    def _load_discovery_filter_config(self) -> Dict[str, Any]:
        config_path = os.path.join(os.path.dirname(__file__), '../../../config/integrated_workflow_config.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                filters_cfg = data.get('discovery_filters', {})
                return filters_cfg if isinstance(filters_cfg, dict) else {}
        except Exception:
            pass
        return {}

    def _load_discovery_runtime_config(self) -> Dict[str, Any]:
        config_path = os.path.join(os.path.dirname(__file__), '../../../config/integrated_workflow_config.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                runtime_cfg = data.get('discovery_runtime', {})
                return runtime_cfg if isinstance(runtime_cfg, dict) else {}
        except Exception:
            pass
        return {}

    def _load_discovery_seed_config(self) -> Dict[str, Any]:
        config_path = os.path.join(os.path.dirname(__file__), '../../../config/integrated_workflow_config.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                seed_cfg = data.get('discovery_seeds', {})
                return seed_cfg if isinstance(seed_cfg, dict) else {}
        except Exception:
            pass
        return {}

    def get_seed_profiles(self) -> List[str]:
        """返回可用的种子关键词配置名称列表"""
        return list(self.seed_profiles.keys())

    def get_seed_terms(self, profile: Optional[str] = None, limit: Optional[int] = None) -> List[str]:
        """根据配置获取种子关键词列表"""
        profile_name = profile or self.default_seed_profile
        terms: List[str] = []

        def _extract_terms(profile_key: Optional[str]) -> List[str]:
            if not profile_key:
                return []
            profile_cfg = self.seed_profiles.get(profile_key)
            if profile_cfg is None:
                return []
            if isinstance(profile_cfg, dict):
                source = profile_cfg.get('terms') or profile_cfg.get('keywords') or []
            elif isinstance(profile_cfg, (list, tuple, set)):
                source = profile_cfg
            else:
                source = []
            cleaned = []
            for term in source:
                if isinstance(term, str):
                    normalized = term.strip()
                    if normalized:
                        cleaned.append(normalized)
            return cleaned

        terms = _extract_terms(profile_name)
        if not terms and profile_name != self.default_seed_profile:
            terms = _extract_terms(self.default_seed_profile)
        if not terms and self.seed_profiles:
            # Fallback到第一个可用配置
            fallback_profile = next(iter(self.seed_profiles.keys()))
            terms = _extract_terms(fallback_profile)

        # 去重同时保留顺序
        unique_terms = []
        seen = set()
        for term in terms:
            lower_term = term.lower()
            if lower_term not in seen:
                unique_terms.append(term)
                seen.add(lower_term)

        if limit and limit > 0:
            return unique_terms[:limit]
        return unique_terms

    def prepare_search_terms(self,
                              seeds: Optional[List[str]] = None,
                              profile: Optional[str] = None,
                              limit: Optional[int] = None,
                              min_terms: Optional[int] = None) -> List[str]:
        """组合输入的种子关键词与配置中的默认种子"""
        cleaned: List[str] = []
        seen: set = set()

        def _append(term: str):
            lower_term = term.lower()
            if lower_term not in seen:
                cleaned.append(term)
                seen.add(lower_term)

        if seeds:
            for term in seeds:
                if isinstance(term, str):
                    normalized = term.strip()
                    if normalized:
                        _append(normalized)

        target_min = max(min_terms or self.min_seed_terms, 1)
        if len(cleaned) < target_min:
            fallback_terms = self.get_seed_terms(profile=profile)
            for term in fallback_terms:
                _append(term)
                if limit and len(cleaned) >= limit:
                    break

        if len(cleaned) < target_min:
            additional_terms = self.get_seed_terms(profile=self.default_seed_profile)
            for term in additional_terms:
                _append(term)
                if limit and len(cleaned) >= limit:
                    break
            if len(cleaned) < target_min and not additional_terms:
                # 仍不足时，至少保留已有值
                pass

        if limit and limit > 0:
            cleaned = cleaned[:limit]

        return cleaned

    def _build_rate_limit_map(self, override: Optional[Any]) -> Dict[str, float]:
        """合并默认与配置的速率限制"""
        defaults = {
            'www.reddit.com': 1.1,
            'reddit.com': 1.1,
            'hn.algolia.com': 0.6,
            'news.ycombinator.com': 0.6,
            'suggestqueries.google.com': 0.25,
            'api.producthunt.com': 1.0,
            'www.producthunt.com': 1.0,
        }
        defaults['*'] = max(self.default_rate_interval, 0.1)

        if override:
            payload = override
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = None
            if isinstance(payload, dict):
                for host, value in payload.items():
                    try:
                        interval = float(value)
                    except (TypeError, ValueError):
                        continue
                    normalized_host = str(host).lower().strip()
                    if normalized_host:
                        defaults[normalized_host] = max(interval, 0.05)
        return defaults

    def _build_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {'User-Agent': self.user_agent}
        if extra:
            for key, value in extra.items():
                if value:
                    headers[key] = value
        return headers

    def _normalize_cache_key(self, raw_key: str) -> str:
        normalized = re.sub(r'[^a-zA-Z0-9_-]+', '_', raw_key.lower()).strip('_')
        hash_suffix = hashlib.sha1(raw_key.encode('utf-8')).hexdigest()[:10]
        if normalized:
            normalized = normalized[:60]
            return f"{normalized}_{hash_suffix}"
        return hash_suffix

    def _reconfigure_cache_backend(self) -> None:
        self._cache_backend = _TTLCache(
            self.cache_dir,
            self._cache_ttl,
            self._cache_enabled,
            self._cache_store,
            self._normalize_cache_key,
        )

    def _ensure_cache_backend_current(self) -> None:
        target_dir = Path(self.cache_dir)
        target_ttl = max(int(self._cache_ttl), 0)
        target_enabled = bool(self._cache_enabled) and target_ttl != 0
        backend = getattr(self, '_cache_backend', None)
        if backend is None or backend.cache_dir != target_dir or backend.ttl_seconds != target_ttl or backend.enabled != target_enabled:
            self._cache_ttl = target_ttl
            self._cache_enabled = target_enabled
            self._reconfigure_cache_backend()
        else:
            backend.ttl_seconds = target_ttl
            backend.enabled = target_enabled

    def _load_cached_payload(self, namespace: str, key: str):
        self._ensure_cache_backend_current()
        return self._cache_backend.get(namespace, key)

    def _save_cached_payload(self, namespace: str, key: str, payload: Any) -> None:
        self._ensure_cache_backend_current()
        self._cache_backend.set(namespace, key, payload)

    def _run_async(self, coroutine):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coroutine)
        if loop.is_running():
            raise RuntimeError('discover_all_platforms 需在同步上下文调用，可直接使用 await 版本')
        return loop.run_until_complete(coroutine)

    async def _run_single_platform(
        self,
        builder: Callable[[aiohttp.ClientSession, asyncio.Semaphore], Awaitable[List[Dict[str, Any]]]]
    ) -> List[Dict[str, Any]]:
        semaphore = asyncio.Semaphore(self.max_concurrency)
        async with aiohttp.ClientSession(headers=self._build_headers()) as session:
            return await builder(session, semaphore)

    async def _fetch_json(
        self,
        session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_payload: Optional[Any] = None
    ) -> Any:
        attempt = 0
        host = urlparse(url).netloc
        request_headers = self._build_headers(headers)
        while True:
            attempt += 1
            recorded_failure = False
            start_ts = None
            try:
                await self._rate_limiter.throttle(host)
                async with semaphore:
                    start_ts = time.perf_counter()
                    async with session.request(
                        method.upper(),
                        url,
                        params=params,
                        headers=request_headers,
                        json=json_payload,
                        timeout=self.request_timeout
                    ) as response:
                        elapsed = time.perf_counter() - start_ts
                        status = response.status
                        if status >= 400:
                            recorded_failure = True
                            telemetry_manager.record_request(
                                host=host,
                                method=method.upper(),
                                url=url,
                                status=status,
                                ok=False,
                                elapsed=elapsed,
                            )
                            response.raise_for_status()

                        data = await response.json()
                        telemetry_manager.record_request(
                            host=host,
                            method=method.upper(),
                            url=url,
                            status=status,
                            ok=True,
                            elapsed=elapsed,
                        )
                        return data
            except (
                aiohttp.ClientError,
                asyncio.TimeoutError,
                aiohttp.ContentTypeError,
                json.JSONDecodeError
            ) as exc:
                status = getattr(exc, 'status', None)
                elapsed = time.perf_counter() - start_ts if start_ts is not None else None
                if not recorded_failure:
                    telemetry_manager.record_request(
                        host=host,
                        method=method.upper(),
                        url=url,
                        status=status,
                        ok=False,
                        elapsed=elapsed,
                    )
                if attempt >= self.max_retries:
                    raise exc
                await asyncio.sleep(random.uniform(*self.retry_backoff))

    async def _fetch_text(
        self,
        session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> str:
        attempt = 0
        host = urlparse(url).netloc
        request_headers = self._build_headers(headers)
        while True:
            attempt += 1
            recorded_failure = False
            start_ts = None
            try:
                await self._rate_limiter.throttle(host)
                async with semaphore:
                    start_ts = time.perf_counter()
                    async with session.request(
                        method.upper(),
                        url,
                        params=params,
                        headers=request_headers,
                        timeout=self.request_timeout
                    ) as response:
                        elapsed = time.perf_counter() - start_ts
                        status = response.status
                        if status >= 400:
                            recorded_failure = True
                            telemetry_manager.record_request(
                                host=host,
                                method=method.upper(),
                                url=url,
                                status=status,
                                ok=False,
                                elapsed=elapsed,
                            )
                            response.raise_for_status()

                        content = await response.text()
                        telemetry_manager.record_request(
                            host=host,
                            method=method.upper(),
                            url=url,
                            status=status,
                            ok=True,
                            elapsed=elapsed,
                        )
                        return content
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                status = getattr(exc, 'status', None)
                elapsed = time.perf_counter() - start_ts if start_ts is not None else None
                if not recorded_failure:
                    telemetry_manager.record_request(
                        host=host,
                        method=method.upper(),
                        url=url,
                        status=status,
                        ok=False,
                        elapsed=elapsed,
                    )
                if attempt >= self.max_retries:
                    raise exc
                await asyncio.sleep(random.uniform(*self.retry_backoff))

    def _get_embedding_model(self):
        cached = getattr(self, '_embedding_model', None)
        if cached is not None:
            return cached

        model_name = self.embedding_model_name
        shared = _EMBEDDING_MODEL_CACHE.get(model_name)
        if shared is not None:
            self._embedding_model = shared
            return shared

        with _EMBEDDING_MODEL_LOCK:
            shared = _EMBEDDING_MODEL_CACHE.get(model_name)
            if shared is None:
                from sentence_transformers import SentenceTransformer

                shared = SentenceTransformer(model_name)
                _EMBEDDING_MODEL_CACHE[model_name] = shared

        self._embedding_model = shared
        return shared

    async def _discover_reddit_keywords_async(
        self,
        session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
        subreddit: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        cache_key = f"{subreddit.lower()}_{int(limit)}"
        cached = self._load_cached_payload('reddit', cache_key)
        if cached is not None:
            print(f"⚡ Reddit r/{subreddit} 使用缓存结果")
            return cached

        print(f"🔍 正在分析 Reddit r/{subreddit}...")
        url = f"https://www.reddit.com/r/{subreddit}/hot.json"
        params = {'limit': max(int(limit), 1)}
        try:
            data = await self._fetch_json(session, semaphore, 'GET', url, params=params)
        except Exception as exc:
            print(f"❌ Reddit r/{subreddit} 分析失败: {exc}")
            return []

        posts = data.get('data', {}).get('children', [])
        keywords: List[Dict[str, Any]] = []
        for post in posts:
            post_data = post.get('data', {})
            title = post_data.get('title', '')
            selftext = post_data.get('selftext', '')
            score = post_data.get('score', 0)
            num_comments = post_data.get('num_comments', 0)

            extracted = self._extract_keywords_from_text(f"{title} {selftext}")
            for keyword in extracted:
                keywords.append({
                    'keyword': keyword,
                    'source': f'reddit_r_{subreddit}',
                    'title': title,
                    'score': score,
                    'comments': num_comments,
                    'url': f"https://reddit.com{post_data.get('permalink', '')}",
                    'platform': 'reddit'
                })

        if keywords:
            self._save_cached_payload('reddit', cache_key, keywords)
        return keywords

    def discover_reddit_keywords(self, subreddit: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self._run_async(
            self._run_single_platform(
                lambda session, semaphore: self._discover_reddit_keywords_async(
                    session, semaphore, subreddit, limit
                )
            )
        )

    async def _discover_hackernews_keywords_async(
        self,
        session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
        query: str = 'AI',
        days: int = 30
    ) -> List[Dict[str, Any]]:
        cache_key = f"{query.lower()}_{int(days)}"
        cached = self._load_cached_payload('hackernews', cache_key)
        if cached is not None:
            print(f"⚡ Hacker News (查询: {query}) 使用缓存结果")
            return cached

        print(f"🔍 正在分析 Hacker News (查询: {query})...")
        end_time = int(time.time())
        start_time = end_time - (int(days) * 24 * 3600)
        url = "https://hn.algolia.com/api/v1/search"
        params = {
            'query': query,
            'tags': 'story',
            'numericFilters': f'created_at_i>{start_time},created_at_i<{end_time}',
            'hitsPerPage': 100
        }
        try:
            data = await self._fetch_json(session, semaphore, 'GET', url, params=params)
        except Exception as exc:
            print(f"❌ Hacker News 分析失败: {exc}")
            return []

        hits = data.get('hits', [])
        keywords: List[Dict[str, Any]] = []
        for hit in hits:
            title = hit.get('title', '')
            post_url = hit.get('url', '')
            points = hit.get('points', 0)
            num_comments = hit.get('num_comments', 0)
            extracted = self._extract_keywords_from_text(title)
            for keyword in extracted:
                keywords.append({
                    'keyword': keyword,
                    'source': 'hackernews',
                    'title': title,
                    'score': points,
                    'comments': num_comments,
                    'url': post_url or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    'platform': 'hackernews'
                })

        if keywords:
            self._save_cached_payload('hackernews', cache_key, keywords)
        return keywords

    def discover_hackernews_keywords(self, query: str = 'AI', days: int = 30) -> List[Dict[str, Any]]:
        return self._run_async(
            self._run_single_platform(
                lambda session, semaphore: self._discover_hackernews_keywords_async(
                    session, semaphore, query, days
                )
            )
        )

    async def _discover_youtube_keywords_async(
        self,
        session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
        search_term: str
    ) -> List[Dict[str, Any]]:
        cache_key = search_term.lower()
        cached = self._load_cached_payload('youtube', cache_key)
        if cached is not None:
            print(f"⚡ YouTube 搜索建议 (查询: {search_term}) 使用缓存结果")
            return cached

        print(f"🔍 正在分析 YouTube 搜索建议 (查询: {search_term})...")
        url = "https://suggestqueries.google.com/complete/search"
        params = {'client': 'youtube', 'ds': 'yt', 'q': search_term}
        try:
            content = await self._fetch_text(session, semaphore, 'GET', url, params=params)
        except Exception as exc:
            print(f"❌ YouTube 分析失败: {exc}")
            return []

        keywords: List[Dict[str, Any]] = []
        if content.startswith('window.google.ac.h('):
            json_str = content[19:-1]
            try:
                data = json.loads(json_str)
                suggestions = data[1] if len(data) > 1 else []
                for suggestion in suggestions:
                    if isinstance(suggestion, list) and suggestion:
                        keyword = suggestion[0]
                        keywords.append({
                            'keyword': keyword,
                            'source': 'youtube_suggestions',
                            'title': f'YouTube搜索建议: {keyword}',
                            'score': 0,
                            'comments': 0,
                            'url': f'https://www.youtube.com/results?search_query={quote(keyword)}',
                            'platform': 'youtube'
                        })
            except Exception as exc:
                print(f"⚠️ YouTube 建议解析失败: {exc}")

        if keywords:
            self._save_cached_payload('youtube', cache_key, keywords)
        return keywords

    def discover_youtube_keywords(self, search_term: str) -> List[Dict[str, Any]]:
        return self._run_async(
            self._run_single_platform(
                lambda session, semaphore: self._discover_youtube_keywords_async(
                    session, semaphore, search_term
                )
            )
        )

    async def _discover_google_suggestions_async(
        self,
        session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
        search_term: str
    ) -> List[Dict[str, Any]]:
        cache_key = search_term.lower()
        cached = self._load_cached_payload('google', cache_key)
        if cached is not None:
            print(f"⚡ Google 搜索建议 (查询: {search_term}) 使用缓存结果")
            return cached

        print(f"🔍 正在分析 Google 搜索建议 (查询: {search_term})...")
        url = "https://suggestqueries.google.com/complete/search"
        params = {'client': 'firefox', 'q': search_term}
        try:
            data = await self._fetch_json(session, semaphore, 'GET', url, params=params)
        except Exception as exc:
            print(f"❌ Google搜索建议分析失败: {exc}")
            return []

        suggestions = data[1] if isinstance(data, list) and len(data) > 1 else []
        keywords: List[Dict[str, Any]] = []
        for suggestion in suggestions:
            keywords.append({
                'keyword': suggestion,
                'source': 'google_suggestions',
                'title': f'Google搜索建议: {suggestion}',
                'score': 0,
                'comments': 0,
                'url': f'https://www.google.com/search?q={quote(suggestion)}',
                'platform': 'google'
            })

        if keywords:
            self._save_cached_payload('google', cache_key, keywords)
        return keywords

    def discover_google_suggestions(self, search_term: str) -> List[Dict[str, Any]]:
        return self._run_async(
            self._run_single_platform(
                lambda session, semaphore: self._discover_google_suggestions_async(
                    session, semaphore, search_term
                )
            )
        )

    async def _discover_producthunt_keywords_async(
        self,
        session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
        search_term: str = 'AI',
        days: int = 30
    ) -> List[Dict[str, Any]]:
        if not self.platforms.get('producthunt', {}).get('enabled'):
            return []

        cache_key = f"{search_term.lower()}_{int(days)}"
        cached = self._load_cached_payload('producthunt', cache_key)
        if cached is not None:
            print(f"⚡ ProductHunt (查询: {search_term}) 使用缓存结果")
            return cached

        print(f"🔍 正在分析 ProductHunt (查询: {search_term})...")
        query = """
        query($search: String!, $first: Int!) {
          posts(search: $search, first: $first, order: VOTES) {
            edges {
              node {
                id
                name
                tagline
                description
                votesCount
                commentsCount
                url
                topics {
                  edges {
                    node {
                      name
                    }
                  }
                }
              }
            }
          }
        }
        """
        variables = {
            "search": search_term,
            "first": 50
        }
        try:
            data = await self._fetch_json(
                session,
                semaphore,
                'POST',
                self.platforms['producthunt']['base_url'],
                json_payload={'query': query, 'variables': variables},
                headers=self.ph_headers
            )
        except Exception as exc:
            print(f"❌ ProductHunt 分析失败: {exc}")
            return []

        posts = ((data or {}).get('data') or {}).get('posts', {}).get('edges', [])
        keywords: List[Dict[str, Any]] = []
        for edge in posts:
            node = edge.get('node', {})
            name = node.get('name', '')
            tagline = node.get('tagline', '')
            description = node.get('description', '')
            votes = node.get('votesCount', 0)
            comments = node.get('commentsCount', 0)
            url = node.get('url', '')
            topics = [t.get('node', {}).get('name', '') for t in node.get('topics', {}).get('edges', [])]
            combined_text = " ".join(filter(None, [name, tagline, description] + topics))
            extracted = self._extract_keywords_from_text(combined_text)
            for keyword in extracted:
                keywords.append({
                    'keyword': keyword,
                    'source': 'producthunt',
                    'title': name,
                    'score': votes,
                    'comments': comments,
                    'url': url,
                    'platform': 'producthunt'
                })

        if keywords:
            self._save_cached_payload('producthunt', cache_key, keywords)
        return keywords

    def discover_producthunt_keywords(self, search_term: str = 'AI', days: int = 30) -> List[Dict[str, Any]]:
        return self._run_async(
            self._run_single_platform(
                lambda session, semaphore: self._discover_producthunt_keywords_async(
                    session, semaphore, search_term, days
                )
            )
        )

    async def _async_discover_all_platforms(self, search_terms: List[str]) -> pd.DataFrame:
        telemetry_stage = telemetry_manager.start_stage(
            "discovery.multi_platform",
            metadata={
                "input_terms": len(search_terms),
                "platforms": [p for p, cfg in self.platforms.items() if cfg.get('enabled', True)],
            }
        )
        try:
            print("🚀 开始多平台关键词发现...")
            prepared_terms = self.prepare_search_terms(search_terms)
            if not prepared_terms:
                print("⚠️ 缺少有效的搜索词，无法执行多平台发现")
                telemetry_manager.end_stage(
                    telemetry_stage,
                    extra={'result_keywords': 0, 'prepared_terms': 0, 'tasks': 0}
                )
                return pd.DataFrame(columns=['keyword', 'platform'])

            semaphore = asyncio.Semaphore(self.max_concurrency)
            tasks: List[Awaitable[List[Dict[str, Any]]]] = []

            async with aiohttp.ClientSession(headers=self._build_headers()) as session:
                for subreddit in self.ai_subreddits[:5]:
                    tasks.append(self._discover_reddit_keywords_async(session, semaphore, subreddit, 50))

                for term in prepared_terms:
                    tasks.append(self._discover_hackernews_keywords_async(session, semaphore, term))
                    tasks.append(self._discover_youtube_keywords_async(session, semaphore, term))
                    tasks.append(self._discover_google_suggestions_async(session, semaphore, term))
                    if self.platforms.get('producthunt', {}).get('enabled'):
                        tasks.append(self._discover_producthunt_keywords_async(session, semaphore, term))

                results = await asyncio.gather(*tasks, return_exceptions=True)

            all_keywords: List[Dict[str, Any]] = []
            for result in results:
                if isinstance(result, Exception):
                    print(f"❌ 平台采集任务异常: {result}")
                    telemetry_manager.log_event(
                        'discovery.error',
                        'platform_task_failed',
                        {'error': str(result)},
                    )
                    continue
                if result:
                    all_keywords.extend(result)

            telemetry_manager.increment_counter('discovery.multi_platform_runs')
            telemetry_manager.set_gauge('discovery.multi_platform.last_result_count', len(all_keywords))
            telemetry_manager.end_stage(
                telemetry_stage,
                extra={
                    'result_keywords': len(all_keywords),
                    'prepared_terms': len(prepared_terms),
                    'tasks': len(tasks),
                }
            )

            return self._post_process_keywords(all_keywords)
        except Exception as exc:
            telemetry_manager.end_stage(telemetry_stage, status='failed', error=str(exc))
            raise

    def discover_all_platforms(self, search_terms: List[str]) -> pd.DataFrame:
        return self._run_async(self._async_discover_all_platforms(search_terms))

    def _post_process_keywords(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        df = pd.DataFrame(records)
        if 'keyword' not in df.columns:
            print("⚠️ 结果缺少关键词字段")
            return df

        if df.empty:
            return df

        try:
            df['keyword'] = df['keyword'].astype(str)
            df['normalized_keyword'] = df['keyword'].apply(standardize_term)
            df = df[df['normalized_keyword'].apply(lambda term: is_valid_term(term, self._cleaning_config))]
            df = df.drop_duplicates(subset='normalized_keyword')
            df['keyword'] = df['normalized_keyword']
            df = df.drop(columns=['normalized_keyword'])
        except Exception as exc:
            print(f"⚠️ 关键词清洗失败: {exc}")
            df['keyword'] = df['keyword'].astype(str)

        if df.empty:
            print("⚠️ 清洗后无有效关键词")
            return df

        if 'platform' not in df.columns:
            df['platform'] = 'unknown'
        else:
            df['platform'] = df['platform'].fillna('unknown')

        if self.brand_filter_config.get('enabled', True):
            before_brand = len(df)
            df = df[~df['keyword'].apply(self._is_brand_heavy)].reset_index(drop=True)
            if len(df) < before_brand:
                print(f"⚠️ 移除了 {before_brand - len(df)} 个品牌泛词")
        elif not self._brand_filter_notice_shown:
            print("ℹ️ 品牌词过滤已禁用，保留品牌相关关键词")
            self._brand_filter_notice_shown = True

        if df.empty:
            return df

        if self.generic_filter_config.get('enabled', True):
            before_generic = len(df)
            df = df[~df['keyword'].apply(self._is_underspecified_keyword)].reset_index(drop=True)
            if len(df) < before_generic:
                print(f"⚠️ 移除了 {before_generic - len(df)} 个泛化头部词")
        elif not self._generic_filter_notice_shown:
            print("ℹ️ 泛词过滤已禁用，将保留更广泛的热门词")
            self._generic_filter_notice_shown = True

        df = self._limit_brand_keywords(df)
        if df.empty:
            print("⚠️ 过滤后无有效关键词")
            return df

        try:
            from datasketch import MinHash, MinHashLSH
            from sklearn.cluster import AgglomerativeClustering
            import numpy as np

            texts = df['keyword'].tolist()

            def shingles(s: str, k: int = 3):
                s = s.replace(' ', '_')
                return {s[i:i + k] for i in range(max(len(s) - k + 1, 1))}

            mhashes = []
            for text_value in texts:
                mh = MinHash(num_perm=64)
                for sh in shingles(text_value):
                    mh.update(sh.encode('utf-8'))
                mhashes.append(mh)

            lsh = MinHashLSH(threshold=self.lsh_similarity_threshold, num_perm=64)
            for idx, mh in enumerate(mhashes):
                lsh.insert(str(idx), mh)

            keep_idx = []
            seen = set()
            for idx, mh in enumerate(mhashes):
                if idx in seen:
                    continue
                near = lsh.query(mh)
                group = sorted(int(x) for x in near)
                for member in group:
                    seen.add(member)
                keep_idx.append(group[0])

            df = df.iloc[keep_idx].reset_index(drop=True)

            embeddings = None
            if self.embedding_enabled and len(df) >= self.embedding_min_keywords:
                try:
                    model = self._get_embedding_model()
                    embeddings = model.encode(df['keyword'].tolist(), normalize_embeddings=True)
                except Exception as exc:
                    print(f"Embedding model load failed: {exc}")
                    self.embedding_enabled = False
            else:
                if self.embedding_enabled and len(df) < self.embedding_min_keywords:
                    print(f"Skipping embedding stage: {len(df)} keywords, threshold {self.embedding_min_keywords}")

            if embeddings is not None and len(df) >= self.embedding_min_keywords:
                clustering = AgglomerativeClustering(
                    n_clusters=None,
                    distance_threshold=self.cluster_distance_threshold,
                    affinity='cosine',
                    linkage='average'
                )
                labels = clustering.fit_predict(embeddings)
                df['cluster_id'] = labels

                representatives = []
                for cluster_id in sorted(set(labels)):
                    idxs = np.where(labels == cluster_id)[0]
                    subset = embeddings[idxs]
                    center = subset.mean(axis=0, keepdims=True)
                    sims = (subset @ center.T).ravel()
                    representative = idxs[int(np.argmax(sims))]
                    representatives.append(representative)
                df = df.iloc[sorted(set(representatives))].reset_index(drop=True)
            else:
                if 'cluster_id' not in df.columns:
                    df['cluster_id'] = 0
        except Exception as exc:
            print(f"Keyword clustering failed: {exc}")
            if 'cluster_id' not in df.columns:
                df['cluster_id'] = 0
            pass

        if 'score' not in df.columns:
            df['score'] = 0
        df['long_tail_score'] = df['keyword'].apply(self._calculate_long_tail_score)
        df['weighted_score'] = df['score'] * df['long_tail_score']
        df = df.sort_values('weighted_score', ascending=False)
        df['discovered_at'] = datetime.now().isoformat()
        print(f"✅ 发现 {len(df)} 个关键词")

        return df

    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """从文本中提取关键词（论坛/新闻名词短语抽取 + 模式词）"""
        keywords = []
        text = text.lower()
        try:
            import nltk
            from nltk import pos_tag, word_tokenize, RegexpParser
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
            try:
                nltk.data.find('taggers/averaged_perceptron_tagger')
            except LookupError:
                nltk.download('averaged_perceptron_tagger', quiet=True)
            tokens = word_tokenize(text)
            tagged = pos_tag(tokens)
            grammar = r"NP: {<JJ>*<NN|NNS|NNP|NNPS>+}"
            cp = RegexpParser(grammar)
            tree = cp.parse(tagged)
            nps = []
            for subtree in tree.subtrees(filter=lambda t: t.label() == 'NP'):
                phrase = ' '.join(w for w, t in subtree.leaves())
                nps.append(phrase)
            for np in nps:
                np_clean = re.sub(r'[^a-z0-9\s-]', ' ', np).strip()
                if 3 <= len(np_clean) <= 40 and 1 <= len(np_clean.split()) <= 3:
                    keywords.append(np_clean)
        except Exception:
            pass
        for pattern in self.keyword_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                keyword = re.sub(r'[^a-z0-9\s-]', ' ', match).strip()
                if 3 <= len(keyword) <= 40 and 1 <= len(keyword.split()) <= 3:
                    keywords.append(keyword)
        base = [
            'ai tool', 'ai generator', 'ai writer', 'ai assistant', 'ai chatbot',
            'machine learning', 'deep learning', 'neural network', 'gpt',
            'artificial intelligence', 'automation', 'nlp', 'computer vision'
        ]
        for term in base:
            if term in text and 3 <= len(term) <= 40:
                keywords.append(term)
        return list(set(keywords))
    
    def _is_long_tail_keyword(self, keyword: str) -> bool:
        """
        判断是否为长尾关键词
        
        Args:
            keyword: 关键词
            
        Returns:
            是否为长尾关键词
        """
        words = keyword.split()
        # 长尾词标准：3个以上词汇且总长度15个字符以上
        return len(words) >= 3 and len(keyword) >= 15
    
    def _calculate_long_tail_score(self, keyword: str) -> float:
        """
        计算长尾词评分加权
        
        Args:
            keyword: 关键词
            
        Returns:
            评分倍数
        """
        word_count = len(keyword.split())
        keyword_lower = keyword.lower()
        
        base_score = 1.0
        
        # 基于词数的评分加权
        if word_count >= 5:
            base_score *= 3.0  # 5+词汇获得最高加权
        elif word_count >= 4:
            base_score *= 2.5  # 4词汇获得高加权
        elif word_count >= 3:
            base_score *= 2.0  # 3词汇获得中等加权
        
        # 基于意图明确性的加权
        high_intent_phrases = ['how to', 'step by step', 'tutorial', 'guide', 'without', 'for beginners']
        if any(phrase in keyword_lower for phrase in high_intent_phrases):
            base_score *= 1.5
        
        # 基于竞争度的调整
        high_competition_words = ['best', 'top', 'review', 'vs', 'comparison']
        if any(comp in keyword_lower for comp in high_competition_words):
            base_score *= 0.6  # 高竞争词降低评分

        return base_score

    def _is_brand_heavy(self, keyword: str) -> bool:
        """过滤品牌词及其常见附属词"""
        if not keyword or not self.brand_filter_config.get('enabled', True):
            return False

        keyword_lower = keyword.lower()
        tokens = [t for t in re.split(r"[^a-z0-9]+", keyword_lower) if t]
        if not tokens:
            return False

        brand_present = any(phrase in keyword_lower for phrase in self.brand_phrases)
        if not brand_present:
            brand_present = any(token in self.brand_tokens for token in tokens)
        if not brand_present:
            return False

        non_brand_tokens = [t for t in tokens if t not in self.brand_tokens]
        if not non_brand_tokens:
            return True

        min_non_brand = max(int(self.brand_filter_config.get('min_non_brand_tokens', 1) or 0), 0)
        if min_non_brand and len(non_brand_tokens) < min_non_brand:
            return True

        if self.brand_filter_config.get('strict_brand_modifiers', False):
            if all(token in self.brand_modifier_tokens for token in non_brand_tokens):
                return True
            if len(non_brand_tokens) == 1 and non_brand_tokens[0] in self.brand_modifier_tokens:
                return True

        return False

    def _is_underspecified_keyword(self, keyword: str) -> bool:
        """过滤缺乏限定词的泛词"""
        if not keyword:
            return True

        keyword_lower = keyword.lower()
        if keyword_lower in self.generic_head_terms:
            return True

        tokens = [t for t in re.split(r"[^a-z0-9]+", keyword_lower) if t]
        if not tokens:
            return True

        if len(tokens) == 1:
            token = tokens[0]
            return token in self.generic_head_terms or len(token) <= 3

        if len(tokens) == 2:
            joined = " ".join(tokens)
            if joined in self.generic_head_terms:
                return True
            if tokens[0] in self.generic_head_terms and tokens[1] in self.generic_head_terms:
                return True
            if tokens[0] in self.generic_lead_tokens and tokens[1] in self.generic_tail_tokens:
                return True
            if tokens[1] in self.generic_lead_tokens and tokens[0] in self.generic_tail_tokens:
                return True
            if not any(token in self.long_tail_tokens for token in tokens):
                return False

        if any(keyword_lower.startswith(prefix) for prefix in self.question_prefixes):
            return False

        if len(tokens) >= 3:
            informative_tokens = [t for t in tokens if t in self.long_tail_tokens]
            return len(informative_tokens) == 0

        return False

    def _identify_brand(self, keyword: str) -> Optional[str]:
        """识别关键词所属品牌"""
        if not keyword:
            return None

        keyword_lower = keyword.lower()
        for phrase in self.brand_phrases:
            if phrase in keyword_lower:
                return phrase

        tokens = [t for t in re.split(r"[^a-z0-9]+", keyword_lower) if t]
        for token in tokens:
            if token in self.brand_tokens:
                return token
        return None

    def _limit_brand_keywords(self, df: pd.DataFrame) -> pd.DataFrame:
        """限制单一品牌的关键词数量"""
        if df.empty or 'keyword' not in df.columns or self.max_brand_variations <= 0:
            return df

        keep_indices = []
        brand_counts: Dict[str, int] = {}

        for idx, keyword in df['keyword'].items():
            brand = self._identify_brand(str(keyword))
            if not brand:
                keep_indices.append(idx)
                continue

            count = brand_counts.get(brand, 0)
            if count < self.max_brand_variations:
                keep_indices.append(idx)
                brand_counts[brand] = count + 1

        return df.loc[keep_indices].reset_index(drop=True)
    
    def analyze_keyword_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析关键词趋势"""
        if df.empty:
            return {}
        
        platform_distribution = df['platform'].value_counts().to_dict() if 'platform' in df.columns else {}

        score_df = df.copy()
        if 'score' not in score_df.columns:
            score_df['score'] = 0.0
        if 'platform' not in score_df.columns:
            score_df['platform'] = 'unknown'

        top_keywords = score_df.nlargest(10, 'score')[['keyword', 'score', 'platform']].to_dict('records')

        analysis = {
            'total_keywords': len(df),
            'platform_distribution': platform_distribution,
            'top_keywords_by_score': top_keywords,
            'keyword_length_stats': {
                'avg_length': df['keyword'].str.len().mean(),
                'min_length': df['keyword'].str.len().min(),
                'max_length': df['keyword'].str.len().max()
            },
            'common_terms': self._get_common_terms(df['keyword'].tolist())
        }
        
        return analysis
    
    def _get_common_terms(self, keywords: List[str]) -> Dict[str, int]:
        """获取常见词汇"""
        all_words = []
        for keyword in keywords:
            words = keyword.lower().split()
            all_words.extend([word for word in words if len(word) > 2])
        
        return dict(Counter(all_words).most_common(20))
    
    def save_results(self, df: pd.DataFrame, analysis: Dict, output_dir: str = 'data/multi_platform_keywords'):
        """保存结果"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存关键词数据
        csv_path = os.path.join(output_dir, f'multi_platform_keywords_{timestamp}.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # 保存分析报告（处理numpy类型序列化问题）
        json_path = os.path.join(output_dir, f'keyword_analysis_{timestamp}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            # 转换numpy类型为Python原生类型
            def convert_numpy_types(obj):
                if hasattr(obj, 'item'):
                    return obj.item()
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(v) for v in obj]
                else:
                    return obj
            
            serializable_analysis = convert_numpy_types(analysis)
            json.dump(serializable_analysis, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结果已保存:")
        print(f"   关键词数据: {csv_path}")
        print(f"   分析报告: {json_path}")
        
        return csv_path, json_path


def run_discovery(input_keywords=None, limit=10, output_dir=None, verbose=True, seed_profile: Optional[str] = None, min_terms: Optional[int] = None):
    """
    运行多平台关键词发现
    
    参数:
        input_keywords: 输入关键词列表，如果为None则使用默认关键词
        limit: 限制使用的关键词数量
        output_dir: 输出目录，如果为None则使用默认目录
        verbose: 是否打印详细信息
    
    返回:
        tuple: (关键词DataFrame, 分析结果字典, 输出CSV路径, 输出JSON路径)
    """
    # 初始化发现工具
    discoverer = MultiPlatformKeywordDiscovery()
    
    raw_terms = input_keywords if input_keywords else []
    search_terms = discoverer.prepare_search_terms(
        seeds=raw_terms,
        profile=seed_profile,
        limit=limit,
        min_terms=min_terms
    )
    if verbose:
        if input_keywords:
            print(f"✅ 使用 {len(raw_terms)} 个输入关键词，合并后搜索 {len(search_terms)} 个种子词")
        else:
            profile_label = seed_profile or discoverer.default_seed_profile or 'default'
            print(f"ℹ️ 从配置 '{profile_label}' 载入 {len(search_terms)} 个默认关键词")

    if verbose:
        print("🔍 多平台关键词发现工具")
        print(f"📊 搜索词汇: {', '.join(search_terms)}")
        print("-" * 50)
    
    # 发现关键词
    df = discoverer.discover_all_platforms(search_terms)
    
    if not df.empty:
        # 分析趋势
        analysis = discoverer.analyze_keyword_trends(df)
        
        if verbose:
            # 显示结果摘要
            print("\n📈 发现结果摘要:")
            print(f"总关键词数: {analysis['total_keywords']}")
            print(f"平台分布: {analysis['platform_distribution']}")
            print(f"平均关键词长度: {analysis['keyword_length_stats']['avg_length']:.1f} 字符")
            
            print("\n🏆 热门关键词 (按评分排序):")
            for i, kw in enumerate(analysis['top_keywords_by_score'][:5], 1):
                print(f"  {i}. {kw['keyword']} (评分: {kw['score']}, 来源: {kw['platform']})")
            
            print("\n🔤 常见词汇:")
            for word, count in list(analysis['common_terms'].items())[:10]:
                print(f"  {word}: {count}次")
        
        # 保存结果
        csv_path, json_path = discoverer.save_results(df, analysis, output_dir=output_dir)
        
        return df, analysis, csv_path, json_path
    else:
        if verbose:
            print("❌ 未发现任何关键词，请检查网络连接或调整搜索参数")
        return pd.DataFrame(), {}, None, None


def main():
    """命令行入口函数"""
    import argparse
    
    # 命令行参数解析
    parser = argparse.ArgumentParser(description="多平台关键词发现工具")
    parser.add_argument("--input", "-i", help="输入关键词文件路径 (CSV格式，包含keyword列)")
    parser.add_argument("--keywords", "-k", help="直接指定关键词，用逗号分隔")
    parser.add_argument("--use-root-words", "-r", action="store_true", help="使用词根趋势数据")
    parser.add_argument("--limit", "-l", type=int, default=10, help="每个来源使用的关键词数量限制")
    parser.add_argument("--output-dir", "-o", help="输出目录")
    parser.add_argument("--seed-profile", help="指定配置中的种子关键词档案")
    parser.add_argument("--min-terms", type=int, help="确保最少使用的种子关键词数量")
    args = parser.parse_args()
    
    # 获取初始关键词
    search_terms = []
    
    if args.input:
        # 从CSV文件读取关键词
        try:
            import pandas as pd
            df_input = pd.read_csv(args.input)
            if 'keyword' in df_input.columns:
                search_terms = df_input['keyword'].tolist()
                print(f"✅ 从文件 {args.input} 读取了 {len(search_terms)} 个关键词")
            else:
                print("❌ 输入文件必须包含'keyword'列")
                return
        except Exception as e:
            print(f"❌ 读取输入文件失败: {e}")
            return
    
    elif args.keywords:
        # 直接使用指定的关键词
        search_terms = [k.strip() for k in args.keywords.split(',')]
        print(f"✅ 使用指定的 {len(search_terms)} 个关键词")
    
    elif args.use_root_words:
        # 使用词根相关关键词
        try:
            # 尝试从词根趋势数据目录读取
            root_words_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'root_word_trends')
            if os.path.exists(root_words_dir):
                # 查找最新的词根趋势文件
                files = [f for f in os.listdir(root_words_dir) if f.endswith('.csv')]
                if files:
                    # 按修改时间排序，获取最新文件
                    latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(root_words_dir, f)))
                    file_path = os.path.join(root_words_dir, latest_file)
                    
                    # 读取词根趋势数据
                    import pandas as pd
                    df_roots = pd.read_csv(file_path)
                    if 'keyword' in df_roots.columns:
                        # 获取关键词
                        search_terms = df_roots['keyword'].head(args.limit).tolist()
                        print(f"✅ 从词根趋势文件 {latest_file} 读取了 {len(search_terms)} 个关键词")
                    else:
                        raise ValueError("词根趋势文件缺少'keyword'列")
                else:
                    raise FileNotFoundError("未找到词根趋势CSV文件")
            else:
                raise FileNotFoundError(f"词根趋势目录不存在: {root_words_dir}")
                
        except Exception as e:
            print(f"❌ 读取词根趋势数据失败: {e}")
            search_terms = []
            print("⚠️ 将使用配置中的默认种子关键词")
    
    # 运行发现过程
    run_discovery(
        input_keywords=search_terms,
        limit=args.limit,
        output_dir=args.output_dir,
        verbose=True,
        seed_profile=args.seed_profile,
        min_terms=args.min_terms
    )


if __name__ == "__main__":
    main()
    
# 示例用法:
# 1. 命令行使用:
#    - 使用默认关键词: python multi_platform_keyword_discovery.py
#    - 指定关键词: python multi_platform_keyword_discovery.py --keywords "AI tools,machine learning,data science"
#    - 从文件读取: python multi_platform_keyword_discovery.py --input path/to/keywords.csv
#    - 使用词根: python multi_platform_keyword_discovery.py --use-root-words --limit 20
#
# 2. 作为模块导入:
#    from demand_mining.tools.multi_platform_keyword_discovery import run_discovery
#    
#    # 使用主流程中获取的关键词
#    keywords = ["ai writing", "machine learning", "data science"]
#    df, analysis, csv_path, json_path = run_discovery(
#        input_keywords=keywords,
#        limit=10,
#        output_dir="output/multi_platform_keywords",
#        verbose=True
#    )
#    
#    # 使用结果进行后续处理
#    top_keywords = df.head(20)
