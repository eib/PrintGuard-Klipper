from typing import List, Optional
from pydantic import BaseModel
from ...types import ScopeType

class UserCreate(BaseModel):
    username: str
    password: str
    scopes: List[ScopeType] = [ScopeType.USER]

class ServiceAccountCreate(BaseModel):
    client_secret: str
    scopes: List[ScopeType] = [ScopeType.USER]

class IdentityUpdate(BaseModel):
    # User-specific fields
    username: Optional[str] = None
    password: Optional[str] = None
    # M2M-specific fields
    client_secret: Optional[str] = None
    # Shared fields
    scopes: Optional[List[ScopeType]] = None