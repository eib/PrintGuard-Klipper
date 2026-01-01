from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from ...core.state.manager import ws_manager, state_manager
from ...core.state.models import WebSocketEvent


router = APIRouter(prefix="/ws")

@router.websocket("/live")
async def live_updates_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    await websocket.send_json({
        "event": WebSocketEvent.INITIAL_SYNC.value,
        "data": state_manager.get_all_json()
    })
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)