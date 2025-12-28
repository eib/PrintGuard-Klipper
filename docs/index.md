# PrintGuard Documentation

**Local, real-time 3D printing failure detection and monitoring on edge devices.**

PrintGuard uses computer vision to detect print failures in real-time, allowing automatic intervention before wasted filament and time. It is designed to run privately on your local network, with optional secure remote access.

## Features

- **Real-time Detection**: Custom ML model optimized for edge deployment.
- **Multiple Camera Support**: Monitor multiple printers simultaneously from a single dashboard.
- **Broad Integration**: Native support for OctoPrint, Bambu Labs, and Home Assistant.
- **Push Notifications**: Get alerts via Web Push or Home Assistant.
- **Auto-Actions**: Automatically pause or stop failed prints to save your printer and filament.
- **Privacy Focused**: Processing happens locally. No video is sent to the cloud.

## Quick Links

- [Installation Guide](getting-started/installation.md)
- [Quick Start](getting-started/quick-start.md)
- [Home Assistant Integration](home-assistant/installation.md)
- [Docker Deployment](deployment/docker.md)
- [API Reference](api/overview.md)

## Requirements

PrintGuard is primarily distributed as a **Docker container** to ensure all AI dependencies work out of the box.

- **Environment**: Docker (Linux, macOS, or Windows via WSL2)
- **Hardware**: Raspberry Pi 4/5, Jetson Nano, or any modern x86/ARM server
- **Camera**: USB webcam, network-accessible IP camera (RTSP/MJPEG) or camera's from HomeAssistant, OctoPrint or BambuLabs printers
- **Printer**: Optional connection to OctoPrint Bambu Labs or HomeAssistant for auto-pause features
