import pytest
import time
from src.security.replay.checker import is_packet_expired
from src.sos.deduplication.dedup import is_duplicate_msg
from src.database.models import SOSReport
from datetime import datetime, timezone

def test_replay_checker_valid():
    """Test that a recent packet is not expired."""
    now_ms = int(time.time() * 1000)
    # 30 seconds ago
    assert is_packet_expired(now_ms - 30000) is False
    
def test_replay_checker_expired():
    """Test that a packet older than REPLAY_WINDOW_SECONDS is rejected."""
    now_ms = int(time.time() * 1000)
    # 6 minutes ago
    assert is_packet_expired(now_ms - 360000) is True

def test_replay_checker_future():
    """Test that a packet far in the future (skew) is rejected."""
    now_ms = int(time.time() * 1000)
    # 6 minutes in the future
    assert is_packet_expired(now_ms + 360000) is True

@pytest.mark.asyncio
async def test_deduplication(async_db):
    """Test the idempotent msg_id deduplication logic."""
    msg_id = "test-msg-123"
    
    # Initially not a duplicate
    assert await is_duplicate_msg(async_db, msg_id) is False
    
    # Insert a dummy report
    report = SOSReport(
        msg_id=msg_id, origin_id="o1", origin_key_id="ok1",
        created_at=datetime.now(timezone.utc), nonce="n1",
        lat=1.0, lon=1.0, acc=1.0, trigger_type="t", request_type="r",
        severity="s", regex_score=0, local_model_score=0, confidence=0.0,
        payload_enc="p"
    )
    async_db.add(report)
    await async_db.commit()
    
    # Now it should be flagged as a duplicate
    assert await is_duplicate_msg(async_db, msg_id) is True
