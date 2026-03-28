#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"
. "$ROOT_DIR/scripts/lib/compose.sh"

cleanup() {
  COMPOSE_PROJECT_NAME=fityq-e2e \
  compose_cmd \
    -f "$ROOT_DIR/compose/base.yml" \
    -f "$ROOT_DIR/compose/verify.yml" \
    -f "$ROOT_DIR/compose/e2e.yml" \
    down --remove-orphans >/dev/null 2>&1 || true
}

trap cleanup EXIT

log_section "Running E2E"
COMPOSE_PROJECT_NAME=fityq-e2e \
compose_cmd \
  -f "$ROOT_DIR/compose/base.yml" \
  -f "$ROOT_DIR/compose/verify.yml" \
  -f "$ROOT_DIR/compose/e2e.yml" \
  run --rm playwright
