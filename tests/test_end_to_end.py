"""End-to-end integration test verifying complete data flow through features, inference, replay, and producer handoff."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from starlette.testclient import TestClient

from ml.cyclone.export.producer import (
    file_drop,
    write_jsonl,
)
from ml.cyclone.features.fusion import make_fused_sample
from ml.cyclone.fusion.run_cycle import (
    load_sample_for_cycle,
    run_cycle,
)
from ml.cyclone.replay.replay import (
    precompute_replay,
    resolve_preset_frame_index,
)
from ml.cyclone.schema.models import CycloneIntelligence
from tests.test_sos_unbroken import DistressScorer


def test_full_pipeline_raw_to_producer_integration() -> None:
    """Tests the full end-to-end pipeline from raw input to producer output with zero manual intervention."""
    # Step 1: Ingest sample and extract features
    sample = load_sample_for_cycle(storm_id="Amphan", frame_idx=2)
    assert "lat" in sample
    assert "lon" in sample
    assert "history" in sample

    fused = make_fused_sample(sample)
    assert fused.env_vector.shape == (6,)
    assert fused.track_sequence.shape[1] == 7

    # Step 2: Run public entrypoint run_cycle()
    cyclone_dict = run_cycle(sample=sample)
    validated_obj = CycloneIntelligence(**cyclone_dict)
    assert validated_obj.cyclone_id in ["CYC-2020-AMP", "CYC-2020-BAY-001"]
    assert validated_obj.identification.detected is True
    assert validated_obj.identification.confidence > 0.5
    assert validated_obj.prediction is not None
    assert len(validated_obj.prediction.predicted_path) == 6
    assert len(validated_obj.prediction.uncertainty.cone_radius_km) == 6
    assert validated_obj.prediction.uncertainty.cone_radius_km[0] == 0.0  # r(0) is strictly 0.0 km

    # Step 3: Run Replay Driver precomputation and streaming
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        cache_path = tmp_path / "replay_test.jsonl"

        frames = precompute_replay(storm_id="Amphan", output_path=cache_path)
        assert len(frames) >= 5
        assert cache_path.is_file()

        # Verify frame sequence properties
        for i, frame in enumerate(frames):
            cyc = CycloneIntelligence(**frame)
            assert cyc.cyclone_id in ["CYC-2020-AMP", "CYC-2020-BAY-001"]
            assert cyc.timestamp is not None
            if cyc.prediction:
                assert not any(
                    f is None
                    for f in [
                        cyc.prediction.current_position.lat,
                        cyc.prediction.current_position.lon,
                    ]
                )

            # Check 24h jump preset
            if i == 0:
                idx_24h = resolve_preset_frame_index("amphan_2020", "landfall-24h", len(frames))
                assert 0 <= idx_24h < len(frames)

        # Step 4: Producer File-Drop and JSONL Export Verification
        drop_dir = tmp_path / "file_drops"
        jsonl_out = tmp_path / "stream_output.jsonl"

        # Write JSONL
        out_file = write_jsonl(frames, jsonl_out)
        assert out_file.is_file()
        assert jsonl_out.is_file()

        # File drop
        drop_file = file_drop(frames[0], drop_dir)
        assert drop_file.is_file()
        with open(drop_file, encoding="utf-8") as f:
            dropped_data = json.load(f)
        assert dropped_data["cyclone_id"] in ["CYC-2020-AMP", "CYC-2020-BAY-001"]

        # Step 5: Producer POST to Stub Server Verification
        from ml.cyclone.serving.service import create_app

        app = create_app()
        client = TestClient(app)

        # Verify health and replay endpoints
        resp_health = client.get("/health")
        assert resp_health.status_code == 200
        assert resp_health.json()["status"] in ["ok", "healthy"]

        resp_next = client.get("/replay/Amphan/next")
        assert resp_next.status_code == 200
        first_frame = resp_next.json()
        cyc_resp = CycloneIntelligence(**first_frame)
        assert cyc_resp.cyclone_id in ["CYC-2020-AMP", "CYC-2020-BAY-001"]


def test_sos_pipeline_tripwire_unbroken() -> None:
    """Asserts that the SOS text scoring and triage path is completely functional and intact."""
    test_packet = {
        "sos_id": "SOS-INTEG-001",
        "lat": 19.5,
        "lon": 86.2,
        "battery_pct": 9,
    }
    msg = "Emergency! Sea wall breached, building collapsed, people trapped in rising water!"
    scored = DistressScorer.score(test_packet, msg)
    assert scored["severity_score"] >= 0.90
    assert scored["urgency_category"] == "CRITICAL_LIFE_THREAT"
    assert scored["is_actionable"] is True
