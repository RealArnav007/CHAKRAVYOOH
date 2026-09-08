"""Unit and integration tests for run_cycle() inference orchestrator and CLI."""

from __future__ import annotations

import json
import subprocess
import sys

from ml.cyclone.fusion.run_cycle import (
    run_cycle,
)
from ml.cyclone.schema.models import CycloneIntelligence


def test_run_cycle_detected_storm() -> None:
    """Verifies that run_cycle produces a certified CycloneIntelligence dict for a detected storm frame."""
    result = run_cycle(storm_id="Amphan", frame=2)

    # 1. Schema Validation (raises if invalid)
    validated_model = CycloneIntelligence.model_validate(result)
    assert validated_model.schema_version == "1.0"
    assert validated_model.cyclone_id == "CYC-2020-AMP"
    assert "Amphan" in validated_model.name
    assert validated_model.basin == "Bay of Bengal"

    # 2. Identification
    assert result["identification"]["detected"] is True
    assert 0.0 <= result["identification"]["confidence"] <= 1.0

    # 3. Intensity & Scales
    assert result["intensity"]["max_wind_kt"] > 0.0
    assert result["intensity"]["scale"] == "IMD"
    assert result["extra"]["saffir_simpson"] in [
        "Tropical Depression",
        "Tropical Storm",
        "Category 1",
        "Category 2",
        "Category 3",
        "Category 4",
        "Category 5",
    ]

    # 4. Trajectory & Uncertainty Cone
    assert result["prediction"] is not None
    pred = result["prediction"]
    assert len(pred["predicted_path"]) >= 2
    assert pred["predicted_path"][0]["t_plus_h"] == 0
    assert pred["predicted_path"][0]["lat"] == pred["current_position"]["lat"]
    assert pred["predicted_path"][0]["lon"] == pred["current_position"]["lon"]

    cone_radii = pred["uncertainty"]["cone_radius_km"]
    assert len(cone_radii) == len(pred["predicted_path"])
    assert cone_radii[0] == 0.0
    assert all(r >= 0.0 for r in cone_radii)

    # 5. Execution Tier & Provenance Consistency
    assert result["tier"] in ["tier1", "tier0", "mixed"]
    prov = result["extra"]["provenance"]
    assert prov["object_tier"] == result["tier"]
    assert "sources" in prov
    assert "reasons" in prov
    assert prov["sources"]["identification"] in ["tier1", "tier0"]
    assert prov["sources"]["prediction"] in ["tier1", "tier0"]

    # 6. Active Modalities & Class Probabilities
    assert len(result["sources"]) >= 1
    assert "intensity_class_probs" in result["extra"]
    assert len(result["extra"]["intensity_class_probs"]) == 7
    assert "stage_class_probs" in result["extra"]
    assert len(result["extra"]["stage_class_probs"]) == 6


def test_run_cycle_no_detect_frame() -> None:
    """Verifies that a calm ocean / no-detect frame sets detected=False, prediction=null, and valid provenance."""
    result = run_cycle(storm_id="no_detect")

    # 1. Schema Validation
    validated_model = CycloneIntelligence.model_validate(result)
    assert validated_model.identification.detected is False
    assert validated_model.prediction is None

    # 2. Strict invariant: In JSON / dict, prediction MUST be None
    assert result["prediction"] is None
    assert result["identification"]["detected"] is False

    # 3. Provenance reflects omitted prediction
    prov = result["extra"]["provenance"]
    assert prov["object_tier"] == result["tier"]
    assert "none" in prov["sources"]["prediction"]
    assert (
        "omitted" in prov["reasons"]["prediction"].lower()
        or "not detected" in prov["reasons"]["prediction"].lower()
    )


def test_run_cycle_custom_sample_dictionary() -> None:
    """Verifies that passing a custom sample dictionary executes seamlessly."""
    custom_sample = {
        "storm_id": "CYC-CUSTOM-001",
        "name": "Custom-Test-System",
        "basin": "Arabian Sea",
        "time": "2026-09-08T12:00:00Z",
        "lat": 18.2,
        "lon": 67.5,
        "wind_kt": 65.0,
        "pres_mb": 978.0,
        "image_available": True,
        "env": {
            "sst_c": 29.2,
            "shear_ms": 6.0,
            "rh500": 75.0,
            "vort850": 10.0,
            "mslp_mb": 978.0,
            "wind10m_ms": 25.0,
        },
        "history": [
            {
                "t_offset_h": -6.0,
                "lat": 17.9,
                "lon": 67.3,
                "wind_kt": 60.0,
                "pres_mb": 982.0,
                "speed_kt": 9.5,
                "heading_deg": 340.0,
            },
            {
                "t_offset_h": 0.0,
                "lat": 18.2,
                "lon": 67.5,
                "wind_kt": 65.0,
                "pres_mb": 978.0,
                "speed_kt": 10.0,
                "heading_deg": 345.0,
            },
        ],
    }

    result = run_cycle(sample=custom_sample)

    assert result["cyclone_id"] == "CYC-CUSTOM-001"
    assert result["name"] == "Custom-Test-System"
    assert result["basin"] == "Arabian Sea"
    assert result["identification"]["detected"] is True
    assert result["prediction"] is not None
    assert result["prediction"]["current_position"]["lat"] == 18.2
    assert result["prediction"]["current_position"]["lon"] == 67.5


def test_run_cycle_missing_modalities_graceful_degradation() -> None:
    """Verifies graceful multi-modal degradation when images and/or ERA5 fields are absent."""
    # 1. Missing satellite image (env + track only)
    no_image_sample = {
        "storm_id": "CYC-NO-IMG",
        "name": "No-Image-Storm",
        "basin": "Bay of Bengal",
        "time": "2026-09-08T12:00:00Z",
        "lat": 15.0,
        "lon": 85.0,
        "wind_kt": 50.0,
        "pres_mb": 990.0,
        "image_available": False,
        "image_path": None,
        "env": {
            "sst_c": 29.0,
            "shear_ms": 8.0,
            "rh500": 65.0,
            "vort850": 6.0,
            "mslp_mb": 990.0,
            "wind10m_ms": 18.0,
        },
        "history": [
            {"t_offset_h": 0.0, "lat": 15.0, "lon": 85.0, "wind_kt": 50.0, "pres_mb": 990.0}
        ],
    }
    res_no_img = run_cycle(sample=no_image_sample)
    assert "insat3d_ir" not in res_no_img["sources"]
    assert res_no_img["tier"] in ["tier1", "tier0", "mixed"]

    # 2. Missing ERA5 scalars (image + track only)
    no_env_sample = {
        "storm_id": "CYC-NO-ENV",
        "name": "No-Env-Storm",
        "basin": "Bay of Bengal",
        "time": "2026-09-08T12:00:00Z",
        "lat": 15.0,
        "lon": 85.0,
        "wind_kt": 50.0,
        "pres_mb": 990.0,
        "image_available": True,
        "env": None,
        "history": [
            {"t_offset_h": 0.0, "lat": 15.0, "lon": 85.0, "wind_kt": 50.0, "pres_mb": 990.0}
        ],
    }
    res_no_env = run_cycle(sample=no_env_sample)
    assert "era5" not in res_no_env["sources"]

    # 3. Missing both image and ERA5 (track only -> Tier-0 fallback)
    track_only_sample = {
        "storm_id": "CYC-TRACK-ONLY",
        "name": "Track-Only-Storm",
        "basin": "Bay of Bengal",
        "time": "2026-09-08T12:00:00Z",
        "lat": 15.0,
        "lon": 85.0,
        "wind_kt": 40.0,
        "pres_mb": 996.0,
        "image_available": False,
        "env": None,
        "history": [
            {
                "t_offset_h": -6.0,
                "lat": 14.8,
                "lon": 84.9,
                "wind_kt": 35.0,
                "pres_mb": 998.0,
                "speed_kt": 10.0,
                "heading_deg": 350.0,
            },
            {
                "t_offset_h": 0.0,
                "lat": 15.0,
                "lon": 85.0,
                "wind_kt": 40.0,
                "pres_mb": 996.0,
                "speed_kt": 10.0,
                "heading_deg": 350.0,
            },
        ],
    }
    res_track_only = run_cycle(sample=track_only_sample)
    assert res_track_only["tier"] == "tier0"
    assert res_track_only["extra"]["provenance"]["object_tier"] == "tier0"


def test_run_cycle_returns_pydantic_instance() -> None:
    """Verifies return_model_object=True returns a pydantic CycloneIntelligence instance."""
    res_obj = run_cycle(storm_id="Biparjoy", frame=1, return_model_object=True)
    assert isinstance(res_obj, CycloneIntelligence)
    assert res_obj.cyclone_id.startswith("CYC-")
    assert res_obj.identification.detected is True
    assert res_obj.prediction is not None


def test_run_cycle_cli_execution() -> None:
    """Verifies that the CLI `python -m ml.cyclone.fusion.run_cycle --storm <id> --frame <k>` prints valid JSON."""
    cmd = [
        sys.executable,
        "-m",
        "ml.cyclone.fusion.run_cycle",
        "--storm",
        "Biparjoy",
        "--frame",
        "1",
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert proc.returncode == 0

    # Parse stdout JSON
    json_str = proc.stdout.strip()
    # Handle any HF hub warning lines preceding JSON
    json_start = json_str.find("{")
    assert json_start != -1, f"No JSON found in CLI stdout: {json_str}"

    json_payload = json.loads(json_str[json_start:])

    # Validate against schema model
    validated = CycloneIntelligence.model_validate(json_payload)
    assert "Biparjoy" in validated.name
    assert validated.prediction is not None
    assert validated.prediction.current_position.lat > 0.0
