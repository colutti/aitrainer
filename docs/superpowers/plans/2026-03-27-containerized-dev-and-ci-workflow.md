# Containerized Dev And CI Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current mixed host/container workflow with a script-driven, containerized development and verification flow exposed through a minimal `Makefile` interface.

**Architecture:** Move orchestration out of `Makefile` into shell scripts under `scripts/`, split Compose files by responsibility under `compose/`, and make `make dev`, `make verify`, and `make verify-all` the official workflows. Keep all official dev, lint, typecheck, tests, E2E, and security flows containerized.

**Tech Stack:** GNU Make, Bash, Podman/Docker Compose, FastAPI, React/Vite, Playwright, Semgrep

---

### Task 1: Baseline the current workflow and lock the public interface

**Files:**
- Modify: `docs/superpowers/specs/2026-03-27-containerized-dev-and-ci-workflow-design.md`
- Create: `compose/`
- Modify: `Makefile`

- [ ] **Step 1: Write the failing interface test as a shell acceptance check**

Create a temporary checklist in the plan execution notes with the required final public commands:

```text
make dev
make stop
make reset
make logs
make verify
make verify-all
```

Success condition: no other public workflow commands remain in `Makefile`.

- [ ] **Step 2: Inspect current `Makefile` to confirm the old command surface**

Run:

```bash
sed -n '1,260p' Makefile
```

Expected: many legacy commands still exist, including `debug-rebuild`, `test-once`, `ci-fast`, and host-local targets.

- [ ] **Step 3: Replace the public `Makefile` interface with the new command surface only**

Update `Makefile` so it exposes only:

```make
.PHONY: dev stop reset logs verify verify-all

dev:
	./scripts/dev/dev.sh

stop:
	./scripts/dev/stop.sh

reset:
	./scripts/dev/reset.sh

logs:
	./scripts/dev/logs.sh

verify:
	./scripts/verify/quick.sh

verify-all:
	./scripts/verify/all.sh
```

- [ ] **Step 4: Verify the public interface is reduced**

Run:

```bash
sed -n '1,120p' Makefile
```

Expected: only the six public commands above remain.

### Task 2: Add shared script infrastructure

**Files:**
- Create: `scripts/lib/log.sh`
- Create: `scripts/lib/checks.sh`
- Create: `scripts/lib/compose.sh`

- [ ] **Step 1: Write the failing smoke check**

Run before files exist:

```bash
bash -n scripts/lib/log.sh
```

Expected: fail because file does not exist.

- [ ] **Step 2: Create shared logging helpers**

Add `scripts/lib/log.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

log_section() {
  printf '\n==> %s\n' "$1"
}

log_info() {
  printf '[info] %s\n' "$1"
}

log_error() {
  printf '[error] %s\n' "$1" >&2
}
```

- [ ] **Step 3: Create environment and tool checks**

Add `scripts/lib/checks.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

require_compose_runtime() {
  if command -v podman >/dev/null 2>&1; then
    return 0
  fi
  if command -v docker >/dev/null 2>&1; then
    return 0
  fi
  echo "No supported container runtime found (podman or docker)." >&2
  exit 1
}
```

- [ ] **Step 4: Create compose wrapper helpers**

Add `scripts/lib/compose.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/checks.sh"

compose_cmd() {
  require_compose_runtime
  if command -v podman >/dev/null 2>&1; then
    podman compose "$@"
    return
  fi
  docker compose "$@"
}
```

- [ ] **Step 5: Verify the helper scripts are syntactically valid**

Run:

```bash
bash -n scripts/lib/log.sh
bash -n scripts/lib/checks.sh
bash -n scripts/lib/compose.sh
```

Expected: all commands exit 0.

### Task 3: Modularize Compose files

**Files:**
- Create: `compose/base.yml`
- Create: `compose/dev.app.yml`
- Create: `compose/dev.admin.yml`
- Create: `compose/verify.yml`
- Create: `compose/e2e.yml`
- Create: `compose/security.yml`
- Verify: `docker-compose.yml`
- Verify: `docker-compose.test.yml`

- [ ] **Step 1: Write the failing config check**

Run before creating the new files:

```bash
./scripts/compose.sh -f compose/base.yml -f compose/dev.app.yml -f compose/dev.admin.yml config
```

Expected: fail because the new compose files do not exist.

- [ ] **Step 2: Create `compose/base.yml` with shared infrastructure**

Move shared infra definitions into:

```yaml
services:
  mongo:
  qdrant:
  stripe-mock:
networks:
  app-network:
    driver: bridge
volumes:
  mongodata:
  qdrant_data:
```

Populate with the existing working container definitions from the current compose files.

- [ ] **Step 3: Create `compose/dev.app.yml`**

Include:

```yaml
services:
  backend:
  frontend:
  mongo-express:
```

Use the current dev behavior for backend/frontend, but keep references aligned to services from `compose/base.yml`.

- [ ] **Step 4: Create `compose/dev.admin.yml`**

Add containerized admin services:

```yaml
services:
  backend-admin:
  frontend-admin:
```

Both should run in dev mode inside containers and bind their ports for local use.

- [ ] **Step 5: Create `compose/verify.yml`**

Add runner services for:

```yaml
services:
  backend-verify:
  backend-admin-verify:
  frontend-verify:
  frontend-admin-verify:
```

Each runner should execute the fast category gate inside the container.

- [ ] **Step 6: Create `compose/e2e.yml`**

Add:

```yaml
services:
  playwright:
```

Use the current working Playwright image and wiring.

- [ ] **Step 7: Create `compose/security.yml`**

Add scanner services such as:

```yaml
services:
  semgrep:
```

Keep security scans containerized and read-only where practical.

- [ ] **Step 8: Verify the new compose stacks render**

Run:

```bash
./scripts/compose.sh -f compose/base.yml -f compose/dev.app.yml -f compose/dev.admin.yml config >/tmp/dev-compose.out
./scripts/compose.sh -f compose/base.yml -f compose/verify.yml config >/tmp/verify-compose.out
./scripts/compose.sh -f compose/base.yml -f compose/verify.yml -f compose/e2e.yml -f compose/security.yml config >/tmp/all-compose.out
```

Expected: all `config` commands exit 0.

### Task 4: Implement the development lifecycle scripts

**Files:**
- Create: `scripts/dev/dev.sh`
- Create: `scripts/dev/stop.sh`
- Create: `scripts/dev/reset.sh`
- Create: `scripts/dev/logs.sh`
- Modify: `scripts/lib/compose.sh`

- [ ] **Step 1: Write the failing smoke check**

Run before the scripts exist:

```bash
bash -n scripts/dev/dev.sh
```

Expected: fail because file does not exist.

- [ ] **Step 2: Create `scripts/dev/dev.sh`**

Use:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"
. "$ROOT_DIR/scripts/lib/compose.sh"

log_section "Starting full development stack"
compose_cmd \
  -f "$ROOT_DIR/compose/base.yml" \
  -f "$ROOT_DIR/compose/dev.app.yml" \
  -f "$ROOT_DIR/compose/dev.admin.yml" \
  up --build
```

- [ ] **Step 3: Create `scripts/dev/stop.sh`**

Use:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"
. "$ROOT_DIR/scripts/lib/compose.sh"

log_section "Stopping development stack"
compose_cmd \
  -f "$ROOT_DIR/compose/base.yml" \
  -f "$ROOT_DIR/compose/dev.app.yml" \
  -f "$ROOT_DIR/compose/dev.admin.yml" \
  down --remove-orphans
```

- [ ] **Step 4: Create `scripts/dev/reset.sh`**

Use:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"
. "$ROOT_DIR/scripts/lib/compose.sh"

log_section "Resetting development stack"
compose_cmd \
  -f "$ROOT_DIR/compose/base.yml" \
  -f "$ROOT_DIR/compose/dev.app.yml" \
  -f "$ROOT_DIR/compose/dev.admin.yml" \
  down --volumes --remove-orphans || true

"$ROOT_DIR/scripts/dev/dev.sh"
```

- [ ] **Step 5: Create `scripts/dev/logs.sh`**

Use:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/compose.sh"

compose_cmd \
  -f "$ROOT_DIR/compose/base.yml" \
  -f "$ROOT_DIR/compose/dev.app.yml" \
  -f "$ROOT_DIR/compose/dev.admin.yml" \
  logs -f
```

- [ ] **Step 6: Mark scripts executable and verify syntax**

Run:

```bash
chmod +x scripts/dev/*.sh scripts/lib/*.sh
bash -n scripts/dev/dev.sh
bash -n scripts/dev/stop.sh
bash -n scripts/dev/reset.sh
bash -n scripts/dev/logs.sh
```

Expected: all commands exit 0.

### Task 5: Implement the fast verification workflow

**Files:**
- Create: `scripts/verify/quick.sh`
- Create: `scripts/verify/backend.sh`
- Create: `scripts/verify/backend-admin.sh`
- Create: `scripts/verify/frontend.sh`
- Create: `scripts/verify/frontend-admin.sh`
- Modify: `compose/verify.yml`

- [ ] **Step 1: Write the failing smoke check**

Run before the scripts exist:

```bash
bash -n scripts/verify/quick.sh
```

Expected: fail because file does not exist.

- [ ] **Step 2: Create `scripts/verify/backend.sh`**

Use:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"
. "$ROOT_DIR/scripts/lib/compose.sh"

log_section "Verify backend"
compose_cmd -f "$ROOT_DIR/compose/base.yml" -f "$ROOT_DIR/compose/verify.yml" run --rm backend-verify
```

- [ ] **Step 3: Create `scripts/verify/backend-admin.sh`**

Use:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"
. "$ROOT_DIR/scripts/lib/compose.sh"

log_section "Verify backend-admin"
compose_cmd -f "$ROOT_DIR/compose/base.yml" -f "$ROOT_DIR/compose/verify.yml" run --rm backend-admin-verify
```

- [ ] **Step 4: Create `scripts/verify/frontend.sh`**

Use:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"
. "$ROOT_DIR/scripts/lib/compose.sh"

log_section "Verify frontend"
compose_cmd -f "$ROOT_DIR/compose/base.yml" -f "$ROOT_DIR/compose/verify.yml" run --rm frontend-verify
```

- [ ] **Step 5: Create `scripts/verify/frontend-admin.sh`**

Use:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"
. "$ROOT_DIR/scripts/lib/compose.sh"

log_section "Verify frontend-admin"
compose_cmd -f "$ROOT_DIR/compose/base.yml" -f "$ROOT_DIR/compose/verify.yml" run --rm frontend-admin-verify
```

- [ ] **Step 6: Create `scripts/verify/quick.sh`**

Use:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"

log_section "Running fast verification gate"
"$ROOT_DIR/scripts/verify/backend.sh"
"$ROOT_DIR/scripts/verify/backend-admin.sh"
"$ROOT_DIR/scripts/verify/frontend.sh"
"$ROOT_DIR/scripts/verify/frontend-admin.sh"
```

- [ ] **Step 7: Configure the runner commands in `compose/verify.yml`**

Use these service commands:

```yaml
backend-verify: ruff + pylint + pytest fast suite
backend-admin-verify: pylint + pyright
frontend-verify: npm run lint && npm run typecheck && npm test
frontend-admin-verify: npm run lint && npm run typecheck && npm test
```

Keep them containerized and mounted against the workspace.

- [ ] **Step 8: Verify script syntax**

Run:

```bash
chmod +x scripts/verify/*.sh
bash -n scripts/verify/backend.sh
bash -n scripts/verify/backend-admin.sh
bash -n scripts/verify/frontend.sh
bash -n scripts/verify/frontend-admin.sh
bash -n scripts/verify/quick.sh
```

Expected: all commands exit 0.

### Task 6: Implement the complete verification workflow

**Files:**
- Create: `scripts/verify/e2e.sh`
- Create: `scripts/verify/security.sh`
- Create: `scripts/verify/all.sh`
- Modify: `compose/e2e.yml`
- Modify: `compose/security.yml`

- [ ] **Step 1: Write the failing smoke check**

Run before the scripts exist:

```bash
bash -n scripts/verify/all.sh
```

Expected: fail because file does not exist.

- [ ] **Step 2: Create `scripts/verify/e2e.sh`**

Use:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"
. "$ROOT_DIR/scripts/lib/compose.sh"

log_section "Running E2E"
compose_cmd -f "$ROOT_DIR/compose/base.yml" -f "$ROOT_DIR/compose/verify.yml" -f "$ROOT_DIR/compose/e2e.yml" run --rm playwright
```

- [ ] **Step 3: Create `scripts/verify/security.sh`**

Use:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$ROOT_DIR/scripts/lib/log.sh"
. "$ROOT_DIR/scripts/lib/compose.sh"

log_section "Running security scans"
compose_cmd -f "$ROOT_DIR/compose/security.yml" run --rm semgrep
```

- [ ] **Step 4: Create `scripts/verify/all.sh`**

Use:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

"$ROOT_DIR/scripts/verify/quick.sh"
"$ROOT_DIR/scripts/verify/e2e.sh"
"$ROOT_DIR/scripts/verify/security.sh"
```

- [ ] **Step 5: Verify the complete verification scripts**

Run:

```bash
bash -n scripts/verify/e2e.sh
bash -n scripts/verify/security.sh
bash -n scripts/verify/all.sh
```

Expected: all commands exit 0.

### Task 7: Final validation and cleanup

**Files:**
- No new files unless validation reveals issues.

- [ ] **Step 1: Verify `make` entrypoints map correctly**

Run:

```bash
make -n dev
make -n stop
make -n reset
make -n logs
make -n verify
make -n verify-all
```

Expected: each target expands to the intended script only.

- [ ] **Step 2: Verify the script files exist and are executable**

Run:

```bash
find scripts/dev scripts/verify scripts/lib -maxdepth 2 -type f | sort
```

Expected: the new script layout is present and complete.

- [ ] **Step 3: Verify compose config combinations one more time**

Run:

```bash
./scripts/compose.sh -f compose/base.yml -f compose/dev.app.yml -f compose/dev.admin.yml config >/tmp/dev-final.out
./scripts/compose.sh -f compose/base.yml -f compose/verify.yml config >/tmp/verify-final.out
./scripts/compose.sh -f compose/base.yml -f compose/verify.yml -f compose/e2e.yml -f compose/security.yml config >/tmp/verify-all-final.out
```

Expected: all commands exit 0.

- [ ] **Step 4: Run the fast validation command**

Run:

```bash
make verify
```

Expected: fast containerized validation gate completes successfully.

- [ ] **Step 5: Run the full validation command**

Run:

```bash
make verify-all
```

Expected: fast gate, E2E, and security all run through the new containerized entrypoint.
