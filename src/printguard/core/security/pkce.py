"""PKCE (Proof Key for Code Exchange) utilities for OAuth 2.0 Authorization Code flow."""
import hashlib
import secrets
import time
from base64 import urlsafe_b64encode
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional
import uuid

from ..config import settings


class PkceMethod(str, Enum):
    S256 = "S256"
    PLAIN = "plain"


_auth_codes: Dict[str, "AuthorizationCode"] = {}


@dataclass
class AuthorizationCode:
    """Stored authorization code with PKCE challenge."""
    code: str
    identity_id: uuid.UUID
    code_challenge: str
    code_challenge_method: PkceMethod
    redirect_uri: Optional[str]
    created_at: float


def generate_auth_code() -> str:
    """Generate a cryptographically secure authorization code."""
    return secrets.token_urlsafe(32)


def create_auth_code(
    identity_id: uuid.UUID,
    code_challenge: str,
    code_challenge_method: PkceMethod = PkceMethod.S256,
    redirect_uri: Optional[str] = None,
) -> str:
    """Create and store an authorization code with PKCE challenge."""
    code = generate_auth_code()
    _auth_codes[code] = AuthorizationCode(
        code=code,
        identity_id=identity_id,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        redirect_uri=redirect_uri,
        created_at=time.time(),
    )
    _cleanup_expired_codes()
    return code


def verify_and_consume_code(
    code: str,
    code_verifier: str,
    redirect_uri: Optional[str] = None,
) -> Optional[uuid.UUID]:
    """Verify PKCE and consume the authorization code.
    
    Returns identity_id if valid, None otherwise.
    """
    auth_code = _auth_codes.pop(code, None)
    if not auth_code:
        return None

    # Check expiry
    if time.time() - auth_code.created_at > settings.AUTH_CODE_EXPIRY_MINUTES * 60:
        return None

    # Check redirect_uri matches (if provided during authorization)
    if auth_code.redirect_uri and auth_code.redirect_uri != redirect_uri:
        return None

    # Verify PKCE
    if not _verify_pkce(code_verifier, auth_code.code_challenge, auth_code.code_challenge_method):
        return None

    return auth_code.identity_id


def _verify_pkce(code_verifier: str, code_challenge: str, method: PkceMethod) -> bool:
    """Verify code_verifier matches code_challenge."""
    if method == PkceMethod.S256:
        # SHA256 hash, base64url encoded without padding
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        computed_challenge = urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        return secrets.compare_digest(computed_challenge, code_challenge)
    elif method == PkceMethod.PLAIN:
        return secrets.compare_digest(code_verifier, code_challenge)
    return False


def _cleanup_expired_codes() -> None:
    """Remove expired authorization codes."""
    now = time.time()
    expired = [k for k, v in _auth_codes.items() if now - v.created_at > settings.AUTH_CODE_EXPIRY_MINUTES * 60]
    for k in expired:
        _auth_codes.pop(k, None)
