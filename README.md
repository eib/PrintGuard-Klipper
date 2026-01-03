# PrintGuard - Real-Time 3D Print Failure Detection

PrintGuard offers a modern, scalable architecture for real-time 3D print failure detection. Built with FastAPI, Redis, and MediaMTX, it provides an edge deployable failure detection solution for 3D printers.

> **Note:** The machine learning model's training code and technical research paper can be found [here](https://github.com/oliverbravery/Edge-FDM-Fault-Detection).

## Features

- **Real-Time Failure Detection**: Custom prototypical network with ShuffleNetv2 backbone optimized for edge devices
- **Multi-Printer Support**: Monitor multiple printers simultaneously with independent detection pipelines
- **WebSocket Live Updates**: Real-time state synchronization via WebSocket with Redis pub/sub
- **Connection Providers**: Extensible architecture supporting Home Assistant (with more providers planned)
- **MediaMTX Integration**: Professional-grade RTSP/WebRTC streaming for low-latency camera feeds
- **Camera Tuning**: Per-camera brightness, contrast, and sharpness adjustments (0-500%)
- **Health Monitoring**: Automatic connection health checks with graceful degradation
- **Docker-First**: Production-ready Docker Compose setup with Redis and MediaMTX

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
  - [Docker Installation (Recommended)](#docker-installation-recommended)
- [Configuration](#configuration)
- [Usage](#usage)
- [Technical Documentation](docs/overview.md)
- [API Reference](docs/api.md)

## Architecture

PrintGuard uses a modern microservices-inspired architecture:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Web Client    │────▶│   PrintGuard    │────▶│  Home Assistant │
│   (WebSocket)   │◀────│   (FastAPI)     │◀────│   (Cameras)     │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │  Redis   │ │ MediaMTX │ │  SQLite  │
              │ (State)  │ │ (Streams)│ │   (DB)   │
              └──────────┘ └──────────┘ └──────────┘
```

See [Architecture Documentation](docs/architecture.md) for detailed diagrams and explanations.

## Installation

### Docker Installation (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/oliverbravery/PrintGuard.git
   cd PrintGuard
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the services:**
   ```bash
   docker compose up -d --build
   ```

4. **Verify the deployment:**
   ```bash
   docker compose logs -f printguard
   ```

   The API will be available at `http://localhost:8000`.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `DATA_DIR` | Data storage directory | `/app/data` |
| `MODEL_DIR` | ML model directory | `/app/models` |
| `DATABASE_URL` | SQLite database URL | Auto-generated |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `MEDIAMTX_API_URL` | MediaMTX API endpoint | `http://localhost:9997/v3` |
| `MEDIAMTX_WEBRTC_URL` | MediaMTX WebRTC endpoint | `http://localhost:8889` |
| `DETECTION_INTERVAL` | Inference interval (seconds) | `0.5` |
| `MAX_CONCURRENT_INFERENCES` | Concurrent inference limit | `3` |

### Camera Tuning

Each camera component supports image adjustments applied before inference:

- **Brightness**: 0-500% (default: 100%)
- **Contrast**: 0-500% (default: 100%)
- **Sharpness**: 0-500% (default: 100%)

These settings are stored per-camera in the database and applied in real-time during the detection pipeline.

## Usage

### Docker Commands

```bash
# Start all services
docker compose up -d --build

# View logs
docker compose logs -f printguard

# Stop all services
docker compose down

# Rebuild and restart
docker compose down && docker compose up -d --build

# Access container shell
docker compose exec printguard /bin/bash
```

### API Endpoints

The API is available at `http://localhost:8000`. Key endpoints:

- `GET /` - Health check
- `WS /ws/live` - WebSocket for live state updates

See [API Documentation](docs/api.md) for complete reference.

### WebSocket Events

Connect to `/ws/live` for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event, 'Data:', data.data);
};
```

Events include:
- `INITIAL_SYNC` - Full state on connection
- `PRINTER_LIVE_STATE` - Printer status updates
- `CONNECTION_LIVE_STATE` - Connection health updates
- `PRINTER_UPDATE` / `COMPONENT_UPDATE` / `CONNECTION_UPDATE` - CRUD notifications

## License

This project is licensed under the GPL-2.0 License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgements

- [Edge-FDM-Fault-Detection - My computer-vision model that powers PrintGuard](https://github.com/oliverbravery/Edge-FDM-Fault-Detection) research
- [FastAPI](https://fastapi.tiangolo.com/) framework
- [MediaMTX](https://github.com/bluenviron/mediamtx) streaming server
