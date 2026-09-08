"""Unit and integration tests for replay driver, landfall presets, JSONL caching, and serving."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pytest

from ml.cyclone.replay.replay import (
    ROOT_REPLAY_CACHE_DIR,
    precompute_replay,
    replay,
    resolve_preset_frame_index,
)
from ml.cyclone.schema.models import CycloneIntelligence
from ml.cyclone.serving.service import FASTAPI_AVAILABLE, app


def test_precompute_replay_validation_time_ordering_and_constant_id() -> None:
    """Verifies that precomputed replay frames are strictly time-ordered, share a constant cyclone_id, and validate."""
    frames = precompute_replay(storm_id="Amphan", step_hours=6, force_recompute=True)

    assert len(frames) >= 8, f"Expected at least 8 frames for Amphan, got {len(frames)}"
    canonical_id = frames[0]["cyclone_id"]
    assert canonical_id == "CYC-2020-BAY-001"

    prev_dt = None
    for idx, frame in enumerate(frames):
        # 1. Validate every frame against frozen schema
        model_inst = CycloneIntelligence.model_validate(frame)
        assert model_inst.schema_version == "1.0"
        assert model_inst.basin == "Bay of Bengal"

        # 2. Assert constant cyclone_id across entire lifecycle
        assert (
            frame["cyclone_id"] == canonical_id
        ), f"Frame {idx} cyclone_id {frame['cyclone_id']} != {canonical_id}"

        # 3. Assert strictly increasing chronological timestamps
        cur_dt = datetime.fromisoformat(frame["timestamp"].replace("Z", "+00:00"))
        if prev_dt is not None:
            assert cur_dt > prev_dt, f"Frame {idx} timestamp {cur_dt} <= previous {prev_dt}"
        prev_dt = cur_dt

        # 4. Invariant checks
        if frame["identification"]["detected"]:
            assert frame["prediction"] is not None
            assert len(frame["prediction"]["predicted_path"]) >= 2
            assert frame["prediction"]["uncertainty"]["cone_radius_km"][0] == 0.0
        else:
            assert frame["prediction"] is None


def test_replay_landfall_minus_24h_preset_resolution() -> None:
    """Verifies that '--jump landfall-24h' presets start at the frame exactly 24h prior to landfall."""
    # Amphan landfall is at lead hour 72h (frame 6). Landfall - 24h is at lead hour 48h (frame 4).
    idx_amphan = resolve_preset_frame_index("amphan_2020", preset="landfall-24h", total_frames=8)
    assert idx_amphan == 4

    idx_amphan_alias = resolve_preset_frame_index(
        "amphan_2020", preset="landfall_minus_24h", total_frames=8
    )
    assert idx_amphan_alias == 4

    idx_biparjoy = resolve_preset_frame_index(
        "biparjoy_2023", preset="landfall-24h", total_frames=8
    )
    assert idx_biparjoy == 4

    idx_genesis = resolve_preset_frame_index("amphan_2020", preset="genesis", total_frames=8)
    assert idx_genesis == 0

    idx_landfall = resolve_preset_frame_index("amphan_2020", preset="landfall", total_frames=8)
    assert idx_landfall == 6


def test_replay_generator_cadence_and_visible_evolution() -> None:
    """Verifies that the replay generator yields frames sequentially starting from the landfall-24h preset."""
    frames_yielded: list[dict[str, Any]] = []

    # Run generator with speed=0 (instant execution for test speed)
    for frame in replay(storm_id="Amphan", jump="landfall-24h", speed=0.0):
        frames_yielded.append(frame)

    assert len(frames_yielded) == 4  # Frames 4, 5, 6, 7

    # Check evolution across consecutive frames
    latitudes = [
        f["prediction"]["current_position"]["lat"] for f in frames_yielded if f["prediction"]
    ]
    assert len(latitudes) >= 3
    # Cyclone moves northwards from ~17.8°N towards ~25.1°N
    assert latitudes[-1] > latitudes[0]

    # Check intensity evolution
    winds = [f["intensity"]["max_wind_kt"] for f in frames_yielded]
    assert len(winds) == 4
    # Landfall transition shows decay from intense to remnant
    assert winds[-1] < winds[0]


def test_replay_jsonl_cache_file_persisted() -> None:
    """Verifies that precompute_replay writes valid JSONL files to cache directories."""
    precompute_replay(storm_id="Biparjoy", force_recompute=True)

    cache_file = ROOT_REPLAY_CACHE_DIR / "biparjoy_2023.jsonl"
    assert cache_file.is_file(), f"Cache file {cache_file} does not exist"

    lines = cache_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 8

    # Ensure each line is valid CycloneIntelligence JSON
    for line in lines:
        payload = json.loads(line)
        CycloneIntelligence.model_validate(payload)
        assert payload["cyclone_id"] == "CYC-2023-ARB-001"
        assert "Biparjoy" in payload["name"]


def test_fastapi_serving_endpoints() -> None:
    """Verifies FastAPI serving endpoints for replay streaming and cursor advancing."""
    if not FASTAPI_AVAILABLE:
        pytest.skip("FastAPI not installed")

    from fastapi.testclient import TestClient

    client = TestClient(app)

    # 1. Health check
    resp_health = client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "ok"

    # 2. Reset replay with jump to landfall-24h
    resp_reset = client.post("/replay/Amphan/reset?jump=landfall-24h")
    assert resp_reset.status_code == 200
    reset_data = resp_reset.json()
    assert reset_data["cursor_frame"] == 4
    assert reset_data["current_frame"]["cyclone_id"] == "CYC-2020-BAY-001"

    # 3. Next frame
    resp_next = client.get("/replay/Amphan/next")
    assert resp_next.status_code == 200
    frame_data = resp_next.json()
    CycloneIntelligence.model_validate(frame_data)
    assert frame_data["cyclone_id"] == "CYC-2020-BAY-001"

    # 4. Tick endpoint
    resp_tick = client.post("/replay/Amphan/tick")
    assert resp_tick.status_code == 200
    tick_data = resp_tick.json()
    assert tick_data["cyclone_id"] == "CYC-2020-BAY-001"

    # 5. Fetch all frames
    resp_all = client.get("/replay/Amphan/all")
    assert resp_all.status_code == 200
    all_frames = resp_all.json()
    assert len(all_frames) >= 8
