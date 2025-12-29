# Configuration Reference

PrintGuard is configured via environment variables or `.env` file.

## Core Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server bind address | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Enable debug mode | `false` |
| `WEBUI_PORT` | WebUI port (used for tunnels / dev defaults) | `8000` (`5173` in local dev) |

## Security

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | JWT signing secret | `changeme-in-production-use-a-secure-key` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `10080` (7 days) |
| `CRYPTO_PRIVATE_KEY` | Base64 server private key (enables stable encrypted clients) | empty (in-memory key) |

## Database

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite URL | `sqlite+aiosqlite:///./printguard.db` |

## Push Notifications

| Variable | Description | Default |
|----------|-------------|---------|
| `VAPID_PUBLIC_KEY` | VAPID public key | auto-generated if missing (may be saved to `.vapid_keys.json`) |
| `VAPID_PRIVATE_KEY` | VAPID private key | auto-generated if missing (may be saved to `.vapid_keys.json`) |

## Tunneling

| Variable | Description | Default |
|----------|-------------|---------|
| `TUNNEL_PROVIDER` | `local`, `cloudflare`, `ngrok` | `local` |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token | - |
| `CLOUDFLARE_DOMAIN` | Domain name | - |
| `CLOUDFLARE_TUNNEL_NAME` | Cloudflare tunnel name | `printguard-tunnel` |
| `CLOUDFLARE_SUBDOMAIN` | Subdomain to create/use | `camera` |
| `CLOUDFLARE_TUNNEL_ID` | Tunnel id (persisted after setup) | - |
| `CLOUDFLARE_TUNNEL_SECRET` | Tunnel secret (persisted after setup) | - |
| `CLOUDFLARE_ACCOUNT_ID` | Account id (persisted after setup) | - |
| `NGROK_AUTHTOKEN` | ngrok auth token | - |
| `NGROK_DOMAIN` | Static ngrok domain | - |
| `NGROK_EDGE` | ngrok edge id | - |

## Screenshots

| Variable | Description | Default |
|----------|-------------|---------|
| `SCREENSHOT_RETENTION_HOURS` | How long to keep screenshots | `24` |
| `SCREENSHOT_MAX_COUNT` | Maximum screenshots to store | `100` |
| `SCREENSHOT_CLEANUP_INTERVAL_MINUTES` | Cleanup interval | `60` |

