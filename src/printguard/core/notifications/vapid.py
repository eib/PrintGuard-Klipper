import json
import logging
from base64 import urlsafe_b64encode
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VapidKeys:
    public_key: str
    private_key: str
    subject: str


def ensure_vapid_configured() -> Optional[VapidKeys]:
    """Ensure WebPush VAPID keys exist.

    Loads from settings.WEBPUSH_VAPID_KEYS_PATH if present.
    Otherwise, generates new keys and persists them under DATA_DIR (Docker volume).

    Returns loaded/generated keys, or None if something went wrong.
    """

    keys_path = settings.WEBPUSH_VAPID_KEYS_PATH
    if keys_path and keys_path.exists():
        keys = load_vapid_from_file(keys_path)
        if keys:
            return keys

    if keys_path is None:
        keys_path = settings.DATA_DIR / "webpush_vapid_keys.json"

    return _generate_and_persist(keys_path)


def load_vapid_from_file(keys_path: Path) -> Optional[VapidKeys]:
    try:
        data = json.loads(keys_path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("Failed reading VAPID keys file")
        return None

    public_key = data.get("public_key")
    private_key = data.get("private_key")
    subject = data.get("subject")

    if not (public_key and private_key and subject):
        logger.warning("VAPID keys file missing required fields: %s", str(keys_path))
        return None

    return VapidKeys(public_key=public_key, private_key=private_key, subject=subject)


def _generate_and_persist(keys_path: Path) -> Optional[VapidKeys]:
    keys_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate P-256 keypair
    private_key = ec.generate_private_key(ec.SECP256R1())

    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )

    # Persist private key as a PEM file and store its path in the JSON.
    private_pem_path = keys_path.parent / "webpush_vapid_private_key.pem"
    private_pem_path.write_bytes(private_pem)

    public_numbers = private_key.public_key().public_numbers()
    x = public_numbers.x.to_bytes(32, "big")
    y = public_numbers.y.to_bytes(32, "big")
    raw_uncompressed = b"\x04" + x + y
    public_key_b64url = urlsafe_b64encode(raw_uncompressed).rstrip(b"=").decode("ascii")

    subject = "mailto:admin@localhost"

    keys = VapidKeys(
        public_key=public_key_b64url,
        private_key=str(private_pem_path),
        subject=subject,
    )

    payload: Dict[str, Any] = {
        "public_key": keys.public_key,
        "private_key": keys.private_key,
        "subject": keys.subject,
    }
    keys_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    logger.warning(
        "VAPID keys file missing/invalid; generated and persisted VAPID keys at %s. "
        "Public key (use in frontend): %s",
        str(keys_path),
        keys.public_key,
    )

    return keys
