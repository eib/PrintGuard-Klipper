# Home Assistant Installation

## HACS Installation (Recommended)

1. Open HACS in Home Assistant
2. Click **Integrations**
3. Click the menu (three dots) → **Custom repositories**
4. Add: `https://github.com/oliverbravery/PrintGuard`
5. Category: **Integration**
6. Click **Add**
7. Search for "PrintGuard" and install
8. Restart Home Assistant

## Manual Installation

1. Download the `custom_components/printguard` folder
2. Copy to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "PrintGuard"
4. Enter your PrintGuard/Home Assistant details:
   - **URL**: `http://your-server:8000`
   - **Client ID**: From M2M application
   - **Client Secret**: From M2M application
   - **Token**: a Home Assistant long-lived access token (used by PrintGuard to query HA entities/cameras)

## Creating M2M Credentials

On your PrintGuard server:

1. Login as admin
2. Go to **Settings** → **M2M Applications**
3. Click **Create Application**
4. Name it "Home Assistant"
5. Copy the `client_id` and `client_secret`

> Important: the Home Assistant integration requests scopes including `printer:read`, `printer:write`, `rtc:stream`, and currently also `admin`. Make sure your M2M application includes the scopes the integration requests.

