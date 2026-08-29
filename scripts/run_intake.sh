#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Prefer Drive inbox if it exists; fallback to local inbox.
DRIVE_INBOX="/Users/Raafet/Library/CloudStorage/GoogleDrive-raafet.ch@gmail.com/My Drive/Papers inbox"
LOCAL_INBOX="/Users/Raafet/Projects/Papers/_inbox"

INBOX=""
if [[ -d "$DRIVE_INBOX" ]]; then
  INBOX="$DRIVE_INBOX"
  log "Inbox: DRIVE -> $DRIVE_INBOX"
elif [[ -d "$LOCAL_INBOX" ]]; then
  INBOX="$LOCAL_INBOX"
  log "WARNING: Drive inbox is NOT reachable from this process."
  log "WARNING:   path: $DRIVE_INBOX"
  log "WARNING: Google Drive uses macOS FileProvider; ~/Library/CloudStorage is"
  log "WARNING: TCC-gated. A launchd agent has no such grant and cannot prompt,"
  log "WARNING: so the directory simply appears not to exist."
  log "WARNING: Fix: System Settings > Privacy & Security > Full Disk Access,"
  log "WARNING:      add /bin/bash, then reload the agent."
  if [[ "${PAPERS_ALLOW_LOCAL_FALLBACK:-0}" != "1" ]]; then
    log "ERROR: refusing to silently run against the empty local inbox."
    log "ERROR: set PAPERS_ALLOW_LOCAL_FALLBACK=1 to allow the fallback."
    exit 2
  fi
  log "Inbox: LOCAL (fallback allowed) -> $LOCAL_INBOX"
else
  log "ERROR: no inbox found (neither Drive nor local)."
  exit 2
fi

ARGS=()
if [[ -n "$INBOX" ]]; then
  if [[ " $* " != *" --inbox "* ]]; then
    ARGS+=(--inbox "$INBOX")
  fi
fi

# Use the project venv so brew/pyenv upgrades can't knock out PyPDF2.
PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  log "ERROR: missing venv at $ROOT/.venv"
  log "Recreate it with:"
  log "  cd \"$ROOT\" && python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt"
  exit 1
fi

# ${ARGS[@]+...} guard: bash 3.2 + `set -u` errors on an empty array otherwise.
"$PY" "$ROOT/scripts/intake.py" ${ARGS[@]+"${ARGS[@]}"} "$@"
