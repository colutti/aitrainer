#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

ENV_BACKEND_FILE="${ENV_BACKEND_FILE:-$ROOT_DIR/backend/.env.prod}"
ENV_FRONTEND_FILE="${ENV_FRONTEND_FILE:-$ROOT_DIR/frontend/.env.prod}"

build_update_arg_from_env_file() {
  local env_file="$1"
  python3 - "$env_file" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    print("")
    sys.exit(0)

pairs = []
for raw in path.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    if line.lower().startswith("export "):
        line = line[7:].strip()
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        continue
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    pairs.append(f"{key}={value}")

if not pairs:
    print("")
else:
    delim = "@@"
    print("^" + delim + "^" + delim.join(pairs))
PY
}

update_arg_backend="$(build_update_arg_from_env_file "$ENV_BACKEND_FILE")"
update_arg_frontend="$(build_update_arg_from_env_file "$ENV_FRONTEND_FILE")"

if [[ -n "$update_arg_backend" ]]; then
  echo "updating backend env vars from ${ENV_BACKEND_FILE}"
  run_cmd gcloud run services update "$BACKEND_SERVICE" \
    --project "$GCP_PROJECT_ID" \
    --region "$GCP_REGION" \
    --update-env-vars "$update_arg_backend" \
    --quiet
else
  echo "no backend env updates applied (file missing or empty): ${ENV_BACKEND_FILE}"
fi

if [[ -n "$update_arg_frontend" ]]; then
  echo "updating frontend env vars from ${ENV_FRONTEND_FILE}"
  run_cmd gcloud run services update "$FRONTEND_SERVICE" \
    --project "$GCP_PROJECT_ID" \
    --region "$GCP_REGION" \
    --update-env-vars "$update_arg_frontend" \
    --quiet
else
  echo "no frontend env updates applied (file missing or empty): ${ENV_FRONTEND_FILE}"
fi

if bool_true "$ENABLE_ADMIN_DEPLOY"; then
  ENV_ADMIN_BACKEND_FILE="${ENV_ADMIN_BACKEND_FILE:-$ROOT_DIR/backend-admin/.env.prod}"
  ENV_ADMIN_FRONTEND_FILE="${ENV_ADMIN_FRONTEND_FILE:-$ROOT_DIR/frontend/admin/.env.prod}"

  update_arg_backend_admin="$(build_update_arg_from_env_file "$ENV_ADMIN_BACKEND_FILE")"
  update_arg_frontend_admin="$(build_update_arg_from_env_file "$ENV_ADMIN_FRONTEND_FILE")"

  if [[ -n "$update_arg_backend_admin" ]]; then
    echo "updating backend-admin env vars from ${ENV_ADMIN_BACKEND_FILE}"
    run_cmd gcloud run services update "$BACKEND_ADMIN_SERVICE" \
      --project "$GCP_PROJECT_ID" \
      --region "$GCP_REGION" \
      --update-env-vars "$update_arg_backend_admin" \
      --quiet
  fi

  if [[ -n "$update_arg_frontend_admin" ]]; then
    echo "updating frontend-admin env vars from ${ENV_ADMIN_FRONTEND_FILE}"
    run_cmd gcloud run services update "$FRONTEND_ADMIN_SERVICE" \
      --project "$GCP_PROJECT_ID" \
      --region "$GCP_REGION" \
      --update-env-vars "$update_arg_frontend_admin" \
      --quiet
  fi
fi

echo "prod env sync completed"
