import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionCreate(BaseModel):
    """Client request to create/update a push subscription. Identity derived from auth."""
    endpoint: str
    keys: PushSubscriptionKeys
    expiration_time_ms: Optional[int] = None
    user_agent: Optional[str] = Field(default=None, max_length=512)


class PushSubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    identity_id: Optional[uuid.UUID] = None
    endpoint: str
    expiration_time_ms: Optional[int] = None
    user_agent: Optional[str] = None


class PushUnsubscribeRequest(BaseModel):
    endpoint: str
