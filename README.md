# AI Personal Trainer (FityQ)

**AI Personal Trainer** is a comprehensive fitness coaching platform powered by Artificial Intelligence. It adapts to your style by offering multiple trainer personalities—from analytical and surgical to motivational sergeants, holistic guides, and gym partners who celebrate every achievement.

---

## 🚀 Key Features

- **Master Plan Engine**: Each user has one AI-managed master plan combining a clear goal, timeline, nutrition targets, weekly training program, and checkpoint-based revisions.
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
- **Framework**: React 19 + Vite 7.2.4 + TypeScript 5.9.3
- **Styling**: TailwindCSS v4
- **State**: Zustand 5 + React Hook Form 7
- **Charts**: Recharts 2.15+
- **Routing**: React Router 7.6
- **i18n**: i18next 25.8 + react-i18next 16.5
- **Testing**: Vitest 3.0.5 + Testing Library + Playwright 1.50.2

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

This runs:
- `quick.sh`: backend, backend-admin, frontend, admin-frontend verification
- `e2e.sh`: Playwright E2E against real backend and frontend services

For complete verification including security checks:

```bash
make verify-all
```

This runs:
- `quick.sh`: all service verification
- `e2e.sh`: Playwright E2E tests
- `security.sh`: security verification

The container stack also starts MongoDB, Qdrant, and `stripe-mock` as internal dependencies.

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

## 🤖 Agent Workflows

Project-specific workflows live in [`.agent/workflows`](/.agent/workflows):
- `brainstorming.md`
- `writing-plans.md`
- `executing-plans.md`
- `report-bug.md`
- `run-all-tests.md`
- `cleancode.md`

Project-specific design skill:
- [`.agent/skills/ui-ux-pro-max/SKILL.md`](/.agent/skills/ui-ux-pro-max/SKILL.md)

---

## 📄 License & Credits
Proprietary - All Rights Reserved. Created by **Rafael Colutti**.
