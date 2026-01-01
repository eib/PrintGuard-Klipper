from fastapi import WebSocket
from typing import Dict, List, Optional
import uuid
from .models import PrinterLiveState, InferenceResult, PrintingState, WebSocketEvent

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
    """The central hub for live state updates and triggers."""
    def __init__(self, ws_manager: ConnectionManager):
        self._states: Dict[uuid.UUID, PrinterLiveState] = {}
        self.ws_manager = ws_manager

    async def update_printer(
        self, 
        printer_id: uuid.UUID, 
        status: Optional[PrintingState] = None, 
        detection_active: Optional[bool] = None, 
        inference_result: Optional[InferenceResult] = None, 
    ):
        """
        Updates the live state with explicit parameters and broadcasts changes.
        """
        if printer_id not in self._states:
            self._states[printer_id] = PrinterLiveState(
                printer_id=printer_id
            )
        state = self._states[printer_id]

        if status:
            state.status = status
        if detection_active:
            state.detection_active = detection_active
        if inference_result:
            state.detection_history.append(inference_result)

        await self.ws_manager.broadcast({
            "event": WebSocketEvent.PRINTER_UPDATE.value,
            "data": state.model_dump(mode="json")
        })

    def get_all_json(self) -> Dict:
        """Returns all states formatted for JSON transmission."""
        return {str(k): v.model_dump(mode="json") for k, v in self._states.items()}

ws_manager = ConnectionManager()
state_manager = GlobalStateManager(ws_manager)