"""Unit tests for Tier-0 Persistence + CLIPER track baseline and parametric uncertainty cone."""

from ml.cyclone.models.baseline_track import (
    cliper_forecast,
    parametric_cone,
    persistence_forecast,
    predict_track,
)
from ml.cyclone.schema.models import PredictionPayload

# -----------------------------------------------------------------------------
# Persistence Forecast Tests
# -----------------------------------------------------------------------------


def test_persistence_straight_line_continuation():
    """Asserts persistence forecast continues straight along velocity vector."""
    # Synthetic history moving due North at 10 knots
    history_north = [
        {"t_offset_h": -12.0, "lat": 10.0, "lon": 85.0, "speed_kt": 10.0, "heading_deg": 0.0},
        {"t_offset_h": -6.0, "lat": 11.0, "lon": 85.0, "speed_kt": 10.0, "heading_deg": 0.0},
        {"t_offset_h": 0.0, "lat": 12.0, "lon": 85.0, "speed_kt": 10.0, "heading_deg": 0.0},
    ]

    forecast = persistence_forecast(history_north, horizons=[0, 6, 12, 24, 48, 72])

    assert len(forecast) == 6
    # Current point
    assert forecast[0] == (0, 12.0, 85.0)

    # All future points must stay at lon=85.0 and have strictly increasing latitude
    prev_lat = 12.0
    for h, lat, lon in forecast[1:]:
        assert abs(lon - 85.0) < 1e-3
        assert lat > prev_lat
        prev_lat = lat


# -----------------------------------------------------------------------------
# Parametric Cone Tests
# -----------------------------------------------------------------------------


def test_parametric_cone_monotonicity_and_anchor():
    """Asserts parametric cone starts at 0.0 km and grows strictly monotonically with time."""
    horizons = [0, 6, 12, 24, 48, 72]
    radii = parametric_cone(horizons)

    assert len(radii) == len(horizons)
    assert radii[0] == 0.0

    # Strictly monotonically increasing
    for i in range(1, len(radii)):
        assert radii[i] > radii[i - 1]

    # IMD benchmark range checks
    assert 40.0 <= radii[2] <= 52.0  # 12h: ~46 km
    assert 70.0 <= radii[3] <= 85.0  # 24h: ~78 km
    assert 120.0 <= radii[4] <= 145.0  # 48h: ~132 km
    assert 190.0 <= radii[5] <= 220.0  # 72h: ~205 km


# -----------------------------------------------------------------------------
# CLIPER Damping & Recurvature Tests
# -----------------------------------------------------------------------------


def test_cliper_recurvature_at_high_latitude():
    """Asserts CLIPER damps northward track toward northeastward climatological recurvature in upper Bay."""
    # Storm in northern Bay of Bengal (lat 19.5 N) moving due North
    history_north_bay = [
        {"t_offset_h": -6.0, "lat": 19.0, "lon": 87.0, "speed_kt": 12.0, "heading_deg": 0.0},
        {"t_offset_h": 0.0, "lat": 19.8, "lon": 87.0, "speed_kt": 12.0, "heading_deg": 0.0},
    ]

    cliper_pts = cliper_forecast(history_north_bay, horizons=[0, 6, 12, 24, 48, 72])

    assert len(cliper_pts) == 6
    assert cliper_pts[0] == (0, 19.8, 87.0)

    # At 72h, climatology should have pulled longitude eastward (> 87.0)
    final_h, final_lat, final_lon = cliper_pts[-1]
    assert final_lat > 19.8
    assert final_lon > 87.0  # Eastward recurvature


# -----------------------------------------------------------------------------
# Pydantic Contract Compliance Tests
# -----------------------------------------------------------------------------


def test_predict_track_pydantic_contract_validity():
    """Asserts predict_track output dictionary strictly passes Pydantic PredictionPayload validation."""
    history = [
        {"t_offset_h": -18.0, "lat": 14.0, "lon": 85.5, "speed_kt": 10.0, "heading_deg": 340.0},
        {"t_offset_h": -12.0, "lat": 15.0, "lon": 85.2, "speed_kt": 11.0, "heading_deg": 345.0},
        {"t_offset_h": -6.0, "lat": 16.0, "lon": 84.9, "speed_kt": 11.5, "heading_deg": 348.0},
        {"t_offset_h": 0.0, "lat": 17.0, "lon": 84.6, "speed_kt": 12.0, "heading_deg": 350.0},
    ]

    # Test both CLIPER and Persistence modes
    for method in ["cliper", "persistence"]:
        pred_dict = predict_track(history, method=method)

        # Validate through Pydantic model
        pydantic_model = PredictionPayload.model_validate(pred_dict)
        assert pydantic_model.forecast_hours == 72
        assert len(pydantic_model.predicted_path) == 6
        assert len(pydantic_model.uncertainty.cone_radius_km) == 6
        assert 0.40 <= pydantic_model.confidence <= 0.95
        assert pydantic_model.uncertainty.cone_radius_km[0] == 0.0
        assert pydantic_model.predicted_path[0].lat == pydantic_model.current_position.lat
        assert pydantic_model.predicted_path[0].lon == pydantic_model.current_position.lon
