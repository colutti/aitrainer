#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

if [[ ! -f "$LAST_BUILD_FILE" ]]; then
  echo "build metadata not found: $LAST_BUILD_FILE" >&2
  echo "run ./scripts/deploy/build_images.sh first" >&2
  exit 1
fi

# shellcheck disable=SC1090
. "$LAST_BUILD_FILE"

: "${BACKEND_IMAGE_URI:?missing BACKEND_IMAGE_URI in $LAST_BUILD_FILE}"
: "${FRONTEND_IMAGE_URI:?missing FRONTEND_IMAGE_URI in $LAST_BUILD_FILE}"
ENABLED_SERVICES_CSV="${ENABLED_SERVICES_CSV-}"
ENABLED_SERVICES_STR="${ENABLED_SERVICES_CSV//,/ }"

service_enabled() {
  local service_name="$1"
  case " ${ENABLED_SERVICES_STR} " in
    *" ${service_name} "*) return 0 ;;
    *) return 1 ;;
  esac
}

run_service_update() {
  local service="$1"
  local image_uri="$2"

  echo "deploying ${service} -> ${image_uri}"
  run_cmd gcloud run services update "$service" \
    --project "$GCP_PROJECT_ID" \
    --region "$GCP_REGION" \
    --image "$image_uri" \
    --update-labels "managed-by=codex,deploy-tag=${DEPLOY_TAG_RESOLVED}" \
    --quiet
}

start_epoch="$(date +%s)"
if [[ -z "${ENABLED_SERVICES_STR// }" ]]; then
  echo "no services enabled for deploy update (change-aware no-op)"
fi

if service_enabled backend; then
  run_service_update "$BACKEND_SERVICE" "$BACKEND_IMAGE_URI"
fi
if service_enabled frontend; then
  run_service_update "$FRONTEND_SERVICE" "$FRONTEND_IMAGE_URI"
fi

if bool_true "$ENABLE_ADMIN_DEPLOY" && service_enabled backend-admin; then
  : "${BACKEND_ADMIN_IMAGE_URI:?missing BACKEND_ADMIN_IMAGE_URI in $LAST_BUILD_FILE}"
  run_service_update "$BACKEND_ADMIN_SERVICE" "$BACKEND_ADMIN_IMAGE_URI"
fi
if bool_true "$ENABLE_ADMIN_DEPLOY" && service_enabled frontend-admin; then
  : "${FRONTEND_ADMIN_IMAGE_URI:?missing FRONTEND_ADMIN_IMAGE_URI in $LAST_BUILD_FILE}"
  run_service_update "$FRONTEND_ADMIN_SERVICE" "$FRONTEND_ADMIN_IMAGE_URI"
fi

backend_url="$(gcloud run services describe "$BACKEND_SERVICE" --project "$GCP_PROJECT_ID" --region "$GCP_REGION" --format='value(status.url)')"
frontend_url="$(gcloud run services describe "$FRONTEND_SERVICE" --project "$GCP_PROJECT_ID" --region "$GCP_REGION" --format='value(status.url)')"

backend_admin_url=""
frontend_admin_url=""
if bool_true "$ENABLE_ADMIN_DEPLOY"; then
  backend_admin_url="$(gcloud run services describe "$BACKEND_ADMIN_SERVICE" --project "$GCP_PROJECT_ID" --region "$GCP_REGION" --format='value(status.url)')"
  frontend_admin_url="$(gcloud run services describe "$FRONTEND_ADMIN_SERVICE" --project "$GCP_PROJECT_ID" --region "$GCP_REGION" --format='value(status.url)')"
fi

cat >"$ROOT_DIR/scripts/deploy/.last_deploy.env" <<EOM
DEPLOY_TAG=${DEPLOY_TAG_RESOLVED}
BACKEND_URL=${backend_url}
FRONTEND_URL=${frontend_url}
BACKEND_ADMIN_URL=${backend_admin_url}
FRONTEND_ADMIN_URL=${frontend_admin_url}
EOM

duration="$(( $(date +%s) - start_epoch ))"
echo "deploy finished in ${duration}s"
echo "backend: ${backend_url}"
echo "frontend: ${frontend_url}"
if bool_true "$ENABLE_ADMIN_DEPLOY"; then
  echo "backend-admin: ${backend_admin_url}"
  echo "frontend-admin: ${frontend_admin_url}"
fi
