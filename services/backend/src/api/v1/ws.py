import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from src.auth.jwt import verify_token
from src.realtime.connection_manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket, token: str = Query(None)):
    """
    Real-time WebSocket endpoint for the Web Command Center.
    Requires ?token=<jwt> query parameter to prevent unauthorized eavesdropping.
    Uses verify_token with type='access' — refresh tokens are explicitly rejected.
    """
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return

    payload = verify_token(token, token_type="access")
    user_id = payload.get("sub")

    if not user_id:
        logger.warning("WebSocket auth failed: invalid or expired token")
        await websocket.close(code=1008, reason="Invalid or expired token")
        return

    # Authenticated
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
