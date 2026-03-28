#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"
. "$ROOT_DIR/scripts/lib/compose.sh"

log_section "Stopping development stack"
COMPOSE_PROJECT_NAME=fityq-dev \
compose_cmd \
  -f "$ROOT_DIR/compose/base.yml" \
  -f "$ROOT_DIR/compose/dev.app.yml" \
  -f "$ROOT_DIR/compose/dev.admin.yml" \
  down --remove-orphans
