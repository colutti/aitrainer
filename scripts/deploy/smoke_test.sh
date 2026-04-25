#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

LAST_DEPLOY_FILE="$ROOT_DIR/scripts/deploy/.last_deploy.env"
if [[ -f "$LAST_DEPLOY_FILE" ]]; then
  # shellcheck disable=SC1090
  . "$LAST_DEPLOY_FILE"
else
  BACKEND_URL="$(gcloud run services describe "$BACKEND_SERVICE" --project "$GCP_PROJECT_ID" --region "$GCP_REGION" --format='value(status.url)')"
  FRONTEND_URL="$(gcloud run services describe "$FRONTEND_SERVICE" --project "$GCP_PROJECT_ID" --region "$GCP_REGION" --format='value(status.url)')"
fi

: "${BACKEND_URL:?missing backend url}"
: "${FRONTEND_URL:?missing frontend url}"

start_epoch="$(date +%s)"

echo "smoke: backend health"
curl -fsS "${BACKEND_URL}/health" >/dev/null

echo "smoke: frontend runtime config"
runtime_config="$(curl -fsS "${FRONTEND_URL}/runtime-config.js")"

# Guarantee runtime social auth settings are injected.
for required_key in \
  VITE_FIREBASE_API_KEY \
  VITE_FIREBASE_AUTH_DOMAIN \
  VITE_FIREBASE_PROJECT_ID \
  VITE_FIREBASE_STORAGE_BUCKET \
  VITE_FIREBASE_MESSAGING_SENDER_ID \
  VITE_FIREBASE_APP_ID; do
  if ! grep -q "${required_key}: '" <<<"$runtime_config"; then
    echo "missing runtime config key: ${required_key}" >&2
    exit 1
  fi
  if grep -q "${required_key}: ''" <<<"$runtime_config"; then
    echo "runtime config key is empty: ${required_key}" >&2
    exit 1
  fi
done

# Verify frontend can reach backend route through nginx proxy path.
echo "smoke: frontend proxy to backend"
curl -fsS "${FRONTEND_URL}/api/health" >/dev/null

duration="$(( $(date +%s) - start_epoch ))"
echo "smoke checks passed in ${duration}s"
