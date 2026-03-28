#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"

log_section "Running complete verification workflow"
"$ROOT_DIR/scripts/verify/quick.sh"
"$ROOT_DIR/scripts/verify/e2e.sh"
"$ROOT_DIR/scripts/verify/security.sh"
