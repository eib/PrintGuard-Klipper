# Connections

Connections store credentials/config for external systems (Home Assistant / OctoPrint / Bambu Labs). Components can reference a connection, and PrintGuard will merge the connection config into the component’s runtime configuration.

## Overview

Managing external service connections.

## Usage

1. Go to **Connections**.
2. Click **Add Connection**.
3. Choose a provider and fill in the fields (the form is generated from `GET /api/printer/providers/{provider}/schema`).
4. Save. You can now attach this connection to components.

## Tips

- Connection validation and “health” checks are provider-specific and can be run from the API (`GET /api/connections/{id}/health`).
- Sensitive fields may be masked in API responses (for example `token`, `api_key`, `access_code` are returned as `"********"`).
- Deleting a connection may be blocked if components reference it; the API supports a `cascade` delete (`DELETE /api/connections/{id}?cascade=true`) but the WebUI will prompt first.

