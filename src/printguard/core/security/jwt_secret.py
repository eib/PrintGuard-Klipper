"""JWT secret key management with auto-generation."""
import json
import logging
import secrets
from pathlib import Path
from typing import Optional

from ..config import settings

logger = logging.getLogger(__name__)

_jwt_secret: Optional[str] = None


def ensure_jwt_secret() -> str:
    """Ensure JWT secret key exists.

    If JWT_SECRET_KEY is blank/default, loads from file or generates new key.
    Generated keys are persisted to DATA_DIR and printed once to terminal.

    Returns the secret key to use.
    """
    global _jwt_secret
    if _jwt_secret:
        return _jwt_secret

    # If a real secret is configured, use it
    if settings.JWT_SECRET_KEY and settings.JWT_SECRET_KEY != "":
        _jwt_secret = settings.JWT_SECRET_KEY
        return _jwt_secret

    # Try loading from file
    keys_path = settings.DATA_DIR / "jwt_secret.json"
    if keys_path.exists():
        secret = _load_from_file(keys_path)
        if secret:
            _jwt_secret = secret
            return _jwt_secret

    # Generate and persist
    _jwt_secret = _generate_and_persist(keys_path)
    return _jwt_secret


def _load_from_file(keys_path: Path) -> Optional[str]:
    try:
        data = json.loads(keys_path.read_text(encoding="utf-8"))
        return data.get("secret_key")
    except Exception:
        logger.exception("Failed reading JWT secret file")
        return None


def _generate_and_persist(keys_path: Path) -> str:
    secret = secrets.token_urlsafe(32)

    keys_path.parent.mkdir(parents=True, exist_ok=True)
    keys_path.write_text(
        json.dumps({"secret_key": secret}, indent=2),
        encoding="utf-8",
    )

    # Print once to terminal
    print("\n" + "=" * 60)
    print("JWT SECRET KEY AUTO-GENERATED")
    print("=" * 60)
    print(f"Secret: {secret}")
    print(f"Saved to: {keys_path}")
    print("Set JWT_SECRET_KEY env var to use a custom key.")
    print("=" * 60 + "\n")

    logger.info("Generated and saved JWT secret to %s", keys_path)
    return secret


def get_jwt_secret() -> str:
    """Get the active JWT secret. Call ensure_jwt_secret() first during startup."""
    if _jwt_secret is None:
        return ensure_jwt_secret()
    return _jwt_secret
