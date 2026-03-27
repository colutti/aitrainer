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

COMPOSE_DEV=./scripts/compose.sh -f docker-compose.yml
COMPOSE_TEST=COMPOSE_PROJECT_NAME=personal-test ./scripts/compose.sh -f docker-compose.test.yml
CONTAINER_RUNTIME?=podman
STRIPE_FORWARD_TO?=http://localhost:8000/stripe/webhook

.PHONY: up down build build-prod restart api front front-admin api-admin admin user-create user-list user-get user-update user-password user-delete user-nuke user-nuke-force invite-create invite-list admin-promote admin-promote-rafael admin-list backend-lint backend-typecheck frontend-lint frontend-typecheck wait-for-services test test-once test-stack-up test-stack-down test-backend test-backend-local test-backend-cov test-backend-verbose test-backend-watch test-frontend test-frontend-watch test-frontend-cov test-admin test-admin-watch test-admin-cov test-cov e2e e2e-ui e2e-journey e2e-report ci-fast ci-test security-sast security-sca security-check gcp-full gcp-build gcp-push gcp-deploy gcp-setup-telegram gcp-hosting gcp-list stripe-login stripe-listen

up:
	$(COMPOSE_DEV) up -d

down:
	$(COMPOSE_DEV) down

init-db:
	cd backend && export PYTHONPATH=$$PYTHONPATH:. && .venv/bin/python src/api/main.py --init-db --email "$(USUARIO)" --password "$(SENHA)"

api:
	cd backend && export PYTHONPATH=$$PYTHONPATH:. && .venv/bin/python src/api/main.py

front:
	$(COMPOSE_DEV) up -d frontend

front-admin:
	cd frontend/admin && npm run dev

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
	$(COMPOSE_DEV) build

build-prod:
	BUILD_MODE=production $(COMPOSE_DEV) build

restart:
	$(COMPOSE_DEV) down
	$(COMPOSE_DEV) build
	$(COMPOSE_DEV) up -d

debug-rebuild:
	$(COMPOSE_DEV) down
	$(COMPOSE_DEV) build backend frontend mongo qdrant mongo-express
	$(COMPOSE_DEV) up

debug-rebuild-admin:
	$(COMPOSE_DEV) down
	$(COMPOSE_DEV) build
	$(COMPOSE_DEV) up

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
	@$(COMPOSE_DEV) exec backend python scripts/promote_admin.py $(EMAIL)

admin-promote-rafael:
	@echo "Promovendo Rafael Colucci a admin..."
	@$(COMPOSE_DEV) exec backend python scripts/promote_admin.py rafacolucci@gmail.com

admin-list:
	@echo "Listando usuários admin..."
	@$(COMPOSE_DEV) exec mongo mongosh -u admin -p password --authenticationDatabase admin --quiet --eval "use aitrainerdb; db.users.find({role: 'admin'}, {email: 1, role: 1, _id: 0}).forEach(printjson)"

# Quality Check Commands
backend-lint:
	cd backend && .venv/bin/ruff check src
	cd backend && .venv/bin/pylint src

backend-typecheck:
	cd backend && .venv/bin/pyright src

frontend-lint:
	cd frontend && npm run lint

frontend-typecheck:
	cd frontend && npm run typecheck

# Infrastructure Helpers
wait-for-services:
	@echo "⏳ Waiting for services to be healthy..."
	@for i in {1..30}; do \
		if [ $$( $(COMPOSE_DEV) ps --filter "health=healthy" --quiet | wc -l) -ge 4 ]; then \
			echo "✅ All services are healthy!"; \
			exit 0; \
		fi; \
		echo "Waiting... ($$i/30)"; \
		sleep 2; \
	done; \
	echo "❌ Services failed to become healthy in time"; \
	$(COMPOSE_DEV) ps; \
	exit 1

# Test Commands

test-stack-up:
	$(COMPOSE_TEST) up -d --build mongo qdrant stripe-mock backend frontend

test-stack-down:
	$(COMPOSE_TEST) down --volumes --remove-orphans

test-once:
	@set -e; \
	trap '$(COMPOSE_TEST) down --volumes --remove-orphans' EXIT; \
	$(COMPOSE_TEST) up -d --build mongo qdrant stripe-mock backend frontend; \
	$(COMPOSE_TEST) run --rm backend-tests; \
	$(COMPOSE_TEST) run --rm frontend-tests; \
	$(COMPOSE_TEST) run --rm admin-tests; \
	$(COMPOSE_TEST) run --rm playwright

## Backend Tests
test-backend:
	@set -e; \
	trap '$(COMPOSE_TEST) down --volumes --remove-orphans' EXIT; \
	$(COMPOSE_TEST) up -d --build mongo qdrant stripe-mock backend; \
	$(COMPOSE_TEST) run --rm backend-tests

test-backend-local:
	cd backend && .venv/bin/pytest

test-backend-cov:
	@set -e; \
	trap '$(COMPOSE_TEST) down --volumes --remove-orphans' EXIT; \
	$(COMPOSE_TEST) up -d --build mongo qdrant stripe-mock backend; \
	$(COMPOSE_TEST) run --rm backend-tests pytest --cov=src --cov-report=html --cov-report=term-missing

test-backend-verbose:
	@set -e; \
	trap '$(COMPOSE_TEST) down --volumes --remove-orphans' EXIT; \
	$(COMPOSE_TEST) up -d --build mongo qdrant stripe-mock backend; \
	$(COMPOSE_TEST) run --rm backend-tests pytest -v

test-backend-watch:
	@echo "Use test-backend or test-backend-verbose for the containerized flow."

## Frontend Tests
test-frontend:
	$(COMPOSE_TEST) run --rm frontend-tests

test-frontend-watch:
	cd frontend && npm test -- --watch

test-frontend-cov:
	cd frontend && npm test -- --coverage

## Admin Frontend Tests
test-admin:
	$(COMPOSE_TEST) run --rm admin-tests

test-admin-watch:
	cd frontend/admin && npm test -- --watch

test-admin-cov:
	cd frontend/admin && npm test -- --coverage

## All Tests
test: test-once

test-cov: test-backend-cov test-frontend-cov

# E2E Tests (Playwright + Real Backend)

## Playwright (Automated Headless)
e2e:
	@set -e; \
	trap '$(COMPOSE_TEST) down --volumes --remove-orphans' EXIT; \
	$(COMPOSE_TEST) up -d --build mongo qdrant stripe-mock backend frontend; \
	$(COMPOSE_TEST) run --rm playwright

## Playwright UI (Debug Mode)
e2e-ui:
	@echo "Use a containerized Playwright shell if you need interactive debugging."
	@echo "The official stable E2E path is: make e2e"

## Playwright Journey (Automatic Animated Run)
e2e-journey:
	@echo "🛠️  Construindo App para testes..."
	cd frontend && npm run build
	@echo "🏃 Rodando jornada completa (Navegador Real)..."
	cd frontend && npx playwright test e2e/real/complete_user_journey.spec.ts --project=chromium --headed

## Playwright Report
e2e-report:
	cd frontend && npx playwright show-report

# CI/CD Validation Commands

## CI Fast: Gate rápido para PRs
## - Qualidade estática + Testes Unitários
ci-fast: backend-lint backend-typecheck frontend-lint frontend-typecheck test-backend test-frontend test-admin
	@echo "✅ CI Fast Gate Passed!"

## CI Full: Tudo que a CI/CD roda no GitHub Actions
## - Qualidade + Testes Unitários + E2E
ci-test: ci-fast e2e
	@echo "✅ CI Full Test Suite Passed!"

# -----------------------------------------------------------------------------
# Security Scanning (ephemeral containers)
# -----------------------------------------------------------------------------

security-sast:
	@echo "🔍 Running SAST (Semgrep)..."
	$(CONTAINER_RUNTIME) run --rm -v $$(pwd):/src:ro -w /src docker.io/semgrep/semgrep:latest \
		semgrep scan --config auto --error --severity ERROR --severity WARNING .

security-sca:
	@echo "🔍 Running SCA + Secret Scanning (Trivy)..."
	$(CONTAINER_RUNTIME) run --rm -v $$(pwd):/src:ro -w /src docker.io/aquasec/trivy:latest \
		fs --exit-code 1 --severity HIGH,CRITICAL --scanners vuln,secret --skip-files "backend/firebase-admin-dev.json,backend/firebase-admin.json,backend/.env,.env" .

security-check: security-sast security-sca
	@echo "✅ Security checks passed!"

# -----------------------------------------------------------------------------
# GCP Production Deployment (Google Cloud Run)
# -----------------------------------------------------------------------------

gcp-full: gcp-build gcp-push gcp-deploy
	@echo "🚀 Full GCP Deployment Complete!"

gcp-build:
	@echo "📦 Building production images..."
	$(CONTAINER_RUNTIME) build -t $(GCP_REGISTRY)/backend:latest ./backend
	$(CONTAINER_RUNTIME) build -t $(GCP_REGISTRY)/frontend:latest ./frontend
	$(CONTAINER_RUNTIME) build -t $(GCP_REGISTRY)/backend-admin:latest ./backend-admin
	@ADMIN_KEY=$$(grep '^ADMIN_SECRET_KEY=' backend/.env.prod | cut -d'=' -f2) && \
	$(CONTAINER_RUNTIME) build --build-arg VITE_ADMIN_SECRET_KEY=$$ADMIN_KEY -t $(GCP_REGISTRY)/frontend-admin:latest -f ./frontend/admin/Dockerfile ./frontend

gcp-push:
	@echo "⬆️  Pushing images to Artifact Registry..."
	$(CONTAINER_RUNTIME) push $(GCP_REGISTRY)/backend:latest
	$(CONTAINER_RUNTIME) push $(GCP_REGISTRY)/frontend:latest
	$(CONTAINER_RUNTIME) push $(GCP_REGISTRY)/backend-admin:latest
	$(CONTAINER_RUNTIME) push $(GCP_REGISTRY)/frontend-admin:latest

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


# -----------------------------------------------------------------------------
# Stripe Local Testing
# -----------------------------------------------------------------------------

stripe-login:
	$(CONTAINER_RUNTIME) run --rm -it -v stripe-config:/root/.config/stripe stripe/stripe-cli login

stripe-listen:
	$(CONTAINER_RUNTIME) run --rm -it -v stripe-config:/root/.config/stripe --network host stripe/stripe-cli listen --forward-to $(STRIPE_FORWARD_TO)
