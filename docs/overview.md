# System Overview

This document provides a comprehensive overview of PrintGuard's architecture, components, and data flows.

## Table of Contents

- [System Overview](#system-overview)
- [Core Components](#core-components)
- [Data Communication](#data-communication)
- [Detection Pipeline](#detection-pipeline)
- [State Management](#state-management)
- [Connection Providers](#connection-providers)

---

## System Overview

PrintGuard is built on a modern, event-driven architecture designed for real-time 3D print monitoring. The system consists of several interconnected services:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PrintGuard System                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │  Web Client  │    │   FastAPI    │    │   Worker     │              │
│  │  (WebSocket) │◀──▶│   Server     │◀──▶│ Orchestrator │              │
│  └──────────────┘    └──────┬───────┘    └──────┬───────┘              │
│                             │                    │                      │
│         ┌───────────────────┼────────────────────┼─────────────┐       │
│         │                   │                    │             │       │
│         ▼                   ▼                    ▼             ▼       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ ┌─────────┐ │
│  │    Redis     │    │   SQLite     │    │   MediaMTX   │ │  ONNX   │ │
│  │  Pub/Sub +   │    │   Database   │    │   Streams    │ │  Model  │ │
│  │    Cache     │    │              │    │              │ │         │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ └─────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │     External Integrations     │
                    ├───────────────────────────────┤
                    │  • Home Assistant (Cameras)   │
                    │  • OctoPrint (Coming Soon)    │
                    │  • Bambu Labs (Coming Soon)   │
                    └───────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**: Each component has a single responsibility
2. **Event-Driven**: State changes propagate via Redis pub/sub
3. **Async-First**: Built on asyncio for efficient I/O handling
4. **Provider Agnostic**: Extensible connection system for different integrations

---

## Core Components

### FastAPI Server (`main.py`)

The main application entry point that:
- Initializes the database and creates tables
- Downloads ML models from HuggingFace if not present
- Syncs cameras with MediaMTX
- Starts background worker tasks
- Sets up WebSocket and API routes

```python
# Lifecycle events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Init DB, download models, sync cameras, start workers
    await init_db()
    await download_model()
    await stream_manager.sync_cameras()
    await worker_orchestrator.start()
    yield
    # Shutdown: Stop workers gracefully
    await worker_orchestrator.stop()
```

### Worker Orchestrator (`core/worker.py`)

Manages three background task loops:

| Loop | Interval | Purpose |
|------|----------|---------|
| Connection Health | 10s | Checks connection availability |
| Printer Status | 10s | Polls printer states from providers |
| Inference | 0.5s | Runs defect detection on active printers |

```
┌─────────────────────────────────────────────────────────────┐
│                    Worker Orchestrator                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  Health Loop    │  │  Status Loop    │  │  Inference  │ │
│  │  (10s interval) │  │  (10s interval) │  │  (0.5s)     │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘ │
│           │                    │                   │        │
│           ▼                    ▼                   ▼        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              State Manager (Redis)                      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Stream Manager (`core/stream_manager.py`)

Handles camera stream registration with MediaMTX:

- **Register Camera**: Creates MediaMTX path for RTSP ingestion
- **Unregister Camera**: Removes MediaMTX path
- **Get Snapshot**: Captures frame via OpenCV from RTSP stream
- **Sync Cameras**: Reconciles DB cameras with MediaMTX state

### State Manager (`core/state/manager.py`)

Central hub for live state using Redis:

- **Printer States**: Detection status, history, active detection flag
- **Connection States**: Health status, last activity timestamp
- **WebSocket Broadcasting**: Publishes events to Redis channel
- **Detection Logic**: Determines when detection should be active

---

## Data Communication

### WebSocket Flow

```
┌──────────┐                    ┌──────────┐                    ┌──────────┐
│  Client  │                    │  Server  │                    │  Redis   │
└────┬─────┘                    └────┬─────┘                    └────┬─────┘
     │                               │                               │
     │  1. Connect to /ws/live       │                               │
     │──────────────────────────────▶│                               │
     │                               │                               │
     │  2. INITIAL_SYNC (full state) │                               │
     │◀──────────────────────────────│                               │
     │                               │                               │
     │                               │  3. Subscribe to channel      │
     │                               │──────────────────────────────▶│
     │                               │                               │
     │                               │  4. State change published    │
     │                               │◀──────────────────────────────│
     │                               │                               │
     │  5. PRINTER_LIVE_STATE        │                               │
     │◀──────────────────────────────│                               │
     │                               │                               │
```

### Event Types

| Event | Direction | Description |
|-------|-----------|-------------|
| `INITIAL_SYNC` | Server → Client | Full state on connection |
| `PRINTER_LIVE_STATE` | Server → Client | Printer detection updates |
| `CONNECTION_LIVE_STATE` | Server → Client | Connection health updates |
| `PRINTER_UPDATE` | Server → Client | Printer CRUD notification |
| `COMPONENT_UPDATE` | Server → Client | Component CRUD notification |
| `CONNECTION_UPDATE` | Server → Client | Connection CRUD notification |

---

## Detection Pipeline

The inference pipeline processes camera frames to detect print failures:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Detection Pipeline                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. GET SNAPSHOT           2. APPLY TUNING          3. PREPROCESS       │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐      │
│  │   MediaMTX  │          │  Brightness │          │   Resize    │      │
│  │    RTSP     │─────────▶│  Contrast   │─────────▶│  Grayscale  │      │
│  │   Stream    │          │  Sharpness  │          │  Normalize  │      │
│  └─────────────┘          └─────────────┘          └──────┬──────┘      │
│                                                           │             │
│                                                           ▼             │
│  6. UPDATE STATE           5. CLASSIFY              4. INFERENCE        │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐      │
│  │   Redis     │          │  Distance   │          │    ONNX     │      │
│  │   State     │◀─────────│  to Proto-  │◀─────────│   Model     │      │
│  │  Manager    │          │   types     │          │  Embedding  │      │
│  └─────────────┘          └─────────────┘          └─────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Image Tuning

Camera-specific adjustments are applied before inference:

```python
def apply_image_tuning(image: Image, tuning: dict) -> Image:
    # Values are 0-500%, with 100% being neutral
    brightness_factor = tuning.get("brightness", 100.0) / 100.0
    contrast_factor = tuning.get("contrast", 100.0) / 100.0
    sharpness_factor = tuning.get("sharpness", 100.0) / 100.0
    
    image = ImageEnhance.Brightness(image).enhance(brightness_factor)
    image = ImageEnhance.Contrast(image).enhance(contrast_factor)
    image = ImageEnhance.Sharpness(image).enhance(sharpness_factor)
    return image
```

### Prototypical Network Inference

The model uses prototypical networks for few-shot classification:

1. **Embedding**: Frame is encoded to a feature vector
2. **Distance Calculation**: Euclidean distance to class prototypes
3. **Classification**: Closest prototype determines class (success/defect)
4. **Confidence**: Derived from distance (`1 / (1 + distance)`)

---

## State Management

### Redis Key Patterns

| Pattern | Purpose | TTL |
|---------|---------|-----|
| `printer:live:{id}` | Printer live state | None |
| `printer:history:{id}` | Detection history (rolling) | None |
| `connection:live:{id}` | Connection health state | None |

### Printer Live State

```python
class PrinterLiveState(BaseModel):
    printer_id: uuid.UUID
    status: PrintingState  # IDLE or PRINTING
    detection_active: bool  # Auto-managed based on status + health
    detection_history: Deque[InferenceResult]  # Rolling window
```

### Detection Auto-Toggle Logic

Detection automatically enables/disables based on:

```python
def _should_detect(status: PrintingState, connection_healthy: bool) -> bool:
    """Detection ON only when: connection healthy AND status is PRINTING"""
    return connection_healthy and status == PrintingState.PRINTING
```

---

## Connection Providers

### Provider Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Connection Provider System                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐                                           │
│  │  BaseConnection │◀─────────────────────────────────┐        │
│  │   (Abstract)    │                                  │        │
│  └────────┬────────┘                                  │        │
│           │                                           │        │
│           │ implements                                │        │
│           ▼                                           │        │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐│
│  │  HomeAssistant  │    │   OctoPrint     │    │  BambuLabs  ││
│  │   Connection    │    │  (Planned)      │    │  (Planned)  ││
│  └─────────────────┘    └─────────────────┘    └─────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Home Assistant Integration

Provides camera, status, and control entities:

| Component Type | HA Domains | Purpose |
|----------------|------------|---------|
| Camera | `camera.*` | Video feeds for detection |
| Status | `sensor.*`, `binary_sensor.*` | Print state monitoring |
| Control | `switch.*`, `button.*`, etc. | Printer control actions |

### Camera Component Config

```python
class CameraComponentConfig(BaseModel):
    provider: Literal[ConnectionType.HOMEASSISTANT]
    entity_id: str
    brightness: float = Field(100.0, ge=0.0, le=500.0)
    contrast: float = Field(100.0, ge=0.0, le=500.0)
    sharpness: float = Field(100.0, ge=0.0, le=500.0)
```

---

## Next Steps

- [Architecture Diagrams](architecture.md) - Visual system documentation
- [API Reference](api.md) - Complete endpoint documentation
- [Setup Guide](setup.md) - Installation and configuration
- [Development Guide](development.md) - Contributing and local setup
