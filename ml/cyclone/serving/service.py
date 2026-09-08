"""FastAPI HTTP service exposing historical replay endpoints and live cyclone intelligence."""

from __future__ import annotations

import argparse
import logging
from typing import Any, Dict, List, Optional, Union

from ml.cyclone.replay.replay import (
    normalize_storm_key,
    precompute_replay,
    resolve_preset_frame_index,
)

logger = logging.getLogger(__name__)

# Replay session cursor state: {storm_key: current_frame_idx}
_SESSION_CURSORS: Dict[str, int] = {}
_PRECOMPUTED_STORM_CACHE: Dict[str, List[Dict[str, Any]]] = {}

# Check if FastAPI is available
try:
    from fastapi import FastAPI, HTTPException, Query, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FastAPI = None
    HTTPException = Exception
    FASTAPI_AVAILABLE = False


def get_cached_frames(storm_id: str) -> List[Dict[str, Any]]:
    """Retrieves or precomputes cached frames for a storm."""
    sk = normalize_storm_key(storm_id)
    if sk not in _PRECOMPUTED_STORM_CACHE:
        _PRECOMPUTED_STORM_CACHE[sk] = precompute_replay(storm_id=storm_id)
    return _PRECOMPUTED_STORM_CACHE[sk]


def create_app() -> Any:
    """Factory creating and configuring the FastAPI application."""
    if not FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI is not installed. Please install fastapi and uvicorn to use the HTTP server.")

    app = FastAPI(
        title="Chakravyuh Cyclone Intelligence & Replay Engine",
        version="1.0.0",
        description="High-cadence multi-modal cyclone intelligence and historical replay serving API.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health_check() -> Dict[str, Any]:
        return {
            "status": "ok",
            "service": "chakravyuh-cyclone-brain",
            "version": "1.0.0",
            "fastapi_available": True,
        }

    @app.get("/replay/{storm_id}/next")
    def get_next_frame(storm_id: str) -> Dict[str, Any]:
        """Returns the next frame in the historical replay sequence, advancing the playback cursor."""
        sk = normalize_storm_key(storm_id)
        frames = get_cached_frames(storm_id)
        if not frames:
            raise HTTPException(status_code=404, detail=f"No replay frames found for storm '{storm_id}'.")

        cur_idx = _SESSION_CURSORS.get(sk, 0)
        frame = frames[cur_idx]

        # Advance cursor (loop back to start upon completion)
        _SESSION_CURSORS[sk] = (cur_idx + 1) % len(frames)
        return frame

    @app.post("/replay/{storm_id}/tick")
    @app.post("/tick")
    def post_replay_tick(storm_id: str = "Amphan") -> Dict[str, Any]:
        """Advances the replay tick and returns the new active frame."""
        return get_next_frame(storm_id=storm_id)

    @app.post("/replay/{storm_id}/reset")
    @app.get("/replay/{storm_id}/reset")
    def reset_replay(
        storm_id: str,
        jump: Optional[str] = Query(None, description="Optional preset jump (e.g. 'landfall-24h', 'genesis')"),
    ) -> Dict[str, Any]:
        """Resets the playback cursor for a storm to frame 0 or a specified preset."""
        sk = normalize_storm_key(storm_id)
        frames = get_cached_frames(storm_id)
        if not frames:
            raise HTTPException(status_code=404, detail=f"No replay frames found for storm '{storm_id}'.")

        target_idx = 0
        if jump is not None:
            target_idx = resolve_preset_frame_index(sk, preset=jump, total_frames=len(frames))

        _SESSION_CURSORS[sk] = target_idx
        return {
            "status": "reset",
            "storm": storm_id,
            "cursor_frame": target_idx,
            "total_frames": len(frames),
            "current_frame": frames[target_idx],
        }

    @app.get("/replay/{storm_id}/frame/{frame_idx}")
    def get_specific_frame(storm_id: str, frame_idx: int) -> Dict[str, Any]:
        """Returns a specific frame by integer index."""
        frames = get_cached_frames(storm_id)
        if not frames:
            raise HTTPException(status_code=404, detail=f"No replay frames found for storm '{storm_id}'.")
        if frame_idx < 0 or frame_idx >= len(frames):
            raise HTTPException(status_code=400, detail=f"Frame index {frame_idx} out of range [0, {len(frames) - 1}].")
        return frames[frame_idx]

    @app.get("/replay/{storm_id}/all")
    def get_all_frames(storm_id: str) -> List[Dict[str, Any]]:
        """Returns the full sequence of precomputed frames for a storm."""
        return get_cached_frames(storm_id)

    return app


# Lazy app instance
app = create_app() if FASTAPI_AVAILABLE else None


def main() -> None:
    """CLI runner for serving the FastAPI HTTP service."""
    parser = argparse.ArgumentParser(description="Serve Chakravyuh Cyclone Intelligence Replay HTTP API.")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host bind address (default: 0.0.0.0).")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000).")
    parser.add_argument("--storm", type=str, default="Amphan", help="Default storm to precompute on startup.")
    args = parser.parse_args()

    if not FASTAPI_AVAILABLE:
        print("[ERROR] FastAPI and Uvicorn are required to start the HTTP server. Run: pip install fastapi uvicorn")
        return

    # Pre-cache default storm
    print(f"[SERVING] Precomputing cache for {args.storm}...")
    get_cached_frames(args.storm)

    print(f"[SERVING] Starting Chakravyuh Replay Server on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
