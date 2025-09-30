from __future__ import annotations

import pytest

from src.pipeline.cleaning import cleaner


@pytest.fixture(autouse=True)
def _reset_cleaning_cache():
    cleaner.clear_cleaning_cache()
    yield
    cleaner.clear_cleaning_cache()


def test_clean_terms_disables_langdetect_in_large_batches(monkeypatch):
    calls = []

    def fake_detect(text: str):
        calls.append(text)
        return "en"

    monkeypatch.setattr(cleaner, "detect", lambda text: "en")
    monkeypatch.setattr(cleaner, "_detect_lang_cached", fake_detect)

    cfg = cleaner.CleaningConfig(
        enable_langdetect=True,
        langdetect_strategy='auto',
        langdetect_batch_threshold=2,
    )

    terms = ["Alpha AI", "Beta tool", "Gamma app"]
    cleaned = cleaner.clean_terms(terms, cfg)

    assert len(cleaned) == 3
    assert calls == []  # langdetect should be skipped when batch exceeds threshold


def test_clean_terms_uses_cache_to_skip_reprocessing(monkeypatch):
    calls = []

    def fake_standardize(value: str) -> str:
        calls.append(value)
        return value.strip().lower()

    monkeypatch.setattr(cleaner, "standardize_term", fake_standardize)

    cfg = cleaner.CleaningConfig(enable_langdetect=False, cache_enabled=True)
    terms = ["Alpha", "Beta"]

    first = cleaner.clean_terms(terms, cfg)
    assert first == ['alpha', 'beta']
    assert calls == ["Alpha", "Beta"]

    calls.clear()
    second = cleaner.clean_terms(terms, cfg)
    assert second == ['alpha', 'beta']
    assert calls == []  # cached results avoid redundant standardization
