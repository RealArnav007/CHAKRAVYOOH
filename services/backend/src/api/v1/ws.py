import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from src.config import get_settings
from src.realtime.connection_manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket, token: str = Query(None)):
    """
    Real-time WebSocket endpoint for the Web Command Center.
    Requires ?token=<jwt> query parameter to prevent unauthorized eavesdropping.
    """
    settings = get_settings()
    
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return
        
    try:
        # Verify JWT signature
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token payload")
            return
    except JWTError as e:
        logger.warning(f"WebSocket auth failed: {e}")
        await websocket.close(code=1008, reason="Invalid or expired token")
        return
        
    # Authenticated
    await manager.connect(websocket)
    try:
        while True:
            # Mostly expecting keep-alives
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
