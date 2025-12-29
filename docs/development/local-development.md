# Local Development

This guide is for running PrintGuard from source during development.

## Setup

### Backend (FastAPI)

Prerequisites:

- Python **3.13+** (see `pyproject.toml`)

Steps:

```bash
git clone https://github.com/oliverbravery/PrintGuard.git
cd PrintGuard

python -m venv venv
source venv/bin/activate

pip install -e .
pip install -e ./printguard-shared

printguard serve --reload
```

The API will be available at `http://localhost:8000/api`.

### Frontend (WebUI)

Prerequisites:

- Node.js / npm

Steps:

```bash
cd webui
npm install
npm run dev
```

The WebUI will be available at `http://localhost:5173` and will proxy `/api` to `http://localhost:8000`.

### Docker (from source)

Prerequisites:

- Docker and Docker Compose

#### Using Docker Compose (Recommended)

```bash
git clone https://github.com/oliverbravery/PrintGuard.git
cd PrintGuard

# Build and run
docker-compose up --build
```

The application will be available at `http://localhost:8000`.

#### Using Docker directly

To build and run the image locally for testing:

```bash
# Build the image
docker build -t printguard:local .

# Stop and remove existing container if it exists
docker stop printguard 2>/dev/null; docker rm printguard 2>/dev/null

# Run the container
docker run -d \
  --name printguard \
  -p 8000:8000 \
  -v "$(pwd)/model:/app/model" \
  --privileged \
  printguard:local
```

**Note**: The database (`printguard.db`) is stored in `/app` inside the container. For data persistence, use a named volume: `-v printguard-data:/app` or mount a specific directory and configure `DATABASE_URL` environment variable.

#### Docker options

- **Port mapping**: Change `8000:8000` to map a different host port (e.g., `8080:8000`)
- **Database persistence**: Use a named volume `-v printguard-data:/app` or configure `DATABASE_URL` to point to a mounted directory
- **Model directory**: Mount model directory to persist downloaded models: `-v "$(pwd)/model:/app/model"`
- **Environment variables**: Create a `.env` file (used automatically by docker-compose) or pass with `-e KEY=value`
- **View logs**: `docker logs printguard` or `docker-compose logs -f`
- **Stop container**: `docker stop printguard` or `docker-compose down`

### Notes

- On first run, PrintGuard initializes the SQLite database and prints an auto-generated `admin` password to the server logs.
- If you build the WebUI (`webui/dist`), the backend can serve it directly (see `src/printguard/main.py`).

## Home Assistant Integration Development

To develop and test the PrintGuard Home Assistant custom component, you can run a local Home Assistant instance that mounts the `custom_components` directory from this repository.

Run the following command from the root of the PrintGuard repository:

```bash
docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -v "$(pwd)/config:/config" \
  -v "$(pwd)/custom_components:/config/custom_components" \
  -e TZ=Europe/London \
  -p 8123:8123 \
  ghcr.io/home-assistant/home-assistant:stable
```

This setup allows you to:
1. Make changes to files in `custom_components/printguard/` on your host machine.
2. Restart Home Assistant to apply those changes.
3. Test the integration directly within a real Home Assistant environment.

### Important: Docker Networking

If you are running PrintGuard in Docker, `http://localhost:8123` will **not** work to reach Home Assistant because `localhost` refers to the PrintGuard container itself.

- **On macOS/Windows**: Use `http://host.docker.internal:8123` as the HA URL when configuring the connection in PrintGuard.
- **On Linux**: Use the host's actual LAN IP (e.g., `http://192.168.1.10:8123`) or the container IP if using a custom network.

