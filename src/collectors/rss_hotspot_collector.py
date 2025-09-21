#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""轻量级 RSS 热点采集器，用于补充热门候选关键词"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests
import pandas as pd


DEFAULT_FEEDS = [
    {
        'url': 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=US',
        'label': 'Google Daily Trends'
    },
    {
        'url': 'https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en',
        'label': 'Google News AI'
    },
    {
        'url': 'https://hnrss.org/newest?points=100',
        'label': 'HackerNews Hot'
    }
]


def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (KeywordRadar/1.0; +https://github.com/find-demand)',
        'Accept': 'application/rss+xml,text/xml,application/xml;q=0.9,*/*;q=0.8'
    })
    return session


@dataclass
class FeedEntry:
    title: str
    source: str
    link: Optional[str] = None


class RSSHotspotCollector:
    """从多个 RSS 源提取热点词条"""

    def __init__(self, feeds: Optional[List[Dict[str, str]]] = None, timeout: int = 8):
        self.feeds = feeds or DEFAULT_FEEDS
        self.session = _build_session()
        self.timeout = timeout

    def collect(self, max_items: int = 30) -> pd.DataFrame:
        entries: List[FeedEntry] = []

        for feed in self.feeds:
            url = feed.get('url')
            label = feed.get('label', 'RSS')
            if not url:
                continue
            entries.extend(self._fetch_feed(url, label, max_items=max_items))

        if not entries:
            return pd.DataFrame(columns=['query', 'source', 'feed_link'])

        records = []
        seen = set()
        for entry in entries:
            title_clean = (entry.title or '').strip()
            if not title_clean:
                continue
            norm = title_clean.lower()
            if norm in seen:
                continue
            records.append({
                'query': title_clean,
                'source': f"RSS/{entry.source}",
                'feed_link': entry.link or ''
            })
            seen.add(norm)
            if len(records) >= max_items:
                break

        return pd.DataFrame(records)

    def _fetch_feed(self, url: str, label: str, max_items: int = 30) -> List[FeedEntry]:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except Exception:
            return []

        try:
            content = response.text
            root = ET.fromstring(content)
        except Exception:
            return []

        entries: List[FeedEntry] = []
        count = 0
        for item in root.findall('.//item'):
            title = item.findtext('title')
            link = item.findtext('link')
            if title:
                entries.append(FeedEntry(title=title, source=label, link=link))
                count += 1
            if count >= max_items:
                break

        return entries
