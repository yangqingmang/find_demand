#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单的多源联想词/热词采集器"""

from __future__ import annotations

import json
import time
import os
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional

import requests


DEFAULT_TIMEOUT = 8
DEFAULT_MIN_INTERVAL = 0.35
DEFAULT_MAX_SEED_SAMPLES = 40
DEFAULT_MAX_REQUESTS = 200


def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (KeywordRadar/1.0; +https://github.com/find-demand)',
        'Accept': 'application/json,text/plain,*/*',
        'Accept-Language': 'en-US,en;q=0.8'
    })
    return session


@dataclass
class Suggestion:
    term: str
    source: str
    seed: str
    metadata: Optional[Dict[str, str]] = None


class SuggestionCollector:
    """聚合 Google/YouTube/Reddit 等公开 Suggestion 数据源"""

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        min_interval: float = DEFAULT_MIN_INTERVAL,
        max_seed_samples: int = DEFAULT_MAX_SEED_SAMPLES,
        max_requests: Optional[int] = DEFAULT_MAX_REQUESTS,
        max_collectors_per_seed: Optional[int] = None,
    ):
        self.session = _build_session()
        self.timeout = timeout
        self.serp_api_key = self._load_serp_api_key()
        self.min_interval = max(float(min_interval), 0.0)
        self.max_seed_samples = max(int(max_seed_samples), 0) if max_seed_samples else 0
        self.max_requests = max(int(max_requests), 1) if max_requests else None
        self.max_collectors_per_seed = (
            max(int(max_collectors_per_seed), 1)
            if max_collectors_per_seed
            else None
        )

        self._last_request_ts: float = 0.0
        self._request_count: int = 0
        self._stats: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)

    def fetch_google_autocomplete(self, keyword: str, lang: str = 'en') -> List[str]:
        url = 'https://suggestqueries.google.com/complete/search'
        params = {
            'client': 'firefox',
            'q': keyword,
            'hl': lang,
        }
        return self._fetch_suggestions(url, params, keyword)

    def fetch_google_autocomplete_cn(self, keyword: str) -> List[str]:
        return self.fetch_google_autocomplete(keyword, lang='zh-CN')

    def fetch_youtube_suggestions(self, keyword: str) -> List[str]:
        url = 'https://suggestqueries.google.com/complete/search'
        params = {
            'client': 'youtube',
            'ds': 'yt',
            'q': keyword,
        }
        return self._fetch_suggestions(url, params, keyword)

    def fetch_reddit_suggestions(self, keyword: str, limit: int = 10) -> List[str]:
        url = 'https://www.reddit.com/search.json'
        params = {
            'q': keyword,
            'limit': max(limit, 1),
            'sort': 'new',
            'restrict_sr': 'false',
            't': 'month'
        }
        if not self._acquire_slot():
            return []

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return []
        finally:
            self._register_request()

        results: List[str] = []
        try:
            for child in data.get('data', {}).get('children', []):
                post = child.get('data', {})
                title = post.get('title')
                if title and isinstance(title, str):
                    results.append(title.strip())
        except Exception:
            return []

        return results

    def collect(self, seeds: Iterable[str], per_seed_limit: int = 5) -> List[Suggestion]:
        collectors: List[Callable[[str], List[str]]] = [
            self.fetch_google_autocomplete,
            self.fetch_google_autocomplete_cn,
            self.fetch_youtube_suggestions,
            self.fetch_reddit_suggestions,
        ]
        if self.serp_api_key:
            collectors.append(self.fetch_people_also_ask)

        if self.max_collectors_per_seed and self.max_collectors_per_seed < len(collectors):
            collectors = collectors[: self.max_collectors_per_seed]

        seeds_cleaned: List[str] = []
        seen_seed_tokens: set[str] = set()
        for raw_seed in seeds:
            if not raw_seed:
                continue
            seed = raw_seed.strip()
            if not seed:
                continue
            seed_key = seed.lower()
            if seed_key in seen_seed_tokens:
                continue
            seen_seed_tokens.add(seed_key)
            seeds_cleaned.append(seed)

        total_seeds = len(seeds_cleaned)
        if self.max_seed_samples and total_seeds > self.max_seed_samples:
            self.logger.info(
                "SuggestionCollector: 种子数 %d 超过上限 %d，将截断处理",
                total_seeds,
                self.max_seed_samples,
            )
            seeds_cleaned = seeds_cleaned[: self.max_seed_samples]

        self._reset_counters(len(seeds_cleaned))

        all_suggestions: List[Suggestion] = []
        seen_terms: Dict[str, str] = {}

        for seed in seeds_cleaned:
            self._stats['seeds_processed'] += 1

            for collector in collectors:
                if self._limit_reached():
                    self.logger.warning(
                        "SuggestionCollector: 达到最大请求数 %s，提前结束收集",
                        self.max_requests,
                    )
                    return all_suggestions

                try:
                    terms = collector(seed)
                except Exception:
                    terms = []

                if not terms:
                    continue

                source_name = collector.__name__.replace('fetch_', '').replace('_', ' ').title()
                self._stats['sources_hit'][source_name] = self._stats['sources_hit'].get(source_name, 0) + 1

                count = 0
                for term in terms:
                    canonical = term.strip()
                    if not canonical:
                        continue
                    lower_term = canonical.lower()
                    if lower_term in seen_terms:
                        continue
                    all_suggestions.append(
                        Suggestion(term=canonical, source=source_name, seed=seed)
                    )
                    seen_terms[lower_term] = source_name
                    count += 1
                    self._stats['suggestions_collected'] += 1
                    if count >= per_seed_limit:
                        break

        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info(
                "SuggestionCollector: 本次收集结束，处理 %d/%d 个种子，发送 %d 次请求，获得 %d 条建议",
                self._stats['seeds_processed'],
                self._stats['seeds_total'],
                self._stats['requests_sent'],
                self._stats['suggestions_collected'],
            )

        return all_suggestions

    def get_last_stats(self) -> Dict[str, Any]:
        """获取最近一次 collect 的统计数据"""
        return dict(self._stats)

    # 内部辅助方法
    def _reset_counters(self, seed_count: int) -> None:
        self._last_request_ts = 0.0
        self._request_count = 0
        self._stats = {
            'seeds_total': seed_count,
            'seeds_processed': 0,
            'requests_sent': 0,
            'sources_hit': {},
            'suggestions_collected': 0,
        }

    def _limit_reached(self) -> bool:
        return bool(self.max_requests and self._request_count >= self.max_requests)

    def _acquire_slot(self) -> bool:
        if self._limit_reached():
            return False

        if self.min_interval > 0 and self._last_request_ts > 0.0:
            elapsed = time.monotonic() - self._last_request_ts
            wait_time = self.min_interval - elapsed
            if wait_time > 0:
                time.sleep(wait_time)
        return True

    def _register_request(self) -> None:
        self._last_request_ts = time.monotonic()
        self._request_count += 1
        self._stats['requests_sent'] = self._request_count

    def _fetch_suggestions(self, url: str, params: Dict[str, str], keyword: str) -> List[str]:
        if not self._acquire_slot():
            return []

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return []
        finally:
            self._register_request()

        # Google suggest API returns list [query, [suggestions...]]
        if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
            return [str(item).strip() for item in data[1] if isinstance(item, str)]

        # Some endpoints return JSONP-like string
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
                if isinstance(parsed, list) and len(parsed) >= 2:
                    return [str(item).strip() for item in parsed[1] if isinstance(item, str)]
            except Exception:
                return []

        return []

    def _load_serp_api_key(self) -> Optional[str]:
        key = os.getenv('SERP_API_KEY')
        if key:
            return key
        try:
            from config.config_manager import get_config

            config = get_config()
            return getattr(config, 'SERP_API_KEY', '') or None
        except Exception:
            return None

    def fetch_people_also_ask(self, keyword: str) -> List[str]:
        if not self.serp_api_key:
            return []

        params = {
            'engine': 'google',
            'q': keyword,
            'api_key': self.serp_api_key,
            'num': 10
        }
        if not self._acquire_slot():
            return []

        try:
            response = self.session.get('https://serpapi.com/search', params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return []
        finally:
            self._register_request()

        questions = data.get('related_questions') or []
        results = []
        for item in questions:
            question = item.get('question') if isinstance(item, dict) else None
            if question and isinstance(question, str):
                cleaned = question.strip()
                if cleaned:
                    results.append(cleaned)
        return results
