# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Personal Trainer - Full-stack web application for AI-powered fitness coaching with conversation memory, workout tracking, nutrition logging, and metabolism analysis.

**Tech Stack:**
- Backend: FastAPI + Python 3.12 + MongoDB + Qdrant (vector DB)
- Frontend: React 19 + TypeScript + Vite 6 + TailwindCSS v4
- AI/LLM: LangChain + LangGraph + Mem0 (memory management)
- AI Providers: Google Gemini (primary), OpenAI, Ollama (local)
- Container: Docker/Podman + podman-compose
- Testing: Pytest (Backend), Vitest (Frontend), Playwright (E2E)

## Development Methodology

**TDD (Test-Driven Development):** All features and bugfixes MUST follow the TDD cycle: write failing tests first, then implement the minimum code to pass, then refactor.

**Zero Tolerance for Linting Errors:** Both backend and frontend must have ZERO linting errors and ZERO warnings at all times. Always run lint checks after any code change.

### Mandatory Quality Checks

After ANY code modification, run the appropriate checks:

```bash
# Backend: linting
cd backend && ruff check .

# Frontend: linting + type checking (BOTH required)
cd frontend && npm run lint
cd frontend && npm run typecheck

# Combined frontend check (lint + typecheck + tests)
cd frontend && npm run check
```

These checks must pass with zero errors and zero warnings before considering any task complete.

## Development Commands

### Full Stack

```bash
make up              # Start all services (backend, frontend, MongoDB, Qdrant)
make down            # Stop all services
make build           # Build containers (development)
make build-prod      # Build containers (production - minified)
make restart         # Rebuild and restart
```

### Backend

```bash
cd backend && make api            # Run backend locally (outside container)
cd backend && ruff check .        # Lint (zero errors/warnings required)
```

### Frontend

```bash
cd frontend && npm run dev        # Dev server (port 3000)
cd frontend && npm run build      # Production build (includes tsc)
cd frontend && npm run lint       # ESLint (strict TypeScript rules)
cd frontend && npm run lint:fix   # ESLint with auto-fix
cd frontend && npm run typecheck  # TypeScript strict type checking
cd frontend && npm run check      # All checks: lint + typecheck + tests
```

### Testing

```bash
# Backend
cd backend && pytest                        # All tests
cd backend && pytest tests/test_file.py     # Specific file
cd backend && pytest -k "test_function"     # Specific test
cd backend && pytest --cov=src              # Coverage report

# Frontend unit tests (Vitest)
cd frontend && npm test                     # Run all
cd frontend && npm run test:watch           # Watch mode
cd frontend && npm run test:coverage        # Coverage report

# E2E tests (Playwright)
cd frontend && npx playwright test          # Headless
cd frontend && npx playwright test --ui     # UI mode
cd frontend && npx playwright show-report   # View report

# CI validation
make ci-fast         # Quick gate: backend tests + frontend tests
make ci-test         # Full suite: backend + frontend + e2e
```

### User & Admin Management

```bash
make init-db USUARIO=email@example.com SENHA=password    # Init DB with first user
make user-create EMAIL=user@example.com PASSWORD=pass123  # Create user
make user-list                                            # List all users
make user-get EMAIL=user@example.com                      # Get user details
make user-password EMAIL=user@example.com PASSWORD=new123 # Update password
make user-nuke EMAIL=user@example.com                     # Delete user completely
make user-nuke-force EMAIL=user@example.com               # Delete without confirmation
make invite-create EMAIL=newuser@example.com              # Create invite (48h)
make invite-list                                          # List invites
make admin-promote EMAIL=user@example.com                 # Promote to admin
```

### Render Deployment

```bash
make render-deploy                # Deploy backend + frontend
make render-deploy-backend        # Deploy backend only
make render-deploy-frontend       # Deploy frontend only
make render-deploy-clean          # Deploy with cache clear
make render-logs-backend          # Stream backend logs
make render-logs-frontend         # Stream frontend logs
```

## Architecture & Patterns

### Backend Architecture

```
Request -> API Endpoint -> Service Layer -> Repository Layer -> Database
                |
           Dependency Injection (FastAPI Depends)
                |
           Configuration (Pydantic Settings)
```

**Key Patterns:**

1. **Repository Pattern** (`backend/src/repositories/`) - All DB access through `BaseRepository` subclasses
2. **Service Layer** (`backend/src/services/`) - Business logic separated from endpoints
3. **Dependency Injection** (`backend/src/core/deps.py`) - DB connections, current user, settings via `Depends()`
4. **AI Provider Abstraction** (`backend/src/core/config.py`) - `AI_PROVIDER` switches between gemini/openai/ollama
5. **Trainer Registry** (`backend/src/trainers/registry.py`) - Singleton managing trainer personalities (Atlas, Luna, Sofia, Sargento, GymBro)

### Frontend Architecture

- **Architecture**: Feature-based folder structure (`src/features/`)
- **State Management**: Zustand stores (`useAuth`, `useChat`, etc.)
- **Styling**: TailwindCSS v4 with CSS variables theme
- **Routing**: React Router v7
- **Forms**: React Hook Form + Zod validation
- **API**: Centralized `httpClient` + specialized API modules per feature
- **Linting**: ESLint with `tseslint.configs.strictTypeChecked` + `stylisticTypeChecked`
- **TypeScript**: Strict mode with `noUncheckedIndexedAccess`, `noUnusedLocals`, `noUnusedParameters`

### AI Agent System

```
User Message -> Trainer Service -> LangGraph Agent -> Tools -> Response
                                         |
                                    Mem0 Memory (Qdrant)
```

**Tools:** `workout_tools.py`, `nutrition_tools.py`, `weight_tools.py`, `metabolism_tools.py` + external integrations (Hevy, MyFitnessPal, Zepp Life)

**Memory:** Short-term (last N messages) + Long-term (Mem0/Qdrant vectors) + Auto-summarization

## Configuration & Environment

### Backend `.env`

```bash
AI_PROVIDER=gemini              # gemini | openai | ollama
GEMINI_API_KEY=your-key
MONGO_URI=mongodb://user:pass@mongo:27017/
DB_NAME=aitrainer
QDRANT_HOST=http://qdrant
QDRANT_PORT=6333
SECRET_KEY=your-secret-key
API_SERVER_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000
```

All AI providers use 768-dimensional embeddings for Qdrant compatibility.

## API Endpoints

All in `backend/src/api/endpoints/`: `/user`, `/message`, `/trainer`, `/memory`, `/workout`, `/nutrition`, `/weight`, `/metabolism`, `/integrations/hevy`, `/onboarding`, `/telegram`, `/health`, `/admin`

**Authentication:** JWT tokens via `/user/login`

## Database

### MongoDB Collections
`users`, `chat_history`, `trainers`, `workouts`, `nutrition`, `weights`, `invites`, `tokens`, `telegram_users`

### Qdrant Vector Store
Collection per user: `{collection_name}_{user_id}` with 768-dim vectors
