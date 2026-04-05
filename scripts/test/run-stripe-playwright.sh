#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SPECS="${STRIPE_PLAYWRIGHT_SPECS:-e2e/stripe/checkout-return.spec.ts e2e/stripe/cancellation-and-locks.spec.ts}"

if [[ "${STRIPE_LIVE_TEST_ENABLED:-false}" != "true" ]]; then
  echo "Set STRIPE_LIVE_TEST_ENABLED=true to run Stripe live Playwright tests." >&2
  exit 1
fi

COMPOSE_PROJECT_NAME=fityq-e2e-stripe \
"$ROOT_DIR/scripts/compose.sh" \
  -f "$ROOT_DIR/compose/base.yml" \
  -f "$ROOT_DIR/compose/verify.yml" \
  -f "$ROOT_DIR/compose/e2e.yml" \
  run --rm playwright sh -lc "npx playwright test $SPECS --project=core-chromium --reporter=list"
