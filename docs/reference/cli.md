# CLI Reference

The PrintGuard CLI is exposed as the `printguard` command. It is available:

- **In Docker containers** - The CLI is installed and used by default (see [Docker Installation](../getting-started/installation.md#docker-installation-recommended))
- **When installing from source** - Install with `pip install -e .` (see [From Source](../getting-started/installation.md#from-source-for-developers))

!!! note
    The CLI is **not** available via PyPI. Only `printguard-shared` (a shared library dependency) is published to PyPI. The main `printguard` package with the CLI is only distributed via Docker images or source installation.

## Commands

### `printguard serve`

Start the FastAPI server.

Common options:

- `--host` / `-h` (default `0.0.0.0`)
- `--port` / `-p` (default `8000`)
- `--reload` / `-r` (development auto-reload)
- `--tunnel` / `-t` (`local`, `cloudflare`, `ngrok`)

Example:

```bash
printguard serve --reload
```

### `printguard user add`

Create a new user in the database.

```bash
printguard user add alice
```

You’ll be prompted for a password. You can also set scopes:

```bash
printguard user add alice --scopes "printer:read printer:write rtc:stream"
```

### `printguard m2m add`

Create a machine-to-machine application (client id/secret).

```bash
printguard m2m add "Home Assistant" --scopes "printer:read printer:write rtc:stream admin"
```

### `printguard generate-keys`

Generate VAPID keys for browser push notifications.

```bash
printguard generate-keys --env
```

### `printguard version`

Print the installed PrintGuard version.

```bash
printguard version
```

