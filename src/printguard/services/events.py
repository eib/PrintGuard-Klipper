"""WebSocket event broadcasting service."""

import asyncio
import json
import logging
from typing import Dict, Set, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class EventService:
    """Manages WebSocket connections and broadcasts events to subscribers."""

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, printer_id: str, websocket: WebSocket) -> None:
        """Register a WebSocket connection for a printer."""
        async with self._lock:
            if printer_id not in self._connections:
                self._connections[printer_id] = set()
            self._connections[printer_id].add(websocket)
        logger.debug(f"WebSocket connected for printer {printer_id}")

    async def disconnect(self, printer_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if printer_id in self._connections:
                self._connections[printer_id].discard(websocket)
                if not self._connections[printer_id]:
                    del self._connections[printer_id]
        logger.debug(f"WebSocket disconnected for printer {printer_id}")

    async def broadcast(self, printer_id: str, event_type: str, data: Any) -> None:
        """Broadcast an event to all connections for a printer."""
        connections = self._connections.get(printer_id, set()).copy()
        if not connections:
            return

        message = json.dumps({"type": event_type, "data": data})
        disconnected = []

        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)

        # Clean up disconnected clients
        for ws in disconnected:
            await self.disconnect(printer_id, ws)

    def get_connection_count(self, printer_id: str) -> int:
        """Get number of active connections for a printer."""
        return len(self._connections.get(printer_id, set()))


# Singleton instance
event_service = EventService()

