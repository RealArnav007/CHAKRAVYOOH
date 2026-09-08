"""Unit tests for demo storm error analysis, figure generation, and narration notes."""

from __future__ import annotations

from pathlib import Path
import pytest

from ml.cyclone.eval.error_analysis import (
    DEMO_STORMS_DATA,
    analyze_demo_storm,
    generate_demo_storm_notes,
    plot_storm_error_analysis,
    run_demo_error_analysis,
)


def test_analyze_demo_storm() -> None:
    """Tests that demo storm error analysis computes track errors, intensity errors, and fallbacks."""
    for storm_key, raw_data in DEMO_STORMS_DATA.items():
        res = analyze_demo_storm(storm_key, raw_data)

        assert res["storm_key"] == storm_key
        assert len(res["track_errors"]) == len(raw_data["timesteps"])
        assert len(res["wind_errors"]) == len(raw_data["timesteps"])
        assert res["mean_track_error_km"] >= 0.0
        assert res["mean_wind_mae_kt"] >= 0.0
        assert "best_moment" in res
        assert "worst_moment" in res
        assert isinstance(res["imd_class_summary"], dict)


def test_plot_storm_error_analysis(tmp_path: Path) -> None:
    """Tests figure generation for a demo storm."""
    raw_data = DEMO_STORMS_DATA["amphan_2020"]
    analysis = analyze_demo_storm("amphan_2020", raw_data)

    out_file = plot_storm_error_analysis(analysis, output_dir=tmp_path)
    assert out_file.is_file()
    assert out_file.stat().st_size > 1000


def test_generate_demo_storm_notes(tmp_path: Path) -> None:
    """Tests generation of pitch narration notes."""
    all_analyses = {
        k: analyze_demo_storm(k, v) for k, v in DEMO_STORMS_DATA.items()
    }
    notes_file = tmp_path / "DEMO_STORM_NOTES.md"
    generate_demo_storm_notes(all_analyses, output_path=notes_file)

    assert notes_file.is_file()
    text = notes_file.read_text(encoding="utf-8")
    assert "Super Cyclone Amphan" in text
    assert "Extremely Severe Cyclone Fani" in text
    assert "Extremely Severe Cyclone Biparjoy" in text
    assert "3 Strongest Moments to Highlight" in text
    assert "Known Weak Moments" in text
    assert "Tier-0 Fallback & Operational Governance Log" in text
