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

# Run unit tests (Vitest)
npm test

# Run e2e tests (Playwright)
npx playwright test
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

- **Framework**: React 19 with Vite 6
- **Architecture**: Feature-based folder structure (`src/features/`)
- **State Management**: Zustand for global stores (`useAuth`, `useChat`, etc.)
- **Styling**: TailwindCSS v4 with CSS variables theme
- **Routing**: React Router v7
- **Forms**: React Hook Form + Zod validation
- **API**: Centralized `httpClient` + specialized API modules per feature

### Frontend File Structure

```
src/
  features/         # Feature-based modules (Auth, Chat, Body, etc.)
    auth/
      components/
      api/
    dashboard/
  shared/           # Shared utilities, components, hooks
    components/ui/  # Reusable UI components (Button, Input, Card)
    hooks/          # Global hooks (useTheme, useMediaQuery)
    utils/          # Helper functions (date formatting, calculations)
    types/          # TypeScript interfaces
  App.tsx           # App entry point
  AppRoutes.tsx     # Route definitions
```

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
GEMINI_LLM_MODEL=gemini-1.5-flash
GEMINI_EMBEDDER_MODEL=text-embedding-004

# OpenAI (Alternative)
OPENAI_API_KEY=your-key
OPENAI_LLM_MODEL=gpt-4o-mini

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

### Frontend Tests

```bash
cd frontend
npm test                        # Vitest unit tests
npx playwright test             # E2E tests
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
