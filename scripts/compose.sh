#!/usr/bin/env bash
set -euo pipefail

if command -v podman >/dev/null 2>&1; then
  exec podman compose "$@"
fi

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  exec docker compose "$@"
fi

if command -v podman-compose >/dev/null 2>&1; then
  exec podman-compose "$@"
fi

echo "No supported compose command found. Install podman with compose support, podman-compose, or docker compose." >&2
exit 1
