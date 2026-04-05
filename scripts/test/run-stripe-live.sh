#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ "${STRIPE_LIVE_TEST_ENABLED:-false}" != "true" ]]; then
  echo "Set STRIPE_LIVE_TEST_ENABLED=true to run Stripe live integration tests." >&2
  exit 1
fi

if [[ -z "${STRIPE_TEST_SECRET_KEY:-}" ]]; then
  echo "Missing STRIPE_TEST_SECRET_KEY for live Stripe tests." >&2
  exit 1
fi

if [[ -z "${STRIPE_WEBHOOK_SECRET:-}" ]]; then
  echo "Missing STRIPE_WEBHOOK_SECRET for live Stripe tests." >&2
  exit 1
fi

cd "$ROOT_DIR/backend"
.venv/bin/pytest tests/integration/stripe -v
