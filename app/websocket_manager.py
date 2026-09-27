import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger("websocket_manager")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        payload = json.dumps(message, default=str)
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                dead_connections.append(connection)
        
        for dead in dead_connections:
            self.disconnect(dead)

    async def broadcast_detection(self, detection_data: Dict[str, Any]):
        await self.broadcast({
            "type": "NEW_DETECTION",
            "data": detection_data
        })

    async def broadcast_alert(self, alert_data: Dict[str, Any]):
        await self.broadcast({
            "type": "NEW_ALERT",
            "data": alert_data
        })

    async def broadcast_camera_status(self, camera_id: str, status: str, last_heartbeat: str):
        await self.broadcast({
            "type": "CAMERA_STATUS_UPDATE",
            "data": {
                "camera_id": camera_id,
                "status": status,
                "last_heartbeat": last_heartbeat
            }
        })

ws_manager = ConnectionManager()
