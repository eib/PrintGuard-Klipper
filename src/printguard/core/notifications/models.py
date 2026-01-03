import uuid
from datetime import datetime
import enum

from pydantic import BaseModel, Field

class PushType(str, enum.Enum):
    PRINTER_DEFECT = "printer_defect"

class PushPayloadBase(BaseModel):
    type: PushType

class PrinterDefectMajorityPushPayload(PushPayloadBase):
    type: PushType = PushType.PRINTER_DEFECT
    printer_id: uuid.UUID
    timestamp: datetime = Field(default_factory=datetime.now)
