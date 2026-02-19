# Fork Notes

> Tracking document for fork-specific changes made on top of upstream PrintGuard, to help with later reconciliation.

## Scope

This file records the major behavioral and structural changes introduced in this fork so far, grouped by feature area.

---

## 1) Local-first / zero-setup startup

### Goal

Run PrintGuard locally without mandatory setup wizard, SSL, VAPID, or tunnel preconfiguration.

### Changes

- Startup defaults changed to local-first behavior.
- HTTP local mode supported without forced redirect to `/setup` when configured.
- SSL and VAPID startup requirements made configurable.
- `config.json` defaults now support zero-setup local operation.

### New config keys

- `local_only_mode`
- `require_ssl_for_local`
- `require_vapid_for_startup`
- `allow_unauthenticated_printer_api`

### Primary files

- `printguard/models.py`
- `printguard/utils/config.py`
- `printguard/utils/setup_utils.py`
- `printguard/app.py`

---

## 2) Optional unauthenticated printer API access

### Goal

Allow trusted-LAN deployments to use OctoPrint-compatible endpoints without requiring API keys.

### Changes

- `api_key` made optional in printer models.
- OctoPrint client now sends `X-Api-Key` only if key is provided.
- Backend policy gate added using `allow_unauthenticated_printer_api`.
- Frontend no longer hard-blocks empty API key input.

### Primary files

- `printguard/models.py`
- `printguard/utils/printer_services/octoprint.py`
- `printguard/routes/printer_routes.py`
- `printguard/templates/index.html`
- `printguard/static/js/index.js`
- `docs/api.md`

---

## 3) Moonraker integration (initial)

### Goal

Add Moonraker as a printer backend for state polling and pause/cancel actions.

### Changes

- Added printer type: `moonraker`.
- Added Moonraker service client.
- Printer polling path supports Moonraker.
- Alert countdown actions (`pause` / `cancel`) support Moonraker.
- Printer link UI updated to offer Moonraker option.

### Primary files

- `printguard/models.py`
- `printguard/utils/printer_services/moonraker.py` (new)
- `printguard/utils/printer_utils.py`
- `printguard/routes/printer_routes.py`
- `printguard/templates/index.html`
- `printguard/static/js/index.js`

---

## 4) Camera source extensions for HTTP snapshot workflows

### Goal

Support Spyglass-style consumption via HTTP snapshot polling (and keep stream URL support).

### Changes

- Camera state now includes:
  - `source_type` (`auto` / `snapshot`)
  - `poll_interval_ms`
- Add camera and preview endpoints accept source type + polling interval.
- Shared video stream supports snapshot polling mode using HTTP JPEG fetches.
- Add camera modal UI supports snapshot toggle and polling interval input.

### Primary files

- `printguard/models.py`
- `printguard/utils/camera_utils.py`
- `printguard/routes/camera_routes.py`
- `printguard/utils/shared_video_stream.py`
- `printguard/templates/index.html`
- `printguard/static/js/index.js`

---

## 5) Configurable application HTTP port

### Goal

Remove hardcoded `8000` and allow runtime port changes via JSON config.

### Changes

- Added default constant: `DEFAULT_HTTP_PORT = 8000`.
- Added helper: `get_http_port()` with validation and fallback.
- Added config key: `http_port`.
- Replaced hardcoded `8000` in app startup, ngrok tunnel setup, and Cloudflare command generation paths.

### Primary files

- `printguard/models.py`
- `printguard/utils/config.py`
- `printguard/app.py`
- `printguard/utils/setup_utils.py`
- `printguard/utils/cloudflare_utils.py`
- `printguard/routes/setup_routes.py`

---

## 6) Local development workflow docs + helper script

### Goal

Make source-based development on a Pi or local machine straightforward.

### Changes

- Added lazy-start helper script that:
  - creates/activates `.venv`
  - installs requirements only when hash changes
  - starts app from source
- Added local development documentation.
- Linked docs from README and docs index.

### Primary files

- `dev_start.sh` (new)
- `docs/development.md` (new)
- `README.md`
- `docs/overview.md`

---

## 7) Dependency updates

### Changes

- Added explicit `requests` dependency to support HTTP integrations.

### Primary files

- `pyproject.toml`
- `printguard/requirements.txt`

---

## 8) Documentation updates summary

### Updated docs

- `README.md`
- `docs/setup.md`
- `docs/api.md`
- `docs/overview.md`
- `docs/development.md` (new)
- `docs/Fork_Notes.md` (this file)

---

## 9) Setup wizard UX updates (skip + help)

### Goal

Reduce setup friction for local/self-managed installs while keeping users informed.

### Changes

- Added explicit skip paths in setup flow for:
  - VAPID setup
  - SSL setup
  - Final review step
- Added contextual help icons with external references for:
  - VAPID/web push concepts
  - SSL/TLS setup guidance
  - Setup documentation
- Setup progress and summary now treat skipped VAPID/SSL steps as completed states.
- Added `vapidSkipped` / `sslSkipped` state handling in setup frontend logic.
- Fixed Cloudflare finish button event binding to match the correct element id.
- Applied template/style/script formatting normalization in touched setup/index frontend files.

### Primary files

- `printguard/templates/setup.html`
- `printguard/static/js/setup.js`
- `printguard/static/css/setup.css`
- `printguard/templates/index.html`

---

## 10) Printer-linking UX/error handling hardening

### Goal

Improve reliability and clarity of printer-linking outcomes in the browser UI.

### Changes

- Fixed frontend runtime errors caused by referencing an undefined variable (`camIdx`) during printer link/unlink refresh flows.
- Improved printer add request handling to surface HTTP error details from non-2xx responses (for example `detail` from 400 responses) instead of showing generic `unknown` failures.

### Primary files

- `printguard/static/js/index.js`

---

## 11) Camera details read-only modal

### Goal

Provide a quick, non-editable view of camera configuration and runtime status, similar to the printer details popup.

### Changes

- Added a new **Camera Details** action in the settings panel.
- Added a read-only camera details modal showing source metadata and current settings/state.
- Wired modal data loading to existing `/camera/state` endpoint for selected camera.
- Added modal open/close behavior (button, close icon, and click-outside).
- Added dedicated styles for camera details rows inside the modal.

### Primary files

- `printguard/templates/index.html`
- `printguard/static/js/index.js`
- `printguard/static/css/index.css`

---

## Reconciliation notes for upstream merge/cherry-pick

### High-impact behavior differences to flag

- Startup defaults are now local-first (instead of setup-gated flow).
- Local HTTP operation is supported by default.
- Printer API key requirement can be disabled via config.
- Moonraker backend exists in fork but not in upstream baseline.
- Snapshot polling camera mode exists in fork.
- Runtime HTTP port is configurable via config JSON.

### Suggested merge strategy

1. Reconcile config schema additions first (`SavedConfig`, defaults, migrations).
2. Reconcile startup flow behavior (`app.py`, `setup_utils.py`).
3. Reconcile printer backend extensions (Moonraker + auth policy).
4. Reconcile camera source model and snapshot polling path.
5. Reconcile docs and helper tooling.

---

## Current example local-first config

```json
{
  "version": "1.0.0",
  "startup_mode": "local",
  "local_only_mode": true,
  "require_ssl_for_local": false,
  "require_vapid_for_startup": false,
  "allow_unauthenticated_printer_api": true,
  "http_port": 8000,
  "site_domain": "localhost",
  "push_subscriptions": [],
  "camera_states": {}
}
```
