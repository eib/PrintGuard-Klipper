from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

class Settings(BaseSettings):
    # --- App Info ---
    APP_NAME: str = "PrintGuard"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # --- Database ---
    DATA_DIR: Path = PROJECT_ROOT / "data"
    DATABASE_PATH: Path | None = None
    DATABASE_URL: str | None = None
    
    # --- ML / Model Config ---
    MODEL_REPO_ID: str = "oliverbravery/printguard"
    MODEL_FILES: List[str] = ["model.onnx", "opt.json", "prototypes.pkl"]
    MODEL_DIR: Path = PROJECT_ROOT / "models"

    # --- MediaMTX ---
    MEDIAMTX_API_URL: str = "http://localhost:9997/v3"
    MEDIAMTX_WEBRTC_URL: str = "http://localhost:8889"

    # --- SafeHTTPClient ---
    MAX_RETRIES: int = 3
    INITIAL_DELAY: float = 0.5
    DEFAULT_TIMEOUT: float = 10.0

    # --- Detection ---
    MAX_DETECTON_HISTORY: int = 100

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    REDIS_CHANNEL: str = "printguard:events"

    # --- Pydantic Configuration ---
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("MODEL_DIR", "DATA_DIR")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist on startup."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    def model_post_init(self, __context) -> None:
        """Compute derived paths after all fields are set."""
        if self.DATABASE_PATH is None:
            object.__setattr__(self, "DATABASE_PATH", self.DATA_DIR / "printguard.db")
        if self.DATABASE_URL is None:
            object.__setattr__(self, "DATABASE_URL", f"sqlite+aiosqlite:///{self.DATABASE_PATH}")

settings = Settings()