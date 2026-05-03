#!/bin/bash
# Suite completa de testes de conversação
# Requer: backend rodando com podman-compose up

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/../../.venv/bin/pytest"

echo "================================================"
echo "  Conversation Flow E2E Test Suite"
echo "  10 tests - ~10 minutos"
echo "================================================"
echo ""

trap 'echo ""; echo "Interrupted."; exit 130' INT TERM

for test in "$DIR"/test_0[1-9]_*.py "$DIR"/test_10_*.py; do
    name=$(basename "$test")
    echo ""
    echo "▶ $(printf '%-50s' "$name")"
    if "$VENV" "$test" -v --tb=short 2>&1; then
        echo "  ✅ PASSED"
    else
        echo "  ❌ FAILED"
    fi
done

echo ""
echo "================================================"
echo "  Suite complete"
echo "================================================"
