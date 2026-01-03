"""Authentication dependencies for FastAPI routes."""
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ..core.security.jwt import TokenData, decode_access_token
from ..core.db.types import ScopeType

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


async def get_current_identity(token: Optional[str] = Depends(oauth2_scheme)) -> TokenData:
    """Require a valid JWT and return the decoded token data."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    data = decode_access_token(token)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return data


async def get_current_identity_optional(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[TokenData]:
    """Return decoded token data if present and valid, else None (anonymous)."""
    if not token:
        return None
    return decode_access_token(token)


def require_scopes(required: List[ScopeType]):
    """Dependency factory that checks the user has ALL required scopes."""

    async def _check(current: TokenData = Depends(get_current_identity)) -> TokenData:
        missing = set(required) - set(current.scopes)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scopes: {[s.value for s in missing]}",
            )
        return current

    return _check
