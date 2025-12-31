import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict
from .components import ComponentRead

class PrinterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    camera_component: Optional[ComponentRead] = None
    status_component: Optional[ComponentRead] = None
    start_control: Optional[ComponentRead] = None
    stop_control: Optional[ComponentRead] = None

class PrinterCreate(BaseModel):
    name: str
    camera_comp_id: Optional[uuid.UUID] = None
    status_comp_id: Optional[uuid.UUID] = None
    start_ctrl_comp_id: Optional[uuid.UUID] = None
    stop_ctrl_comp_id: Optional[uuid.UUID] = None