import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional, Tuple

try:
    from langdetect import detect
except Exception:
    detect = None

URL_RE = re.compile(r"https?://\S+|www\.[^\s]+", re.IGNORECASE)
MULTISPACE_RE = re.compile(r"\s+")
VALID_CHARS_RE = re.compile(r"[^a-zA-Z0-9\u4e00-\u9fff\s\-_'&+/]", re.UNICODE)


@dataclass
class CleaningConfig:
    target_langs: Tuple[str, ...] = ("en",)
    min_len: int = 3
    max_len: int = 40
    max_words: int = 6
    max_symbol_ratio: float = 0.2
    enable_langdetect: bool = True


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


def is_valid_term(s: str, cfg: Optional[CleaningConfig] = None) -> bool:
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

    if (
        detect
        and cfg.enable_langdetect
        and cfg.target_langs
    ):
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


def clean_terms(terms: List[str], cfg: Optional[CleaningConfig] = None) -> List[str]:
    cfg = cfg or CleaningConfig()
    results = []
    seen = set()
    for t in terms:
        std = standardize_term(t)
        if not is_valid_term(std, cfg):
            continue
        if std in seen:
            continue
        seen.add(std)
        results.append(std)
    return results
