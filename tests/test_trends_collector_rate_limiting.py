from __future__ import annotations

import time

import pandas as pd
import pytest

import src.collectors.trends_collector as trends_collector_module


class _StubTrendsCollector:
    def __init__(self):
        self._callback = None
        self.related_calls = 0

    def set_rate_limit_callback(self, callback):
        self._callback = callback

    # 以下方法满足 TrendsCollector 使用需求
    def build_payload(self, *args, **kwargs):
        return None

    def related_queries(self, *args, **kwargs):
        self.related_calls += 1
        return {'stub': {'top': pd.DataFrame(), 'rising': pd.DataFrame()}}

    def get_related_topics(self, *args, **kwargs):
        return {}

    def suggestions(self, *args, **kwargs):
        return []

    def trending_searches(self, *args, **kwargs):
        return pd.DataFrame()

    def interest_by_region(self, *args, **kwargs):
        return pd.DataFrame()

    def get_historical_interest(self, *args, **kwargs):
        return pd.DataFrame()

    def get_keyword_trends(self, *args, **kwargs):
        return pd.DataFrame()

    def trigger_rate_limit(self, penalty: float, severity: str = 'high'):
        if self._callback:
            self._callback(penalty, severity)


@pytest.fixture
def stubbed_trends_collector(monkeypatch):
    monkeypatch.setattr(
        trends_collector_module,
        'CustomTrendsCollector',
        _StubTrendsCollector,
    )
    collector = trends_collector_module.TrendsCollector()
    assert isinstance(collector.trends_collector, _StubTrendsCollector)
    return collector


def test_related_queries_skipped_during_cooldown(monkeypatch, stubbed_trends_collector):
    collector = stubbed_trends_collector
    stub = collector.trends_collector

    collector._start_cooldown(2.0)
    result = collector.get_related_queries('keyword')

    assert result == {}
    assert stub.related_calls == 0


def test_rate_limit_callback_sets_cooldown(monkeypatch, stubbed_trends_collector):
    collector = stubbed_trends_collector
    stub = collector.trends_collector

    assert not collector.is_in_cooldown()
    stub.trigger_rate_limit(1.0, 'high')

    assert collector.is_in_cooldown()
    time.sleep(1.05)
    assert not collector.is_in_cooldown()
