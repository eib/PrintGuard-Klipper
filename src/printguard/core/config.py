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
    DATABASE_PATH: Path = DATA_DIR / "printguard.db"
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATABASE_PATH}"
    
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

    # --- Detection ---
    MAX_DETECTON_HISTORY: int = 100

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

settings = Settings()