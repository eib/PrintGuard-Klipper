# HA Integration Configuration

The Home Assistant integration connects HA to PrintGuard in two directions:

- **HA → PrintGuard**: during config flow, you can export HA cameras/sensors/buttons as PrintGuard components.
- **PrintGuard → HA**: once printers exist in PrintGuard, HA creates entities to monitor/control them.

## Config Flow

### Step 1: Connect to PrintGuard

You will be asked for:

- **PrintGuard URL** (e.g. `http://printguard.local:8000`)
- **Client ID / Client Secret**: from a PrintGuard M2M application
- **Token**: a Home Assistant long-lived access token

During setup, the integration will:

- Call `GET /api/health` and `GET /api/crypto/key`
- Generate a client keypair for optional encrypted API calls
- Authenticate to PrintGuard via `POST /api/auth/token`
- Create a PrintGuard connection named **Home Assistant** with provider `homeassistant` that stores your HA URL and token

### Step 2: Export entities to PrintGuard (optional but recommended)

You’ll be prompted to select:

- **Cameras** (`camera.*`) to export as PrintGuard **camera** components
- **Sensors** (`sensor.*` / `binary_sensor.*`) to export as PrintGuard **status** components
- **Status mapping** (comma-separated lists for printing/paused/error states)
- **Controls** (`switch.*` / `button.*`) to export as PrintGuard **control** components

These are created in PrintGuard via `/api/components`, attached to the Home Assistant connection.

### After setup: create printers in PrintGuard

Exporting components does not automatically create printers. In the PrintGuard WebUI, create printers and select the exported components for their roles.

