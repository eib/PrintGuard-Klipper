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

PrintGuard uses OAuth 2.0 with JWT tokens. Supports:
- **Authorization Code + PKCE** — Secure flow for public clients (SPAs, mobile apps)
- **Client Credentials** — M2M service accounts

### Scopes

| Scope | Description |
|-------|-------------|
| `admin` | Full administrative access |
| `user` | Standard user access |

### Authorization Code Flow with PKCE

#### Step 1: Generate PKCE Values (Client-side)

```javascript
// Generate code_verifier (43-128 chars)
const codeVerifier = generateRandomString(64);

// Generate code_challenge = base64url(sha256(code_verifier))
const encoder = new TextEncoder();
const data = encoder.encode(codeVerifier);
const digest = await crypto.subtle.digest('SHA-256', data);
const codeChallenge = base64UrlEncode(digest);
```

#### Step 2: Authorize

##### `POST /api/auth/authorize`

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password",
  "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
  "code_challenge_method": "S256",
  "redirect_uri": "https://myapp.com/callback",
  "state": "random-state-value"
}
```

**Response (if redirect_uri provided):** 302 redirect to `redirect_uri?code=...&state=...`

**Response (if no redirect_uri):**
```json
{
  "code": "authorization-code",
  "state": "random-state-value"
}
```

#### Step 3: Exchange Code for Token

##### `POST /api/auth/token`

**Request:**
```json
{
  "grant_type": "authorization_code",
  "code": "authorization-code",
  "code_verifier": "original-code-verifier",
  "redirect_uri": "https://myapp.com/callback"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### M2M / Service Account (Client Credentials)

##### `POST /api/auth/token`

**Request:**
```json
{
  "grant_type": "client_credentials",
  "client_id": "uuid-string",
  "client_secret": "your-secret"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### Current Identity

#### `GET /api/auth/me`

Returns the authenticated identity. Requires `Authorization: Bearer <token>`.

**Response:**
```json
{
  "identity_id": "uuid-string",
  "type": "user",
  "scopes": ["user"]
}
```

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

---

### Web Push Notifications

PrintGuard supports standard Web Push subscriptions (VAPID).

If a push send returns `410 Gone`, the server deletes that subscription immediately.

#### Payloads

When a majority defect is detected, PrintGuard sends:

```json
{
    "type": "printer_defect"
}
```

#### `POST /api/push/subscribe`

Register or update a browser/device push subscription. **Requires authentication.**

**Request:**
```json
{
  "endpoint": "https://...",
  "keys": {
    "p256dh": "...",
    "auth": "..."
  },
  "expiration_time_ms": 0,
  "user_agent": "optional"
}
```

**Response:**
```json
{
  "id": "uuid-string",
  "identity_id": "uuid-string",
  "endpoint": "https://...",
  "expiration_time_ms": 0,
  "user_agent": "..."
}
```

#### `POST /api/push/unsubscribe`

Remove a subscription by endpoint. **Requires authentication; owner-only.**

**Request:**
```json
{ "endpoint": "https://..." }
```

**Response:**
```json
{ "ok": true }
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
- `PUSH_SUBSCRIPTION_UPDATE`

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
