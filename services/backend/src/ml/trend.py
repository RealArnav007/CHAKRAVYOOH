"""
Project Pukar - Zone Escalation & Real-Time Trend Analysis
==========================================================
Detects when a geographic area / rescue zone is escalating, feeding zone severity
multipliers and the "zone ignites" demo beat in Harshit's incident engine.

Pure functional module over timestamp sequences.
Zero database dependencies.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Sequence
import yaml

from .contracts import EscalationResult, EscalationState

logger = logging.getLogger("pukar.ml.trend")

# Default configuration fallback
DEFAULT_CONFIG: dict[str, Any] = {
    "sliding_windows": {
        "recent_window_seconds": 300.0,
        "prior_window_seconds": 900.0,
        "min_reports_for_acceleration": 2,
    },
    "rate_scaling": {
        "saturation_rate_per_min": 4.0,
        "rate_weight": 0.55,
        "acceleration_weight": 0.45,
    },
    "acceleration_scaling": {
        "saturation_acceleration": 2.5,
        "deceleration_damping": 0.50,
    },
    "burst_detection": {
        "burst_interval_seconds": 45.0,
        "min_burst_cluster_size": 3,
        "burst_signal_bonus": 0.15,
    },
    "state_thresholds": {
        "ignited": 0.75,
        "surging": 0.50,
        "escalating": 0.25,
        "steady": 0.08,
        "quiet": 0.0,
    },
}

_CONFIG_CACHE: dict[str, Any] | None = None


def load_trend_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Loads trend analysis configuration from YAML with cached fallback."""
    global _CONFIG_CACHE
    if config_path is None and _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    search_paths = []
    if config_path:
        search_paths.append(Path(config_path))
    else:
        # Standard repository search paths
        search_paths.extend([
            Path(__file__).parent / "configs" / "trend.yaml",
            Path(__file__).parents[4] / "ml" / "configs" / "trend.yaml",
            Path("services/backend/src/ml/configs/trend.yaml"),
            Path("ml/configs/trend.yaml"),
        ])

    for p in search_paths:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                    if isinstance(cfg, dict):
                        if config_path is None:
                            _CONFIG_CACHE = cfg
                        return cfg
            except Exception as e:
                logger.warning("Failed to load trend config from %s: %s", p, e)

    return DEFAULT_CONFIG


def _parse_timestamp(ts: Any) -> float | None:
    """Safely converts various timestamp formats to Unix epoch seconds."""
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        # If timestamp is in milliseconds (e.g. > 1e11), normalize to seconds
        val = float(ts)
        return val / 1000.0 if val > 1e11 else val
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.timestamp()
    if isinstance(ts, str):
        try:
            # Try float/int string first
            return float(ts)
        except ValueError:
            pass
        try:
            # ISO 8601 string parsing
            clean_str = ts.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            return None
    return None


def escalation(
    reports_in_zone: Sequence[Any],
    reference_time: Any | None = None,
    config_path: str | Path | None = None,
) -> EscalationResult:
    """
    Computes real-time zone escalation from sliding-window report arrival dynamics.

    Parameters:
        reports_in_zone: Sequence of report timestamps (epoch float/int, ISO str, datetime).
        reference_time: Optional evaluation epoch timestamp (defaults to latest report timestamp).
        config_path: Optional path to trend.yaml configuration.

    Returns:
        EscalationResult containing rate_per_min, acceleration, escalation_signal (0.0-1.0),
        state_hint, and window report counts.
    """
    cfg = load_trend_config(config_path)
    windows_cfg = cfg.get("sliding_windows", DEFAULT_CONFIG["sliding_windows"])
    rate_cfg = cfg.get("rate_scaling", DEFAULT_CONFIG["rate_scaling"])
    accel_cfg = cfg.get("acceleration_scaling", DEFAULT_CONFIG["acceleration_scaling"])
    burst_cfg = cfg.get("burst_detection", DEFAULT_CONFIG["burst_detection"])
    state_cfg = cfg.get("state_thresholds", DEFAULT_CONFIG["state_thresholds"])

    recent_win_sec = float(windows_cfg.get("recent_window_seconds", 300.0))
    prior_win_sec = float(windows_cfg.get("prior_window_seconds", 900.0))
    min_reports_accel = int(windows_cfg.get("min_reports_for_acceleration", 2))

    # Parse and sort all valid timestamps
    parsed_timestamps: list[float] = []
    for r in reports_in_zone:
        parsed = _parse_timestamp(r)
        if parsed is not None:
            parsed_timestamps.append(parsed)

    parsed_timestamps.sort()

    # Empty case
    if not parsed_timestamps:
        return EscalationResult(
            rate_per_min=0.0,
            acceleration=0.0,
            escalation_signal=0.0,
            state_hint=EscalationState.QUIET.value,
            report_count=0,
            recent_count=0,
            prior_count=0,
        )

    # Reference time anchor (t_now)
    ref_ts = _parse_timestamp(reference_time)
    if ref_ts is None:
        ref_ts = parsed_timestamps[-1]

    # Partition into recent window [t_ref - recent_win_sec, t_ref]
    # and prior baseline window [t_ref - prior_win_sec, t_ref - recent_win_sec]
    recent_cutoff = ref_ts - recent_win_sec
    prior_cutoff = ref_ts - prior_win_sec

    recent_reports = [t for t in parsed_timestamps if recent_cutoff <= t <= ref_ts]
    prior_reports = [t for t in parsed_timestamps if prior_cutoff <= t < recent_cutoff]
    total_window_reports = [t for t in parsed_timestamps if prior_cutoff <= t <= ref_ts]

    n_recent = len(recent_reports)
    n_prior = len(prior_reports)

    # 1. Calculate Arrival Rates (reports per minute)
    recent_duration_min = max(0.1, recent_win_sec / 60.0)
    prior_duration_min = max(0.1, (prior_win_sec - recent_win_sec) / 60.0)

    rate_recent = n_recent / recent_duration_min
    rate_prior = n_prior / prior_duration_min

    # 2. Calculate Rate Acceleration (delta in reports/min)
    if len(total_window_reports) < min_reports_accel:
        acceleration = 0.0
    else:
        acceleration = rate_recent - rate_prior

    # 3. Detect Concentrated Arrival Bursts (rapid consecutive arrivals)
    burst_interval_sec = float(burst_cfg.get("burst_interval_seconds", 45.0))
    min_burst_cluster = int(burst_cfg.get("min_burst_cluster_size", 3))
    burst_bonus_val = float(burst_cfg.get("burst_signal_bonus", 0.15))

    has_active_burst = False
    if len(recent_reports) >= min_burst_cluster:
        # Check if there is a consecutive chain of rapid arrivals
        quick_intervals = 0
        for i in range(1, len(recent_reports)):
            if (recent_reports[i] - recent_reports[i - 1]) <= burst_interval_sec:
                quick_intervals += 1
            else:
                quick_intervals = 0
            if quick_intervals >= (min_burst_cluster - 1):
                has_active_burst = True
                break

    # 4. Compute Escalation Signal (0.0 to 1.0)
    sat_rate = float(rate_cfg.get("saturation_rate_per_min", 4.0))
    w_rate = float(rate_cfg.get("rate_weight", 0.55))
    w_accel = float(rate_cfg.get("acceleration_weight", 0.45))
    sat_accel = float(accel_cfg.get("saturation_acceleration", 2.5))
    decel_damping = float(accel_cfg.get("deceleration_damping", 0.50))

    # Rate component [0.0, 1.0]
    s_rate = min(1.0, max(0.0, rate_recent / sat_rate))

    # Acceleration component [0.0, 1.0]
    if acceleration > 0:
        s_accel = min(1.0, acceleration / sat_accel)
    else:
        # Damped negative acceleration (deceleration)
        s_accel = max(-0.25, (acceleration / sat_accel) * decel_damping)

    raw_signal = (w_rate * s_rate) + (w_accel * s_accel)

    if has_active_burst:
        raw_signal += burst_bonus_val

    escalation_signal = round(min(1.0, max(0.0, raw_signal)), 3)

    # 5. Map to Escalation State Hint
    th_ignited = float(state_cfg.get("ignited", 0.75))
    th_surging = float(state_cfg.get("surging", 0.50))
    th_escalating = float(state_cfg.get("escalating", 0.25))
    th_steady = float(state_cfg.get("steady", 0.08))

    if escalation_signal >= th_ignited:
        state_hint = EscalationState.IGNITED.value
    elif escalation_signal >= th_surging:
        state_hint = EscalationState.SURGING.value
    elif escalation_signal >= th_escalating:
        state_hint = EscalationState.ESCALATING.value
    elif escalation_signal >= th_steady:
        state_hint = EscalationState.STEADY.value
    else:
        state_hint = EscalationState.QUIET.value

    return EscalationResult(
        rate_per_min=round(rate_recent, 3),
        acceleration=round(acceleration, 3),
        escalation_signal=escalation_signal,
        state_hint=state_hint,
        report_count=len(total_window_reports),
        recent_count=n_recent,
        prior_count=n_prior,
    )
