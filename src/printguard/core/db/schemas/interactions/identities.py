import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from ...types import IdentityType, ScopeType

class ScopeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    scope: ScopeType

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username: str

class ServiceAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    client_id: uuid.UUID

class IdentityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: IdentityType
    created_at: datetime
    scopes: List[ScopeRead]
    user: Optional[UserRead] = None
    service_account: Optional[ServiceAccountRead] = None

class UserCreate(BaseModel):
    username: str
    password: str
    scopes: List[ScopeType] = [ScopeType.USER]

class ServiceAccountCreate(BaseModel):
    scopes: List[ScopeType] = [ScopeType.USER]