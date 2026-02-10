.PHONY: up down build restart logs init-db api front clean-pod db db-down db-logs test test-backend test-backend-cov test-backend-verbose test-backend-watch test-frontend test-frontend-watch test-frontend-cov test-cov e2e e2e-ui e2e-report ci-test ci-fast

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

debug-rebuild:
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

## All Tests
test: test-backend test-frontend

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

# Render Deployment Commands

.PHONY: render-deploy render-deploy-backend render-deploy-frontend render-deploy-all render-logs render-list render-status

## Deploy backend (com espera até conclusão)
render-deploy-backend:
	@./scripts/render-deploy.sh backend

## Deploy frontend (com espera até conclusão)
render-deploy-frontend:
	@./scripts/render-deploy.sh frontend

## Deploy ambos backend e frontend (com espera até conclusão)
render-deploy-all: render-deploy-backend render-deploy-frontend

## Deploy com limpeza de cache (rebuild completo)
render-deploy-clean:
	@./scripts/render-deploy.sh all --clear-cache

## Alias: render-deploy = render-deploy-all
render-deploy:
	@$(MAKE) render-deploy-all

## List all Render services
render-list:
	@echo "🔍 Listando serviços no Render..."
	@render services list --output json | jq -r '.[] | "\(.service.name) - \(.service.id) - \(.service.type)"'

## Stream logs backend em tempo real
render-logs-backend:
	@./scripts/render-deploy.sh stream-logs-backend

## Stream logs frontend em tempo real
render-logs-frontend:
	@./scripts/render-deploy.sh stream-logs-frontend

## Alias: stream logs de ambos os serviços
render-logs:
	@echo "🔀 Para logs de um serviço específico, use:"
	@echo "  make render-logs-backend    # Backend em tempo real"
	@echo "  make render-logs-frontend   # Frontend em tempo real"

## View deployment status
render-status:
	@render deploys list

## Ver últimos logs (não streaming)
render-logs-recent-backend:
	@render logs --resources srv-d5f2utqli9vc73dak390 --limit 50 --output text

render-logs-recent-frontend:
	@render logs --resources srv-d5f3e8u3jp1c73bkjbf0 --limit 50 --output text
