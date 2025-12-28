# Local Network Access

Local mode is the simplest and recommended default: you access PrintGuard from the same LAN as the server.

## Overview

## What you get

- No third-party tunnel dependencies
- Lowest latency for video/inference
- Access controlled via PrintGuard auth and your network perimeter

## How to access

- WebUI: `http://<server-ip>:5173` (default)
- API: `http://<server-ip>:8000/api` (default)

> Ports are configurable; see `src/printguard/core/config.py` and your `.env`.

## When you need more

If you want access from outside your network, use one of the tunnel options:

- Cloudflare Tunnel
- ngrok

