"""Authentication routes: PKCE authorization code flow, M2M client_credentials, and /me."""
from enum import Enum
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import uuid

from ..deps import get_services
from ..deps_auth import get_current_identity
from ...core.db.session import ServiceManager
from ...core.db.types import IdentityType, ScopeType
from ...core.security.passwords import verify_password
from ...core.security.jwt import TokenResponse, TokenData, create_access_token
from ...core.security.pkce import PkceMethod, create_auth_code, verify_and_consume_code

router = APIRouter(prefix="/auth")


class GrantType(str, Enum):
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"


class AuthorizationRequest(BaseModel):
    """Request body for /authorize (PKCE)."""
    username: str
    password: str
    code_challenge: str
    code_challenge_method: PkceMethod = PkceMethod.S256
    redirect_uri: Optional[str] = None
    state: Optional[str] = None


class TokenRequest(BaseModel):
    """Request body for /token endpoint."""
    grant_type: GrantType
    # For authorization_code grant
    code: Optional[str] = None
    code_verifier: Optional[str] = None
    redirect_uri: Optional[str] = None
    # For client_credentials grant
    client_id: Optional[uuid.UUID] = None
    client_secret: Optional[str] = None


class MeResponse(BaseModel):
    """Current identity info."""
    identity_id: uuid.UUID
    type: IdentityType
    scopes: list[ScopeType]


@router.post("/authorize")
async def authorize(
    data: AuthorizationRequest,
    services: ServiceManager = Depends(get_services),
):
    """Authorization endpoint for PKCE flow.
    
    Authenticates user and returns an authorization code.
    The code must be exchanged at /token with grant_type=authorization_code.
    """
    user = await services.identities.get_user_by_username(data.username)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    code = create_auth_code(
        identity_id=user.identity.id,
        code_challenge=data.code_challenge,
        code_challenge_method=data.code_challenge_method,
        redirect_uri=data.redirect_uri,
    )

    if data.redirect_uri:
        redirect_url = f"{data.redirect_uri}?code={code}"
        if data.state:
            redirect_url += f"&state={data.state}"
        return RedirectResponse(url=redirect_url, status_code=302)

    return {"code": code, "state": data.state}


@router.post("/token", response_model=TokenResponse)
async def token(
    data: TokenRequest,
    services: ServiceManager = Depends(get_services),
):
    """OAuth2 token endpoint.
    
    Supports:
    - authorization_code: Exchange PKCE code for token
    - client_credentials: M2M service account authentication
    """
    if data.grant_type == GrantType.AUTHORIZATION_CODE:
        if not data.code or not data.code_verifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="code and code_verifier required for authorization_code grant",
            )
        identity_id = verify_and_consume_code(
            code=data.code,
            code_verifier=data.code_verifier,
            redirect_uri=data.redirect_uri,
        )
        if not identity_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authorization code, or PKCE verification failed",
            )
        identity = await services.identities.get_identity(identity_id)

    elif data.grant_type == GrantType.CLIENT_CREDENTIALS:
        if not data.client_id or not data.client_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="client_id and client_secret required for client_credentials grant",
            )
        identity = await services.identities.get_identity(data.client_id)
        if not identity or not identity.service_account:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not verify_password(data.client_secret, identity.service_account.client_secret_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported grant_type")

    if not identity:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identity not found")

    scopes = [s.scope for s in identity.scopes]
    access_token = create_access_token(identity.id, identity.type, scopes)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=MeResponse)
async def get_me(current: TokenData = Depends(get_current_identity)):
    """Return current authenticated identity info."""
    return MeResponse(identity_id=current.sub, type=current.type, scopes=current.scopes)
