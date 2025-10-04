from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.ws_manager import manager

router = APIRouter()


@router.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json({"ready": True})
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(msg)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        return
