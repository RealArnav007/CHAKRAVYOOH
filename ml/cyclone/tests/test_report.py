"""Unit tests for comprehensive evaluation report generation (Markdown + HTML)."""

from __future__ import annotations

from pathlib import Path
import pytest

from ml.cyclone.eval.report import (
    build_html_report,
    build_markdown_report,
    generate_evaluation_figures,
    generate_full_evaluation_report,
)


def test_generate_evaluation_figures(tmp_path: Path) -> None:
    """Tests that all diagnostic and demo storm figures are properly created."""
    figs = generate_evaluation_figures(output_dir=tmp_path)

    expected_keys = [
        "track_comparison",
        "intensity_comparison",
        "confusion_matrices",
        "demo_storm_amphan.png",
        "demo_storm_fani.png",
        "demo_storm_biparjoy.png",
    ]
    for k in expected_keys:
        assert k in figs
        assert figs[k].is_file()
        assert figs[k].stat().st_size > 1000


def test_build_markdown_and_html_report(tmp_path: Path) -> None:
    """Tests that Markdown and standalone HTML reports are generated with all components."""
    figs_dir = tmp_path / "figs"
    fig_paths = generate_evaluation_figures(output_dir=figs_dir)

    md_path = tmp_path / "CHAKRAVYUH_EVAL.md"
    md_content = build_markdown_report(eval_results={}, fig_paths=fig_paths, output_path=md_path)

    assert md_path.is_file()
    assert "# 🌪️ CHAKRAVYUH CYCLONE INTELLIGENCE ENGINE" in md_content
    assert "Headline Metrics" in md_content
    assert "Super Cyclone Amphan" in md_content
    assert "Extremely Severe Cyclone Fani" in md_content

    html_path = tmp_path / "CHAKRAVYUH_EVAL.html"
    build_html_report(md_content=md_content, figs_dir=figs_dir, output_html_path=html_path)

    assert html_path.is_file()
    html_text = html_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html_text
    assert "data:image/png;base64," in html_text  # Self-contained embedded images
    assert "Headline Metrics" in html_text
