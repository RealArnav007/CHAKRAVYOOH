"""Unit and contract tests for CycloneIntelligence schema and Pydantic models."""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

try:
    import jsonschema
except ImportError:
    jsonschema = None

from ml.cyclone.schema.models import (
    ClassificationPayload,
    CycloneIntelligence,
    GeoPoint,
    IdentificationPayload,
    IntensityLevelEnum,
    IntensityPayload,
    PredictionPayload,
    StageEnum,
    TierEnum,
    TrajectoryPoint,
    UncertaintyCone,
)


FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "cyclone_intelligence.schema.json"


@pytest.fixture
def json_schema():
    assert SCHEMA_PATH.is_file(), f"Schema file missing at {SCHEMA_PATH}"
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def golden_fixtures():
    fixture_files = ["no_detect.json", "early_stage.json", "landfall_imminent.json"]
    loaded = {}
    for filename in fixture_files:
        p = FIXTURES_DIR / filename
        assert p.is_file(), f"Fixture {filename} not found at {p}"
        with open(p, "r", encoding="utf-8") as f:
            loaded[filename] = json.load(f)
    return loaded


# -----------------------------------------------------------------------------
# Positive Golden Fixture Validation Tests
# -----------------------------------------------------------------------------


def test_golden_fixtures_against_json_schema(json_schema, golden_fixtures):
    """Assert all 3 golden fixtures conform strictly to draft 2020-12 JSON Schema."""
    if jsonschema is None:
        pytest.skip("jsonschema not installed")
    for name, data in golden_fixtures.items():
        try:
            jsonschema.validate(instance=data, schema=json_schema)
        except jsonschema.ValidationError as err:
            pytest.fail(f"Fixture '{name}' failed JSON Schema validation: {err.message}")


def test_golden_fixtures_against_pydantic_models(golden_fixtures):
    """Assert all 3 golden fixtures parse into Pydantic models and enforce contract invariants."""
    for name, data in golden_fixtures.items():
        model = CycloneIntelligence.model_validate(data)
        assert model.schema_version == "1.0"
        assert model.cyclone_id
        assert model.name
        assert 0.0 <= model.identification.confidence <= 1.0
        assert 0.0 <= model.classification.confidence <= 1.0
        assert 0.0 <= model.intensity.confidence <= 1.0
        assert model.intensity.scale == "IMD"
        assert model.tier in {TierEnum.TIER1, TierEnum.TIER0, TierEnum.MIXED}

        if not model.identification.detected:
            assert model.prediction is None
        else:
            assert model.prediction is not None
            pred = model.prediction
            assert 0.0 <= pred.confidence <= 1.0
            assert 0.0 <= pred.heading_deg <= 360.0
            assert pred.speed_kt >= 0.0
            assert len(pred.predicted_path) == len(pred.uncertainty.cone_radius_km)
            assert pred.predicted_path[0].t_plus_h == 0
            assert pred.uncertainty.cone_radius_km[0] == 0.0
            assert abs(pred.predicted_path[0].lat - pred.current_position.lat) < 1e-3
            assert abs(pred.predicted_path[0].lon - pred.current_position.lon) < 1e-3


def test_model_to_validated_dict(golden_fixtures):
    """Assert model serialization and .to_validated_dict() executes without error."""
    for name, data in golden_fixtures.items():
        model = CycloneIntelligence.model_validate(data)
        out_dict = model.to_validated_dict()
        assert isinstance(out_dict, dict)
        assert out_dict["schema_version"] == "1.0"


# -----------------------------------------------------------------------------
# Negative Invariant Tests
# -----------------------------------------------------------------------------


def test_negative_confidence_above_one(golden_fixtures):
    """Confidence > 1.0 must fail validation."""
    data = json.loads(json.dumps(golden_fixtures["landfall_imminent.json"]))
    data["identification"]["confidence"] = 1.35
    with pytest.raises(ValidationError):
        CycloneIntelligence.model_validate(data)


def test_negative_confidence_below_zero(golden_fixtures):
    """Confidence < 0.0 must fail validation."""
    data = json.loads(json.dumps(golden_fixtures["landfall_imminent.json"]))
    data["classification"]["confidence"] = -0.1
    with pytest.raises(ValidationError):
        CycloneIntelligence.model_validate(data)


def test_negative_heading_out_of_bounds(golden_fixtures):
    """Heading > 360 or < 0 must fail validation."""
    data = json.loads(json.dumps(golden_fixtures["landfall_imminent.json"]))
    data["prediction"]["heading_deg"] = 365.0
    with pytest.raises(ValidationError):
        CycloneIntelligence.model_validate(data)


def test_negative_cone_length_mismatch(golden_fixtures):
    """cone_radius_km length != predicted_path length must fail validation."""
    data = json.loads(json.dumps(golden_fixtures["landfall_imminent.json"]))
    # Drop one radius point
    data["prediction"]["uncertainty"]["cone_radius_km"] = data["prediction"]["uncertainty"]["cone_radius_km"][:-1]
    with pytest.raises(ValidationError):
        CycloneIntelligence.model_validate(data)


def test_negative_cone_nonzero_initial_radius(golden_fixtures):
    """cone_radius_km[0] != 0.0 must fail validation."""
    data = json.loads(json.dumps(golden_fixtures["landfall_imminent.json"]))
    data["prediction"]["uncertainty"]["cone_radius_km"][0] = 15.0
    with pytest.raises(ValidationError):
        CycloneIntelligence.model_validate(data)


def test_negative_path_first_point_mismatch_current_pos(golden_fixtures):
    """predicted_path[0] coordinate mismatching current_position must fail validation."""
    data = json.loads(json.dumps(golden_fixtures["landfall_imminent.json"]))
    data["prediction"]["predicted_path"][0]["lat"] = data["prediction"]["current_position"]["lat"] + 5.0
    with pytest.raises(ValidationError):
        CycloneIntelligence.model_validate(data)


def test_negative_path_unordered_timestamps(golden_fixtures):
    """Non-increasing forecast hours in predicted_path must fail validation."""
    data = json.loads(json.dumps(golden_fixtures["landfall_imminent.json"]))
    # Swap t_plus_h orders
    data["prediction"]["predicted_path"][2]["t_plus_h"] = 4
    with pytest.raises(ValidationError):
        CycloneIntelligence.model_validate(data)


def test_negative_detected_false_with_prediction(golden_fixtures):
    """When detected is false, non-null prediction must fail validation."""
    data = json.loads(json.dumps(golden_fixtures["early_stage.json"]))
    data["identification"]["detected"] = False
    # prediction is not null
    with pytest.raises(ValidationError):
        CycloneIntelligence.model_validate(data)


def test_negative_invalid_stage_enum(golden_fixtures):
    """Unrecognized stage enum must fail validation."""
    data = json.loads(json.dumps(golden_fixtures["landfall_imminent.json"]))
    data["classification"]["stage"] = "SUPER_TYPHOON_UNKNOWN"
    with pytest.raises(ValidationError):
        CycloneIntelligence.model_validate(data)


def test_negative_invalid_intensity_level_enum(golden_fixtures):
    """Unrecognized intensity level enum must fail validation."""
    data = json.loads(json.dumps(golden_fixtures["landfall_imminent.json"]))
    data["intensity"]["level"] = "CATEGORY_5_HURRICANE"
    with pytest.raises(ValidationError):
        CycloneIntelligence.model_validate(data)


def test_negative_invalid_scale(golden_fixtures):
    """Intensity scale not equal to 'IMD' must fail validation."""
    data = json.loads(json.dumps(golden_fixtures["landfall_imminent.json"]))
    data["intensity"]["scale"] = "JTWC"
    with pytest.raises(ValidationError):
        CycloneIntelligence.model_validate(data)


def test_negative_invalid_schema_version(golden_fixtures):
    """Schema version not '1.0' must fail validation."""
    data = json.loads(json.dumps(golden_fixtures["landfall_imminent.json"]))
    data["schema_version"] = "2.0"
    with pytest.raises(ValidationError):
        CycloneIntelligence.model_validate(data)


def test_negative_invalid_tier(golden_fixtures):
    """Invalid tier enum must fail validation."""
    data = json.loads(json.dumps(golden_fixtures["landfall_imminent.json"]))
    data["tier"] = "tier3_experimental"
    with pytest.raises(ValidationError):
        CycloneIntelligence.model_validate(data)


def test_negative_invalid_iso_timestamp(golden_fixtures):
    """Invalid timestamp string format must fail validation."""
    data = json.loads(json.dumps(golden_fixtures["landfall_imminent.json"]))
    data["timestamp"] = "yesterday at 5pm"
    with pytest.raises(ValidationError):
        CycloneIntelligence.model_validate(data)
