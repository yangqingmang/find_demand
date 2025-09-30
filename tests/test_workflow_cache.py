import json
import time
from pathlib import Path

from src.utils.workflow_cache import WorkflowCacheManager


def test_workflow_cache_store_and_load(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    manager = WorkflowCacheManager(cache_dir, ttl_hours=0.000001)

    payload = {"records": [{"keyword": "alpha"}], "seed_pool": ["alpha"]}
    manager.store_stage(manager.STAGE_TRENDING, payload)

    loaded = manager.load_stage(manager.STAGE_TRENDING)
    assert loaded is not None
    assert loaded["payload"]["records"][0]["keyword"] == "alpha"

    # wait for expiry and ensure stale cache is purged
    time.sleep(0.01)
    expired = manager.load_stage(manager.STAGE_TRENDING)
    assert expired is None


def test_workflow_cache_clear_stage(tmp_path: Path):
    manager = WorkflowCacheManager(tmp_path / "cache")
    manager.store_stage(manager.STAGE_HOT_ANALYSIS, {"result": {"total_keywords": 10}})
    assert manager.load_stage(manager.STAGE_HOT_ANALYSIS) is not None
    manager.clear_stage(manager.STAGE_HOT_ANALYSIS)
    assert manager.load_stage(manager.STAGE_HOT_ANALYSIS) is None


def test_workflow_cache_persists_state(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    manager = WorkflowCacheManager(cache_dir)
    manager.store_stage(manager.STAGE_DISCOVERY, {"records": [], "seed_terms": ["alpha"]})

    state_path = cache_dir / "state.json"
    assert state_path.exists()
    with state_path.open("r", encoding="utf-8") as fh:
        state_payload = json.load(fh)
    assert manager.STAGE_DISCOVERY in state_payload["stages"]

    new_manager = WorkflowCacheManager(cache_dir)
    loaded = new_manager.load_stage(manager.STAGE_DISCOVERY)
    assert loaded is not None
