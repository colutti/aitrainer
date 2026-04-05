#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"
. "$ROOT_DIR/scripts/lib/compose.sh"

PROJECT_NAME="fityq-verify-$(date +%s)-$$-$RANDOM"

cleanup() {
  COMPOSE_PROJECT_NAME="$PROJECT_NAME" \
  compose_cmd \
    -f "$ROOT_DIR/compose/test-base.yml" \
    -f "$ROOT_DIR/compose/verify.yml" \
    down --volumes --remove-orphans >/dev/null 2>&1 || true
}

trap cleanup EXIT

log_section "Running fast verification gate"
log_info "Using disposable test project: $PROJECT_NAME"

log_section "Verify backend"
COMPOSE_PROJECT_NAME="$PROJECT_NAME" \
compose_cmd \
  -f "$ROOT_DIR/compose/test-base.yml" \
  -f "$ROOT_DIR/compose/verify.yml" \
  run --rm backend-verify

log_section "Verify backend-admin"
COMPOSE_PROJECT_NAME="$PROJECT_NAME" \
compose_cmd \
  -f "$ROOT_DIR/compose/test-base.yml" \
  -f "$ROOT_DIR/compose/verify.yml" \
  run --rm backend-admin-verify

log_section "Verify frontend"
COMPOSE_PROJECT_NAME="$PROJECT_NAME" \
compose_cmd \
  -f "$ROOT_DIR/compose/test-base.yml" \
  -f "$ROOT_DIR/compose/verify.yml" \
  run --rm frontend-verify

log_section "Verify frontend-admin"
COMPOSE_PROJECT_NAME="$PROJECT_NAME" \
compose_cmd \
  -f "$ROOT_DIR/compose/test-base.yml" \
  -f "$ROOT_DIR/compose/verify.yml" \
  run --rm frontend-admin-verify
