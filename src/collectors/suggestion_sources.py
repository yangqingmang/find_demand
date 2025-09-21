#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单的多源联想词/热词采集器"""

from __future__ import annotations

import json
import time
import os
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional

import requests


DEFAULT_TIMEOUT = 8


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

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.session = _build_session()
        self.timeout = timeout
        self.serp_api_key = self._load_serp_api_key()

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
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return []

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

        all_suggestions: List[Suggestion] = []
        seen_terms: Dict[str, str] = {}

        for raw_seed in seeds:
            if not raw_seed:
                continue
            seed = raw_seed.strip()
            if not seed:
                continue

            for collector in collectors:
                try:
                    terms = collector(seed)
                except Exception:
                    terms = []

                if not terms:
                    continue

                source_name = collector.__name__.replace('fetch_', '').replace('_', ' ').title()

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
                    if count >= per_seed_limit:
                        break
                time.sleep(0.2)

        return all_suggestions

    def _fetch_suggestions(self, url: str, params: Dict[str, str], keyword: str) -> List[str]:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return []

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
        try:
            response = self.session.get('https://serpapi.com/search', params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return []

        questions = data.get('related_questions') or []
        results = []
        for item in questions:
            question = item.get('question') if isinstance(item, dict) else None
            if question and isinstance(question, str):
                cleaned = question.strip()
                if cleaned:
                    results.append(cleaned)
        return results
