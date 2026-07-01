# FityQ

FityQ is an AI personal trainer platform with a main web app, a separate admin app, and a FastAPI backend that runs chat, plans, body metrics, nutrition, workouts, billing, and integrations.

## Current stack

- `backend/`: FastAPI, Python 3.12, MongoDB, Qdrant, Pydantic AI, OpenRouter
- `frontend/`: React 19, TypeScript 5.9, Vite 7, TailwindCSS v4, Zustand, React Router 7, Vitest, Playwright
- `backend-admin/`: separate FastAPI admin service
- `frontend/admin/`: separate React admin app

The current AI chat runtime is documented in [backend/docs/architecture/ai-chat-runtime.md](backend/docs/architecture/ai-chat-runtime.md). It uses one application-level Pydantic AI run per user turn with typed domain tools and fail-closed validation.

## Repository layout

```text
.
├── backend/
├── backend-admin/
├── frontend/
├── scripts/
│   └── deploy/
├── docs/
├── .agent/
└── Makefile
```

## Local development

### Main app stack

```bash
make up
make down
make build
make debug-rebuild
```

`make up` starts the supported local compose stack for the main app: backend, frontend, MongoDB, Mongo Express, and Qdrant.

Local URLs:

- Main app: `http://localhost:3000`
- Main backend: `http://localhost:8000`
- FastAPI docs: `http://localhost:8000/docs`
- Mongo Express: `http://localhost:8081`
- Qdrant: `http://localhost:6333`

### Admin services

The admin services are not part of `make up`.

Run them separately when needed:

```bash
cd backend-admin && .venv/bin/python src/main.py
cd frontend/admin && npm run dev
```

Default local ports:

- Admin frontend: `http://localhost:3001`
- Admin backend: `http://localhost:8001`

## Quality and tests

Supported verification commands:

```bash
make verify
make verify-all
make test-once
make e2e
make test-backend-cov
make test-conversation
```

Rules:

- `make verify` is the fast verification gate.
- `make verify-all` adds Playwright and security checks.
- `make test-once` is the official full-suite containerized path.
- Playwright validation must run through `make e2e`, `make verify-all`, or `make test-once`.

Surface-specific validation:

```bash
cd backend && .venv/bin/ruff check src tests && .venv/bin/pylint src
cd backend-admin && .venv/bin/pylint src && .venv/bin/pyright src
cd frontend && npm run lint && npm run typecheck
cd frontend/admin && npm run lint && npm run typecheck
```

## Production deploy

The supported production path is Cloud Run via the deploy scripts in `scripts/deploy/`.

```bash
make deploy-prod
```

Useful deploy commands:

```bash
make deploy-preflight
make deploy-build
make deploy-prod
make deploy-prod-fast
make deploy-smoke
make deploy-prod-env
```

Reference docs:

- [scripts/deploy/README.md](scripts/deploy/README.md)
- [GCP_DEPLOYMENT_GUIDE.md](GCP_DEPLOYMENT_GUIDE.md)
- [ADMIN_DEPLOYMENT.md](ADMIN_DEPLOYMENT.md)

## Chat API contract

`POST /message` supports structured SSE when the client sends header `X-Chat-Stream-Format: sse-v1`.

Current SSE event types:

- `status`
- `delta`
- `done`
- `error`

Current `status.stage` values:

- `preparing_context`
- `using_tools`
- `writing_reply`
- `saving`

`GET /message/history` remains the persisted conversation source of truth.

## Active documentation

Start with these files when orienting in the repo:

- [AGENTS.md](AGENTS.md)
- [docs/README.md](docs/README.md)
- [backend/docs/architecture/ai-chat-runtime.md](backend/docs/architecture/ai-chat-runtime.md)
- [frontend/ARCH_GUIDELINES.md](frontend/ARCH_GUIDELINES.md)

Historical planning/spec documents that no longer describe the live system have been removed from the repository.

## License

Proprietary. All rights reserved.
