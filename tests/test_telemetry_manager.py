from pathlib import Path
import json
import time

from src.utils.telemetry import TelemetryManager


def test_stage_context_records_metrics(tmp_path: Path):
    telemetry = TelemetryManager()
    telemetry.reset(run_id="test-run")

    with telemetry.stage("demo", {"step": 1}):
        time.sleep(0.01)

    token = telemetry.start_stage("manual", {"step": 2})
    telemetry.end_stage(token, extra={"output": 42})

    telemetry.record_request(
        host="example.com",
        method="GET",
        url="https://example.com",
        status=200,
        ok=True,
        elapsed=0.02,
    )
    telemetry.record_request(
        host="example.com",
        method="GET",
        url="https://example.com/429",
        status=429,
        ok=False,
        elapsed=0.01,
    )

    telemetry.increment_counter("runs")
    telemetry.set_gauge("latest", 5)

    snapshot = telemetry.snapshot()
    stages = snapshot["metrics"]["stages"]
    assert stages["demo"]["count"] == 1
    assert stages["demo"]["last_status"] == "completed"
    assert stages["manual"]["last_payload"]["output"] == 42

    requests = snapshot["metrics"]["requests"]
    assert requests["total"] == 2
    assert requests["rate_limited"] == 1
    assert requests["by_host"]["example.com"]["errors"] == 1

    counters = snapshot["metrics"]["counters"]
    gauges = snapshot["metrics"]["gauges"]
    assert counters["runs"] == 1
    assert gauges["latest"] == 5

    output_path = telemetry.write_snapshot(tmp_path / "telemetry.json")
    assert output_path.exists()
    with output_path.open("r", encoding="utf-8") as fh:
        on_disk = json.load(fh)
    assert on_disk["metrics"]["requests"]["total"] == 2
