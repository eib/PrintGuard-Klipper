# Printers API

Printer management endpoints. Printers are “modular”: each printer can be composed of up to three components (`status`, `camera`, `control`), which are separate records managed via the Components API.

## Auth

- Requires an **access token**
- Most endpoints require `printer:read` or `printer:write`
- Deleting printers requires `admin`

## Encryption (optional)

These routes use `EncryptedRoute`. Clients may send/receive encrypted payloads via `X-Encrypted: true` and `X-Client-Public-Key`.

## Provider utilities

### List providers

**GET** `/api/printer/providers`

Requires `printer:read`.

### Provider schema

**GET** `/api/printer/providers/{provider}/schema`

Returns the provider’s JSON schema for configuration fields. Requires `printer:read`.

## List Printers

**GET** `/api/printer`

Optional query params:
- `endpoint`: push subscription endpoint (when provided, each printer includes `notifications_enabled` for that device)

**Response:**
```json
[
  {
    "id": "abc123",
    "name": "Ender 3",
    "status": "idle",
    "has_camera": true,
    "has_control": false,
    "linked_session_id": "optional-session",
    "notifications_enabled": false,
    "inference_majority_voting": 1,
    "inference_sensitivity": 1.0,
    "inference_target_fps": 2.0,
    "detection_action": "pause",
    "inference_paused": false
  }
]
```

## Create Printer

**POST** `/api/printer`

**Request:**
```json
{
  "id": "optional-fixed-id",
  "name": "My Printer",
  "client_public_key": "optional-client-public-key",
  "components": {
    "camera": "component-id-here"
  },
  "inference_majority_voting": 1,
  "inference_sensitivity": 1.0,
  "inference_target_fps": 2.0,
  "detection_action": "none"
}
```

## Get Printer

**GET** `/api/printer/{id}`

Optional query params:
- `endpoint`: push subscription endpoint (adds `notifications_enabled` for that device)

## Update Printer

**PUT** `/api/printer/{id}`

**Request:**
```json
{
  "name": "New Name",
  "inference_sensitivity": 1.5,
  "inference_majority_voting": 3,
  "inference_target_fps": 5.0,
  "detection_action": "pause"
}
```

## Delete Printer

**DELETE** `/api/printer/{id}`

Requires `admin` scope.

## Send Command

**POST** `/api/printer/{id}/{command}`

Commands: `start`, `pause`, `resume`, `stop`

Requires printer to have a control component.

## Start Stream

**POST** `/api/printer/{id}/stream?session_id=unique-id`

Starts (or multiplexes) a camera stream for inference.

- Requires scopes: `printer:write` and `rtc:stream`
- Optional body: `FeedSettings` (if omitted, defaults to the printer’s saved inference settings)

## Control Inference

**POST** `/api/printer/{id}/inference/{action}`

Actions: `start`, `stop`

This flips the printer’s persisted `inference_paused` flag and also updates the live session processor (if streaming).

