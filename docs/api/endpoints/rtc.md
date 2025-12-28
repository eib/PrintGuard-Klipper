# Streaming API

WebRTC streaming endpoints (session setup, viewing, snapshots, and inference results).

## Auth

- Requires an **access token** with **`rtc:stream`**

## Encryption (optional)

These routes use `EncryptedRoute`. Clients may send/receive encrypted payloads via `X-Encrypted: true` and `X-Client-Public-Key`.

## Endpoints

### Session setup

- `POST /api/rtc/offer`: Submit a WebRTC offer and receive an answer

  ```json
  {
    "sdp": "v=0...",
    "type": "offer",
    "session_id": "my-session",
    "device_name": "Workshop cam",
    "printer_id": "optional-printer-id",
    "settings": {
      "resolution": [640, 480],
      "brightness": 1.0,
      "contrast": 1.0,
      "sensitivity": 1.0,
      "majority_voting": 1,
      "target_fps": 1000.0,
      "detection_action": "none",
      "inference_paused": false
    }
  }
  ```

  If `printer_id` is provided and exists, the server will load that printer’s stored inference settings and apply them.

- `DELETE /api/rtc/{session_id}`: Close a WebRTC session

### Viewing an existing session

- `POST /api/rtc/view/{session_id}`: Create a viewer connection to an existing session
  - Body: same shape as the offer (only `sdp`/`type` are used for the viewer connection)

### Streams and snapshots

- `GET /api/rtc/streams`: List active streams
- `GET /api/rtc/snapshot/{session_id}`: Get a JPEG snapshot of an active stream (`image/jpeg`)

### Results and tuning

- `GET /api/rtc/result/{session_id}`: Get latest inference result / timeline for a session
- `PUT /api/rtc/settings/{session_id}`: Update feed settings for a session
  - Body: `FeedSettings` (same as in `/offer`)

