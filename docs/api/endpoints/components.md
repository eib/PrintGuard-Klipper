# Components API

Manage “components” (camera / control / status building blocks) that can be linked into printers.

## Auth

- Requires an **access token** in `Authorization: Bearer ...`
- Read operations require **`printer:read`**
- Write operations require **`printer:write`**

## Encryption (optional)

These routes use the server’s `EncryptedRoute` wrapper. Clients may send/receive encrypted payloads by setting:

- `X-Encrypted: true`
- `X-Client-Public-Key: <base64>`
- `X-Decrypted-Content-Type: application/json` (when sending JSON)

To fetch the server public key, use `GET /api/crypto/key`.

## Endpoints

### List / read

- `GET /api/components`: List components
  - Optional query params: `type`, `provider`, `connection_id`
- `GET /api/components/{id}`: Get a component by id

### Create / update / delete

- `POST /api/components`: Create a component

  ```json
  {
    "name": "Workshop camera",
    "type": "camera",
    "provider": "webcam",
    "connection_id": "optional-connection-id",
    "entity_config": {}
  }
  ```

- `PUT /api/components/{id}`: Update a component (merges `entity_config`)

  ```json
  {
    "name": "New name",
    "entity_config": { "some_key": "some_value" }
  }
  ```

- `DELETE /api/components/{id}`: Delete a component
  - Optional query param: `force=true` to delete even if linked to printers (otherwise returns 409 with printer ids)

### Health / usage

- `GET /api/components/{id}/health`: Validate the component via its provider
- `GET /api/components/{id}/printers`: List printers that reference this component

### Streaming (camera components only)

- `POST /api/components/{id}/stream?session_id=...`: Ensure a camera component is being streamed/multiplexed for preview/inference
  - Requires scopes: `printer:write` and `rtc:stream`
  - Optional body: `FeedSettings` (see `POST /api/rtc/offer` and `PUT /api/rtc/settings/{session_id}`)

