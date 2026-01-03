# Setup Guide

Complete setup instructions for PrintGuard.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Docker Setup](#docker-setup)
- [Configuration](#configuration)
- [Home Assistant Integration](#home-assistant-integration)

---

## Prerequisites

### Docker Setup (Recommended)

- Docker Engine 20.10+
- Docker Compose V2
- 1GB+ RAM
- Home Assistant instance with camera entities

---

## Docker Setup

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/oliverbravery/PrintGuard.git
   cd PrintGuard
   ```

2. **Start all services:**
   ```bash
   docker compose up -d --build
   ```

3. **Verify deployment:**
   ```bash
   docker compose ps
   docker compose logs -f printguard
   ```

### Docker Commands Reference

| Command | Description |
|---------|-------------|
| `docker compose up -d` | Start services in background |
| `docker compose up -d --build` | Rebuild and start services |
| `docker compose down` | Stop all services |
| `docker compose down && docker compose up -d --build` | Full restart with rebuild |
| `docker compose logs -f printguard` | Follow PrintGuard logs |
| `docker compose logs -f` | Follow all service logs |
| `docker compose ps` | Show service status |
| `docker compose exec printguard /bin/bash` | Shell into container |
| `docker compose restart printguard` | Restart PrintGuard only |

### Volume Locations

| Volume | Container Path | Purpose |
|--------|----------------|---------|
| `printguard-data` | `/app/data` | SQLite database |
| `printguard-models` | `/app/models` | ONNX model files |

To find volume locations on host:
```bash
docker volume inspect printguard_printguard-data
```

### Custom Environment Variables

Create a `.env` file for custom configuration:

```bash
# .env
DEBUG=true
DETECTION_INTERVAL=1.0
MAX_CONCURRENT_INFERENCES=2
```

---


**With environment variables:**
```bash
DEBUG=true \
REDIS_URL=redis://localhost:6379 \
MEDIAMTX_API_URL=http://localhost:9997/v3 \
uvicorn printguard.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `DATA_DIR` | `./data` | Data storage directory |
| `MODEL_DIR` | `./models` | ML model directory |
| `DATABASE_URL` | Auto | SQLite database URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `REDIS_DB` | `0` | Redis database number |
| `REDIS_CHANNEL` | `printguard:events` | Redis pub/sub channel |
| `MEDIAMTX_API_URL` | `http://localhost:9997/v3` | MediaMTX API endpoint |
| `MEDIAMTX_WEBRTC_URL` | `http://localhost:8889` | MediaMTX WebRTC endpoint |
| `MEDIAMTX_API_USERNAME` | - | MediaMTX API username (if auth enabled) |
| `MEDIAMTX_API_PASSWORD` | - | MediaMTX API password (if auth enabled) |
| `DETECTION_INTERVAL` | `0.5` | Inference interval (seconds) |
| `MAX_CONCURRENT_INFERENCES` | `3` | Max parallel inferences |
| `CONNECTION_HEALTH_INTERVAL` | `10.0` | Health check interval |
| `PRINTER_STATUS_INTERVAL` | `10.0` | Status poll interval |
| `MAX_DETECTION_HISTORY` | `100` | Detection history size |
| `WEBPUSH_VAPID_KEYS_PATH` | Auto | Path to VAPID keys JSON file |

### Web Push (VAPID)

PrintGuard uses standard Web Push (VAPID) and reads credentials from a single JSON file.

**Docker default behavior:** if the keys file does not exist, PrintGuard auto-generates a keypair on startup and persists it into the data volume at `/app/data/webpush_vapid_keys.json`.

The generated **public key** is logged on startup (frontend needs it to subscribe).

**Optional:** override the path with:

```bash
WEBPUSH_VAPID_KEYS_PATH=/app/data/webpush_vapid_keys.json
```

**Keys file format:**

```json
{
  "public_key": "...",
  "private_key": "/app/data/webpush_vapid_private_key.pem",
  "subject": "mailto:admin@example.com"
}
```

### MediaMTX Configuration

The `mediamtx.yml` file configures camera streaming:

```yaml
# MediaMTX configuration for PrintGuard
api: yes
apiAddress: :9997

rtspTransports: [tcp]

# Allow API access from any IP (required for Docker networking)
authInternalUsers:
  - user: any
    pass:
    ips: []
    permissions:
      - action: api
      - action: publish
      - action: read
      - action: playback
      - action: metrics
```

---

## Home Assistant Integration

### Prerequisites

1. Home Assistant instance accessible from PrintGuard
2. Long-lived access token from Home Assistant
3. Camera entities configured in Home Assistant

### Creating Access Token

1. Open Home Assistant
2. Go to **Profile** → **Security** → **Long-Lived Access Tokens**
3. Click **Create Token**
4. Copy the token (shown only once)

### Supported Entity Types

| Type | HA Domains | Use Case |
|------|------------|----------|
| Camera | `camera.*` | Video feed for detection |
| Status | `sensor.*`, `binary_sensor.*` | Print state monitoring |
| Control | `switch.*`, `button.*`, `light.*`, etc. | Printer actions |

### Camera Entity Setup

Ensure your camera entity is properly configured in Home Assistant:

```yaml
# configuration.yaml example
camera:
  - platform: generic
    name: Ender 3 Camera
    still_image_url: http://192.168.1.100/snapshot.jpg
    stream_source: rtsp://192.168.1.100/stream
```

### Testing Connection

Verify Home Assistant connectivity:

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  http://homeassistant.local:8123/api/
```

Expected response:
```json
{"message": "API running."}
```

---

## Next Steps

- [API Reference](api.md) - Endpoint documentation
- [Architecture](architecture.md) - System design
- [Development Guide](development.md) - Contributing
