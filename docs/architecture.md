# Architecture Documentation

This document provides detailed architecture diagrams and explanations for PrintGuard.

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [Service Topology](#service-topology)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [Inference Flow](#inference-flow)
- [WebSocket Architecture](#websocket-architecture)
- [Component Relationships](#component-relationships)

---

## High-Level Architecture

### System Context Diagram

```
                                    ┌─────────────────────┐
                                    │                     │
                                    │    3D Printer +     │
                                    │      Camera         │
                                    │                     │
                                    └──────────┬──────────┘
                                               │
                                               │ MJPEG/RTSP
                                               ▼
┌─────────────────────┐            ┌─────────────────────┐
│                     │            │                     │
│   Home Assistant    │◀───────────│   Camera Entity     │
│     Instance        │            │                     │
│                     │            └─────────────────────┘
└──────────┬──────────┘
           │
           │ REST API
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                         PrintGuard                                  │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │   FastAPI   │  │   Worker    │  │   Stream    │  │   State   │  │
│  │   Server    │  │ Orchestrator│  │   Manager   │  │  Manager  │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘  │
│         │                │                │               │        │
│         └────────────────┴────────────────┴───────────────┘        │
│                                   │                                 │
└───────────────────────────────────┼─────────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
    ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
    │   SQLite    │          │    Redis    │          │  MediaMTX   │
    │  Database   │          │   Server    │          │   Server    │
    └─────────────┘          └─────────────┘          └─────────────┘
```

---

## Service Topology

### Docker Compose Services

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Network: printguard-network              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    printguard-api                            │   │
│  │                    (Port 8000)                               │   │
│  │  ┌─────────────────────────────────────────────────────────┐│   │
│  │  │  FastAPI Application                                    ││   │
│  │  │  • API Routes (/ws/live, etc.)                          ││   │
│  │  │  • Worker Orchestrator                                  ││   │
│  │  │  • Stream Manager                                       ││   │
│  │  │  • ML Inference Engine                                  ││   │
│  │  └─────────────────────────────────────────────────────────┘│   │
│  │                                                              │   │
│  │  Volumes:                                                    │   │
│  │  • printguard-data:/app/data (SQLite DB)                    │   │
│  │  • printguard-models:/app/models (ONNX models)              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│          ┌────────────────┴────────────────┐                       │
│          │                                 │                        │
│          ▼                                 ▼                        │
│  ┌───────────────────┐          ┌───────────────────┐              │
│  │  printguard-redis │          │     mediamtx      │              │
│  │   (Port 6379)     │          │  (Ports 8889,     │              │
│  │                   │          │   8890, 9997)     │              │
│  │  • State Cache    │          │                   │              │
│  │  • Pub/Sub Events │          │  • RTSP Ingestion │              │
│  │  • Detection Hist │          │  • WebRTC Output  │              │
│  └───────────────────┘          │  • REST API       │              │
│                                 └───────────────────┘              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Port Mapping

| Service | Internal Port | External Port | Protocol | Purpose |
|---------|---------------|---------------|----------|---------|
| PrintGuard | 8000 | 8000 | HTTP/WS | API & WebSocket |
| Redis | 6379 | - | TCP | Internal only |
| MediaMTX | 9997 | - | HTTP | API (internal) |
| MediaMTX | 8889 | 8889 | HTTP | WebRTC |
| MediaMTX | 8890 | 8890 | UDP | WebRTC ICE |
| MediaMTX | 8554 | - | RTSP | Stream ingestion |

---

## Data Flow

### Complete Request Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           Data Flow Diagram                               │
└──────────────────────────────────────────────────────────────────────────┘

 Client                PrintGuard              Redis           Home Assistant
   │                       │                     │                    │
   │  1. WS Connect        │                     │                    │
   │──────────────────────▶│                     │                    │
   │                       │                     │                    │
   │  2. Initial Sync      │                     │                    │
   │◀──────────────────────│                     │                    │
   │                       │                     │                    │
   │                       │  3. Start Workers   │                    │
   │                       │─────────────────────│                    │
   │                       │                     │                    │
   │                       │  4. Health Check    │                    │
   │                       │─────────────────────────────────────────▶│
   │                       │                     │                    │
   │                       │  5. Camera Stream URL                    │
   │                       │◀────────────────────────────────────────│
   │                       │                     │                    │
   │                       │  6. Register with MediaMTX               │
   │                       │───────────────────▶ │                    │
   │                       │                     │                    │
   │                       │  7. Poll Status     │                    │
   │                       │─────────────────────────────────────────▶│
   │                       │                     │                    │
   │                       │  8. Status Response │                    │
   │                       │◀────────────────────────────────────────│
   │                       │                     │                    │
   │                       │  9. Update State    │                    │
   │                       │────────────────────▶│                    │
   │                       │                     │                    │
   │                       │  10. Publish Event  │                    │
   │                       │────────────────────▶│                    │
   │                       │                     │                    │
   │  11. State Update     │                     │                    │
   │◀──────────────────────│                     │                    │
   │                       │                     │                    │
```

### Inference Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Inference Data Flow                                │
└──────────────────────────────────────────────────────────────────────────┘

┌─────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌───────┐
│ Camera  │────▶│ MediaMTX │────▶│ OpenCV   │────▶│ PIL      │────▶│ ONNX  │
│ (HA)    │MJPEG│ (RTSP)   │RTSP │ Capture  │bytes│ Transform│numpy│ Model │
└─────────┘     └──────────┘     └──────────┘     └──────────┘     └───┬───┘
                                                                       │
                                                                       │
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐        │
│ Client  │◀────│  Redis   │◀────│ State    │◀────│ Classify │◀───────┘
│ (WS)    │event│ Pub/Sub  │     │ Manager  │     │          │embedding
└─────────┘     └──────────┘     └──────────┘     └──────────┘
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Database Schema                                  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│     connections     │
├─────────────────────┤
│ id          UUID PK │
│ name        VARCHAR │
│ configuration JSON  │──────┐
└─────────────────────┘      │
                             │
                             │ 1:N
                             │
                             ▼
                    ┌─────────────────────┐
                    │  device_components  │
                    ├─────────────────────┤
                    │ id           UUID PK│
                    │ type         ENUM   │
                    │ connection_id UUID FK│
                    │ config       JSON   │
                    └─────────┬───────────┘
                              │
                              │ N:1 (multiple FKs)
                              │
                              ▼
                    ┌─────────────────────┐
                    │      printers       │
                    ├─────────────────────┤
                    │ id             UUID │
                    │ name          VARCHAR│
                    │ camera_comp_id   FK │───▶ device_components (CAMERA)
                    │ status_comp_id   FK │───▶ device_components (STATUS)
                    │ start_ctrl_id    FK │───▶ device_components (CONTROL)
                    │ stop_ctrl_id     FK │───▶ device_components (CONTROL)
                    └─────────────────────┘
```

### Component Config Schemas

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Component Config Schemas                             │
└─────────────────────────────────────────────────────────────────────────┘

Camera Component (HomeAssistant):
┌─────────────────────────────────┐
│ {                               │
│   "provider": "homeassistant",  │
│   "entity_id": "camera.xxx",    │
│   "brightness": 100.0,          │  ← 0-500%
│   "contrast": 100.0,            │  ← 0-500%
│   "sharpness": 100.0            │  ← 0-500%
│ }                               │
└─────────────────────────────────┘

Status Component (HomeAssistant):
┌─────────────────────────────────┐
│ {                               │
│   "provider": "homeassistant",  │
│   "entity_id": "sensor.xxx",    │
│   "is_printing_attr": "on",     │
│   "is_idle_attr": "off",        │
│   "attributes": ["state", ...]  │
│ }                               │
└─────────────────────────────────┘

Control Component (HomeAssistant):
┌─────────────────────────────────┐
│ {                               │
│   "provider": "homeassistant",  │
│   "entity_id": "switch.xxx"     │
│ }                               │
└─────────────────────────────────┘
```

---

## Inference Flow

### Detection Pipeline Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Detection Pipeline                                │
└──────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────┐
                    │     Active Detection Check      │
                    │  (printer status == PRINTING    │
                    │   && connection healthy)        │
                    └───────────────┬─────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────┐
                    │        Get Snapshot             │
                    │   (RTSP → OpenCV → bytes)       │
                    └───────────────┬─────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────┐
                    │       Load Camera Config        │
                    │  (brightness, contrast, sharp)  │
                    └───────────────┬─────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                          Image Preprocessing                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │  Load   │───▶│ Apply   │───▶│ Resize  │───▶│ Gray-   │───▶│ Normal- │ │
│  │  Image  │    │ Tuning  │    │  256    │    │ scale   │    │  ize    │ │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘ │
│                                                                           │
│  Tuning applies:           Resize to 256px    Convert to    Normalize    │
│  • Brightness (0-500%)     on shortest side   3-channel     [0.485,      │
│  • Contrast (0-500%)                          grayscale     0.456,       │
│  • Sharpness (0-500%)                                       0.406]       │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────┐
                    │        Center Crop 224          │
                    │    (224x224 input tensor)       │
                    └───────────────┬─────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                           ONNX Inference                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Input: [1, 3, 224, 224]     Model: ShuffleNetV2     Output: embedding   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                                                                     │ │
│  │   ┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────┐ │ │
│  │   │ Input   │───▶│ ShuffleNet  │───▶│  Embedding  │───▶│ Output  │ │ │
│  │   │ Tensor  │    │    v2       │    │   Layer     │    │ Vector  │ │ │
│  │   └─────────┘    └─────────────┘    └─────────────┘    └─────────┘ │ │
│  │                                                                     │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         Classification                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│                      embedding                                            │
│                          │                                                │
│           ┌──────────────┼──────────────┐                                │
│           │              │              │                                 │
│           ▼              ▼              ▼                                 │
│     ┌──────────┐   ┌──────────┐   ┌──────────┐                           │
│     │ Success  │   │ Defect   │   │  Other   │                           │
│     │Prototype │   │Prototype │   │Prototype │                           │
│     └────┬─────┘   └────┬─────┘   └────┬─────┘                           │
│          │              │              │                                  │
│          ▼              ▼              ▼                                  │
│     ┌──────────────────────────────────────────┐                         │
│     │        Euclidean Distance                │                         │
│     │   d = ||embedding - prototype||₂         │                         │
│     └──────────────────────────────────────────┘                         │
│                          │                                                │
│                          ▼                                                │
│     ┌──────────────────────────────────────────┐                         │
│     │     Predicted Class = argmin(distances)  │                         │
│     │     Confidence = 1 / (1 + min_distance)  │                         │
│     └──────────────────────────────────────────┘                         │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────┐
                    │      Update State Manager       │
                    │  (Redis → WebSocket broadcast)  │
                    └─────────────────────────────────┘
```

---

## Defect Response Features

When a defect is detected (majority classification over recent inferences), PrintGuard can automatically respond in two ways:

### Auto-Stop on Defect

If a printer has a **stop control component** configured (`stop_ctrl_comp_id`), PrintGuard will automatically trigger that control to stop the print when a defect is detected.

**How it works:**
1. Inference detects defect as the majority class
2. System checks if the printer has `stop_ctrl_comp_id` set
3. If set, PrintGuard calls `trigger_control()` on that component via the connection interface
4. The connection (e.g., Home Assistant) sends the stop command to the printer

**To enable auto-stop:**
- Create a control component linked to your printer's power/stop control (e.g., a smart plug or printer API endpoint)
- Set the `stop_ctrl_comp_id` field on the printer to reference that component

**To disable auto-stop:**
- Remove or unset the `stop_ctrl_comp_id` field on the printer
- The printer will still detect defects but won't automatically stop

### Push Notifications

Users who have subscribed to a printer's notifications will receive a web push alert when a defect is detected. See the Push Notification section for subscription management.

---

## WebSocket Architecture

### Connection Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       WebSocket Architecture                              │
└──────────────────────────────────────────────────────────────────────────┘

┌─────────────┐                                           ┌─────────────┐
│   Client    │                                           │   Client    │
│      A      │                                           │      B      │
└──────┬──────┘                                           └──────┬──────┘
       │                                                         │
       │ WebSocket                                     WebSocket │
       │                                                         │
       ▼                                                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         WebSocket Router                                 │
│                         /ws/live                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    ConnectionManager                             │   │
│  │  • active_connections: List[WebSocket]                          │   │
│  │  • connect(ws): Accept & add to list                            │   │
│  │  • disconnect(ws): Remove from list                             │   │
│  │  • broadcast(msg): Send to all connections                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              │ subscribes                               │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         Redis Pub/Sub                            │   │
│  │                    Channel: printguard:events                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ publishes
                              │
┌─────────────────────────────────────────────────────────────────────────┐
│                        GlobalStateManager                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  • update_printer_state()  ───▶  Publish PRINTER_LIVE_STATE            │
│  • update_connection_state() ──▶  Publish CONNECTION_LIVE_STATE        │
│  • send_update()  ───────────▶  Publish CRUD notifications             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Event Message Format

```json
{
  "event": "PRINTER_LIVE_STATE",
  "data": {
    "printer_id": "uuid-string",
    "status": "printing",
    "detection_active": true,
    "detection_history": [
      {
        "class_name": "success",
        "confidence": 0.95,
        "timestamp": "2026-01-03T12:00:00"
      }
    ]
  }
}
```

---

## Component Relationships

### Printer-Component Relationships

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    Printer Component Relationships                        │
└──────────────────────────────────────────────────────────────────────────┘

                         ┌─────────────────┐
                         │     Printer     │
                         │   "Ender 3"     │
                         └────────┬────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Camera Component│     │Status Component │     │Control Component│
│   (Optional)    │     │   (Optional)    │     │   (Optional)    │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ type: CAMERA    │     │ type: STATUS    │     │ type: CONTROL   │
│ entity_id: ...  │     │ entity_id: ...  │     │ entity_id: ...  │
│ brightness: 100 │     │ is_printing: ...│     │                 │
│ contrast: 100   │     │ is_idle: ...    │     │                 │
│ sharpness: 100  │     │ attributes: ... │     │                 │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┴───────────────────────┘
                                 │
                                 ▼
                       ┌─────────────────┐
                       │   Connection    │
                       │ "Home Assistant"│
                       ├─────────────────┤
                       │ provider: HA    │
                       │ url: http://... │
                       │ api_key: ...    │
                       └─────────────────┘
```

### Type Validation

```
Component Type Validation:
┌──────────────────┬────────────────────┬───────────────────────────────┐
│ Printer Field    │ Required Type      │ Validates Against             │
├──────────────────┼────────────────────┼───────────────────────────────┤
│ camera_comp_id   │ ComponentType.CAMERA│ ConnectionCameraConfigRoot   │
│ status_comp_id   │ ComponentType.STATUS│ ConnectionStatusConfigRoot   │
│ start_ctrl_id    │ ComponentType.CONTROL│ ConnectionControlConfigRoot │
│ stop_ctrl_id     │ ComponentType.CONTROL│ ConnectionControlConfigRoot │
└──────────────────┴────────────────────┴───────────────────────────────┘
```

---

## Next Steps

- [API Reference](api.md) - Complete endpoint documentation
- [Setup Guide](setup.md) - Installation and configuration
- [Development Guide](development.md) - Contributing and local setup
