# AI Personal Trainer (FityQ)

**AI Personal Trainer** is a comprehensive fitness coaching platform powered by Artificial Intelligence. It adapts to your style by offering multiple trainer personalities—from analytical and surgical to motivational sergeants, holistic guides, and gym partners who celebrate every achievement.

---

## 🚀 Key Features

- **Real Long-Term Memory**: The AI remembers your history, injuries, preferences, and goals through a 3-layer memory system (short, medium, and long-term with semantic search).
- **Adaptive TDEE**: Calculates your actual metabolism from weight and nutrition data using linear regression with outlier filtering, not just static formulas.
- **Deep Integrations**:
  - **Hevy**: Import workouts in real-time via webhooks and create routines directly in Hevy.
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
- **Automation**: Telegram Bot API + Webhooks (Hevy)

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
- Docker / Podman + Podman Compose
- Node.js 22+ (for local frontend dev)
- Python 3.12+ (for local backend dev)

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

We maintain high quality standards with **TDD (Test Driven Development)** and strict linting.

### Frontend
```bash
cd frontend
npm test                # Run unit/integration tests
npm run test:coverage   # Coverage (Thresholds: 70% branches, 85% functions, 88% lines)
npm run lint            # Zero warnings policy
npm run typecheck       # Strict TypeScript check
```

### Backend
```bash
cd backend
pytest                  # Run all tests
pylint src              # Linting
pyright                 # Type checking
```

### Full Workflow
Use the provided automation for full verification:
`/run-all-tests` (via AI Agent) or `make test`

---

## 📐 Architecture Principles

1. **Feature Isolation**: Features in `frontend/src/features` are independent.
2. **Standardized CRUD**: Shared repositories and components for consistent data handling.
3. **Mock First**: Frontend tests always mock the backend for speed and isolation.
4. **Zero Tolerance**: 0 warnings or hints allowed in container logs, frontend, or backend.

---

## 📄 License & Credits
Proprietary - All Rights Reserved. Created by **Rafael Colutti**.
