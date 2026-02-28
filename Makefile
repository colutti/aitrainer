# GCP Configuration
GCP_PROJECT_ID=fityq-488619
GCP_REGION=europe-southwest1
GCP_REPO=aitrainer
GCP_REGISTRY=$(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/$(GCP_REPO)

# Helper to load environment variables from .env.prod for Cloud Run
# 1. Filters comments
# 2. Removes quotes (needed for --set-env-vars)
# 3. Joins with commas
GCP_ENV_VARS=$(shell grep -v '^\#' backend/.env.prod | grep -v '^$$' | sed 's/"//g' | paste -sd "," -)

.PHONY: up down build restart logs init-db api front front-admin api-admin admin clean-pod db db-down db-logs debug-rebuild debug-rebuild-admin test test-backend test-backend-cov test-backend-verbose test-backend-watch test-frontend test-frontend-watch test-frontend-cov test-cov e2e e2e-ui e2e-report ci-test ci-fast gcp-full gcp-build gcp-push gcp-deploy gcp-list gcp-setup-telegram gcp-hosting

up:
	podman-compose up -d

down:
	podman-compose down

init-db:
	cd backend && export PYTHONPATH=$$PYTHONPATH:. && .venv/bin/python src/api/main.py --init-db --email "$(USUARIO)" --password "$(SENHA)"

api:
	cd backend && export PYTHONPATH=$$PYTHONPATH:. && .venv/bin/python src/api/main.py

front:
	podman-compose --in-pod 0 up -d --no-deps frontend

# Admin Frontend (porta 3001, dev only)
front-admin:
	podman-compose --in-pod 0 up -d --no-deps frontend-admin

# Admin Backend (porta 8001, dev only)
api-admin:
	cd backend-admin && export PYTHONPATH=$$PYTHONPATH:. && .venv/bin/python src/main.py

# Admin Frontend + Backend (dev only)
admin:
	@echo "🚀 Iniciando Admin (frontend + backend)..."
	@echo "Frontend: http://localhost:3001"
	@echo "Backend: http://localhost:8001"
	@echo ""
	@(cd backend-admin && export PYTHONPATH=$$PYTHONPATH:. && .venv/bin/python src/main.py) & \
	(cd frontend/admin && npm run dev) & \
	wait

# Build padrão (development)
build:
	podman-compose build

# Build de produção (minificado, otimizado)
build-prod:
	BUILD_MODE=production podman-compose build

# Restart com rebuild
restart:
	podman-compose down
	podman-compose build
	podman-compose up -d

# Debug rebuild (without admin - recommended for main app testing)
debug-rebuild:
	podman-compose down
	podman-compose build backend frontend mongo qdrant mongo-express
	podman-compose up

# Debug rebuild with admin services (full stack)
debug-rebuild-admin:
	podman-compose down
	podman-compose build
	podman-compose up

# User Management Commands
user-create:
	@cd backend && .venv/bin/python scripts/manage_users.py create --email "$(EMAIL)" --password "$(PASSWORD)"

user-list:
	@cd backend && .venv/bin/python scripts/manage_users.py list

user-get:
	@cd backend && .venv/bin/python scripts/manage_users.py get "$(EMAIL)"

user-update:
	@cd backend && .venv/bin/python scripts/manage_users.py update "$(EMAIL)" $(ARGS)

user-password:
	@cd backend && .venv/bin/python scripts/manage_users.py password "$(EMAIL)" --new-password "$(PASSWORD)"

user-delete:
	@cd backend && .venv/bin/python scripts/manage_users.py delete "$(EMAIL)"

# Deleta TUDO do usuario (MongoDB + Vector DB + Logs)
user-nuke:
	@cd backend && export PYTHONPATH=. && .venv/bin/python scripts/delete_user.py "$(EMAIL)"

user-nuke-force:
	@cd backend && export PYTHONPATH=. && .venv/bin/python scripts/delete_user.py "$(EMAIL)" --force

# Invite Commands
invite-create:
	@cd backend && export PYTHONPATH=. && .venv/bin/python scripts/manage_invites.py create --email "$(EMAIL)" --expires-hours 48

invite-list:
	@cd backend && export PYTHONPATH=. && .venv/bin/python scripts/manage_invites.py list

# Admin Commands
admin-promote:
	@echo "Promovendo usuário $(EMAIL) a admin..."
	@podman-compose exec backend python scripts/promote_admin.py $(EMAIL)

admin-promote-rafael:
	@echo "Promovendo Rafael Colucci a admin..."
	@podman-compose exec backend python scripts/promote_admin.py rafacolucci@gmail.com

admin-list:
	@echo "Listando usuários admin..."
	@podman-compose exec mongodb mongosh -u admin -p password --authenticationDatabase admin --quiet --eval "use aitrainer; db.users.find({role: 'admin'}, {email: 1, role: 1, _id: 0}).forEach(printjson)"

# Test Commands

## Backend Tests
test-backend:
	podman-compose exec backend pytest

test-backend-cov:
	podman-compose exec backend pytest --cov=src --cov-report=html --cov-report=term-missing

test-backend-verbose:
	podman-compose exec backend pytest -v

test-backend-watch:
	podman-compose exec backend pytest --cov=src -v --tb=short

## Frontend Tests
test-frontend:
	cd frontend && npm test

test-frontend-watch:
	cd frontend && npm test -- --watch

test-frontend-cov:
	cd frontend && npm test -- --coverage

## Admin Frontend Tests
test-admin:
	cd frontend/admin && npm test

test-admin-watch:
	cd frontend/admin && npm test -- --watch

test-admin-cov:
	cd frontend/admin && npm test -- --coverage

## All Tests
test: test-backend test-frontend test-admin

test-cov: test-backend-cov test-frontend-cov

# E2E Tests (Playwright)

## Playwright (headless)
e2e:
	cd frontend && npx playwright test

## Playwright UI
e2e-ui:
	cd frontend && npx playwright test --ui

## Playwright Report
e2e-report:
	cd frontend && npx playwright show-report

# CI/CD Validation Commands

## CI Fast: Gate rápido para PRs
## - Backend: testes unitários + linter
## - Frontend: unit tests + vitest
## - Playwright: omitido para fast check
ci-fast: test-backend test-frontend
	@echo "✅ CI Fast Gate Passed!"

## CI Full: Tudo que a CI/CD roda no GitHub Actions
## - Backend: unit tests + benchmarks + linter
## - Frontend: unit tests + build + playwright
ci-test: test-backend test-frontend e2e
	@echo "✅ CI Full Test Suite Passed!"

# -----------------------------------------------------------------------------
# GCP Production Deployment (Google Cloud Run)
# -----------------------------------------------------------------------------

gcp-full: gcp-build gcp-push gcp-deploy
	@echo "🚀 Full GCP Deployment Complete!"

gcp-build:
	@echo "📦 Building production images..."
	podman build -t $(GCP_REGISTRY)/backend:latest ./backend
	podman build -t $(GCP_REGISTRY)/frontend:latest ./frontend
	podman build -t $(GCP_REGISTRY)/backend-admin:latest ./backend-admin
	@ADMIN_KEY=$$(grep '^ADMIN_SECRET_KEY=' backend/.env.prod | cut -d'=' -f2) && \
	podman build --build-arg VITE_ADMIN_SECRET_KEY=$$ADMIN_KEY -t $(GCP_REGISTRY)/frontend-admin:latest -f ./frontend/admin/Dockerfile ./frontend

gcp-push:
	@echo "⬆️  Pushing images to Artifact Registry..."
	podman push $(GCP_REGISTRY)/backend:latest
	podman push $(GCP_REGISTRY)/frontend:latest
	podman push $(GCP_REGISTRY)/backend-admin:latest
	podman push $(GCP_REGISTRY)/frontend-admin:latest

gcp-deploy:
	@echo "🚀 Deploying to Cloud Run in $(GCP_REGION)..."
	# 1. Backend
	gcloud run deploy aitrainer-backend \
		--image $(GCP_REGISTRY)/backend:latest \
		--region $(GCP_REGION) --platform managed --allow-unauthenticated --port 8000 \
		--set-env-vars "$(GCP_ENV_VARS)"
	
	# 2. Frontend (using Backend URL)
	@BACKEND_URL=$$(gcloud run services describe aitrainer-backend --region $(GCP_REGION) --format 'value(status.url)'); \
	echo "🔗 Mapping Frontend to Backend at $$BACKEND_URL"; \
	gcloud run deploy aitrainer-frontend \
		--image $(GCP_REGISTRY)/frontend:latest \
		--region $(GCP_REGION) --platform managed --allow-unauthenticated --port 80 \
		--set-env-vars "BACKEND_URL=$$BACKEND_URL"
	
	# 3. Admin Backend
	gcloud run deploy aitrainer-backend-admin \
		--image $(GCP_REGISTRY)/backend-admin:latest \
		--region $(GCP_REGION) --platform managed --allow-unauthenticated --port 8000 \
		--set-env-vars "$(GCP_ENV_VARS)"
	
	# 4. Admin Frontend (using Admin Backend URL)
	@ADMIN_BACKEND_URL=$$(gcloud run services describe aitrainer-backend-admin --region $(GCP_REGION) --format 'value(status.url)'); \
	echo "🔗 Mapping Admin Frontend to Admin Backend at $$ADMIN_BACKEND_URL"; \
	gcloud run deploy aitrainer-frontend-admin \
		--image $(GCP_REGISTRY)/frontend-admin:latest \
		--region $(GCP_REGION) --platform managed --allow-unauthenticated --port 80 \
		--set-env-vars "ADMIN_BACKEND_URL=$$ADMIN_BACKEND_URL"

	@$(MAKE) gcp-setup-telegram
	@$(MAKE) gcp-hosting


gcp-setup-telegram:
	@echo "🤖 Verificando configuração do Telegram..."
	@TOKEN=$$(grep TELEGRAM_BOT_TOKEN backend/.env.prod | cut -d'=' -f2 | sed 's/"//g'); \
	SECRET=$$(grep TELEGRAM_WEBHOOK_SECRET backend/.env.prod | cut -d'=' -f2 | sed 's/"//g'); \
	URL=$$(gcloud run services describe aitrainer-backend --region $(GCP_REGION) --format 'value(status.url)'); \
	if [ -n "$$TOKEN" ] && [ "$$TOKEN" != '""' ]; then \
		echo "🚀 Atualizando Webhook para $$URL/telegram/webhook..."; \
		curl -s -X POST "https://api.telegram.org/bot$$TOKEN/setWebhook" \
			-d "url=$$URL/telegram/webhook" \
			-d "secret_token=$$SECRET" | jq .; \
	else \
		echo "⚠️ Telegram não configurado em .env.prod. Pulando..."; \
	fi

gcp-hosting:
	@echo "🌐 Atualizando Firebase Hosting (Custom Domain Proxy)..."
	@npx -y firebase-tools deploy --only hosting --project $(GCP_PROJECT_ID) || echo "⚠️  Falha no deploy do Firebase (pode exigir login manual: firebase login)"


gcp-list:
	@echo "🔍 Cloud Run Services:"
	@gcloud run services list --region $(GCP_REGION)

