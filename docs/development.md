# Local Development (Git Clone)

> Use this guide to run and troubleshoot PrintGuard from source on a local machine (including Raspberry Pi).

## Table of Contents

- [Prerequisites](#prerequisites)
- [1) Clone the Repository](#1-clone-the-repository)
- [2) Start with the Helper Script](#2-start-with-the-helper-script)
- [3) Manual Setup (Optional)](#3-manual-setup-optional)
- [Build Notes](#build-notes)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.11+
- Git
- Camera access permissions on the target machine

On Raspberry Pi OS, ensure `python3-venv` is installed:

- `sudo apt update && sudo apt install -y python3-venv`

## 1) Clone the Repository

- Clone PrintGuard to your target machine.
- Change into the project root directory.

## 2) Start with the Helper Script

From the project root, run:

- `./dev_start.sh`

What the script does:

- Creates `.venv` if missing.
- Activates `.venv`.
- Installs/updates dependencies only when `printguard/requirements.txt` changes.
- Starts PrintGuard from source via `python -m printguard.app`.

## 3) Manual Setup (Optional)

If you prefer manual steps:

1. Create virtual environment:
   - `python3 -m venv .venv`
2. Activate it:
   - `source .venv/bin/activate`
3. Install dependencies:
   - `pip install -r printguard/requirements.txt`
4. Run:
   - `python -m printguard.app`

## Build Notes

A build step is not required for local development from source.

Only build/package when you need distributables:

- Python package build (`sdist`/`wheel`)
- Docker image build

## Troubleshooting

### Python version mismatch

- Symptom: dependency install failures or runtime errors.
- Fix: use Python 3.11+ and recreate venv:
  - remove `.venv`, then re-run `./dev_start.sh`.

### Missing venv module

- Symptom: `No module named venv`.
- Fix (Debian/RPi): install `python3-venv`.

### Dependency install errors on Raspberry Pi

- Re-run the script; it is safe and idempotent.
- Ensure system packages and pip are up to date.

### App starts but camera feed fails

- Verify camera source URL/device and permissions.
- For HTTP snapshot cameras, confirm endpoint returns a JPEG image.
- For MJPEG/RTSP, verify stream is reachable from the Pi.

### Port conflict (8000 already in use)

- Stop the process causing conflicts (e.g. use `lsof -i :8000` to find the process).
- Alternatively, change the `http_port` setting and restart.

### Config location confusion

- Docker: `/data/config.json`
- Native: platform app data directory for `printguard`

For local-first behavior, confirm config flags are set as expected:

- `startup_mode: "local"`
- `local_only_mode: true`
- `http_port: 8000`
- `require_ssl_for_local: false`
- `require_vapid_for_startup: false`
