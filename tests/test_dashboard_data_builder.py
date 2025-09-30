from datetime import datetime
import json
from pathlib import Path

from src.utils.dashboard_data_builder import generate_dashboard_payload


def _write_keyword_analysis(path: Path, total_keywords: int = 3) -> None:
    payload = {
        "total_keywords": total_keywords,
        "analysis_time": datetime.utcnow().isoformat(),
        "keywords": [
            {
                "keyword": "example",
                "opportunity_score": 75,
                "intent": {"primary_intent": "Test"},
                "market": {"search_volume": 100},
            }
        ],
        "intent_summary": {"total_keywords": total_keywords},
        "market_insights": {"avg_opportunity_score": 60, "high_opportunity_count": 1},
        "recommendations": [],
    }
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh)


def test_generate_dashboard_payload_includes_telemetry(tmp_path: Path) -> None:
    reports_dir = tmp_path
    analysis_path = reports_dir / "keyword_analysis_20240101.json"
    _write_keyword_analysis(analysis_path)

    telemetry_payload = {
        "run_id": "test-run",
        "metrics": {"counters": {"runs": 1}},
    }
    with (reports_dir / "telemetry.json").open("w", encoding="utf-8") as fh:
        json.dump(telemetry_payload, fh)

    payload = generate_dashboard_payload(reports_dir)
    assert payload["summary"]["total_keywords"] == 3
    assert payload["telemetry"]["run_id"] == "test-run"
