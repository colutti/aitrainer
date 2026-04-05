#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"
. "$ROOT_DIR/scripts/lib/compose.sh"

PROJECT_NAME="fityq-e2e-$(date +%s)-$$-$RANDOM"

cleanup() {
  COMPOSE_PROJECT_NAME="$PROJECT_NAME" \
  compose_cmd \
    -f "$ROOT_DIR/compose/test-base.yml" \
    -f "$ROOT_DIR/compose/verify.yml" \
    -f "$ROOT_DIR/compose/e2e.yml" \
    down --volumes --remove-orphans >/dev/null 2>&1 || true
}

trap cleanup EXIT

log_section "Running E2E"
log_info "Using disposable test project: $PROJECT_NAME"
COMPOSE_PROJECT_NAME="$PROJECT_NAME" \
compose_cmd \
  -f "$ROOT_DIR/compose/test-base.yml" \
  -f "$ROOT_DIR/compose/verify.yml" \
  -f "$ROOT_DIR/compose/e2e.yml" \
  run --rm playwright
