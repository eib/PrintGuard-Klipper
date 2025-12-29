"""Configuration settings using pydantic-settings."""

import logging
from pathlib import Path
from functools import lru_cache
from enum import Enum
import json

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class TunnelProvider(str, Enum):
    """Available tunnel providers."""
    LOCAL = "local"
    CLOUDFLARE = "cloudflare"
    NGROK = "ngrok"


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_assignment=True,
    )
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    crypto_private_key: str = ""
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    webui_port: int = 8000

    # Tunnel Settings
    tunnel_provider: TunnelProvider = TunnelProvider.LOCAL

    # Cloudflare Tunnel Settings
    cloudflare_api_token: str = ""
    cloudflare_domain: str = ""
    cloudflare_tunnel_name: str = "printguard-tunnel"
    cloudflare_subdomain: str = "camera"
    cloudflare_tunnel_id: str = ""
    cloudflare_tunnel_secret: str = ""
    cloudflare_account_id: str = ""

    # ngrok Settings
    ngrok_authtoken: str = ""
    ngrok_domain: str = ""
    ngrok_edge: str = ""

    # Model Settings
    model_dir: Path = Path(__file__).parent / "model"

    # Security Settings
    jwt_secret_key: str = "changeme-in-production-use-a-secure-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    # Database Settings
    database_url: str = "sqlite+aiosqlite:///./printguard.db"

    # Screenshot Settings
    screenshot_retention_hours: int = 24
    screenshot_max_count: int = 100
    screenshot_cleanup_interval_minutes: int = 60

    # Dynamic States (Not persisted to .env)
    last_known_public_base_url: str = ""


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.
    
    Returns:
        Settings: The application settings instance.
    """
    settings = Settings()
    
    # Generate VAPID keys if missing
    if not settings.vapid_public_key or not settings.vapid_private_key:
        vapid_file = Path(__file__).parent.parent.parent.parent / ".vapid_keys.json"
        if vapid_file.exists():
            try:
                keys = json.loads(vapid_file.read_text())
                settings.vapid_public_key = keys.get("public_key", "")
                settings.vapid_private_key = keys.get("private_key", "")
            except Exception as e:
                logger.error(f"Failed to load VAPID keys from {vapid_file}: {e}")
        
        if not settings.vapid_public_key or not settings.vapid_private_key:
            logger.info("VAPID keys not found, generating new ones...")
            try:
                from cryptography.hazmat.primitives.asymmetric import ec
                from cryptography.hazmat.primitives import serialization
                import base64
                
                private_key = ec.generate_private_key(ec.SECP256R1())
                private_bytes = private_key.private_numbers().private_value.to_bytes(32, 'big')
                public_key = private_key.public_key()
                public_bytes = public_key.public_bytes(
                    encoding=serialization.Encoding.X962,
                    format=serialization.PublicFormat.UncompressedPoint
                )

                settings.vapid_private_key = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')
                settings.vapid_public_key = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
                
                vapid_file.write_text(json.dumps({
                    "public_key": settings.vapid_public_key,
                    "private_key": settings.vapid_private_key
                }))
                logger.info(f"Generated new VAPID keys and saved to {vapid_file}")
            except Exception as e:
                logger.error(f"Failed to generate VAPID keys: {e}")
                
    return settings


def get_model_dir() -> Path:
    """Get the model directory from settings."""
    return get_settings().model_dir


def update_public_base_url(request_headers: dict):
    """Update the last known public base URL from request headers."""
    settings = get_settings()
    
    proto = request_headers.get("x-forwarded-proto", "http")
    host = request_headers.get("x-forwarded-host") or request_headers.get("host")
    
    if host:
        new_url = f"{proto}://{host}"
        if settings.last_known_public_base_url != new_url:
            settings.last_known_public_base_url = new_url
            logger.debug(f"Updated last known public base URL to: {new_url}")
