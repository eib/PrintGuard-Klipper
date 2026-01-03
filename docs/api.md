# API Reference

Complete API documentation for PrintGuard.

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [REST Endpoints](#rest-endpoints)
- [WebSocket](#websocket)
- [Error Handling](#error-handling)

---

## Base URL

```
http://localhost:8000
```

For Docker deployments, replace `localhost` with your server's hostname or IP.

---

## Authentication

> **Note:** Authentication is not yet implemented in the current version. All endpoints are currently open.

---

## REST Endpoints

### Health Check

#### `GET /`

Returns API health status.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

---

## WebSocket

### Live Updates

#### `WS /ws/live`

WebSocket endpoint for real-time state updates.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live');

ws.onopen = () => {
  console.log('Connected to PrintGuard');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Event:', message.event);
  console.log('Data:', message.data);
};

ws.onclose = () => {
  console.log('Disconnected from PrintGuard');
};
```

### WebSocket Events

#### Initial Sync

Sent immediately after connection with complete system state.

**Event:** `INITIAL_SYNC`

```json
{
  "event": "INITIAL_SYNC",
  "data": {
    "printer_live_states": {
      "uuid-string": {
        "printer_id": "uuid-string",
        "status": "idle",
        "detection_active": false,
        "detection_history": []
      }
    },
    "connection_live_states": {
      "uuid-string": {
        "connection_id": "uuid-string",
        "is_healthy": true,
        "last_activity": "2026-01-03T12:00:00"
      }
    }
  }
}
```

#### Printer Live State

Sent when printer state changes (status, detection, inference results).

**Event:** `PRINTER_LIVE_STATE`

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
      },
      {
        "class_name": "defect",
        "confidence": 0.87,
        "timestamp": "2026-01-03T12:00:01"
      }
    ]
  }
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `printer_id` | UUID | Unique printer identifier |
| `status` | string | `idle` or `printing` |
| `detection_active` | boolean | Whether inference is running |
| `detection_history` | array | Rolling window of inference results |

**Inference Result:**

| Field | Type | Description |
|-------|------|-------------|
| `class_name` | string | `success` or `defect` |
| `confidence` | float | 0.0 to 1.0 |
| `timestamp` | datetime | ISO 8601 timestamp |

#### Connection Live State

Sent when connection health status changes.

**Event:** `CONNECTION_LIVE_STATE`

```json
{
  "event": "CONNECTION_LIVE_STATE",
  "data": {
    "connection_id": "uuid-string",
    "is_healthy": true,
    "last_activity": "2026-01-03T12:00:00"
  }
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `connection_id` | UUID | Unique connection identifier |
| `is_healthy` | boolean | Connection availability |
| `last_activity` | datetime | Last successful health check |

#### CRUD Notifications

Sent when database records are created, updated, or deleted.

**Events:**
- `PRINTER_UPDATE`
- `COMPONENT_UPDATE`
- `CONNECTION_UPDATE`

```json
{
  "event": "PRINTER_UPDATE",
  "data": {
    "type": "UPDATE",
    "record_id": "uuid-string"
  }
}
```

**Update Types:**

| Type | Description |
|------|-------------|
| `CREATE` | New record created |
| `UPDATE` | Existing record modified |
| `DELETE` | Record deleted |

---

## Data Models

### Printer

```json
{
  "id": "uuid-string",
  "name": "Ender 3 Pro",
  "camera_component": {
    "id": "uuid-string",
    "type": "camera",
    "config": {
      "provider": "homeassistant",
      "entity_id": "camera.ender3_cam",
      "brightness": 100.0,
      "contrast": 100.0,
      "sharpness": 100.0
    },
    "connection": { ... }
  },
  "status_component": { ... },
  "start_control": { ... },
  "stop_control": { ... }
}
```

### Connection

```json
{
  "id": "uuid-string",
  "name": "Home Assistant",
  "configuration": {
    "provider": "homeassistant",
    "url": "http://homeassistant.local:8123",
    "api_key": "eyJ..."
  }
}
```

### Component

```json
{
  "id": "uuid-string",
  "type": "camera",
  "connection_id": "uuid-string",
  "config": {
    "provider": "homeassistant",
    "entity_id": "camera.printer_cam",
    "brightness": 100.0,
    "contrast": 100.0,
    "sharpness": 100.0
  }
}
```

### Component Types

| Type | Description | Config Fields |
|------|-------------|---------------|
| `camera` | Video feed source | `entity_id`, `brightness`, `contrast`, `sharpness` |
| `status` | Printer state sensor | `entity_id`, `is_printing_attr`, `is_idle_attr`, `attributes` |
| `control` | Printer control action | `entity_id` |

### Camera Config

| Field | Type | Range | Default | Description |
|-------|------|-------|---------|-------------|
| `provider` | string | - | - | Connection provider type |
| `entity_id` | string | - | - | Provider entity identifier |
| `brightness` | float | 0-500 | 100.0 | Brightness adjustment (%) |
| `contrast` | float | 0-500 | 100.0 | Contrast adjustment (%) |
| `sharpness` | float | 0-500 | 100.0 | Sharpness adjustment (%) |

---

## Error Handling

### HTTP Errors

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Input validation failed |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Validation Error Format

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Validation error message",
      "type": "value_error"
    }
  ]
}
```

---

## Examples

### JavaScript WebSocket Client

```javascript
class PrintGuardClient {
  constructor(baseUrl = 'ws://localhost:8000') {
    this.baseUrl = baseUrl;
    this.ws = null;
    this.handlers = {};
  }

  connect() {
    this.ws = new WebSocket(`${this.baseUrl}/ws/live`);
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      const handler = this.handlers[message.event];
      if (handler) {
        handler(message.data);
      }
    };

    return new Promise((resolve, reject) => {
      this.ws.onopen = () => resolve();
      this.ws.onerror = (err) => reject(err);
    });
  }

  on(event, handler) {
    this.handlers[event] = handler;
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Usage
const client = new PrintGuardClient();

client.on('INITIAL_SYNC', (data) => {
  console.log('Initial state:', data);
});

client.on('PRINTER_LIVE_STATE', (data) => {
  console.log('Printer update:', data);
  if (data.detection_history.length > 0) {
    const latest = data.detection_history[data.detection_history.length - 1];
    if (latest.class_name === 'defect') {
      console.warn('Defect detected!', latest.confidence);
    }
  }
});

await client.connect();
```

### Python WebSocket Client

```python
import asyncio
import json
import websockets

async def connect_printguard():
    uri = "ws://localhost:8000/ws/live"
    
    async with websockets.connect(uri) as ws:
        async for message in ws:
            data = json.loads(message)
            event = data["event"]
            payload = data["data"]
            
            if event == "INITIAL_SYNC":
                print(f"Connected. Printers: {len(payload['printer_live_states'])}")
            
            elif event == "PRINTER_LIVE_STATE":
                printer_id = payload["printer_id"]
                status = payload["status"]
                detection = payload["detection_active"]
                print(f"Printer {printer_id}: {status}, detection={detection}")
                
                if payload["detection_history"]:
                    latest = payload["detection_history"][-1]
                    print(f"  Latest: {latest['class_name']} ({latest['confidence']:.2%})")

asyncio.run(connect_printguard())
```

---

## Next Steps

- [Setup Guide](setup.md) - Installation and configuration
- [Architecture](architecture.md) - System design documentation
- [Development](development.md) - Contributing guide
