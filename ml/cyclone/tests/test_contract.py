"""End-to-end handoff contract tests with local stub server proving zero-edit integration."""

from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import jsonschema

from ml.cyclone.export.producer import (
    file_drop,
    run_producer,
    write_jsonl,
)
from ml.cyclone.schema.models import CycloneIntelligence

# -----------------------------------------------------------------------------
# 1. Local Stub Ingestion Server
# -----------------------------------------------------------------------------


class IngestionStubHandler(BaseHTTPRequestHandler):
    """Local HTTP handler simulating Harshit's backend ingestion endpoint."""

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy standard HTTP access logs during pytest
        pass

    def do_POST(self) -> None:
        if (
            self.path == "/api/v1/cyclone/intelligence"
            or self.path == "/api/v1/cyclone/intelligence/"
        ):
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            try:
                payload = json.loads(body_bytes.decode("utf-8"))

                # 1. Strict Contract Validation against Pydantic Model
                validated_model = CycloneIntelligence.model_validate(payload)

                # 2. Strict Contract Validation against Raw JSON Schema
                schema_path = (
                    Path(__file__).resolve().parent.parent
                    / "schema"
                    / "cyclone_intelligence.schema.json"
                )
                with open(schema_path, encoding="utf-8") as f:
                    raw_schema = json.load(f)
                jsonschema.validate(instance=payload, schema=raw_schema)

                # Store received payload in server memory
                self.server.received_payloads.append(payload)

                # Respond 200 OK
                resp_data = {
                    "status": "accepted",
                    "cyclone_id": validated_model.cyclone_id,
                    "timestamp": validated_model.timestamp,
                    "validation": "PASSED_ZERO_EDITS",
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp_data).encode("utf-8"))

            except Exception as e:
                self.send_response(422)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"status": "rejected", "error": str(e)}).encode("utf-8")
                )
        else:
            self.send_response(404)
            self.end_headers()


def get_free_port() -> int:
    """Finds an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# -----------------------------------------------------------------------------
# 2. End-to-End Contract Verification Tests
# -----------------------------------------------------------------------------


def test_end_to_end_contract_handoff_with_stub_server(tmp_path: Path) -> None:
    """Proves Definition-of-Done: POSTs full replay to stub server, asserting zero validation errors and zero manual edits."""
    port = get_free_port()
    stub_server = HTTPServer(("127.0.0.1", port), IngestionStubHandler)
    stub_server.received_payloads = []  # type: ignore[attr-defined]

    # Start server in daemon thread
    server_thread = threading.Thread(target=stub_server.serve_forever, daemon=True)
    server_thread.start()

    stub_endpoint = f"http://127.0.0.1:{port}/api/v1/cyclone/intelligence"
    watch_dir = tmp_path / "replay_watch"

    try:
        # Run producer in 'both' mode (POST to HTTP endpoint + file-drop)
        summary = run_producer(
            storm_id="Amphan",
            mode="both",
            speed=0.0,  # instantaneous execution for fast testing
            endpoint=stub_endpoint,
            watch_dir=watch_dir,
            output_jsonl_path=tmp_path / "amphan_complete.jsonl",
        )

        assert summary["status"] == "completed"
        assert summary["frames_produced"] >= 8
        assert summary["frames_posted"] == summary["frames_produced"]
        assert summary["files_dropped"] == summary["frames_produced"]

        # Assert stub server received and accepted every frame with ZERO contract edits
        received = stub_server.received_payloads  # type: ignore[attr-defined]
        assert len(received) == summary["frames_produced"]

        canonical_id = received[0]["cyclone_id"]
        assert canonical_id == "CYC-2020-BAY-001"

        for idx, payload in enumerate(received):
            # Double check that Pydantic and JSONSchema both validate with no manual edits
            inst = CycloneIntelligence.model_validate(payload)
            assert inst.cyclone_id == canonical_id
            assert inst.schema_version == "1.0"
            assert inst.tier in ["tier1", "tier0", "mixed"]
            assert "saffir_simpson" in inst.extra
            assert "provenance" in inst.extra
            assert inst.extra["provenance"]["object_tier"] == inst.tier.value

        # Assert file drop directory contains all JSON files plus latest.json
        dropped_files = list(watch_dir.glob("*.json"))
        assert (
            len(dropped_files) >= summary["frames_produced"] + 1
        )  # individual frames + latest.json

        latest_path = watch_dir / "latest.json"
        assert latest_path.is_file()
        with open(latest_path, encoding="utf-8") as f:
            latest_payload = json.load(f)
            CycloneIntelligence.model_validate(latest_payload)
            assert latest_payload["cyclone_id"] == canonical_id

        # Assert full JSONL was written and is valid
        jsonl_path = tmp_path / "amphan_complete.jsonl"
        assert jsonl_path.is_file()
        lines = jsonl_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == summary["frames_produced"]

    finally:
        stub_server.shutdown()
        stub_server.server_close()


def test_producer_file_drop_atomic_safety(tmp_path: Path) -> None:
    """Verifies atomic file writing safety guarantees."""
    sample_frame = {
        "schema_version": "1.0",
        "cyclone_id": "CYC-TEST-001",
        "name": "Atomic-Test",
        "timestamp": "2026-09-08T12:00:00Z",
        "basin": "North Indian Ocean",
        "identification": {"detected": True, "confidence": 0.90},
        "classification": {"stage": "TROPICAL_DEPRESSION", "confidence": 0.85},
        "intensity": {
            "level": "DEPRESSION",
            "scale": "IMD",
            "max_wind_kt": 25.0,
            "min_pressure_mb": 1000.0,
            "confidence": 0.85,
        },
        "prediction": {
            "current_position": {"lat": 15.0, "lon": 85.0},
            "heading_deg": 350.0,
            "speed_kt": 10.0,
            "forecast_hours": 72,
            "predicted_path": [
                {"t_plus_h": 0, "lat": 15.0, "lon": 85.0},
                {"t_plus_h": 6, "lat": 15.6, "lon": 84.9},
            ],
            "confidence": 0.80,
            "uncertainty": {"cone_radius_km": [0.0, 45.0]},
        },
        "sources": ["ibtracs_track"],
        "model_version": "chakravyuh-1.0",
        "tier": "tier0",
        "extra": {"saffir_simpson": "Tropical Depression"},
    }

    watch_dir = tmp_path / "atomic_watch"
    written_path = file_drop(sample_frame, watch_dir=watch_dir, keep_latest_symlink=True)

    assert written_path.is_file()
    assert (watch_dir / "latest.json").is_file()

    # No leftover temporary files
    tmp_files = list(watch_dir.glob(".*.tmp"))
    assert len(tmp_files) == 0


def test_producer_write_jsonl(tmp_path: Path) -> None:
    """Verifies write_jsonl produces clean valid lines."""
    frames = [
        {
            "schema_version": "1.0",
            "cyclone_id": f"CYC-JSONL-{i:02d}",
            "name": f"Storm-{i}",
            "timestamp": f"2026-09-08T{i:02d}:00:00Z",
            "basin": "North Indian Ocean",
            "identification": {"detected": True, "confidence": 0.90},
            "classification": {"stage": "DEVELOPING_DISTURBANCE", "confidence": 0.85},
            "intensity": {
                "level": "DEPRESSION",
                "scale": "IMD",
                "max_wind_kt": 25.0,
                "min_pressure_mb": 1000.0,
                "confidence": 0.85,
            },
            "prediction": {
                "current_position": {"lat": 15.0, "lon": 85.0},
                "heading_deg": 350.0,
                "speed_kt": 10.0,
                "forecast_hours": 72,
                "predicted_path": [
                    {"t_plus_h": 0, "lat": 15.0, "lon": 85.0},
                    {"t_plus_h": 6, "lat": 15.6, "lon": 84.9},
                ],
                "confidence": 0.80,
                "uncertainty": {"cone_radius_km": [0.0, 45.0]},
            },
            "sources": ["ibtracs_track"],
            "model_version": "chakravyuh-1.0",
            "tier": "tier0",
        }
        for i in range(5)
    ]

    out_file = tmp_path / "test_out.jsonl"
    write_jsonl(frames, out_file)

    assert out_file.is_file()
    lines = out_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 5
    for l in lines:
        CycloneIntelligence.model_validate(json.loads(l))
