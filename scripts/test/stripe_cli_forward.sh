#!/usr/bin/env bash
set -euo pipefail

FORWARD_URL="${STRIPE_CLI_WEBHOOK_FORWARD_URL:-http://localhost:8000/stripe/webhook}"
OUT_FILE="${STRIPE_LIVE_ENV_FILE:-}"
PRINT_ONLY="${STRIPE_CLI_PRINT_ONLY:-false}"
EVENTS="${STRIPE_CLI_EVENTS:-checkout.session.completed,customer.subscription.created,customer.subscription.updated,customer.subscription.deleted}"

if [[ $# -ge 1 ]]; then
  FORWARD_URL="$1"
fi

if ! command -v stripe >/dev/null 2>&1; then
  echo "stripe CLI not found in PATH" >&2
  exit 1
fi

if [[ -z "${STRIPE_TEST_WEBHOOK_SECRET:-}" ]]; then
  STRIPE_TEST_WEBHOOK_SECRET="$(stripe listen --forward-to "$FORWARD_URL" --events "$EVENTS" --print-secret)"
fi

if [[ -n "$OUT_FILE" ]]; then
  {
    echo "STRIPE_TEST_WEBHOOK_SECRET=$STRIPE_TEST_WEBHOOK_SECRET"
    echo "STRIPE_CLI_WEBHOOK_FORWARD_URL=$FORWARD_URL"
  } > "$OUT_FILE"
fi

echo "STRIPE_TEST_WEBHOOK_SECRET=$STRIPE_TEST_WEBHOOK_SECRET"
echo "STRIPE_CLI_WEBHOOK_FORWARD_URL=$FORWARD_URL"

if [[ "$PRINT_ONLY" == "true" ]]; then
  exit 0
fi

exec stripe listen --forward-to "$FORWARD_URL" --events "$EVENTS"
