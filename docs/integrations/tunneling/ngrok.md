# ngrok Tunnel

Use ngrok to expose your PrintGuard WebUI/API securely over the internet with minimal setup.

## Requirements

- Server has `ngrok-python` installed
- A valid ngrok auth token

## Setup (WebUI)

1. Go to **Settings → Remote Access**.
2. Choose **Ngrok Tunnel**.
3. Paste your **Ngrok Auth Token**.
4. Optionally set a **custom domain**.
5. Start the tunnel; the WebUI will show the public URL.

## API endpoints used

- `GET /api/tunnel/status` (view current status)
- `GET /api/tunnel/check-dependencies` (admin-only)
- `POST /api/ngrok/tunnel` (requires `tunnel:manage`)
- `POST /api/tunnel/disable` (admin-only)

## Notes

- ngrok is configured to forward to the WebUI port (`webui_port`, default `5173`).

## Setup

1. Set up ngrok for remote access.

