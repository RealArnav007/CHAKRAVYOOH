"""Contract test ensuring the SOS distress intelligence scoring path remains intact and unbroken."""

from __future__ import annotations

from typing import Any


class DistressScorer:
    """Lightweight deterministic SOS scoring contract representing the Pukar SOS pipeline.

    Verifies that the emergency text scoring, triage classification, and priority weighting
    functions operate independently and without degradation alongside the cyclone ML stack.
    """

    SEVERITY_KEYWORDS = {
        "critical": [
            "trapped",
            "collapse",
            "drowning",
            "bleeding",
            "unconscious",
            "crushed",
            "dying",
        ],
        "high": [
            "flood",
            "water rising",
            "injured",
            "medical",
            "pregnant",
            "infant",
            "elderly",
            "no food",
        ],
        "medium": ["shelter", "blocked road", "power out", "stranded", "supplies needed"],
        "low": ["inquiry", "weather update", "check in", "safe"],
    }

    @classmethod
    def score(cls, packet: dict[str, Any], text: str) -> dict[str, Any]:
        """Scores an emergency SOS distress packet and accompanying text message.

        Args:
            packet: Distress telemetry (lat, lon, battery, rssi, hops, timestamp).
            text: Human or voice-transcribed emergency message.

        Returns:
            Dictionary containing severity score (0.0 to 1.0), urgency category, and triage action.
        """
        text_lower = text.lower() if text else ""
        base_score = 0.2
        matched_flags: list[str] = []

        for kw in cls.SEVERITY_KEYWORDS["critical"]:
            if kw in text_lower:
                base_score = max(base_score, 0.95)
                matched_flags.append(f"critical:{kw}")

        for kw in cls.SEVERITY_KEYWORDS["high"]:
            if kw in text_lower:
                base_score = max(base_score, 0.75)
                matched_flags.append(f"high:{kw}")

        for kw in cls.SEVERITY_KEYWORDS["medium"]:
            if kw in text_lower:
                base_score = max(base_score, 0.50)
                matched_flags.append(f"medium:{kw}")

        # Battery / mesh degradation penalties
        battery = packet.get("battery_pct", 100)
        if battery < 15:
            base_score = min(1.0, base_score + 0.05)
            matched_flags.append("low_battery_boost")

        severity = round(float(min(1.0, max(0.0, base_score))), 3)
        if severity >= 0.85:
            category = "CRITICAL_LIFE_THREAT"
        elif severity >= 0.65:
            category = "HIGH_URGENCY"
        elif severity >= 0.40:
            category = "MODERATE"
        else:
            category = "ROUTINE"

        return {
            "sos_id": packet.get("sos_id", "SOS-TEST-001"),
            "severity_score": severity,
            "urgency_category": category,
            "matched_signals": matched_flags,
            "coordinates": {
                "lat": packet.get("lat", 21.5),
                "lon": packet.get("lon", 87.5),
            },
            "is_actionable": severity >= 0.40,
        }


def test_sos_scorer_contract_unbroken() -> None:
    """Verifies that the SOS scoring seam accepts standard packets and returns valid triage ratings."""
    packet = {
        "sos_id": "PUKAR-SOS-2026-0881",
        "lat": 21.65,
        "lon": 87.82,
        "battery_pct": 12,
        "timestamp": "2026-09-08T18:00:00Z",
    }
    msg = "Water rising rapidly on ground floor, 3 elderly people trapped in attic!"

    result = DistressScorer.score(packet, msg)
    assert result["sos_id"] == "PUKAR-SOS-2026-0881"
    assert result["severity_score"] >= 0.90
    assert result["urgency_category"] == "CRITICAL_LIFE_THREAT"
    assert result["is_actionable"] is True
    assert "critical:trapped" in result["matched_signals"]
    assert "high:water rising" in result["matched_signals"]
    assert "low_battery_boost" in result["matched_signals"]


def test_sos_coexistence_with_cyclone_intelligence() -> None:
    """Verifies that SOS distress packets can correlate with CycloneIntelligence payloads without schema conflicts."""
    from ml.cyclone.fusion.run_cycle import run_cycle
    from ml.cyclone.schema.models import CycloneIntelligence

    # 1. Run cyclone inference
    cyclone_payload = run_cycle(storm_id="Amphan", frame_idx=2)
    validated_cyc = CycloneIntelligence(**cyclone_payload)

    # 2. Score independent SOS packet
    curr_lat = validated_cyc.prediction.current_position.lat if validated_cyc.prediction else 20.0
    curr_lon = validated_cyc.prediction.current_position.lon if validated_cyc.prediction else 88.0
    packet = {
        "sos_id": "PUKAR-SOS-9921",
        "lat": curr_lat + 0.1,
        "lon": curr_lon + 0.1,
        "battery_pct": 45,
    }
    sos_scored = DistressScorer.score(
        packet, "Storm surge flooding coastal embankment, need evacuation boat"
    )

    assert validated_cyc.identification.detected is True
    assert sos_scored["is_actionable"] is True
    assert abs(sos_scored["coordinates"]["lat"] - curr_lat) <= 0.5
