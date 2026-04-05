#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$1"
LOCK_FILE="$APP_DIR/package-lock.json"
STAMP_FILE="$APP_DIR/node_modules/.package-lock.sha256"
NPM_CI_TIMEOUT_SECONDS="${NPM_CI_TIMEOUT_SECONDS:-300}"
NPM_CI_MAX_RETRIES="${NPM_CI_MAX_RETRIES:-2}"
NPM_CI_REGISTRY_FALLBACKS="${NPM_CI_REGISTRY_FALLBACKS:-${NPM_CONFIG_REGISTRY:-https://registry.npmmirror.com/},https://registry.npmjs.org/}"
NPM_CI_FETCH_RETRIES_PER_ATTEMPT="${NPM_CI_FETCH_RETRIES_PER_ATTEMPT:-1}"
NPM_CI_FETCH_RETRY_MINTIMEOUT_PER_ATTEMPT="${NPM_CI_FETCH_RETRY_MINTIMEOUT_PER_ATTEMPT:-1000}"
NPM_CI_FETCH_RETRY_MAXTIMEOUT_PER_ATTEMPT="${NPM_CI_FETCH_RETRY_MAXTIMEOUT_PER_ATTEMPT:-4000}"

current_hash="$(sha256sum "$LOCK_FILE" | awk '{print $1}')"
stored_hash=""

if [ -f "$STAMP_FILE" ]; then
  stored_hash="$(cat "$STAMP_FILE")"
fi

if [ ! -x "$APP_DIR/node_modules/.bin/vitest" ] || [ "$current_hash" != "$stored_hash" ]; then
  echo "[info] Installing npm dependencies in $APP_DIR"
  declare -a registries=()
  normalized_fallbacks="${NPM_CI_REGISTRY_FALLBACKS//,/ }"
  for registry in $normalized_fallbacks; do
    [ -n "$registry" ] || continue
    duplicate=0
    for existing in "${registries[@]}"; do
      if [ "$existing" = "$registry" ]; then
        duplicate=1
        break
      fi
    done
    if [ "$duplicate" -eq 0 ]; then
      registries+=("$registry")
    fi
  done

  if [ "${#registries[@]}" -eq 0 ]; then
    echo "[error] No npm registry configured for npm ci" >&2
    exit 1
  fi

  attempt=1
  until [ "$attempt" -gt "$NPM_CI_MAX_RETRIES" ]; do
    registry_index=$(( (attempt - 1) % ${#registries[@]} ))
    current_registry="${registries[$registry_index]}"
    echo "[info] npm ci attempt $attempt/$NPM_CI_MAX_RETRIES using registry: $current_registry"
    (
      cd "$APP_DIR" || exit 1
      NPM_CONFIG_FETCH_RETRIES="$NPM_CI_FETCH_RETRIES_PER_ATTEMPT" \
      NPM_CONFIG_FETCH_RETRY_MINTIMEOUT="$NPM_CI_FETCH_RETRY_MINTIMEOUT_PER_ATTEMPT" \
      NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT="$NPM_CI_FETCH_RETRY_MAXTIMEOUT_PER_ATTEMPT" \
      NPM_CONFIG_PREFER_OFFLINE=true \
      timeout "$NPM_CI_TIMEOUT_SECONDS" npm ci --registry "$current_registry" --no-audit --no-fund --progress=false --loglevel=info
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
