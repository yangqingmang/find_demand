"""Workflow-level cache manager for --all pipeline resume support."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _json_default(value: Any):  # pragma: no cover - helper for complex objects
    if isinstance(value, set):
        return list(value)
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


class WorkflowCacheManager:
    """Manages persisted stage outputs for the --all workflow."""

    STAGE_TRENDING = "trending_keywords"
    STAGE_HOT_ANALYSIS = "hot_keyword_analysis"
    STAGE_DISCOVERY = "multi_platform_discovery"

    def __init__(
        self,
        cache_dir: Path,
        *,
        enabled: bool = True,
        ttl_hours: Optional[float] = 12.0,
        verbose: bool = False,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.enabled = bool(enabled)
        self.verbose = verbose
        self.ttl_seconds: Optional[float]
        if ttl_hours is None:
            self.ttl_seconds = None
        else:
            try:
                ttl_hours_float = float(ttl_hours)
            except (TypeError, ValueError):
                ttl_hours_float = 0.0
            self.ttl_seconds = max(ttl_hours_float * 3600.0, 0.0) if ttl_hours_float > 0 else None

        self.state_path = self.cache_dir / "state.json"
        self._state: Dict[str, Any] = {"stages": {}, "created_at": _utc_timestamp()}

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_state()
            self._purge_expired()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _log(self, message: str) -> None:
        if self.verbose:
            print(f"[WorkflowCache] {message}")

    def _stage_file(self, stage: str) -> Path:
        return self.cache_dir / f"{stage}.json"

    def _load_state(self) -> None:
        if not self.state_path.exists():
            return
        try:
            with self.state_path.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
            if isinstance(payload, dict):
                self._state.update(payload)
        except Exception as exc:  # pragma: no cover - corrupt state fallback
            self._log(f"Failed to load state.json: {exc}")

    def _save_state(self) -> None:
        try:
            with self.state_path.open("w", encoding="utf-8") as fh:
                json.dump(self._state, fh, ensure_ascii=False, indent=2)
        except Exception as exc:  # pragma: no cover - disk issues
            self._log(f"Failed to persist state.json: {exc}")

    def _is_expired(self, path: Path) -> bool:
        if self.ttl_seconds is None:
            return False
        try:
            age = time.time() - path.stat().st_mtime
        except FileNotFoundError:
            return True
        return age > self.ttl_seconds

    def _purge_expired(self) -> None:
        stages = dict(self._state.get("stages", {}))
        changed = False
        for stage, metadata in stages.items():
            path = self._stage_file(stage)
            if not path.exists() or self._is_expired(path):
                if path.exists():
                    try:
                        path.unlink()
                    except OSError:
                        pass
                self._state["stages"].pop(stage, None)
                changed = True
        if changed:
            self._save_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def clear_all(self) -> None:
        if not self.enabled:
            return
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir, ignore_errors=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._state = {"stages": {}, "created_at": _utc_timestamp()}
        self._save_state()
        self._log("Cache directory cleared")

    def clear_stage(self, stage: str) -> None:
        if not self.enabled:
            return
        path = self._stage_file(stage)
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass
        self._state.get("stages", {}).pop(stage, None)
        self._save_state()

    def store_stage(self, stage: str, payload: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        record = {"cached_at": _utc_timestamp(), "payload": payload}
        path = self._stage_file(stage)
        try:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(record, fh, ensure_ascii=False, indent=2, default=_json_default)
            self._state.setdefault("stages", {})[stage] = {
                "path": path.name,
                "cached_at": record["cached_at"],
            }
            self._save_state()
            self._log(f"Stage '{stage}' stored -> {path}")
        except Exception as exc:  # pragma: no cover - disk issues
            self._log(f"Failed to store stage '{stage}': {exc}")

    def load_stage(self, stage: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        path = self._stage_file(stage)
        if not path.exists():
            return None
        if self._is_expired(path):
            self._log(f"Stage '{stage}' expired; removing")
            self.clear_stage(stage)
            return None
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                raise ValueError("invalid stage payload")
            data.setdefault("cached_at", _utc_timestamp())
            return data
        except Exception as exc:
            self._log(f"Failed to load stage '{stage}': {exc}")
            self.clear_stage(stage)
            return None

    def has_stage(self, stage: str) -> bool:
        return self.load_stage(stage) is not None

    def list_stages(self) -> Dict[str, Any]:
        return dict(self._state.get("stages", {})) if self.enabled else {}

