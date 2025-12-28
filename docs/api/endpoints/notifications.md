# Notifications API

Browser push notification endpoints (Web Push).

## Auth

- `GET /api/notifications/vapid-public-key` does **not** require auth (used by the browser to set up push)
- All other endpoints require an **access token** with **`printer:read`**

## Endpoints

### VAPID key

- `GET /api/notifications/vapid-public-key`: Get the VAPID public key used for browser push

  **Response**

  ```json
  { "public_key": "..." }
  ```

### Device subscription

- `POST /api/notifications/subscribe`: Subscribe this device/browser endpoint

  ```json
  {
    "subscription": {
      "endpoint": "https://pushservice/.../abc",
      "keys": { "p256dh": "...", "auth": "..." }
    }
  }
  ```

- `POST /api/notifications/unsubscribe`: Unsubscribe this device/browser endpoint

  Body is the same shape as subscribe.

### Per-printer toggle

- `PUT /api/notifications/printer/{printer_id}`: Enable/disable notifications for a printer **for a specific device endpoint**

  ```json
  { "enabled": true, "endpoint": "https://pushservice/.../abc" }
  ```

  Notes:
  - `endpoint` is required (notifications are device-specific)
  - The device must be subscribed first via `/subscribe`

### Test notification

- `POST /api/notifications/test/{printer_id}`: Trigger a test defect notification for the current user/printer

