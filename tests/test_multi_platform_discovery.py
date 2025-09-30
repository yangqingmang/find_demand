import asyncio
from pathlib import Path

import pandas as pd
import pytest
import numpy as np
import sys
import types

from src.demand_mining.tools.multi_platform_keyword_discovery import (
    MultiPlatformKeywordDiscovery,
)


def _install_clustering_stubs(monkeypatch):
    class DummyMinHash:
        def __init__(self, num_perm=64):
            self.values = set()

        def update(self, value):
            self.values.add(value)

    class DummyMinHashLSH:
        def __init__(self, threshold, num_perm=64):
            self._entries = []

        def insert(self, key, mh):
            self._entries.append((key, frozenset(getattr(mh, 'values', set()))))

        def query(self, mh):
            target = frozenset(getattr(mh, 'values', set()))
            matches = []
            for key, values in self._entries:
                if values == target:
                    matches.append(key)
            return matches

    class DummyAgglomerative:
        def __init__(self, **kwargs):
            pass

        def fit_predict(self, data):
            return np.arange(len(data))

    dummy_datasketch = types.SimpleNamespace(MinHash=DummyMinHash, MinHashLSH=DummyMinHashLSH)
    dummy_cluster = types.SimpleNamespace(AgglomerativeClustering=DummyAgglomerative)
    dummy_sklearn = types.SimpleNamespace(cluster=dummy_cluster)

    monkeypatch.setitem(sys.modules, 'datasketch', dummy_datasketch)
    monkeypatch.setitem(sys.modules, 'sklearn', dummy_sklearn)
    monkeypatch.setitem(sys.modules, 'sklearn.cluster', dummy_cluster)

@pytest.fixture
def discovery(tmp_path: Path) -> MultiPlatformKeywordDiscovery:
    tool = MultiPlatformKeywordDiscovery()
    tool.cache_dir = tmp_path / "cache"
    tool.cache_dir.mkdir(parents=True, exist_ok=True)
    tool._cache_enabled = True
    tool.ai_subreddits = ["machinelearning"]
    tool.platforms['producthunt']['enabled'] = False
    return tool


def test_discover_reddit_keywords_uses_cache(monkeypatch, discovery: MultiPlatformKeywordDiscovery):
    fetch_calls = []

    async def fake_fetch_json(session, semaphore, rate_state, method, url, **kwargs):
        fetch_calls.append(url)
        return {
            'data': {
                'children': [
                    {
                        'data': {
                            'title': 'Top AI tools',
                            'selftext': 'Discussion about automation',
                            'score': 42,
                            'num_comments': 12,
                            'permalink': '/r/test/123'
                        }
                    }
                ]
            }
        }

    monkeypatch.setattr(discovery, '_fetch_json', fake_fetch_json)
    monkeypatch.setattr(discovery, '_extract_keywords_from_text', lambda text: ['ai tools'])

    first = discovery.discover_reddit_keywords('MachineLearning', limit=10)
    second = discovery.discover_reddit_keywords('MachineLearning', limit=10)

    assert len(fetch_calls) == 1
    assert first == second
    assert first[0]['keyword'] == 'ai tools'


@pytest.mark.asyncio
async def test_async_discover_all_platforms_merges_results(monkeypatch, discovery: MultiPlatformKeywordDiscovery):
    async def fake_reddit(session, semaphore, rate_state, subreddit, limit):
        await asyncio.sleep(0)
        return [{'keyword': f'{subreddit} trend', 'platform': 'reddit'}]

    async def fake_hn(session, semaphore, rate_state, query, days=30):
        await asyncio.sleep(0)
        return [{'keyword': f'{query} news', 'platform': 'hackernews'}]

    async def fake_youtube(session, semaphore, rate_state, query):
        return [{'keyword': f'{query} youtube', 'platform': 'youtube'}]

    async def fake_google(session, semaphore, rate_state, query):
        return [{'keyword': f'{query} google', 'platform': 'google'}]

    monkeypatch.setattr(discovery, '_discover_reddit_keywords_async', fake_reddit)
    monkeypatch.setattr(discovery, '_discover_hackernews_keywords_async', fake_hn)
    monkeypatch.setattr(discovery, '_discover_youtube_keywords_async', fake_youtube)
    monkeypatch.setattr(discovery, '_discover_google_suggestions_async', fake_google)
    monkeypatch.setattr(discovery, '_post_process_keywords', lambda records: pd.DataFrame(records))

    df = await discovery._async_discover_all_platforms(['alpha ai'])

    assert set(df['platform']) == {'reddit', 'hackernews', 'youtube', 'google'}
    assert 'alpha ai youtube' in df['keyword'].to_list()





def test_post_process_keywords_skips_embeddings_when_disabled(monkeypatch, discovery):
    _install_clustering_stubs(monkeypatch)
    discovery.embedding_enabled = False
    discovery.embedding_min_keywords = 1

    def _fail_get_model():
        raise AssertionError('embedding model should not be requested when disabled')

    monkeypatch.setattr(discovery, '_get_embedding_model', _fail_get_model)

    records = [{'keyword': 'alpha ai tool', 'platform': 'reddit'}]
    df = discovery._post_process_keywords(records)
    assert 'cluster_id' in df.columns


def test_post_process_keywords_respects_embedding_threshold(monkeypatch, discovery):
    _install_clustering_stubs(monkeypatch)
    discovery.embedding_enabled = True
    discovery.embedding_min_keywords = 10

    called = []

    def _record_model_call():
        called.append(True)
        return None

    monkeypatch.setattr(discovery, '_get_embedding_model', _record_model_call)

    records = [{'keyword': f'keyword {i}', 'platform': 'reddit'} for i in range(3)]
    df = discovery._post_process_keywords(records)
    assert 'cluster_id' in df.columns
    assert not called


def test_post_process_keywords_uses_embedding_model_when_threshold_met(monkeypatch, discovery):
    _install_clustering_stubs(monkeypatch)
    discovery.embedding_enabled = True
    discovery.embedding_min_keywords = 2

    class DummyModel:
        def __init__(self):
            self.calls = 0

        def encode(self, texts, normalize_embeddings=True):
            self.calls += 1
            return np.arange(len(texts)).reshape(-1, 1).astype(float)

    model = DummyModel()
    monkeypatch.setattr(discovery, '_get_embedding_model', lambda: model)

    records = [{'keyword': f'keyword {i}', 'platform': 'reddit'} for i in range(4)]
    df = discovery._post_process_keywords(records)

    assert model.calls == 1
    assert 'cluster_id' in df.columns
    assert len(df) <= len(records)
