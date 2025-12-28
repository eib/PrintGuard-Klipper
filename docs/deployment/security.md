# Security

PrintGuard is designed to run on a trusted network by default. If you expose it publicly, harden both the service and your network.

## Best Practices

Securing your PrintGuard instance.

## Recommendations

- **Change the JWT secret**: set `JWT_SECRET_KEY` in `.env` (the default is not safe for production).
- **Persist crypto keys**: set `CRYPTO_PRIVATE_KEY` so encrypted clients (e.g. Home Assistant) don’t break across restarts.
- **Use least-privilege scopes**:
  - Create M2M applications with only the scopes they need.
  - Avoid giving `admin` unless necessary.
- **Protect secrets**:
  - Treat `.env` and `.vapid_keys.json` as secrets (file permissions, backups, etc.).
  - Don’t commit them to source control.
- **Use HTTPS for remote access**:
  - Prefer Cloudflare Tunnel or another TLS-terminating reverse proxy.
  - If using a reverse proxy, ensure it forwards `X-Forwarded-Proto`/`X-Forwarded-Host` correctly.
- **Restrict access**:
  - Bind to LAN only if you don’t need remote access.
  - Use firewall rules to restrict access to the API/WebUI ports.
- **Keep dependencies updated**:
  - Regularly update the container/image and Home Assistant integration.

