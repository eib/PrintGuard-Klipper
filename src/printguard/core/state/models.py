from pydantic import BaseModel, Field, field_validator, PlainSerializer
from typing import List, Deque, Annotated
from collections import deque
import uuid
import enum
from datetime import datetime

from ..config import settings

SafeDeque = Annotated[
    Deque, 
    PlainSerializer(lambda d: list(d), return_type=List)
]

class WebSocketEvent(str, enum.Enum):
    # High-Frequency
    PRINTER_LIVE_STATE = "PRINTER_LIVE_STATE"
    CONNECTION_LIVE_STATE = "CONNECTION_LIVE_STATE"
    # Low-Frequency
    PRINTER_UPDATE = "PRINTER_UPDATE"
    COMPONENT_UPDATE = "COMPONENT_UPDATE"
    CONNECTION_UPDATE = "CONNECTION_UPDATE"
    IDENTITY_UPDATE = "USER_UPDATE"
    # Inital Sync
    INITIAL_SYNC = "INITIAL_SYNC"

class WebSocketEventUpdateType(str, enum.Enum):
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"

class InferenceClass(str, enum.Enum):
    SUCCESS = "success"
    DEFECT = "defect"

class PrintingState(str, enum.Enum):
    IDLE = "idle"
    PRINTING = "printing"

class InferenceResult(BaseModel):
    class_name: InferenceClass
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.now)

class ConnectionProviderLiveState(BaseModel):
    connection_id: uuid.UUID
    is_healthy: bool = False
    last_activity: datetime = Field(default_factory=datetime.now)

class PrinterLiveState(BaseModel):
    printer_id: uuid.UUID
    status: PrintingState = PrintingState.OFFLINE
    detection_active: bool = False
    detection_history: SafeDeque = Field(
        default_factory=lambda: deque(maxlen=settings.MAX_DETECTON_HISTORY)
    )

    @field_validator("detection_history", mode="before")
    @classmethod
    def ensure_deque(cls, v):
        if isinstance(v, deque):
            return v
        return deque(v, maxlen=settings.MAX_DETECTON_HISTORY)