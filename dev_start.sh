#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-$PROJECT_ROOT/.venv}"
REQ_FILE="$PROJECT_ROOT/printguard/requirements.txt"
HASH_FILE="$VENV_DIR/.requirements.sha256"
PYTHON_BIN="${PYTHON_BIN:-python3}"

hash_cmd() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    echo "No SHA256 tool found (need sha256sum or shasum)." >&2
    exit 1
  fi
}

if [[ ! -d "$VENV_DIR" ]]; then
  echo "[dev_start] Creating virtual environment at $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

if [[ ! -f "$REQ_FILE" ]]; then
  echo "[dev_start] Requirements file not found: $REQ_FILE" >&2
  exit 1
fi

CURRENT_HASH="$(hash_cmd "$REQ_FILE")"
INSTALLED_HASH=""
if [[ -f "$HASH_FILE" ]]; then
  INSTALLED_HASH="$(cat "$HASH_FILE")"
fi

if [[ "$CURRENT_HASH" != "$INSTALLED_HASH" ]]; then
  echo "[dev_start] Installing/updating dependencies"
  python -m pip install --upgrade pip
  python -m pip install -r "$REQ_FILE"
  printf '%s' "$CURRENT_HASH" > "$HASH_FILE"
else
  echo "[dev_start] Dependencies unchanged; skipping install"
fi

echo "[dev_start] Starting PrintGuard"
exec python -m printguard.app
