"""Utility to aggregate latest demand mining outputs into a dashboard-friendly JSON payload."""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.utils.file_utils import ensure_directory_exists


@dataclass
class AnalysisFiles:
    analysis: Optional[Path]
    discovered: Optional[Path]

    @property
    def available(self) -> bool:
        return self.analysis is not None


def _find_latest_file(directory: Path, pattern: str) -> Optional[Path]:
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_discovered_keywords(path: Path, limit: int = 50) -> List[str]:
    keywords: List[str] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                keyword = (row.get("keyword") or row.get("query") or "").strip()
                if keyword:
                    keywords.append(keyword)
                if len(keywords) >= limit:
                    break
    except Exception:
        pass
    return keywords


def _parse_analysis_time(raw: Optional[str], fallback: datetime) -> Tuple[str, datetime]:
    if not raw:
        return fallback.isoformat(), fallback
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        dt = fallback
    return dt.isoformat(), dt


def _build_opportunity_segments(keywords: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    segments: Dict[str, Dict[str, Any]] = {
        "high": {"count": 0, "sample": []},
        "medium": {"count": 0, "sample": []},
        "low": {"count": 0, "sample": []},
    }
    for kw in keywords:
        score = float(kw.get("opportunity_score", 0))
        bucket = "high" if score >= 70 else "medium" if score >= 40 else "low"
        seg = segments[bucket]
        seg["count"] += 1
        if len(seg["sample"]) < 12:
            seg["sample"].append({
                "keyword": kw.get("keyword", ""),
                "score": score,
                "search_volume": kw.get("market", {}).get("search_volume"),
                "competition": kw.get("market", {}).get("competition"),
            })
    return segments


def _build_top_keywords(keywords: Iterable[Dict[str, Any]], limit: int = 15) -> List[Dict[str, Any]]:
    sorted_keywords = sorted(
        keywords,
        key=lambda kw: kw.get("opportunity_score", 0),
        reverse=True,
    )
    top_items: List[Dict[str, Any]] = []
    for kw in sorted_keywords[:limit]:
        market = kw.get("market", {})
        intent = kw.get("intent", {})
        top_items.append({
            "keyword": kw.get("keyword", ""),
            "opportunity_score": float(kw.get("opportunity_score", 0)),
            "search_volume": market.get("search_volume"),
            "competition": market.get("competition"),
            "trend": market.get("trend"),
            "ai_bonus": market.get("ai_bonus"),
            "commercial_value": market.get("commercial_value"),
            "primary_intent": intent.get("primary_intent"),
            "intent_description": intent.get("intent_description"),
            "confidence": intent.get("confidence"),
        })
    return top_items


def _collect_history(files: List[Path], history_size: int = 20) -> List[Dict[str, Any]]:
    history: List[Dict[str, Any]] = []
    tail = files[-history_size:]
    for path in tail:
        try:
            data = _load_json(path)
        except Exception:
            continue
        analysis_time = data.get("analysis_time")
        parsed_time, _ = _parse_analysis_time(analysis_time, datetime.fromtimestamp(path.stat().st_mtime))
        market = data.get("market_insights", {})
        history.append({
            "file": path.name,
            "analysis_time": parsed_time,
            "total_keywords": data.get("total_keywords", 0),
            "high_opportunity_count": market.get("high_opportunity_count", 0),
            "avg_opportunity_score": market.get("avg_opportunity_score", 0),
        })
    return history


def _discover_files(source_dir: Path) -> AnalysisFiles:
    analysis = _find_latest_file(source_dir, "keyword_analysis_*.json")
    discovered = _find_latest_file(source_dir, "discovered_keywords_*.csv")
    return AnalysisFiles(analysis=analysis, discovered=discovered)


def generate_dashboard_payload(source_dir: Path, history_size: int = 20) -> Dict[str, Any]:
    files = _discover_files(source_dir)
    if not files.available:
        return {
            "last_updated": None,
            "message": "No keyword_analysis JSON files were found. Run the main workflow first.",
            "history": [],
        }

    analysis_data = _load_json(files.analysis)
    keywords: List[Dict[str, Any]] = analysis_data.get("keywords", [])

    fallback_time = datetime.fromtimestamp(files.analysis.stat().st_mtime)
    last_updated_iso, _ = _parse_analysis_time(analysis_data.get("analysis_time"), fallback_time)

    history_files = sorted(source_dir.glob("keyword_analysis_*.json"), key=lambda p: p.stat().st_mtime)
    history = _collect_history(history_files, history_size=history_size)

    payload: Dict[str, Any] = {
        "last_updated": last_updated_iso,
        "source_files": {
            "analysis": files.analysis.name if files.analysis else None,
            "discovered_keywords": files.discovered.name if files.discovered else None,
        },
        "summary": {
            "total_keywords": analysis_data.get("total_keywords", 0),
            "analysis_time": last_updated_iso,
            "avg_opportunity_score": analysis_data.get("market_insights", {}).get("avg_opportunity_score", 0),
            "high_opportunity_count": analysis_data.get("market_insights", {}).get("high_opportunity_count", 0),
            "medium_opportunity_count": analysis_data.get("market_insights", {}).get("medium_opportunity_count", 0),
            "low_opportunity_count": analysis_data.get("market_insights", {}).get("low_opportunity_count", 0),
        },
        "intent_summary": analysis_data.get("intent_summary", {}),
        "market_insights": analysis_data.get("market_insights", {}),
        "new_word_summary": analysis_data.get("new_word_summary", {}),
        "recommendations": analysis_data.get("recommendations", []),
        "opportunity_segments": _build_opportunity_segments(keywords),
        "top_keywords": _build_top_keywords(keywords),
        "history": history,
        "discovered_keywords": _read_discovered_keywords(files.discovered) if files.discovered else [],
    }

    telemetry_path = source_dir / "telemetry.json"
    if telemetry_path.exists():
        try:
            with telemetry_path.open("r", encoding="utf-8") as fh:
                payload["telemetry"] = json.load(fh)
        except Exception as exc:  # pragma: no cover - best effort
            payload["telemetry"] = {"error": f"failed_to_load: {exc}"}
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate dashboard_data.json for the HTML dashboard")
    parser.add_argument("--source", default="output/reports", help="Directory containing keyword_analysis JSON files")
    parser.add_argument("--output", help="Destination JSON file (default: <source>/dashboard_data.json)")
    parser.add_argument("--history-size", type=int, default=20, help="Number of historical runs to include")
    args = parser.parse_args()

    source_dir = Path(args.source).resolve()
    ensure_directory_exists(str(source_dir))

    payload = generate_dashboard_payload(source_dir, history_size=args.history_size)

    output_path = Path(args.output).resolve() if args.output else source_dir / "dashboard_data.json"
    ensure_directory_exists(str(output_path.parent))
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Dashboard data saved to {output_path}")


if __name__ == "__main__":
    main()
