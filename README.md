# 🛡️ PrintGuard

**Local, real-time 3D printing failure detection and monitoring on edge devices.**

PrintGuard uses computer vision and machine learning to detect 3D print failures as they happen, allowing for automatic intervention before wasting filament or damaging your printer.

## 🚀 Quick Start (Docker)

The fastest way to get started is by running the PrintGuard server via Docker:

```bash
docker run -d \
  --name printguard \
  -p 8000:8000 \
  -v "$(pwd)/data:/data" \
  --privileged \
  ghcr.io/oliverbravery/printguard:latest
```

Then visit `http://localhost:8000` to access the dashboard.

## ✨ Features

- **Local & Private**: All image processing happens on your hardware. No cloud required.
- **Smart Detection**: Detects spaghetti, adhesion failures, and more using an optimized AI model.
- **Home Assistant Integration**: Full control and monitoring from your smart home dashboard.
- **Broad Support**: Works with OctoPrint, Bambu Labs, and any standard USB or IP camera.
- **Remote Access**: Built-in support for secure tunneling via Cloudflare or ngrok.

## 📖 Documentation

For full installation guides, configuration details, and development setup, please visit our documentation site:

👉 **[https://oliverbravery.github.io/PrintGuard/](https://oliverbravery.github.io/PrintGuard/)**

## 📦 Distribution

- **Main Server**: Distributed as a [Docker Image](https://github.com/oliverbravery/PrintGuard/pkgs/container/printguard).
- **Home Assistant Integration**: Available via [HACS](https://hacs.xyz/).
- **Shared Library**: Available on [PyPI](https://pypi.org/project/printguard-shared/) (for developers and integrations).

## ⚖️ License

Distributed under the GPL-2.0 License. See `LICENSE.md` for more information.

