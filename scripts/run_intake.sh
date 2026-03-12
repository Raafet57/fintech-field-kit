#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Prefer Drive inbox if it exists; fallback to local inbox.
DRIVE_INBOX="/Users/Raafet/Library/CloudStorage/GoogleDrive-raafet.ch@gmail.com/My Drive/Papers inbox"
LOCAL_INBOX="/Users/Raafet/Projects/Papers/_inbox"

INBOX=""
if [[ -d "$DRIVE_INBOX" ]]; then
  INBOX="$DRIVE_INBOX"
elif [[ -d "$LOCAL_INBOX" ]]; then
  INBOX="$LOCAL_INBOX"
fi

ARGS=()
if [[ -n "$INBOX" ]]; then
  if [[ " $* " != *" --inbox "* ]]; then
    ARGS+=(--inbox "$INBOX")
  fi
fi

python3 "$ROOT/scripts/intake.py" "${ARGS[@]}" "$@"
