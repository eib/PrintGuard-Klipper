# Bambu Labs Integration

Use the `bambulabs` provider to integrate a Bambu printer over the local network.

## What it supports

- **Status**: derived from local MQTT state (printing vs idle)
- **Control**: start/pause/resume/stop via MQTT commands
- **Camera**:
  - X1/H2/P2S series: **RTSPS** (`rtsps://...:322/streaming/live/1`)
  - P1/A1 series: **TCP+TLS** camera feed (port 6000, Bambu protocol)

## Setup

1. **Enable LAN mode** on the printer and obtain the **LAN access code**.
2. In PrintGuard, create a Connection with provider `bambulabs` using these fields:
   - `host`: printer IP address
   - `access_code`: LAN access code
   - `serial`: printer serial number
   - `model`: printer model (e.g. `X1C`, `P1P`, `A1`)
3. Create components for the roles you want to use (camera/status/control) and attach the connection.

## Notes

- MQTT uses port `8883` with TLS, username `bblp`, password = LAN access code.
- Camera access relies on the printer being reachable from the server running PrintGuard.

