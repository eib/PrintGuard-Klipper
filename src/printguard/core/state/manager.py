from fastapi import WebSocket
from typing import Dict, List, Optional
import uuid
import json
from .models import PrinterLiveState, InferenceResult, PrintingState, WebSocketEvent, ConnectionProviderLiveState, WebSocketEventUpdateType
from ..config import settings
from ..redis_client import get_redis

# Redis key patterns
PRINTER_STATE_KEY = "printer:live:{}"
PRINTER_HISTORY_KEY = "printer:history:{}"
CONNECTION_STATE_KEY = "connection:live:{}"


class ConnectionManager:
    """Manages active WebSocket subscribers and broadcasting."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Sends a JSON-serializable dict to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


class GlobalStateManager:
    """The central hub for live state updates using Redis."""
    def __init__(self, ws_manager: ConnectionManager):
        self.ws_manager = ws_manager

    async def _get_printer_state(self, printer_id: uuid.UUID) -> PrinterLiveState:
        """Fetch printer state from Redis, creating if not exists."""
        r = await get_redis()
        key = PRINTER_STATE_KEY.format(printer_id)
        data = await r.get(key)
        if data:
            state_dict = json.loads(data)
            history_key = PRINTER_HISTORY_KEY.format(printer_id)
            history_data = await r.lrange(history_key, 0, -1)
            state_dict["detection_history"] = [json.loads(h) for h in history_data]
            return PrinterLiveState.model_validate(state_dict)
        return PrinterLiveState(printer_id=printer_id)

    async def _save_printer_state(self, state: PrinterLiveState) -> None:
        """Save printer state to Redis (excludes detection_history)."""
        r = await get_redis()
        key = PRINTER_STATE_KEY.format(state.printer_id)
        state_dict = state.model_dump(mode="json")
        state_dict.pop("detection_history", None)
        await r.set(key, json.dumps(state_dict))

    async def _append_inference_result(self, printer_id: uuid.UUID, result: InferenceResult) -> None:
        """Append inference result to Redis list with rolling window."""
        r = await get_redis()
        key = PRINTER_HISTORY_KEY.format(printer_id)
        await r.lpush(key, result.model_dump_json())
        await r.ltrim(key, 0, settings.MAX_DETECTON_HISTORY - 1)

    async def update_printer_state(
        self, 
        printer_id: uuid.UUID, 
        status: Optional[PrintingState] = None, 
        detection_active: Optional[bool] = None, 
        inference_result: Optional[InferenceResult] = None, 
    ):
        """Updates the live state and publishes to Redis channel."""
        state = await self._get_printer_state(printer_id)
        if status:
            state.status = status
        if detection_active is not None:
            state.detection_active = detection_active
        if inference_result:
            await self._append_inference_result(printer_id, inference_result)
            state.detection_history.append(inference_result)
        await self._save_printer_state(state)
        # Publish update to Redis channel
        r = await get_redis()
        message = {
            "event": WebSocketEvent.PRINTER_LIVE_STATE.value,
            "data": state.model_dump(mode="json")
        }
        await r.publish(settings.REDIS_CHANNEL, json.dumps(message))

    async def update_connection_state(self, connection_id: uuid.UUID, is_healthy: bool):
        """Updates connection state in Redis and publishes."""
        r = await get_redis()
        key = CONNECTION_STATE_KEY.format(connection_id)
        data = await r.get(key)
        if data:
            state = ConnectionProviderLiveState.model_validate_json(data)
        else:
            state = ConnectionProviderLiveState(connection_id=connection_id)
        state.is_healthy = is_healthy
        await r.set(key, state.model_dump_json())
        message = {
            "event": WebSocketEvent.CONNECTION_LIVE_STATE.value,
            "data": state.model_dump(mode="json")
        }
        await r.publish(settings.REDIS_CHANNEL, json.dumps(message))

    async def send_update(self, update_type: WebSocketEventUpdateType, event: WebSocketEvent, record_id: str):
        """Publish CRUD update notification to Redis channel."""
        r = await get_redis()
        message = {
            "event": event.value,
            "data": {
                "type": update_type.value,
                "record_id": record_id
            }
        }
        await r.publish(settings.REDIS_CHANNEL, json.dumps(message))

    async def get_all_json(self) -> Dict:
        """Returns all states from Redis formatted for JSON transmission."""
        r = await get_redis()
        # Fetch all printer states
        printer_states = {}
        async for key in r.scan_iter(match="printer:live:*"):
            printer_id = key.split(":")[-1]
            state = await self._get_printer_state(uuid.UUID(printer_id))
            printer_states[printer_id] = state.model_dump(mode="json")
        # Fetch all connection states
        connection_states = {}
        async for key in r.scan_iter(match="connection:live:*"):
            data = await r.get(key)
            if data:
                state = ConnectionProviderLiveState.model_validate_json(data)
                connection_states[str(state.connection_id)] = state.model_dump(mode="json")
        return {
            "printer_live_states": printer_states,
            "connection_live_states": connection_states,
        }


ws_manager = ConnectionManager()
state_manager = GlobalStateManager(ws_manager)