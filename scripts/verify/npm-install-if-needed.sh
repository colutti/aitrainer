#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$1"
LOCK_FILE="$APP_DIR/package-lock.json"
STAMP_FILE="$APP_DIR/node_modules/.package-lock.sha256"
NPM_CI_TIMEOUT_SECONDS="${NPM_CI_TIMEOUT_SECONDS:-300}"
NPM_CI_MAX_RETRIES="${NPM_CI_MAX_RETRIES:-2}"

current_hash="$(sha256sum "$LOCK_FILE" | awk '{print $1}')"
stored_hash=""

if [ -f "$STAMP_FILE" ]; then
  stored_hash="$(cat "$STAMP_FILE")"
fi

if [ ! -x "$APP_DIR/node_modules/.bin/vitest" ] || [ "$current_hash" != "$stored_hash" ]; then
  echo "[info] Installing npm dependencies in $APP_DIR"
  attempt=1
  until [ "$attempt" -gt "$NPM_CI_MAX_RETRIES" ]; do
    (
      cd "$APP_DIR" || exit 1
      timeout "$NPM_CI_TIMEOUT_SECONDS" npm ci --no-audit --no-fund --progress=false --loglevel=info
    ) &
    npm_pid=$!
    while kill -0 "$npm_pid" >/dev/null 2>&1; do
      echo "[info] npm ci still running in $APP_DIR (attempt $attempt/$NPM_CI_MAX_RETRIES)"
      sleep 30
    done

    if wait "$npm_pid"; then
      break
    fi

    if [ "$attempt" -eq "$NPM_CI_MAX_RETRIES" ]; then
      echo "[error] npm ci failed after $NPM_CI_MAX_RETRIES attempts in $APP_DIR" >&2
      exit 1
    fi

    echo "[warn] npm ci failed in $APP_DIR (attempt $attempt/$NPM_CI_MAX_RETRIES), retrying..."
    attempt=$((attempt + 1))
    sleep 2
  done

  mkdir -p "$(dirname "$STAMP_FILE")"
  printf '%s' "$current_hash" >"$STAMP_FILE"
fi
