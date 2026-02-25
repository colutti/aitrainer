# Admin App Deployment Guide

## Overview

The admin panel has been **completely separated** from the main application:

- **frontend/admin/** - Standalone React app (port 3001)
- **backend-admin/** - Standalone FastAPI service (port 8001)
- **frontend/** - Main client app (port 3000, NO admin code)
- **backend/** - Main API service (port 8000, NO admin endpoints)

## ⚠️ Production Safety

**CRITICAL:** Admin services are **NOT** included in production deployment via Render.

This is intentional for security:
1. Admin code is completely isolated from client bundle
2. Admin backend is not exposed on public API surface
3. Admin deployment must be managed separately with additional auth

## Local Development

### Start Full Stack (including admin)

```bash
make up
```

Starts all services including admin:
- Client: http://localhost:3000
- Admin: http://localhost:3001
- Backend: http://localhost:8000
- Admin API: http://localhost:8001
- MongoDB: localhost:27017
- Qdrant: localhost:6333

### Start Only Admin Services

```bash
# Frontend admin only
make front-admin

# Backend admin only (outside container)
make api-admin

# Run admin tests
make test-admin
make test-admin-watch
make test-admin-cov
```

### Build Containers

```bash
# Development build
make build

# Production build
make build-prod

# Just admin containers
podman-compose build frontend-admin backend-admin
```

## Production Deployment

### For Main App (AUTOMATED via Render)

```bash
make render-deploy-all
```

Deploys:
- ✅ Backend to Render
- ✅ Frontend to Render
- ❌ Admin (NOT included intentionally)

### For Admin App (MANUAL setup)

Currently, admin deployment requires manual Render configuration. Here's how:

#### Option 1: Deploy Admin to Separate Render Account

1. Create separate Render account for admin
2. Create `frontend-admin` service:
   ```
   Name: admin-frontend
   Build: npm install && npm run build
   Publish: dist/
   Env: VITE_ADMIN_API_URL=https://admin-api.yourdomain.com
   ```

3. Create `backend-admin` service:
   ```
   Name: admin-backend
   Build: pip install -r requirements.txt
   Start: gunicorn src.main:app --worker-class uvicorn...
   Env vars: MONGO_URI, DB_NAME, SECRET_KEY, ADMIN_SECRET_KEY, etc.
   ```

#### Option 2: Deploy Admin to Separate Subdomain (Same Render)

1. In Render Dashboard, create two new services:
   - Static site: `admin-frontend` → `frontend/admin/dist`
   - Web service: `admin-backend` → `backend-admin/src.main:app`

2. Set environment:
   ```
   frontend-admin:
     VITE_ADMIN_API_URL=https://admin-api.yourdomain.com

   backend-admin:
     ADMIN_SECRET_KEY=<strong-random-key>
     MONGO_URI=<production-mongodb>
     (all other vars from main backend)
   ```

3. Update DNS/firewall:
   - Point `admin.yourdomain.com` to admin frontend
   - Point `admin-api.yourdomain.com` to admin backend

#### Option 3: Don't Deploy Admin (Recommended for High-Security)

If you don't need public admin deployment:
1. Keep admin in internal/staging only
2. Use VPN or private network for admin access
3. Admin remains completely isolated from production client infrastructure

## Authentication

### Admin Frontend (frontend/admin)

- Uses `admin_auth_token` in localStorage (separate from client)
- Login: POST `/user/login` → validates `is_admin: true`
- Rejects non-admin users with error message

### Admin Backend (backend-admin)

Dual authentication on ALL endpoints:

```
Header: Authorization: Bearer {jwt_token}
Header: X-Admin-Key: {ADMIN_SECRET_KEY}
```

Both must be valid:
1. JWT token must have `is_admin: true`
2. X-Admin-Key must match `ADMIN_SECRET_KEY` env var

Returns: `403 Forbidden` if either is invalid

## Environment Variables

### frontend/admin

```env
VITE_ADMIN_API_URL=http://localhost:8001    # Dev
VITE_ADMIN_API_URL=https://admin-api.prod  # Prod
```

### backend-admin

```env
MONGO_URI=mongodb://user:pass@mongo:27017/
DB_NAME=aitrainer
SECRET_KEY=<jwt-signing-key>
ADMIN_SECRET_KEY=<generate-with: openssl rand -hex 32>
QDRANT_HOST=http://localhost
QDRANT_PORT=6333
ALLOWED_ORIGINS=http://localhost:3001,https://admin.yourdomain.com
```

## Security Checklist

Before deploying admin to production:

- [ ] ✅ Admin services are on DIFFERENT domain from main app
- [ ] ✅ ADMIN_SECRET_KEY is long, random, and secure
- [ ] ✅ ADMIN_SECRET_KEY is NOT in version control
- [ ] ✅ Admin API requires BOTH JWT + X-Admin-Key headers
- [ ] ✅ Admin frontend is HTTPS only in production
- [ ] ✅ Admin backend is HTTPS only in production
- [ ] ✅ Rate limiting is enabled on admin endpoints
- [ ] ✅ Admin IP whitelist is configured (if possible)
- [ ] ✅ Audit logging is enabled for admin actions
- [ ] ✅ Main backend has NO admin endpoints remaining

## Testing

```bash
# Admin frontend tests
make test-admin

# Full CI validation (includes admin)
make ci-test

# Watch mode
make test-admin-watch

# Coverage report
make test-admin-cov
```

## Troubleshooting

### Admin frontend can't reach admin backend

Check docker-compose.yml:
- `frontend-admin` depends on `backend-admin`
- VITE_ADMIN_API_URL env var is correct
- backend-admin is running and healthy

### 403 Forbidden on admin API

Check backend-admin logs:
```bash
podman-compose logs backend-admin
```

Verify:
- X-Admin-Key header is being sent
- X-Admin-Key matches ADMIN_SECRET_KEY
- JWT token has `is_admin: true`

### Admin frontend shows "Acesso negado"

User account is not admin. Check MongoDB:
```bash
make admin-list
```

Promote user:
```bash
make admin-promote EMAIL=user@example.com
```

## Files Changed for Admin Separation

```
✅ Removed from frontend/src:
  - features/admin/
  - All admin imports in AppRoutes.tsx

✅ Removed from backend/src/api:
  - endpoints/admin_*.py files
  - All admin routes from main.py

✅ Created in frontend/admin:
  - Independent app with auth, components, hooks
  - Separate Node modules and build
  - ZERO admin code sharing with main frontend

✅ Created in backend-admin:
  - Independent FastAPI service
  - Middleware for dual auth
  - Separate requirements.txt

✅ Updated container config:
  - docker-compose.yml: added admin services
  - render.yaml: documented production safety
  - render-deploy.sh: excluded admin from prod
  - Makefile: new admin-specific commands
```

## Questions or Issues?

Check:
1. `/ADMIN_DEPLOYMENT.md` (this file)
2. `/render.yaml` (deployment config)
3. `/docker-compose.yml` (local development)
4. `frontend/admin/README.md` (if created)
5. `backend-admin/README.md` (if created)
