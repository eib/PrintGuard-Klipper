# Docker Deployment

Docker is the primary and recommended deployment method for PrintGuard. It packages the FastAPI application, the ML runtime (ONNX), and all necessary dependencies.

## Quick Start

```bash
docker run -d \
  --name printguard \
  -p 8000:8000 \
  -v "$(pwd)/data:/data" \
  --privileged \
  ghcr.io/oliverbravery/printguard:latest
```

## Docker Compose (Recommended)

Using Docker Compose is the best way to manage your PrintGuard deployment, especially if you want to use external tunnels like Cloudflare.

```yaml
version: '3.8'

services:
  printguard:
    image: ghcr.io/oliverbravery/printguard:latest
    container_name: printguard
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
    privileged: true
    environment:
      - TZ=UTC
      - PRINTGUARD_STORAGE_PATH=/data
```

## Configuration Options

PrintGuard can be configured via environment variables or a configuration file.

### Persistent Storage

The `/data` directory inside the container stores:
- `printguard.db`: The SQLite database containing all your settings, printers, and credentials.
- `models/`: ML models downloaded at runtime.

**Always mount a host directory to `/data` to prevent data loss on container updates.**

### Hardware Access

- **USB Cameras**: Requires `--privileged` or mapping specific devices (e.g., `--device /dev/video0:/dev/video0`).
- **GPU Acceleration**: Currently, the default image uses CPU inference. GPU-optimized images (CUDA/MPS) are planned for future releases.

### Network Configuration

- **Port 8000**: The default port for the Web UI and API.
- **WebRTC**: For live streaming, PrintGuard uses WebRTC. If you are behind a restrictive firewall or NAT, you may need to configure STUN/TURN servers in the application settings.

## Updating

To update to the latest version:

```bash
docker pull ghcr.io/oliverbravery/printguard:latest
docker stop printguard
docker rm printguard
# Run your docker run command again
```

Or with Docker Compose:

```bash
docker compose pull
docker compose up -d
```
