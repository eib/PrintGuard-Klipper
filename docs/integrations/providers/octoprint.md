# OctoPrint Integration

Use the `octoprint` provider to integrate a printer managed by OctoPrint.

## What it supports

- **Status**: via OctoPrint Job API
- **Control**: start/pause/resume/stop via OctoPrint Job API
- **Camera**: attempts to discover the primary webcam via OctoPrint’s webcam endpoints and connect to `camera-streamer` WebRTC signaling

## Requirements

- OctoPrint reachable from the PrintGuard server (same LAN or routed network)
- An OctoPrint API key
- For camera streaming: OctoPrint webcam configured and `camera-streamer` WebRTC signaling available

## Setup

1. Generate an API key in OctoPrint.
2. Create a Connection in PrintGuard with provider `octoprint`:
   - `host`: base URL, e.g. `http://octopi.local`
   - `api_key`: your OctoPrint API key
3. Create the components you want (camera/status/control) and attach the connection.

## Notes

- Connection validation uses `GET {host}/api/version`.
- Camera discovery queries `GET /api/webcam/webcams` and uses the first returned webcam’s stream URL.

