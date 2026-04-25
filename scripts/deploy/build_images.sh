#!/usr/bin/env bash
set -euo pipefail

cleanup_temp_files() {
  rm -f "${backend_id_file:-}" "${frontend_id_file:-}" "${backend_admin_id_file:-}" "${frontend_admin_id_file:-}" 2>/dev/null || true
}
trap cleanup_temp_files EXIT

. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

AUTO_DETECT_CHANGED="${AUTO_DETECT_CHANGED:-false}"
BASE_REF="${BASE_REF:-HEAD~1}"

service_enabled() {
  local service_name="$1"
  for enabled in "${ENABLED_SERVICES[@]}"; do
    if [[ "$enabled" == "$service_name" ]]; then
      return 0
    fi
  done
  return 1
}

append_service_if_missing() {
  local service_name="$1"
  if ! service_enabled "$service_name"; then
    ENABLED_SERVICES+=("$service_name")
  fi
}

resolve_enabled_services() {
  ENABLED_SERVICES=(backend frontend)
  if bool_true "$ENABLE_ADMIN_DEPLOY"; then
    ENABLED_SERVICES+=(backend-admin frontend-admin)
  fi

  if ! bool_true "$AUTO_DETECT_CHANGED"; then
    return 0
  fi

  if ! git -C "$ROOT_DIR" rev-parse --verify "$BASE_REF" >/dev/null 2>&1; then
    echo "change-aware mode skipped: base ref not found ($BASE_REF)"
    return 0
  fi

  mapfile -t changed_files < <(git -C "$ROOT_DIR" diff --name-only "$BASE_REF"..HEAD)
  if [[ "${#changed_files[@]}" -eq 0 ]]; then
    echo "change-aware mode: no file changes detected, skipping builds"
    ENABLED_SERVICES=()
    return 0
  fi

  local selected=()
  for file in "${changed_files[@]}"; do
    case "$file" in
      backend/*)
        selected+=(backend)
        ;;
      frontend/admin/*)
        selected+=(frontend-admin)
        ;;
      frontend/*)
        selected+=(frontend)
        ;;
      backend-admin/*)
        selected+=(backend-admin)
        ;;
      scripts/deploy/*|Makefile|.github/workflows/deploy-prod.yml)
        # Infra deployment changes can impact all deployable services.
        selected=(backend frontend backend-admin frontend-admin)
        break
        ;;
    esac
  done

  if [[ "${#selected[@]}" -eq 0 ]]; then
    echo "change-aware mode: no deployable service changed, skipping builds"
    ENABLED_SERVICES=()
    return 0
  fi

  ENABLED_SERVICES=()
  for item in "${selected[@]}"; do
    append_service_if_missing "$item"
  done
  if ! bool_true "$ENABLE_ADMIN_DEPLOY"; then
    local filtered=()
    for service_name in "${ENABLED_SERVICES[@]}"; do
      case "$service_name" in
        backend-admin|frontend-admin)
          ;;
        *)
          filtered+=("$service_name")
          ;;
      esac
    done
    ENABLED_SERVICES=("${filtered[@]}")
  fi
}

start_build() {
  local service_name="$1"
  local source_dir="$2"
  local dockerfile_path="$3"
  local image_uri="$4"
  local cache_repo="$5"

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[dry-run] gcloud builds submit $source_dir --project $GCP_PROJECT_ID --region $GCP_REGION --config scripts/deploy/cloudbuild-kaniko.yaml --substitutions _DOCKERFILE=$dockerfile_path,_IMAGE_URI=$image_uri,_CACHE_REPO=$cache_repo --async"
    echo "dry-run-${service_name}"
    return 0
  fi

  gcloud builds submit "$source_dir" \
    --project "$GCP_PROJECT_ID" \
    --region "$GCP_REGION" \
    --config "$ROOT_DIR/scripts/deploy/cloudbuild-kaniko.yaml" \
    --substitutions "_DOCKERFILE=${dockerfile_path},_IMAGE_URI=${image_uri},_CACHE_REPO=${cache_repo}" \
    --async \
    --format="value(id)"
}

wait_build() {
  local service_name="$1"
  local build_id="$2"

  if [[ "$build_id" == dry-run-* ]]; then
    return 0
  fi

  while true; do
    local status
    status="$(gcloud builds describe "$build_id" --project "$GCP_PROJECT_ID" --region "$GCP_REGION" --format="value(status)")"
    case "$status" in
      SUCCESS)
        echo "build for ${service_name} succeeded (${build_id})"
        return 0
        ;;
      FAILURE|CANCELLED|TIMEOUT|EXPIRED|INTERNAL_ERROR)
        echo "build for ${service_name} failed with status ${status} (${build_id})" >&2
        gcloud builds describe "$build_id" --project "$GCP_PROJECT_ID" --region "$GCP_REGION" --format="value(logUrl)" >&2 || true
        return 1
        ;;
      *)
        sleep 5
        ;;
    esac
  done
}

submit_build_async() {
  local service_name="$1"
  local source_dir="$2"
  local dockerfile_path="$3"
  local image_uri="$4"
  local cache_repo="$5"
  local out_file="$6"

  (
    build_id="$(start_build "$service_name" "$source_dir" "$dockerfile_path" "$image_uri" "$cache_repo")"
    echo "$build_id" >"$out_file"
  ) &
}

backend_image_uri="${IMAGE_REGISTRY}/aitrainer-backend:${DEPLOY_TAG_RESOLVED}"
frontend_image_uri="${IMAGE_REGISTRY}/aitrainer-frontend:${DEPLOY_TAG_RESOLVED}"
backend_cache_repo="${IMAGE_REGISTRY}/buildcache/aitrainer-backend"
frontend_cache_repo="${IMAGE_REGISTRY}/buildcache/aitrainer-frontend"

backend_admin_image_uri="${IMAGE_REGISTRY}/aitrainer-backend-admin:${DEPLOY_TAG_RESOLVED}"
frontend_admin_image_uri="${IMAGE_REGISTRY}/aitrainer-frontend-admin:${DEPLOY_TAG_RESOLVED}"
backend_admin_cache_repo="${IMAGE_REGISTRY}/buildcache/aitrainer-backend-admin"
frontend_admin_cache_repo="${IMAGE_REGISTRY}/buildcache/aitrainer-frontend-admin"

echo "starting image builds with tag ${DEPLOY_TAG_RESOLVED}"
start_epoch="$(date +%s)"

resolve_enabled_services
echo "enabled services for build: ${ENABLED_SERVICES[*]:-none}"

backend_build_id=""
frontend_build_id=""
backend_admin_build_id=""
frontend_admin_build_id=""
backend_id_file=""
frontend_id_file=""
backend_admin_id_file=""
frontend_admin_id_file=""

if service_enabled backend; then
  backend_id_file="$(mktemp)"
  submit_build_async backend backend Dockerfile "$backend_image_uri" "$backend_cache_repo" "$backend_id_file"
fi
if service_enabled frontend; then
  frontend_id_file="$(mktemp)"
  submit_build_async frontend frontend Dockerfile "$frontend_image_uri" "$frontend_cache_repo" "$frontend_id_file"
fi

if service_enabled backend-admin; then
  backend_admin_id_file="$(mktemp)"
  submit_build_async backend-admin backend-admin Dockerfile "$backend_admin_image_uri" "$backend_admin_cache_repo" "$backend_admin_id_file"
fi
if service_enabled frontend-admin; then
  frontend_admin_id_file="$(mktemp)"
  submit_build_async frontend-admin frontend admin/Dockerfile "$frontend_admin_image_uri" "$frontend_admin_cache_repo" "$frontend_admin_id_file"
fi

wait

if [[ -n "$backend_id_file" && -f "$backend_id_file" ]]; then
  backend_build_id="$(cat "$backend_id_file")"
  rm -f "$backend_id_file"
fi
if [[ -n "$frontend_id_file" && -f "$frontend_id_file" ]]; then
  frontend_build_id="$(cat "$frontend_id_file")"
  rm -f "$frontend_id_file"
fi
if [[ -n "$backend_admin_id_file" && -f "$backend_admin_id_file" ]]; then
  backend_admin_build_id="$(cat "$backend_admin_id_file")"
  rm -f "$backend_admin_id_file"
fi
if [[ -n "$frontend_admin_id_file" && -f "$frontend_admin_id_file" ]]; then
  frontend_admin_build_id="$(cat "$frontend_admin_id_file")"
  rm -f "$frontend_admin_id_file"
fi

if [[ -n "$backend_build_id" ]]; then
  wait_build backend "$backend_build_id"
fi
if [[ -n "$frontend_build_id" ]]; then
  wait_build frontend "$frontend_build_id"
fi

if [[ -n "$backend_admin_build_id" ]]; then
  wait_build backend-admin "$backend_admin_build_id"
fi
if [[ -n "$frontend_admin_build_id" ]]; then
  wait_build frontend-admin "$frontend_admin_build_id"
fi

duration="$(( $(date +%s) - start_epoch ))"
echo "all builds finished in ${duration}s"

cat >"$LAST_BUILD_FILE" <<EOF
DEPLOY_TAG=${DEPLOY_TAG_RESOLVED}
BACKEND_IMAGE_URI=${backend_image_uri}
FRONTEND_IMAGE_URI=${frontend_image_uri}
BACKEND_ADMIN_IMAGE_URI=${backend_admin_image_uri}
FRONTEND_ADMIN_IMAGE_URI=${frontend_admin_image_uri}
ENABLED_SERVICES_CSV=$(IFS=,; echo "${ENABLED_SERVICES[*]}")
EOF

echo "build metadata saved to ${LAST_BUILD_FILE}"
