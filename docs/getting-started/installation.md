# Installation

## Docker Installation (Recommended)

The easiest and most reliable way to run PrintGuard is via Docker. This ensures all AI dependencies (PyTorch, ONNX Runtime) and system libraries are correctly configured for your hardware.

### Pull from GitHub Container Registry

```bash
docker pull ghcr.io/oliverbravery/printguard:latest
```

### Run the Container

```bash
docker run -d \
  --name printguard \
  -p 8000:8000 \
  -v "$(pwd)/data:/data" \
  --privileged \
  --restart unless-stopped \
  ghcr.io/oliverbravery/printguard:latest
```

!!! note
    The `--privileged` flag is required for local USB camera access. The `/data` volume is used to persist your database and configuration.

---

## PyPI Installation (Shared Library Only)

The `printguard-shared` package is available on PyPI. This is **not** the full server application, but a shared library used primarily by the **Home Assistant integration** for secure communication.

```bash
pip install printguard-shared
```

If you are looking for the main server application, please use the **Docker** method above.

---

## From Source (For Developers)

If you wish to contribute or run the server in a development environment:

```bash
git clone https://github.com/oliverbravery/PrintGuard.git
cd PrintGuard

# It is recommended to use a virtual environment
python -m venv venv
source venv/bin/activate

# Install the package in editable mode
pip install -e .
pip install -e ./printguard-shared

# Start the server
printguard
```

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.13+ (for source) | Docker |
| RAM | 2GB | 4GB+ |
| Storage | 1GB | 5GB+ (for models) |
| Camera | USB or network camera | - |
