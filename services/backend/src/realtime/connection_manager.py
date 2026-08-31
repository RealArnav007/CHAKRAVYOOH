import logging

from fastapi import WebSocket

from src.realtime.events import RealtimeEvent

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, event: RealtimeEvent):
        """
        Broadcasts a RealtimeEvent (as JSON) to all connected clients.
        """
        event_dict = event.model_dump()
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(event_dict)
            except Exception as e:
                logger.error(f"Failed to send message to client, disconnecting: {e}")
                dead_connections.append(connection)
                
        for connection in dead_connections:
            self.disconnect(connection)

# Global connection manager instance
manager = ConnectionManager()
