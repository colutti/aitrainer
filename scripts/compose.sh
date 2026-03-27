#!/usr/bin/env bash
set -euo pipefail

if command -v podman-compose >/dev/null 2>&1 && command -v podman >/dev/null 2>&1; then
  exec podman-compose "$@"
fi

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  exec docker compose "$@"
fi

echo "No supported compose command found. Install podman-compose or docker compose." >&2
exit 1
