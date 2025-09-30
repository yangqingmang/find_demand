from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pandas as pd
import pytest

from src.demand_mining.managers.keyword_manager import KeywordManager


class DummyIntentAnalyzer:
    def __init__(self):
        self.calls = []

    def analyze_keywords(self, df: pd.DataFrame):
        queries = list(df['query'])
        self.calls.append(queries)
        results = []
        for query in queries:
            results.append({
                'query': query,
                'intent_primary': 'I',
                'intent_secondary': 'N',
                'probability': 0.82,
                'website_recommendations': {
                    'website_type': 'guide',
                    'ai_tool_category': 'General',
                    'domain_suggestions': [f"{query.replace(' ', '')}.com"],
                    'monetization_strategy': ['ads'],
                    'technical_requirements': ['static'],
                    'competition_analysis': {},
                    'development_priority': {},
                    'content_strategy': []
                }
            })
        return {'results': results, 'summary': {'total_keywords': len(results)}}


class DummyMarketAnalyzer:
    def __init__(self):
        self.calls = []

    def analyze_market_data(self, keywords):
        keyword_list = list(keywords)
        self.calls.append(keyword_list)
        return {
            keyword: {
                'search_volume': 1200 + idx * 10,
                'competition': 0.3,
                'cpc': 1.25,
                'trend': 'stable',
                'seasonality': 'low',
                'execution_cost': 0.2
            }
            for idx, keyword in enumerate(keyword_list)
        }


def _build_manager(tmp_path: Path, enable_cache: bool) -> KeywordManager:
    manager = KeywordManager()
    manager.intent_batch_size = 50
    manager.market_batch_size = 50
    manager._intent_analyzer = DummyIntentAnalyzer()
    manager._market_analyzer = DummyMarketAnalyzer()
    manager._serp_analyzer = False  # Skip SERP lookups during tests

    manager.intent_cache = {}
    manager.market_cache = {}
    manager._cache_dirty = {'intent': False, 'market': False}

    manager._cache_enabled = enable_cache
    if enable_cache:
        manager.cache_ttl = timedelta(hours=12)
        manager.cache_dir = tmp_path / 'keyword_cache'
        manager.intent_cache_path = manager.cache_dir / 'intent_cache.json'
        manager.market_cache_path = manager.cache_dir / 'market_cache.json'
    else:
        manager.cache_ttl = None

    return manager


def test_perform_analysis_batches_and_preserves_order(tmp_path: Path):
    manager = _build_manager(tmp_path, enable_cache=False)

    raw_keywords = [" alpha ai tool ", "beta analyzer", "alpha ai tool"]
    results = manager._perform_analysis(raw_keywords)

    assert [kw['keyword'] for kw in results['keywords']] == [
        "alpha ai tool",
        "beta analyzer",
        "alpha ai tool",
    ]

    assert len(manager._intent_analyzer.calls) == 1
    assert manager._intent_analyzer.calls[0] == ["alpha ai tool", "beta analyzer"]

    assert len(manager._market_analyzer.calls) == 1
    assert manager._market_analyzer.calls[0] == ["alpha ai tool", "beta analyzer"]

    summary = results['processing_summary']
    assert summary['intent_computed'] == 2
    assert summary['market_computed'] == 2
    assert summary['intent_cache_hits'] == 0
    assert summary['market_cache_hits'] == 0
    assert summary['analysis_dataframe_rows'] == len(results['keywords'])
    assert summary['analysis_duplicates'] == 1

    first_entry = results['keywords'][0]
    duplicate_entry = results['keywords'][2]
    assert first_entry['keyword'] == duplicate_entry['keyword']
    assert first_entry['intent'] == duplicate_entry['intent']
    assert first_entry['market'] == duplicate_entry['market']


def test_keyword_analysis_caching_hits_reduce_computation(tmp_path: Path):
    manager = _build_manager(tmp_path, enable_cache=True)

    keywords = ["pricing automation", "content generator"]

    first_results = manager._perform_analysis(keywords)
    assert len(manager._intent_analyzer.calls) == 1
    assert len(manager._market_analyzer.calls) == 1

    manager._intent_analyzer.calls.clear()
    manager._market_analyzer.calls.clear()

    second_results = manager._perform_analysis(keywords)

    assert manager._intent_analyzer.calls == []
    assert manager._market_analyzer.calls == []

    summary = second_results['processing_summary']
    assert summary['intent_cache_hits'] == 2
    assert summary['market_cache_hits'] == 2
    assert summary['analysis_dataframe_rows'] == len(second_results['keywords'])
    assert summary['analysis_duplicates'] == 0

    # 缓存应当落盘，方便跨进程复用
    assert manager.intent_cache_path.exists()
    assert manager.market_cache_path.exists()

    with manager.intent_cache_path.open('r', encoding='utf-8') as fh:
        payload = json.load(fh)
    assert set(payload.keys()) == set(keywords)
