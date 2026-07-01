# Admin Deployment Guide

## Overview

The admin surface is split from the main app:

- `frontend/admin/`: standalone React admin frontend
- `backend-admin/`: standalone FastAPI admin backend

The main local compose stack does not start admin services.

## Local development

Run the admin backend:

```bash
cd backend-admin
.venv/bin/python src/main.py
```

Run the admin frontend:

```bash
cd frontend/admin
npm run dev
```

Default local ports:

- Admin frontend: `http://localhost:3001`
- Admin backend: `http://localhost:8001`

## Validation

Frontend admin:

```bash
cd frontend/admin
npm run lint
npm run typecheck
npm test
```

Backend admin:

```bash
cd backend-admin
.venv/bin/pylint src
.venv/bin/pyright src
```

## Authentication model

The admin backend protects non-public endpoints with two checks:

1. `Authorization: Bearer <token>`
2. `X-Admin-Key: <ADMIN_SECRET_KEY>`

Public endpoints today:

- `/health`
- `/docs`
- `/openapi.json`
- `/user/login`

## Environment variables

`frontend/admin`:

```env
VITE_ADMIN_API_URL=http://localhost:8001
```

`backend-admin`:

```env
SECRET_KEY=<required>
ADMIN_SECRET_KEY=<required>
MONGO_URI=<required>
DB_NAME=<required>
ALLOWED_ORIGINS=http://localhost:3001,http://localhost:5173
INITIAL_ADMIN_EMAIL=<optional>
INITIAL_ADMIN_PASSWORD=<optional but required for bootstrap admin creation>
INITIAL_ADMIN_NAME=<optional>
```

## Production deploy

Admin deploy is optional and disabled by default in the main deploy flow.

To include admin services:

```bash
ENABLE_ADMIN_DEPLOY=true make deploy-prod
```

The same flag applies to:

```bash
ENABLE_ADMIN_DEPLOY=true make deploy-build
ENABLE_ADMIN_DEPLOY=true make deploy-prod-fast
ENABLE_ADMIN_DEPLOY=true make deploy-prod-env
```

Service names used by the deploy scripts:

- `aitrainer-backend-admin`
- `aitrainer-frontend-admin`

## Operational notes

- Keep admin on a separate surface from the public app.
- Never commit `ADMIN_SECRET_KEY`.
- If admin is not needed in production, leave `ENABLE_ADMIN_DEPLOY=false`.
- Prefer discovering live Cloud Run URLs with `gcloud run services describe` instead of hardcoding them in docs.
