# API Overview

PrintGuard provides a RESTful API for all operations.

## Base URL

```
http://localhost:8000/api
```

## Authentication

Most endpoints require authentication.

### No-auth endpoints

- `POST /api/auth/token` (login)
- `GET /api/health` (health check)
- `GET /api/crypto/key` (server public key)
- `GET /api/notifications/vapid-public-key` (browser push setup)

```bash
# Get access token
curl -X POST http://localhost:8000/api/auth/token \
  -d "username=admin&password=yourpassword"

# Use token in requests
curl http://localhost:8000/api/printer \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Scopes

See [Authentication](authentication.md) for available scopes and M2M applications.

## Optional request/response encryption

Some endpoints (notably `printer`, `components`, `connections`, `rtc`, and tunnel routes) support optional payload encryption via the `EncryptedRoute` wrapper.

If you are using encryption, you’ll generally send:

- `X-Encrypted: true`
- `X-Client-Public-Key: <base64>`
- `X-Decrypted-Content-Type: application/json`

## Response Format

All responses are JSON:

```json
{
  "id": "abc123",
  "name": "My Printer",
  "status": "idle"
}
```

## Error Responses

```json
{
  "detail": "Error message here"
}
```

## Available Endpoints

| Prefix | Description |
|--------|-------------|
| `/api/auth` | Authentication |
| `/api/printer` | Printer management |
| `/api/components` | Component library |
| `/api/connections` | Connection management |
| `/api/rtc` | WebRTC streaming |
| `/api/notifications` | Push notifications |
| `/api/admin` | Administration |
| `/api/tunnel` | Tunnel management |

