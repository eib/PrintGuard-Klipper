# Home Assistant Provider

Use the `homeassistant` provider to drive PrintGuard from Home Assistant entities (status, camera, and optional control actions).

## What it supports

- **Status**: maps a Home Assistant entity state to `idle/printing/paused/error`
- **Camera**: consumes Home Assistant camera proxy stream (`/api/camera_proxy_stream/{entity_id}`)
- **Control (optional)**: calls `button.press` or `switch.turn_on/turn_off` for configured action entities

## Setup

1. Create a Home Assistant long-lived access token.
2. Create a Connection in PrintGuard with provider `homeassistant`:
   - `hass_url`: base URL, e.g. `http://homeassistant.local:8123`
   - `token`: long-lived access token
3. Create components and set their `entity_config` based on the role:
   - **Camera**: `entity_id` must be a `camera.*` entity
   - **Status**: `entity_id` should be a sensor/binary_sensor/etc representing print state
   - **Control** (optional): provide action entities:
     - `start_entity_id`, `pause_entity_id`, `resume_entity_id`, `stop_entity_id`
4. Optional state mapping overrides (all comma-separated strings):
   - `printing_states` (default: `printing,on,active`)
   - `paused_states` (default: `paused`)
   - `error_states` (default: `error,unavailable,unknown`)

## Entity browsing

PrintGuard can list candidate entities via:

- `GET /api/connections/{id}/entities` (optionally filter with `?type=camera|status|control`)

