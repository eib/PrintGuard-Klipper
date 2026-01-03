import uuid
from pydantic import BaseModel, ConfigDict


class PrinterSubscriptionCreate(BaseModel):
    printer_id: uuid.UUID


class PrinterSubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    printer_id: uuid.UUID
    identity_id: uuid.UUID
