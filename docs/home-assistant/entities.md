# Home Assistant Entities

The integration creates entities based on what exists in PrintGuard.

- One **PrintGuard Server** device that represents the connection
- One **device per printer** in PrintGuard

## Sensors

### Status Sensor
- **Entity ID**: `sensor.printguard_<printer_id>_status`
- **States**: `idle`, `printing`, `paused`, `error`, `disconnected`, `unknown`

### Connection Status Sensor

- **Entity ID**: `sensor.printguard_<config_entry_id>_connection`
- **States**: `connected`, `error`

## Binary Sensors

### Defect Detected
- **Entity ID**: `binary_sensor.printguard_<printer_id>_defect`
- **On**: Defect detected
- **Off**: Normal

## Buttons

### Refresh

- `button.printguard_<config_entry_id>_refresh`: forces a refresh of PrintGuard data

### Control buttons (only if the printer has control)

- `button.printguard_<printer_id>_start`
- `button.printguard_<printer_id>_pause`
- `button.printguard_<printer_id>_resume`
- `button.printguard_<printer_id>_stop`

## Camera

### Snapshot Camera
- **Entity ID**: `camera.printguard_<printer_id>_camera`
- Returns a still image via PrintGuard’s `/api/rtc/snapshot/{session_id}`
- Supports WebRTC viewing when Home Assistant supports the `WEB_RTC` camera feature

## Events

### Defect Detected Event
- **Event type**: `printguard_defect_detected`
- **Data**:
  ```yaml
  printer_id: "abc123"
  printer_name: "Ender 3"
  class: "defect"
  confidence: 0.95
  session_id: "optional-linked-session"
  ```

