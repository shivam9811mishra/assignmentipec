from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket_manager import ws_manager

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/live")
async def websocket_live_feed(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type": "PONG"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
