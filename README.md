# AI Personal Trainer (FityQ)

**AI Personal Trainer** is a comprehensive fitness coaching platform powered by Artificial Intelligence. It adapts to your style by offering multiple trainer personalities—from analytical and surgical to motivational sergeants, holistic guides, and gym partners who celebrate every achievement.

---

## 🚀 Key Features

- **Real Long-Term Memory**: The AI remembers your history, injuries, preferences, and goals through a 3-layer memory system (short, medium, and long-term with semantic search).
- **Adaptive TDEE**: Calculates your actual metabolism from weight and nutrition data using linear regression with outlier filtering, not just static formulas.
- **Deep Integrations**:
  - **Hevy**: Sync your workout history and create routines directly in Hevy.
  - **MyFitnessPal**: Sync nutrition data.
  - **Zepp Life/Xiaomi**: Import body composition from smart scales.
- **Multi-Platform**: Chat via the web app or directly through **Telegram** with automatic workout analysis.
- **15+ Body Metrics**: Track limb measurements, visceral fat, muscle mass, and weight trends with EMA smoothing.
- **Privacy & Flexibility**: Compatible with Google Gemini, OpenAI, or local models via Ollama.

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 19 + Vite 7 + TypeScript 5.7+
- **Styling**: TailwindCSS v4
- **State**: Zustand 5 + React Hook Form 7
- **Charts**: Recharts 2.15+
- **Testing**: Vitest 3 + Testing Library + Playwright 1.50+

### Backend
- **Framework**: FastAPI (Python 3.12+)
- **Database**: MongoDB (NoSQL) + Qdrant (Vector Database for Memory)
- **AI/LLM**: LangChain + LiteLLM (Gemini, OpenAI, Ollama)
- **Task Queue**: BackgroundTasks (FastAPI internal)
- **Automation**: Telegram Bot API

---

## 📦 Project Structure

```text
.
├── backend/            # FastAPI Backend
│   ├── src/            # Application source code
│   │   ├── api/        # Endpoints and models
│   │   ├── core/       # Config, dependencies, security
│   │   ├── services/   # Business logic (AI Brain, Tools)
│   │   └── repositories/ # Data access layer
│   └── tests/          # Pytest suite
├── frontend/           # React Frontend
│   ├── src/
│   │   ├── features/   # Modulized features (Auth, Chat, Workouts, etc.)
│   │   ├── shared/     # Common hooks, components, API clients
│   │   └── test/       # Global test setup
│   └── e2e/            # Playwright E2E tests
├── scripts/            # Infrastructure and utility scripts
├── docker-compose.yml  # Local development stack
└── Makefile            # Common development commands
```

---

## 🚀 Getting Started (Local Development)

### 1. Prerequisites
- Docker or Podman with a Compose-compatible CLI
- Node.js 22+ and Python 3.12+ only if you want to run app services outside containers

### 2. Setup
```bash
# Clone the repository
git clone <repo-url>
cd personal

# Setup environment variables
cp backend/.env.example backend/.env
# (Edit .env with your LLM keys and credentials)

# Start the full stack with Podman Compose
make up

# Alternatively, run with rebuild
make debug-rebuild
```

### 3. Access
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **Mongo Express**: http://localhost:8081

---

## 🧪 Testing & Quality

We maintain high quality standards with **TDD (Test Driven Development)** and strict linting. The supported local workflow is containerized for system validation and script-backed for verification.

### Official Full-Suite Path

Run the complete containerized system suite with:

```bash
make test-once
```

Test execution guarantees:
- Every run uses a unique disposable Compose project name.
- Test dependencies run without host port bindings (no collision with local dev/debug stacks).
- All test containers/networks/volumes are destroyed at the end of each run.
- If dependency bootstrap gets stuck (for example `npm ci`), the run fails fast by timeout instead of hanging indefinitely.
- Post-feature policy: run `make test-once` before considering the task complete.

This runs:
- backend verification
- backend-admin verification
- frontend verification
- admin frontend verification
- Playwright E2E against real backend and frontend services

The container stack also starts MongoDB, Qdrant, and `stripe-mock` as internal dependencies.

Optional npm network hardening knobs (for unstable DNS/registry links):
- `NPM_CONFIG_FETCH_RETRIES` (default `5`)
- `NPM_CONFIG_FETCH_RETRY_MINTIMEOUT` (default `2000`)
- `NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT` (default `20000`)
- `NPM_CONFIG_FETCH_TIMEOUT` (default `120000`)
- `NPM_CONFIG_REGISTRY` (default `https://registry.npmjs.org/`)
- `NPM_CI_TIMEOUT_SECONDS` (default `420`)
- `NPM_CI_MAX_RETRIES` (default `3`)

### Stripe Hybrid Testing (Mock + Live Test Mode)

Default verification (`make verify`, `make verify-all`, `make test-once`) keeps Stripe on `stripe-mock`.

For high-fidelity subscription lifecycle tests (real Stripe `test mode`):

1. Set live test env vars:
   - `STRIPE_LIVE_TEST_ENABLED=true`
   - `STRIPE_TEST_SECRET_KEY=sk_test_...`
   - `STRIPE_API_KEY=sk_test_...`
   - `STRIPE_CLI_WEBHOOK_FORWARD_URL=http://localhost:8000/stripe/webhook`
2. Start webhook forwarding and capture a signing secret:
   - `STRIPE_LIVE_ENV_FILE=/tmp/stripe-live.env STRIPE_CLI_PRINT_ONLY=true ./scripts/test/stripe_cli_forward.sh`
3. Export the captured secret:
   - `export STRIPE_TEST_WEBHOOK_SECRET=whsec_...`
   - `export STRIPE_WEBHOOK_SECRET=whsec_...`
4. Run integration/e2e suites that target Stripe live.
   - `./scripts/test/run-stripe-live.sh`
   - `./scripts/test/run-stripe-playwright.sh` (optional subset for Stripe e2e)

`scripts/test/stripe_cli_forward.sh` is deterministic by contract:
- Prints `STRIPE_TEST_WEBHOOK_SECRET` and `STRIPE_CLI_WEBHOOK_FORWARD_URL` to stdout.
- Optionally writes them to an env file (`STRIPE_LIVE_ENV_FILE`).
- Runs `stripe listen` in foreground unless `STRIPE_CLI_PRINT_ONLY=true`.

### Verification vs Coverage

Fast verification without per-suite coverage:

```bash
make verify
```

Full verification including Playwright:

```bash
make verify-all
make test-once
```

Per-suite backend coverage:

```bash
make test-backend-cov
```

Per-suite frontend coverage from containers:

```bash
./scripts/compose.sh -f docker-compose.test.yml run --rm frontend-tests sh -lc "npm ci && npm test -- --coverage"
./scripts/compose.sh -f docker-compose.test.yml run --rm admin-tests sh -lc "npm ci && npm test -- --coverage"
```

Playwright E2E only:

```bash
make e2e
```

Important: Playwright E2E must run through the repository's containerized verification flow. Do not use host-local `npx playwright test` as the official path for validation.

### Coverage Thresholds

Main frontend Vitest thresholds:
- branches: `58%`
- functions: `65%`
- lines: `68%`
- statements: `67%`

Admin frontend Vitest thresholds:
- branches: `35%`
- functions: `45%`
- lines: `45%`
- statements: `43%`

Current Playwright runs are execution-only. The repository does not currently emit instrumented E2E code coverage.

### Reports

When coverage or E2E runs complete, the generated reports are written to:
- `backend/htmlcov/index.html`
- `frontend/coverage/index.html`
- `frontend/admin/coverage/index.html`
- `frontend/playwright-report/index.html`

---

## 📐 Architecture Principles

1. **Feature Isolation**: Features in `frontend/src/features` are independent.
2. **Standardized CRUD**: Shared repositories and components for consistent data handling.
3. **Mock First**: Frontend tests always mock the backend for speed and isolation.
4. **Zero Tolerance**: 0 warnings or hints allowed in container logs, frontend, or backend.

---

## 📄 License & Credits
Proprietary - All Rights Reserved. Created by **Rafael Colutti**.
