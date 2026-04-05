#!/usr/bin/env bash
set -euo pipefail

resolve_ip() {
  local host="$1"
  local attempts="${SERVICE_RESOLVE_ATTEMPTS:-30}"
  local sleep_seconds="${SERVICE_RESOLVE_SLEEP_SECONDS:-1}"
  local ip=""

  while [ "$attempts" -gt 0 ]; do
    ip="$(getent hosts "$host" | awk 'NR==1 { print $1 }')"
    if [ -n "$ip" ]; then
      echo "$ip"
      return 0
    fi
    attempts=$((attempts - 1))
    sleep "$sleep_seconds"
  done

  echo "[error] Unable to resolve service host: $host" >&2
  return 1
}

replace_host() {
  local value="$1"
  local from="$2"
  local to="$3"
  echo "${value//$from/$to}"
}

mongo_ip="$(resolve_ip "${MONGO_SERVICE_HOST:-mongo}")"
qdrant_ip="$(resolve_ip "${QDRANT_SERVICE_HOST:-qdrant}")"
stripe_ip="$(resolve_ip "${STRIPE_SERVICE_HOST:-stripe-mock}")"
firebase_ip="$(resolve_ip "${FIREBASE_SERVICE_HOST:-firebase-emulator}")"

if [ -n "${MONGO_URI:-}" ]; then
  MONGO_URI="$(replace_host "$MONGO_URI" "mongo:27017" "${mongo_ip}:27017")"
  export MONGO_URI
fi

if [ -n "${QDRANT_HOST:-}" ]; then
  QDRANT_HOST="$(replace_host "$QDRANT_HOST" "qdrant" "${qdrant_ip}")"
  export QDRANT_HOST
fi

if [ -n "${STRIPE_API_BASE:-}" ]; then
  STRIPE_API_BASE="$(replace_host "$STRIPE_API_BASE" "stripe-mock:12111" "${stripe_ip}:12111")"
  export STRIPE_API_BASE
fi

if [ -n "${FIREBASE_AUTH_EMULATOR_HOST:-}" ]; then
  FIREBASE_AUTH_EMULATOR_HOST="$(replace_host "$FIREBASE_AUTH_EMULATOR_HOST" "firebase-emulator:9099" "${firebase_ip}:9099")"
  export FIREBASE_AUTH_EMULATOR_HOST
fi

exec "$@"
