# Initial Configuration

This guide walks through the first-time setup after installing/running PrintGuard.

## Overview

On first startup, PrintGuard will:

- initialize the database
- create an **initial `admin` user** (if no users exist yet) and print the generated password to the server logs
- generate VAPID keys (if missing) and save them to `.vapid_keys.json`

## Steps

1. Start PrintGuard and watch the logs for the **INITIAL ADMIN USER CREATED** block (it includes the one-time password).
2. Open the WebUI:
   - in production: `http://<server>:8000/` (served from `webui/dist` when present)
   - in development: `http://localhost:5173/`
3. Log in as:
   - username: `admin`
   - password: the generated password from the logs
4. Go to **Settings**:
   - create additional users (optional)
   - create M2M applications for automation clients (Home Assistant, etc.)
   - configure Remote Access (optional)
5. Add your first printer:
   - create Connections (if needed)
   - create Components (camera required; status/control optional)
   - create a Printer and tune inference settings
6. (Optional) enable browser notifications on the printer card (requires browser permission).

