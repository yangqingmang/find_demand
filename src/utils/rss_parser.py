"""Simple RSS/Atom feed parsing helpers."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, Iterator, Optional

try:
    from dateutil import parser as date_parser
except ImportError:  # pragma: no cover - optional dependency
    date_parser = None


def parse_rss(content: str) -> Iterator[Dict[str, Any]]:
    root = ET.fromstring(content)
    channel = root.find('channel')
    if channel is None:
        return iter(())

    for item in channel.findall('item'):
        yield _parse_item(item)


def _parse_item(item: ET.Element) -> Dict[str, Any]:
    def text_of(tag: str) -> Optional[str]:
        element = item.find(tag)
        if element is not None and element.text:
            return element.text.strip()
        return None

    title = text_of('title') or ''
    link = text_of('link') or ''
    author = text_of('author') or text_of('{http://www.w3.org/2005/Atom}author') or ''
    pub_date_raw = text_of('pubDate') or text_of('{http://www.w3.org/2005/Atom}updated')
    parsed_date: Optional[str] = None
    if pub_date_raw:
        if date_parser:
            try:
                parsed = date_parser.parse(pub_date_raw)
                parsed_date = parsed.isoformat()
            except Exception:
                parsed_date = pub_date_raw
        else:
            parsed_date = pub_date_raw

    return {
        'title': title,
        'link': link,
        'author': author,
        'published': parsed_date,
        'summary': text_of('description') or text_of('{http://www.w3.org/2005/Atom}summary') or '',
        'guid': text_of('guid') or link,
    }
