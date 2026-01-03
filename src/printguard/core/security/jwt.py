"""JWT token creation and verification."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from jose import JWTError, jwt
from pydantic import BaseModel

from ..config import settings
from ..db.types import IdentityType, ScopeType
from .jwt_secret import get_jwt_secret


class TokenData(BaseModel):
    """Decoded JWT payload."""
    sub: uuid.UUID  # identity_id
    type: IdentityType
    scopes: List[ScopeType]
    exp: datetime


class TokenResponse(BaseModel):
    """Token endpoint response."""
    access_token: str
    token_type: str = "bearer"


def create_access_token(
    identity_id: uuid.UUID,
    identity_type: IdentityType,
    scopes: List[ScopeType],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(identity_id),
        "type": identity_type.value,
        "scopes": [s.value for s in scopes],
        "exp": expire,
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT. Returns None if invalid."""
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[settings.JWT_ALGORITHM])
        return TokenData(
            sub=uuid.UUID(payload["sub"]),
            type=IdentityType(payload["type"]),
            scopes=[ScopeType(s) for s in payload.get("scopes", [])],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )
    except (JWTError, KeyError, ValueError):
        return None
