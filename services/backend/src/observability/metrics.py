"""
Observability Metrics — B21/B22
Tracks latency timings for the SOS ingestion pipeline stages.
"""
import logging
import time

logger = logging.getLogger(__name__)

# In-memory accumulator for pipeline stage latencies (nanoseconds)
_stage_timings: dict[str, list] = {}


class PipelineTimer:
    """Context manager to measure and record a pipeline stage duration."""

    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self._start = None

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        elapsed_ms = (time.perf_counter() - self._start) * 1000
        if self.stage_name not in _stage_timings:
            _stage_timings[self.stage_name] = []
        timings = _stage_timings[self.stage_name]
        timings.append(elapsed_ms)
        # Cap to last 1000 samples to prevent unbounded RAM growth under load
        if len(timings) > 1000:
            _stage_timings[self.stage_name] = timings[-1000:]
        logger.debug(f"[METRIC] {self.stage_name}: {elapsed_ms:.2f}ms")


def get_stage_averages() -> dict[str, float]:
    """Returns the average latency per stage in milliseconds."""
    return {
        stage: sum(times) / len(times)
        for stage, times in _stage_timings.items()
        if times
    }
