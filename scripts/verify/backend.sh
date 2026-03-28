#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"
. "$ROOT_DIR/scripts/lib/compose.sh"

cleanup() {
  COMPOSE_PROJECT_NAME=fityq-verify \
  compose_cmd \
    -f "$ROOT_DIR/compose/base.yml" \
    -f "$ROOT_DIR/compose/verify.yml" \
    down --volumes --remove-orphans >/dev/null 2>&1 || true
}

trap cleanup EXIT

log_section "Verify backend"
COMPOSE_PROJECT_NAME=fityq-verify \
compose_cmd \
  -f "$ROOT_DIR/compose/base.yml" \
  -f "$ROOT_DIR/compose/verify.yml" \
  run --rm backend-verify
