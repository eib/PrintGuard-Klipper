# Integrations Overview

PrintGuard integrates with printers and camera sources via “providers”. Providers can be used to build modular printers out of:

- **Status** component (is it printing?)
- **Camera** component (video feed for inference)
- **Control** component (start/pause/resume/stop)

Providers declare their configuration schema via `GET /api/printer/providers/{provider}/schema`, split into:

- **connection_fields**: stored on a Connection (`/api/connections`)
- **entity_fields**: stored on a Component (`/api/components` → `entity_config`)

At runtime, PrintGuard merges `connection.config` + `component.entity_config` before instantiating the provider.

## Supported Providers

- Bambu Labs
- OctoPrint
- Home Assistant
- Webcams

## Typical setup flow

1. Create a **Connection** (provider credentials / base URL).
2. Create one or more **Components** for that provider (camera/status/control).
3. Create a **Printer** and link the components into the desired roles.

Not all providers need both a Connection and entity config (for example, Webcam has no Connection; OctoPrint has no entity fields).

