#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

GCP_PROJECT_ID="${GCP_PROJECT_ID:-fityq-488619}"
GCP_REGION="${GCP_REGION:-europe-southwest1}"
AR_REPOSITORY="${AR_REPOSITORY:-aitrainer}"
ENABLE_ADMIN_DEPLOY="${ENABLE_ADMIN_DEPLOY:-false}"
DRY_RUN="${DRY_RUN:-false}"

BACKEND_SERVICE="${BACKEND_SERVICE:-aitrainer-backend}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-aitrainer-frontend}"
BACKEND_ADMIN_SERVICE="${BACKEND_ADMIN_SERVICE:-aitrainer-backend-admin}"
FRONTEND_ADMIN_SERVICE="${FRONTEND_ADMIN_SERVICE:-aitrainer-frontend-admin}"

IMAGE_REGISTRY="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${AR_REPOSITORY}"

if [[ -n "${DEPLOY_TAG:-}" ]]; then
  DEPLOY_TAG_RESOLVED="$DEPLOY_TAG"
else
  DEPLOY_TAG_RESOLVED="$(date +%Y%m%d-%H%M%S)-$(git -C "$ROOT_DIR" rev-parse --short HEAD)"
fi

LAST_BUILD_FILE="$ROOT_DIR/scripts/deploy/.last_build.env"

run_cmd() {
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[dry-run] $*"
    return 0
  fi
  "$@"
}

bool_true() {
  [[ "$1" == "true" || "$1" == "1" || "$1" == "yes" ]]
}
