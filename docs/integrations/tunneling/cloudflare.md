# Cloudflare Tunnel

Use Cloudflare Tunnel to expose your PrintGuard WebUI/API securely with a stable hostname under your domain.

## Requirements

- `cloudflared` installed on the server and available in `PATH`
- A Cloudflare account and a zone (domain) you control
- A Cloudflare API token with permissions to manage:
  - Tunnels
  - DNS records for the target zone

## Setup (WebUI)

1. Go to **Settings → Remote Access**.
2. Choose **Cloudflare Tunnel**.
3. Paste a Cloudflare **API Token**.
4. Select your **Account** and **Zone**.
5. Choose a **Tunnel Name** and **Subdomain** (e.g. `camera` → `https://camera.example.com`).
6. If a tunnel/DNS record already exists, decide whether to overwrite.

## API endpoints used

- `GET /api/tunnel/status` (view current status)
- `GET /api/tunnel/check-dependencies` (admin-only)
- `GET /api/cloudflare/validate-token?api_token=...` (requires `tunnel:manage`)
- `GET /api/cloudflare/accounts?api_token=...` (requires `tunnel:manage`)
- `GET /api/cloudflare/zones?api_token=...` (requires `tunnel:manage`)
- `GET /api/cloudflare/check-existence?...` (requires `tunnel:manage`)
- `POST /api/cloudflare/tunnel?api_token=...` (requires `tunnel:manage`)
- `POST /api/tunnel/disable` (admin-only)

## Notes

- Cloudflare tunnels are configured to forward to the WebUI port (`webui_port`, default `5173`).
- Successful setup persists tunnel settings to `.env` so they survive restarts.

## Setup

1. Configure secure remote access.

