import os
import re
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List, Optional, Tuple

try:
    from langdetect import detect
except Exception:
    detect = None

URL_RE = re.compile(r"https?://\S+|www\.[^\s]+", re.IGNORECASE)
MULTISPACE_RE = re.compile(r"\s+")
VALID_CHARS_RE = re.compile(r"[^a-zA-Z0-9\s\-_'&+/]", re.UNICODE)


def _default_langdetect_strategy() -> str:
    value = os.getenv('CLEANING_LANGDETECT_STRATEGY', 'auto')
    return value.strip().lower() or 'auto'


def _default_langdetect_threshold() -> int:
    raw = os.getenv('CLEANING_LANGDETECT_THRESHOLD')
    try:
        parsed = int(raw)
        return parsed if parsed >= 0 else 0
    except (TypeError, ValueError):
        return 200


def _default_cache_enabled() -> bool:
    raw = os.getenv('CLEANING_CACHE_ENABLED')
    if raw is None:
        return True
    return raw.strip().lower() not in {'0', 'false', 'no', 'off'}


@dataclass
class CleaningConfig:
    target_langs: Tuple[str, ...] = ("en",)
    min_len: int = 3
    max_len: int = 40
    max_words: int = 6
    max_symbol_ratio: float = 0.2
    enable_langdetect: bool = True
    allow_only_ascii: bool = True
    langdetect_strategy: str = field(default_factory=_default_langdetect_strategy)
    langdetect_batch_threshold: int = field(default_factory=_default_langdetect_threshold)
    cache_enabled: bool = field(default_factory=_default_cache_enabled)


@lru_cache(maxsize=4096)
def _detect_lang_cached(text: str) -> Optional[str]:
    if not detect:
        return None
    try:
        return detect(text)
    except Exception:
        return None


def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.strip()
    s = URL_RE.sub(" ", s)
    s = s.replace("\u200b", " ")
    s = re.sub(r"[\t\r\n]", " ", s)
    s = MULTISPACE_RE.sub(" ", s)
    return s


_CLEAN_RESULT_CACHE_MAX = 8192
_clean_result_cache: "OrderedDict[Tuple, Tuple[bool, Optional[str]]]" = OrderedDict()


def clear_cleaning_cache() -> None:
    """Clear memoized cleaning results (useful for tests)."""
    _clean_result_cache.clear()


def is_valid_term(
    s: str,
    cfg: Optional[CleaningConfig] = None,
    *,
    langdetect_enabled: Optional[bool] = None
) -> bool:
    cfg = cfg or CleaningConfig()

    if not s:
        return False
    if len(s) < cfg.min_len or len(s) > cfg.max_len:
        return False
    if len(s.split()) > cfg.max_words:
        return False
    sym_ratio = sum(1 for c in s if not c.isalnum() and not c.isspace()) / max(len(s), 1)
    if sym_ratio > cfg.max_symbol_ratio:
        return False

    if cfg.allow_only_ascii and not _is_ascii_str(s):
        return False

    should_detect = detect and (langdetect_enabled if langdetect_enabled is not None else cfg.enable_langdetect)
    if should_detect and cfg.target_langs:
        lang = _detect_lang_cached(s)
        if lang and lang not in cfg.target_langs:
            return False

    return True


def standardize_term(s: str) -> str:
    s = normalize_text(s)
    s = s.lower()
    s = VALID_CHARS_RE.sub(" ", s)
    s = MULTISPACE_RE.sub(" ", s).strip()
    return s


def _normalized_strategy(strategy: str) -> str:
    strategy = (strategy or 'auto').strip().lower()
    if strategy not in {'auto', 'always', 'disabled'}:
        return 'auto'
    return strategy


def _should_use_langdetect(cfg: CleaningConfig, term_count: int) -> bool:
    if not cfg.enable_langdetect:
        return False
    if not detect or not cfg.target_langs:
        return False

    strategy = _normalized_strategy(getattr(cfg, 'langdetect_strategy', 'auto'))
    if strategy == 'disabled':
        return False
    if strategy == 'always':
        return True

    threshold = getattr(cfg, 'langdetect_batch_threshold', 0)
    try:
        threshold = int(threshold)
    except (TypeError, ValueError):
        threshold = 0

    if threshold <= 0:
        return True
    return term_count <= threshold


def _make_cache_key(term: str, cfg: CleaningConfig, langdetect_enabled: bool) -> Tuple:
    return (
        term,
        cfg.min_len,
        cfg.max_len,
        cfg.max_words,
        round(cfg.max_symbol_ratio, 4),
        tuple(cfg.target_langs),
        cfg.allow_only_ascii,
        langdetect_enabled,
    )


def _cache_get(key: Tuple) -> Optional[Tuple[bool, Optional[str]]]:
    if key not in _clean_result_cache:
        return None
    value = _clean_result_cache[key]
    _clean_result_cache.move_to_end(key)
    return value


def _cache_set(key: Tuple, value: Tuple[bool, Optional[str]]) -> None:
    _clean_result_cache[key] = value
    _clean_result_cache.move_to_end(key)
    if len(_clean_result_cache) > _CLEAN_RESULT_CACHE_MAX:
        _clean_result_cache.popitem(last=False)


def clean_terms(terms: List[str], cfg: Optional[CleaningConfig] = None) -> List[str]:
    cfg = cfg or CleaningConfig()
    if not terms:
        return []

    results: List[str] = []
    seen = set()
    cache_enabled = bool(getattr(cfg, 'cache_enabled', True))
    use_langdetect = _should_use_langdetect(cfg, len(terms))

    for t in terms:
        if t is None:
            continue
        original = str(t)
        if not original.strip():
            continue

        cache_key = None
        cached_result: Optional[Tuple[bool, Optional[str]]] = None
        if cache_enabled:
            cache_key = _make_cache_key(original, cfg, use_langdetect)
            cached_result = _cache_get(cache_key)

        if cached_result is not None:
            is_valid, cleaned = cached_result
            if not is_valid or not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            results.append(cleaned)
            continue

        std = standardize_term(original)
        if not std:
            if cache_enabled and cache_key is not None:
                _cache_set(cache_key, (False, None))
            continue

        if not is_valid_term(std, cfg, langdetect_enabled=use_langdetect):
            if cache_enabled and cache_key is not None:
                _cache_set(cache_key, (False, None))
            continue

        if std in seen:
            if cache_enabled and cache_key is not None:
                _cache_set(cache_key, (True, std))
            continue

        seen.add(std)
        results.append(std)

        if cache_enabled and cache_key is not None:
            _cache_set(cache_key, (True, std))

    return results


def _is_ascii_str(text: str) -> bool:
    try:
        text.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False
