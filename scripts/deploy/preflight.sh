#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing required command: $1" >&2
    exit 1
  }
}

require_service_env_names() {
  local service="$1"
  shift
  local raw
  raw="$(gcloud run services describe "$service" \
    --project "$GCP_PROJECT_ID" \
    --region "$GCP_REGION" \
    --format="value(spec.template.spec.containers[0].env[].name)")"

  for required in "$@"; do
    if ! grep -qE "(^|[;,[:space:]])${required}([;,[:space:]]|$)" <<<"$raw"; then
      echo "missing env var '$required' in Cloud Run service '$service'" >&2
      exit 1
    fi
  done
}

echo "running deploy preflight checks"
require_cmd gcloud
require_cmd git

active_account="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -n 1)"
if [[ -z "$active_account" ]]; then
  echo "no active gcloud account found" >&2
  exit 1
fi
echo "gcloud active account: $active_account"

run_cmd gcloud run services describe "$BACKEND_SERVICE" --project "$GCP_PROJECT_ID" --region "$GCP_REGION" --format='value(metadata.name)' >/dev/null
run_cmd gcloud run services describe "$FRONTEND_SERVICE" --project "$GCP_PROJECT_ID" --region "$GCP_REGION" --format='value(metadata.name)' >/dev/null

if bool_true "$ENABLE_ADMIN_DEPLOY"; then
  run_cmd gcloud run services describe "$BACKEND_ADMIN_SERVICE" --project "$GCP_PROJECT_ID" --region "$GCP_REGION" --format='value(metadata.name)' >/dev/null
  run_cmd gcloud run services describe "$FRONTEND_ADMIN_SERVICE" --project "$GCP_PROJECT_ID" --region "$GCP_REGION" --format='value(metadata.name)' >/dev/null
fi

# Preserve social auth and API connectivity guarantees.
require_service_env_names "$FRONTEND_SERVICE" \
  BACKEND_URL \
  VITE_FIREBASE_API_KEY \
  VITE_FIREBASE_AUTH_DOMAIN \
  VITE_FIREBASE_PROJECT_ID \
  VITE_FIREBASE_STORAGE_BUCKET \
  VITE_FIREBASE_MESSAGING_SENDER_ID \
  VITE_FIREBASE_APP_ID

require_service_env_names "$BACKEND_SERVICE" \
  MONGO_URI \
  SECRET_KEY \
  FIREBASE_CREDENTIALS

echo "preflight checks passed"
