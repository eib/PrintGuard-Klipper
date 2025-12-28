# Connections API

Connections store provider credentials/config (e.g., OctoPrint URL+API key, Home Assistant token, etc.) and are referenced by components.

## Auth

- Requires an **access token** in `Authorization: Bearer ...`
- Read operations require **`printer:read`**
- Write operations require **`printer:write`**
- Deleting requires **`admin`**

## Encryption (optional)

These routes use `EncryptedRoute`. Clients may send/receive encrypted payloads via `X-Encrypted: true` and `X-Client-Public-Key`.

## Endpoints

### List / read

- `GET /api/connections`: List connections
  - Optional query params: `provider`
- `GET /api/connections/{id}`: Get a connection by id

> Secret fields in `config` (`token`, `api_key`, `access_code`) are masked as `"********"` in responses.

### Create / update / delete

- `POST /api/connections`: Create a connection

  ```json
  {
    "name": "My OctoPrint",
    "provider": "octoprint",
    "config": {
      "base_url": "http://octopi.local",
      "api_key": "..."
    }
  }
  ```

- `PUT /api/connections/{id}`: Update a connection (merges `config`)

  ```json
  {
    "name": "New name",
    "config": { "api_key": "new-secret" }
  }
  ```

- `DELETE /api/connections/{id}`: Delete a connection
  - Optional query param: `cascade=true` to delete even if components exist (otherwise returns 409 with component names)
  - Requires `admin`

### Health / relationships

- `GET /api/connections/{id}/health`: Validate credentials/config via provider
- `GET /api/connections/{id}/components`: List components that reference this connection

### Entity browsing

- `GET /api/connections/{id}/entities`: List entities from provider (if supported)
  - Optional query param: `type` (filters returned entities)

