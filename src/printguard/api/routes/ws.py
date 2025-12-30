"""WebSocket endpoint for real-time printer updates."""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError

from ...core.config import get_settings
from ...services.events import event_service
from ...services.streams import stream_manager

logger = logging.getLogger(__name__)
router = APIRouter()

settings = get_settings()


async def verify_token(token: str) -> bool:
    """Verify JWT token for WebSocket auth."""
    try:
        jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[getattr(settings, "jwt_algorithm", "HS256")],
        )
        return True
    except JWTError:
        return False


@router.websocket("/ws/{printer_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    printer_id: str,
    token: str = Query(...)
):
    """WebSocket connection for real-time printer updates.
    
    Events sent:
    - inference: {class_name, confidence, actual_fps, paused}
    - inference_state: {running}
    - defect: {class_name, confidence, screenshot}
    - status: {status} (printer status changes)
    """
    if not await verify_token(token):
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
    await event_service.connect(printer_id, websocket)
    logger.info(f"WebSocket connected for printer {printer_id}")

    try:
        source = stream_manager.get_source(printer_id)
        if source and source.processor:
            processor = source.processor
            await websocket.send_json({
                "type": "snapshot",
                "data": {
                    "paused": getattr(processor, "pause_inference", True),
                    "prediction": getattr(processor, "last_result", None),
                    "timeline_results": processor.get_timeline_results() if hasattr(processor, "get_timeline_results") else [],
                }
            })
    except Exception:
        logger.debug("Failed to send WS snapshot for %s", printer_id, exc_info=True)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await event_service.disconnect(printer_id, websocket)
        logger.info(f"WebSocket disconnected for printer {printer_id}")

