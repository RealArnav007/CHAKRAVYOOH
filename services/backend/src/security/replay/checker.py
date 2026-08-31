import time

from src.config import get_settings


def is_packet_expired(created_at_ms: int) -> bool:
    """
    Checks if a packet's timestamp is outside the freshness window.
    Allows up to 5 minutes into the future for offline mesh clock drift (no NTP sync).
    """
    settings = get_settings()
    now_ms = int(time.time() * 1000)
    
    window_ms = settings.REPLAY_WINDOW_SECONDS * 1000
    
    # Too old
    if (now_ms - created_at_ms) > window_ms:
        return True
        
    # Too far in the future (> 5 mins skew due to lack of NTP)
    if (created_at_ms - now_ms) > 300000:
        return True
        
    return False
