# Authentication

## Getting an Access Token

**Endpoint:** `POST /api/auth/token`

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/token \
  -d "username=admin&password=yourpassword"
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

## Using the Token

Include the token in the `Authorization` header:

```bash
curl http://localhost:8000/api/printer \
  -H "Authorization: Bearer eyJ..."
```

## Scopes

| Scope | Description |
|-------|-------------|
| `printer:read` | Read printer information |
| `printer:write` | Modify printers |
| `rtc:stream` | Access camera streams |
| `tunnel:manage` | Configure tunnels |
| `admin` | Full admin access |

## M2M Applications

For automated access, create an M2M application:

```bash
curl -X POST http://localhost:8000/api/admin/m2m \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My App", "scopes": "printer:read rtc:stream"}'
```

Response includes `client_id` and `client_secret` for authentication.

## Token Expiry

Tokens expire after 7 days by default. Configure via `ACCESS_TOKEN_EXPIRE_MINUTES` environment variable.

