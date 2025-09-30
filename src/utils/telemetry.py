"""Lightweight telemetry manager collecting workflow metrics and request statistics."""

from __future__ import annotations

import json
import threading
import time
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


@dataclass
class _StageToken:
    name: str
    started_at: float
    metadata: Dict[str, Any]
    started_iso: str
    finished: bool = False


class TelemetryManager:
    """Collects telemetry counters and stage durations for the workflow."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reset()

    def reset(self, run_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        with self._lock:
            now = _utc_now_iso()
            self._session_started = time.perf_counter()
            self._data: Dict[str, Any] = {
                "run_id": run_id or now,
                "session_started_at": now,
                "metadata": metadata or {},
                "metrics": {
                    "stages": {},
                    "counters": {},
                    "gauges": {},
                    "requests": {
                        "total": 0,
                        "errors": 0,
                        "rate_limited": 0,
                        "by_host": {},
                        "by_status": {},
                    },
                    "events": [],
                },
            }

    # ------------------------------------------------------------------
    # Stage helpers
    # ------------------------------------------------------------------
    def start_stage(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> _StageToken:
        return _StageToken(name=name, started_at=time.perf_counter(), metadata=metadata or {}, started_iso=_utc_now_iso())

    def _finalise_stage(
        self,
        token: _StageToken,
        status: str,
        extra: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        if token.finished:
            return
        token.finished = True
        duration = max(time.perf_counter() - token.started_at, 0.0)

        with self._lock:
            stages = self._data["metrics"]["stages"]
            stage_entry = stages.setdefault(
                token.name,
                {
                    "count": 0,
                    "total_duration": 0.0,
                    "failures": 0,
                    "max_duration": 0.0,
                },
            )

            stage_entry["count"] += 1
            stage_entry["total_duration"] += duration
            stage_entry["max_duration"] = max(stage_entry["max_duration"], duration)
            stage_entry["avg_duration"] = stage_entry["total_duration"] / stage_entry["count"]

            stage_entry["last_started_at"] = token.started_iso
            stage_entry["last_duration"] = duration
            stage_entry["last_status"] = status
            if token.metadata:
                stage_entry["last_metadata"] = token.metadata
            if extra:
                stage_entry["last_payload"] = extra
            if error:
                stage_entry["last_error"] = error

            if status != "completed":
                stage_entry["failures"] += 1

    def end_stage(
        self,
        token: _StageToken,
        *,
        status: str = "completed",
        extra: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        self._finalise_stage(token, status=status, extra=extra, error=error)

    @contextmanager
    def stage(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        token = self.start_stage(name, metadata)
        try:
            yield token
            self._finalise_stage(token, status="completed")
        except Exception as exc:  # pragma: no cover - passthrough
            self._finalise_stage(token, status="failed", error=str(exc))
            raise

    # ------------------------------------------------------------------
    # Counter & gauge helpers
    # ------------------------------------------------------------------
    def increment_counter(self, key: str, amount: int = 1) -> None:
        with self._lock:
            counters = self._data["metrics"]["counters"]
            counters[key] = counters.get(key, 0) + amount

    def set_gauge(self, key: str, value: Any) -> None:
        with self._lock:
            gauges = self._data["metrics"]["gauges"]
            gauges[key] = value

    # ------------------------------------------------------------------
    # Request helpers
    # ------------------------------------------------------------------
    def record_request(
        self,
        *,
        host: str,
        method: str,
        url: str,
        status: Optional[int],
        ok: bool,
        elapsed: Optional[float] = None,
    ) -> None:
        with self._lock:
            metrics = self._data["metrics"]["requests"]
            metrics["total"] += 1

            if not ok:
                metrics["errors"] += 1
            if status is not None:
                status_key = str(status)
                by_status = metrics["by_status"]
                status_entry = by_status.setdefault(status_key, {"count": 0, "errors": 0})
                status_entry["count"] += 1
                if not ok:
                    status_entry["errors"] += 1
                if status == 429:
                    metrics["rate_limited"] += 1

            host_entry = metrics["by_host"].setdefault(
                host or "unknown",
                {"total": 0, "errors": 0, "rate_limited": 0, "latency_sum": 0.0},
            )
            host_entry["total"] += 1
            if not ok:
                host_entry["errors"] += 1
            if status == 429:
                host_entry["rate_limited"] += 1
            if elapsed is not None:
                host_entry["latency_sum"] += max(elapsed, 0.0)

            # store last request preview for quick debugging
            metrics["last_request"] = {
                "host": host,
                "method": method,
                "url": url,
                "status": status,
                "ok": ok,
                "elapsed": elapsed,
                "timestamp": _utc_now_iso(),
            }

    # ------------------------------------------------------------------
    # Event helpers
    # ------------------------------------------------------------------
    def log_event(self, category: str, message: str, payload: Optional[Dict[str, Any]] = None) -> None:
        with self._lock:
            self._data["metrics"]["events"].append(
                {
                    "timestamp": _utc_now_iso(),
                    "category": category,
                    "message": message,
                    "payload": payload or {},
                }
            )

    # ------------------------------------------------------------------
    # Snapshot helpers
    # ------------------------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            data = deepcopy(self._data)
        uptime = max(time.perf_counter() - self._session_started, 0.0)
        data["uptime_seconds"] = uptime

        # compute average latency per host when data available
        for host_entry in data["metrics"]["requests"].get("by_host", {}).values():
            total = host_entry.get("total", 0)
            latency_sum = host_entry.pop("latency_sum", 0.0)
            if total > 0:
                host_entry["avg_latency"] = latency_sum / total
            else:
                host_entry["avg_latency"] = 0.0
        data["captured_at"] = _utc_now_iso()
        return data

    def write_snapshot(self, output_path: Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.snapshot()
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        return output_path


# Shared singleton used across modules
telemetry_manager = TelemetryManager()

