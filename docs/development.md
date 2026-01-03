# Development Guide

Guide for setting up a development environment.

## Table of Contents

- [Environment Setup](#environment-setup)
- [Project Structure](#project-structure)
- [Code Style](#code-style)
- [Adding New Features](#adding-new-features)

---

## Environment Setup

### Prerequisites

- Python 3.13+
- Git
- Docker & Docker Compose (for testing)
- VS Code (recommended)

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/oliverbravery/PrintGuard.git
   cd PrintGuard
   git checkout api-redesign  # Development branch
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Start Development Services

**Docker stack**
```bash
docker compose up -d --build
docker compose logs -f printguard
```

## Project Structure

```
PrintGuard/
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Container build
├── mediamtx.yml               # MediaMTX streaming config
├── requirements.txt           # Python dependencies
├── README.md                  # Project overview
│
├── docs/                      # Documentation
│   ├── README.md             # Docs index
│   ├── overview.md           # System overview
│   ├── architecture.md       # Architecture diagrams
│   ├── api.md               # API reference
│   ├── setup.md             # Setup guide
│   └── development.md       # This file
│
├── model/                     # ML model files (downloaded)
│   ├── model.onnx
│   └── opt.json
│
└── src/
    └── printguard/
        ├── main.py            # Application entry point
        │
        ├── api/               # API layer
        │   ├── deps.py       # Dependency injection
        │   └── routes/
        │       ├── __init__.py
        │       └── websocket.py
        │
        ├── cli/               # CLI commands (future)
        │
        └── core/              # Core business logic
            ├── config.py      # Settings management
            ├── networking.py  # HTTP client
            ├── redis_client.py
            ├── stream_manager.py
            ├── worker.py      # Background tasks
            │
            ├── connections/   # Provider integrations
            │   ├── __init__.py
            │   ├── base.py   # Abstract base
            │   └── homeassistant.py
            │
            ├── db/            # Database layer
            │   ├── base.py
            │   ├── session.py
            │   ├── types.py
            │   │
            │   ├── schemas/
            │   │   ├── interactions/  # Pydantic DTOs
            │   │   └── tables/        # SQLAlchemy models
            │   │
            │   └── services/          # CRUD operations
            │       ├── __init__.py
            │       ├── components.py
            │       ├── connections.py
            │       ├── identities.py
            │       └── printers.py
            │
            ├── ml/            # Machine learning
            │   ├── inference.py
            │   └── model.py
            │
            └── state/         # State management
                ├── manager.py
                └── models.py
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `main.py` | App initialization, lifespan events |
| `core/config.py` | Pydantic settings with env vars |
| `core/worker.py` | Background task orchestration |
| `core/stream_manager.py` | MediaMTX integration |
| `core/state/manager.py` | Redis state management |
| `core/ml/inference.py` | Image processing & prediction |
| `core/connections/` | Provider implementations |
| `core/db/services/` | Database CRUD operations |

---

## Code Style

### Python Style

- **Formatter:** Black
- **Linter:** Ruff or Flake8
- **Type Hints:** Required for public APIs
- **Docstrings:** Google style

```python
def process_image(
    image: bytes,
    config: dict[str, float],
    *,
    timeout: float = 10.0,
) -> InferenceResult:
    """Process an image through the inference pipeline.
    
    Args:
        image: Raw image bytes (JPEG/PNG)
        config: Camera tuning config with brightness, contrast, sharpness
        timeout: Maximum processing time in seconds
        
    Returns:
        InferenceResult with class_name, confidence, and timestamp
        
    Raises:
        ValueError: If image format is unsupported
        TimeoutError: If processing exceeds timeout
    """
    ...
```

### Async Conventions

- Use `async def` for I/O operations
- Use `asyncio.to_thread()` for CPU-bound work
- Prefer `async with` for context managers

```python
# Good
async def get_snapshot(path: str) -> Optional[bytes]:
    return await asyncio.to_thread(_capture_sync, path)

# Bad - blocking in async context
async def get_snapshot(path: str) -> Optional[bytes]:
    cap = cv2.VideoCapture(path)  # Blocks!
    ...
```

### Import Organization

```python
# Standard library
import asyncio
import uuid
from typing import Optional, List

# Third-party
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

# Local
from .config import settings
from .db.session import get_session_ctx
from ..state.models import PrinterLiveState
```

---

## Adding New Features

### Adding a New Connection Provider

1. **Create provider module:**
   ```python
   # src/printguard/core/connections/octoprint.py
   from typing import Literal, List, Optional
   from pydantic import BaseModel
   
   from .base import BaseConnection
   from ..db.types import ConnectionType, ComponentType
   
   class OctoPrintConnectionConfig(BaseModel):
       provider: Literal[ConnectionType.OCTOPRINT] = ConnectionType.OCTOPRINT
       url: str
       api_key: str
   
   class OctoPrintCameraConfig(BaseModel):
       provider: Literal[ConnectionType.OCTOPRINT] = ConnectionType.OCTOPRINT
       snapshot_url: str
       brightness: float = 100.0
       contrast: float = 100.0
       sharpness: float = 100.0
   
   class OctoPrintConnection(BaseConnection):
       async def is_healthy(self) -> bool:
           # Implementation
           ...
       
       async def get_camera_entities(self, camera_ids=None):
           # Implementation
           ...
   ```

2. **Register in `__init__.py`:**
   ```python
   # src/printguard/core/connections/__init__.py
   from .octoprint import (
       OctoPrintConnectionConfig,
       OctoPrintCameraConfig,
       OctoPrintConnection,
   )
   
   # Update unions
   ConnectionConfig = Annotated[
       Union[HAConnectionConfig, OctoPrintConnectionConfig],
       Field(discriminator="provider")
   ]
   ```

3. **Update factory function:**
   ```python
   def get_connection_instance(conn, services=None):
       config = conn.configuration.root
       if config.provider == ConnectionType.HOMEASSISTANT:
           return HomeAssistantConnection(config, conn.id, services)
       elif config.provider == ConnectionType.OCTOPRINT:
           return OctoPrintConnection(config, conn.id, services)
       return None
   ```

### Adding a New API Endpoint

1. **Create route module:**
   ```python
   # src/printguard/api/routes/printers.py
   from fastapi import APIRouter, Depends
   from ...core.db.session import get_session_ctx
   
   router = APIRouter(prefix="/printers")
   
   @router.get("/")
   async def list_printers():
       async with get_session_ctx() as services:
           printers = await services.printers.list_printers_details()
           return [PrinterRead.model_validate(p) for p in printers]
   ```

2. **Register in api/routes/__init__.py:**
   ```python
   # src/printguard/api/routes/__init__.py
   from .printers import router as printers
   
   app.include_router(printers.router)
   ```

### Adding Camera Tuning Parameters

The system supports adding new tuning parameters:

1. **Update config model:**
   ```python
   # src/printguard/core/connections/homeassistant.py
   class CameraComponentConfig(HABaseComponentConfig):
       entity_id: str
       brightness: float = Field(100.0, ge=0.0, le=500.0)
       contrast: float = Field(100.0, ge=0.0, le=500.0)
       sharpness: float = Field(100.0, ge=0.0, le=500.0)
       saturation: float = Field(100.0, ge=0.0, le=500.0)  # New!
   ```

2. **Update tuning function:**
   ```python
   # src/printguard/core/ml/inference.py
   def apply_image_tuning(image: Image.Image, tuning: dict) -> Image.Image:
       # ... existing code ...
       
       saturation_factor = _clamp(float(tuning.get("saturation", 100.0))) / 100.0
       image = ImageEnhance.Color(image).enhance(saturation_factor)
       
       return image
   ```

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Pydantic V2](https://docs.pydantic.dev/latest/)
- [Redis Python](https://redis-py.readthedocs.io/)
- [MediaMTX](https://github.com/bluenviron/mediamtx)
