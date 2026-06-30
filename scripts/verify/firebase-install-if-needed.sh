#!/usr/bin/env bash
set -euo pipefail

PREFIX_DIR="${1:?prefix dir is required}"
shift

FIREBASE_BIN="$PREFIX_DIR/bin/firebase"

if [ ! -x "$FIREBASE_BIN" ]; then
  mkdir -p "$PREFIX_DIR"
  npm install -g --prefix "$PREFIX_DIR" --offline firebase-tools@14.26.0 || \
    npm install -g --prefix "$PREFIX_DIR" firebase-tools@14.26.0
fi

exec "$FIREBASE_BIN" "$@"
