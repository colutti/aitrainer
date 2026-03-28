#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$1"
LOCK_FILE="$APP_DIR/package-lock.json"
STAMP_FILE="$APP_DIR/node_modules/.package-lock.sha256"

current_hash="$(sha256sum "$LOCK_FILE" | awk '{print $1}')"
stored_hash=""

if [ -f "$STAMP_FILE" ]; then
  stored_hash="$(cat "$STAMP_FILE")"
fi

if [ ! -x "$APP_DIR/node_modules/.bin/vitest" ] || [ "$current_hash" != "$stored_hash" ]; then
  (cd "$APP_DIR" && npm ci)
  mkdir -p "$(dirname "$STAMP_FILE")"
  printf '%s' "$current_hash" >"$STAMP_FILE"
fi
