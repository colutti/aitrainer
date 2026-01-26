# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Personal Trainer - Full-stack web application for AI-powered fitness coaching with conversation memory, workout tracking, nutrition logging, and metabolism analysis.

**Tech Stack:**
- Backend: FastAPI + Python 3.12 + MongoDB + Qdrant (vector DB)
- Frontend: Angular 21 (standalone components) + TailwindCSS
- AI/LLM: LangChain + LangGraph + Mem0 (memory management)
- AI Providers: Google Gemini (primary), OpenAI, Ollama (local)
- Container: Docker/Podman + podman-compose

## Development Commands

### Full Stack Development

```bash
# Start all services (backend, frontend, MongoDB, Qdrant)
make up

# Stop all services
make down

# Build containers (development mode)
make build

# Build containers (production mode - minified)
make build-prod

# Rebuild and restart
make restart

# View logs
podman-compose logs -f [service_name]
```

### Backend Development

```bash
# Run backend locally (outside container)
cd backend
make api

# Run tests
cd backend
pytest

# Run tests with coverage
pytest --cov=src

# Run linter
ruff check .
```

### Frontend Development

```bash
# Serve frontend locally (port 3000)
cd frontend
npm run dev

# Build production
npm run build

# Run tests (Jest)
npm test

# E2E tests (Cypress)
npm run cypress:run
make cypress  # Using podman
```

### User Management

```bash
# Initialize database with first user
make init-db USUARIO=email@example.com SENHA=password

# Create new user
make user-create EMAIL=user@example.com PASSWORD=pass123

# List all users
make user-list

# Get user details
make user-get EMAIL=user@example.com

# Update user password
make user-password EMAIL=user@example.com PASSWORD=newpass123

# Delete user completely (MongoDB + Qdrant + logs)
make user-nuke EMAIL=user@example.com
make user-nuke-force EMAIL=user@example.com  # Skip confirmation
```

### Invite Management

```bash
# Create invite (48h expiration)
make invite-create EMAIL=newuser@example.com

# List all invites
make invite-list
```

## Architecture & Patterns

### Backend Architecture

```
Request → API Endpoint → Service Layer → Repository Layer → Database
              ↓
         Dependency Injection (FastAPI Depends)
              ↓
         Configuration (Pydantic Settings)
```

**Key Patterns:**

1. **Repository Pattern** (`backend/src/repositories/`)
   - `BaseRepository`: Common MongoDB operations
   - Specific repositories: `UserRepository`, `ChatRepository`, etc.
   - All DB access goes through repositories

2. **Service Layer** (`backend/src/services/`)
   - Business logic separated from API endpoints
   - Example: `trainer.py` orchestrates AI agent execution

3. **Dependency Injection** (`backend/src/core/deps.py`)
   - Uses FastAPI's `Depends()` system
   - Database connections, current user, settings injected into endpoints

4. **AI Provider Abstraction** (`backend/src/core/config.py`)
   - `AI_PROVIDER` setting switches between providers (gemini/openai/ollama)
   - `get_mem0_config()` dynamically configures LLM + embeddings + vector store
   - Provider-agnostic code in services/trainers

5. **Trainer Registry** (`backend/src/trainers/registry.py`)
   - Singleton pattern managing all trainer personalities
   - Each trainer extends `BaseTrainer` with custom prompts/tools
   - Available trainers: Atlas, Luna, Sofia, Sargento, GymBro

### Frontend Architecture

- **Standalone Components**: Angular 21 modern architecture (no NgModules)
- **Services**: HTTP client wrappers in `src/services/`
- **Models**: TypeScript interfaces in `src/models/`
- **Routing**: Centralized `NavigationService`
- **State**: Angular signals for reactivity

### AI Agent System

**LangGraph Agent Flow:**
```
User Message → Trainer Service → LangGraph Agent → Tools → Response
                                        ↓
                                   Mem0 Memory (Qdrant)
```

**Tools Available to AI:**
- `backend/src/services/workout_tools.py` - Workout CRUD
- `backend/src/services/nutrition_tools.py` - Nutrition logging
- `backend/src/services/weight_tools.py` - Weight tracking
- `backend/src/services/metabolism_tools.py` - TDEE calculations
- External integrations: Hevy, MyFitnessPal, Zepp Life

**Memory System:**
- Short-term: Last N messages in chat history (configurable)
- Long-term: Mem0AI with Qdrant vector store
- Summarization: Automatic when message buffer exceeds token limit

## Configuration & Environment

### Backend Environment Variables

Critical variables in `backend/.env`:
```bash
# API
SECRET_KEY=your-secret-key
API_SERVER_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000

# AI Provider Selection
AI_PROVIDER=gemini  # or "openai" or "ollama"

# Gemini (Primary)
GEMINI_API_KEY=your-key
LLM_MODEL_NAME=gemini-1.5-flash
EMBEDDER_MODEL_NAME=text-embedding-004

# OpenAI (Alternative)
OPENAI_API_KEY=your-key
OPENAI_MODEL_NAME=gpt-5-mini

# Ollama (Local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=llama3-groq-tool-use:8b

# MongoDB
MONGO_URI=mongodb://user:pass@mongo:27017/
DB_NAME=aitrainer

# Qdrant
QDRANT_HOST=http://qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=personal_trainer_memory
```

### Configuration Priority

From `backend/src/core/config.py`:
- **Container mode** (`RUNNING_IN_CONTAINER=true`): Docker env vars override .env
- **Local scripts**: .env file overrides shell env vars (safer for scripts)

### Switching AI Providers

Change `AI_PROVIDER` in `.env` to switch between:
- `gemini` - Google Gemini (default, fastest)
- `openai` - OpenAI GPT models
- `ollama` - Local models (privacy, offline)

All providers use 768-dimensional embeddings for Qdrant compatibility.

## Testing

### Backend Tests

```bash
cd backend
pytest                          # All tests
pytest tests/test_file.py       # Specific file
pytest -v                       # Verbose
pytest --cov=src               # Coverage report
pytest -k "test_function"      # Specific test
```

**Test structure:** `backend/tests/`
- Unit tests for services, repositories
- Performance benchmarks

**Pytest configuration:** `backend/pytest.ini` (filters deprecation warnings)

### Frontend Tests

```bash
cd frontend
npm test                        # Jest unit tests
npm run cypress:open            # Cypress interactive
npm run cypress:run             # Cypress headless
```

## API Structure

**Endpoints** (all in `backend/src/api/endpoints/`):

- `/user` - Authentication, profile management
- `/message` - Chat conversations
- `/trainer` - Trainer selection & configuration
- `/memory` - Memory management (Mem0)
- `/workout` - Workout logging & stats
- `/nutrition` - Nutrition tracking
- `/weight` - Weight tracking
- `/metabolism` - Metabolism calculations
- `/integrations/hevy` - Hevy app sync
- `/onboarding` - User onboarding flow
- `/telegram` - Telegram bot webhooks
- `/health` - Health check

**Authentication:** JWT tokens via `/user/login`

## Database Schema

### MongoDB Collections

- `users` - User profiles, credentials (bcrypt)
- `chat_history` - Conversation messages
- `trainers` - Trainer configurations per user
- `workouts` - Workout logs with exercises
- `nutrition` - Daily nutrition entries
- `weights` - Weight measurements
- `invites` - Onboarding invite codes
- `tokens` - Auth tokens
- `telegram_users` - Telegram integration

### Qdrant Vector Store

- Collection per user: `{collection_name}_{user_id}`
- Stores semantic embeddings of memories
- 768-dimensional vectors (all providers)

## Code Style & Conventions

### Backend

- **Python 3.12** features encouraged
- **Type hints** required for function signatures
- **Async/await** for I/O operations
- **Pydantic models** for data validation
- **Repository pattern** for DB access (never direct MongoDB in endpoints)
- **Dependency injection** via FastAPI `Depends()`

### Frontend

- **TypeScript strict mode** enabled
- **Standalone components** (no NgModules)
- **Signals** for reactive state
- **Services** for HTTP calls (no direct HTTP in components)
- **TailwindCSS** for styling (no custom CSS unless necessary)

## Important Notes

1. **Multi-Provider LLM Support:**
   - All AI code should work with any provider (gemini/openai/ollama)
   - Use `settings.AI_PROVIDER` to detect current provider
   - Provider-specific code only in `config.py`

2. **Memory System:**
   - Mem0 handles both short-term (recent messages) and long-term (semantic) memory
   - Automatic summarization when token limit exceeded
   - Trainers have context-aware memory through Qdrant

3. **Trainer System:**
   - Each trainer has unique personality in prompts (`backend/src/prompts/`)
   - All trainers share same tool set
   - Registry pattern for easy trainer addition

4. **Container vs Local:**
   - Development: Can run backend/frontend locally OR in containers
   - Production: Always containerized (multi-stage Docker builds)
   - Scripts: Use local venv for user management

5. **Testing Philosophy:**
   - Backend: Unit tests + performance benchmarks
   - Frontend: Jest for components, Cypress for E2E
   - CI/CD: GitHub Actions runs all tests on push

6. **Widget Consistency:**
   - Dashboard widgets should maintain consistent heights
   - Nutrition tab uses specific scale configurations
   - Workouts/Metabolism tabs mirror these dimensions
