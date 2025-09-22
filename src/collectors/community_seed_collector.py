#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""社区与产品发布平台种子采集器."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests

try:
    from langdetect import detect, DetectorFactory  # type: ignore
    from langdetect.lang_detect_exception import LangDetectException  # type: ignore
    DetectorFactory.seed = 42
except Exception:  # pragma: no cover - langdetect may不可用
    detect = None
    LangDetectException = Exception  # type: ignore


@dataclass
class RateLimitInfo:
    """记录接口的限流信息."""

    remaining: Optional[float] = None
    used: Optional[float] = None
    reset_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'remaining': self.remaining,
            'used': self.used,
            'reset_seconds': self.reset_seconds,
        }


@dataclass
class SourceSnapshot:
    """单个数据源的灰度验证快照."""

    source: str
    attempted: int = 0
    succeeded: int = 0
    failed: int = 0
    notes: List[str] = field(default_factory=list)
    rate_limit: Optional[RateLimitInfo] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            'source': self.source,
            'attempted': self.attempted,
            'succeeded': self.succeeded,
            'failed': self.failed,
            'notes': self.notes,
            'extra': self.extra,
        }
        if self.rate_limit:
            payload['rate_limit'] = self.rate_limit.to_dict()
        return payload


def _detect_language(text: str) -> Optional[str]:
    """使用 langdetect 识别语言，失败时返回 None."""
    if not text:
        return None
    if detect is None:
        return None
    try:
        return detect(text)
    except LangDetectException:
        return None
    except Exception:
        return None


class RedditSeedCollector:
    """基于公开 JSON 接口的 Reddit 热帖采集器."""

    DEFAULT_SUBREDDITS = [
        'Futurology',
        'Entrepreneur',
        'technology',
        'startups',
        'SaaS',
        'ArtificialInteligence',
        'MachineLearning',
        'AI_Startup_Ideas'
    ]

    def __init__(
        self,
        subreddits: Optional[List[str]] = None,
        limit_per_subreddit: int = 12,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.subreddits = subreddits or self.DEFAULT_SUBREDDITS
        self.limit_per_subreddit = max(limit_per_subreddit, 1)
        self.session = session or self._build_session()

    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'find-demand-bot/1.0 (https://github.com/find-demand)',
            'Accept': 'application/json, text/plain, */*',
        })
        return session

    def collect(self) -> Tuple[pd.DataFrame, SourceSnapshot]:
        records: List[Dict[str, Any]] = []
        snapshot = SourceSnapshot(source='reddit', attempted=0, succeeded=0, failed=0)

        for subreddit in self.subreddits:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json"
            params = {
                'limit': self.limit_per_subreddit,
                't': 'day'
            }
            snapshot.attempted += 1
            try:
                response = self.session.get(url, params=params, timeout=8)
                if response.status_code == 429:
                    snapshot.failed += 1
                    snapshot.notes.append(f"429 for r/{subreddit}")
                    rate_info = self._parse_rate_limit(response)
                    if rate_info:
                        snapshot.rate_limit = rate_info
                    continue
                response.raise_for_status()
                data = response.json()
                children = data.get('data', {}).get('children', [])
                for child in children:
                    payload = child.get('data', {})
                    title = (payload.get('title') or '').strip()
                    if not title:
                        continue
                    permalink = payload.get('permalink') or ''
                    link = f"https://www.reddit.com{permalink}" if permalink else (payload.get('url') or '')
                    language = _detect_language(title)
                    record = {
                        'query': title,
                        'source': f"Community/Reddit/r/{subreddit}",
                        'origin': 'reddit',
                        'language': language,
                        'link': link,
                        'score': payload.get('score'),
                        'created_utc': payload.get('created_utc'),
                    }
                    records.append(record)
                snapshot.succeeded += 1
                rate_info = self._parse_rate_limit(response)
                if rate_info:
                    snapshot.rate_limit = rate_info
            except Exception as exc:
                snapshot.failed += 1
                snapshot.notes.append(f"{subreddit}: {exc}")

        df = pd.DataFrame(records)
        if 'created_utc' in df.columns and not df.empty:
            df['created_iso'] = df['created_utc'].apply(self._to_iso_utc)
        return df, snapshot

    @staticmethod
    def _parse_rate_limit(response: requests.Response) -> Optional[RateLimitInfo]:
        try:
            remaining = response.headers.get('x-ratelimit-remaining')
            used = response.headers.get('x-ratelimit-used')
            reset = response.headers.get('x-ratelimit-reset')
            if remaining is None and used is None and reset is None:
                return None
            return RateLimitInfo(
                remaining=float(remaining) if remaining is not None else None,
                used=float(used) if used is not None else None,
                reset_seconds=float(reset) if reset is not None else None,
            )
        except Exception:
            return None

    @staticmethod
    def _to_iso_utc(value: Any) -> Optional[str]:
        if value in (None, ''):
            return None
        try:
            ts = float(value)
        except (TypeError, ValueError):
            return None
        return datetime.utcfromtimestamp(ts).isoformat() + 'Z'


class ProductHuntSeedCollector:
    """使用RSS源的 Product Hunt 热门项目采集器."""

    FEED_URL = 'https://www.producthunt.com/feed'

    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session or self._build_session()

    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'find-demand-bot/1.0 (https://github.com/find-demand)',
            'Accept': 'application/rss+xml, application/xml;q=0.9, */*;q=0.8',
        })
        return session

    def collect(self, limit: int = 30) -> Tuple[pd.DataFrame, SourceSnapshot]:
        snapshot = SourceSnapshot(source='product_hunt', attempted=1)
        try:
            response = self.session.get(self.FEED_URL, timeout=8)
            snapshot.extra['status_code'] = response.status_code
            if response.status_code == 429:
                snapshot.failed = 1
                snapshot.notes.append('429 rate limited')
                return pd.DataFrame(columns=['query', 'source']), snapshot
            response.raise_for_status()
        except Exception as exc:
            snapshot.failed = 1
            snapshot.notes.append(str(exc))
            return pd.DataFrame(columns=['query', 'source']), snapshot

        entries = self._parse_rss_entries(response.text, limit)
        if not entries:
            snapshot.succeeded = 1
            snapshot.notes.append('no entries parsed')
            return pd.DataFrame(columns=['query', 'source']), snapshot

        records: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for entry in entries:
            title = (entry.get('title') or '').strip()
            if not title:
                continue
            normalized = title.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            language = _detect_language(title)
            records.append({
                'query': title,
                'source': 'Community/ProductHunt',
                'origin': 'product_hunt',
                'language': language,
                'link': entry.get('link') or '',
                'published': entry.get('published') or '',
            })
        snapshot.succeeded = 1
        snapshot.extra['item_count'] = len(records)
        return pd.DataFrame(records), snapshot

    @staticmethod
    def _parse_rss_entries(content: str, limit: int) -> List[Dict[str, Any]]:
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(content)
        except Exception:
            return []

        entries: List[Dict[str, Any]] = []
        for item in root.findall('.//item'):
            entry = {
                'title': item.findtext('title'),
                'link': item.findtext('link'),
                'published': item.findtext('pubDate'),
            }
            entries.append(entry)
            if len(entries) >= limit:
                break
        return entries


class CommunitySeedCollector:
    """整合 Reddit 与 Product Hunt 的社区种子采集器."""

    def __init__(
        self,
        reddit_collector: Optional[RedditSeedCollector] = None,
        product_hunt_collector: Optional[ProductHuntSeedCollector] = None,
    ) -> None:
        self.reddit_collector = reddit_collector or RedditSeedCollector()
        self.product_hunt_collector = product_hunt_collector or ProductHuntSeedCollector()

    def collect(self, max_items: int = 50) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        frames: List[pd.DataFrame] = []
        diagnostics: Dict[str, Any] = {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'sources': []
        }

        reddit_df, reddit_snapshot = self.reddit_collector.collect()
        diagnostics['sources'].append(reddit_snapshot.to_dict())
        if not reddit_df.empty:
            frames.append(reddit_df)

        ph_df, ph_snapshot = self.product_hunt_collector.collect(limit=max_items)
        diagnostics['sources'].append(ph_snapshot.to_dict())
        if not ph_df.empty:
            frames.append(ph_df)

        if not frames:
            diagnostics['total_candidates'] = 0
            return pd.DataFrame(columns=['query', 'source']), diagnostics

        combined = pd.concat(frames, ignore_index=True)
        combined = combined.dropna(subset=['query'])
        combined['query'] = combined['query'].astype(str).str.strip()
        combined = combined[combined['query'] != '']
        combined = combined.drop_duplicates(subset=['query'], keep='first')
        if max_items > 0:
            combined = combined.head(max_items)

        diagnostics['total_candidates'] = int(len(combined))
        diagnostics['sample_queries'] = combined['query'].head(10).tolist()
        return combined, diagnostics

    @staticmethod
    def to_graylog_payload(metrics: Dict[str, Any], extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            'generated_at': metrics.get('generated_at'),
            'total_candidates': metrics.get('total_candidates'),
            'sources': metrics.get('sources'),
        }
        if extra:
            payload.update(extra)
        return payload


__all__ = [
    'CommunitySeedCollector',
    'ProductHuntSeedCollector',
    'RedditSeedCollector',
    'RateLimitInfo',
    'SourceSnapshot',
]
