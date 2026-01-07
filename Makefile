.PHONY: up down build restart logs init-db api front clean-pod db db-down db-logs

up:
	podman-compose up -d

down:
	podman-compose down

db:
	podman-compose --in-pod 0 up -d mongo qdrant mongo-express

db-down:
	podman-compose stop mongo qdrant mongo-express

db-logs:
	podman-compose logs -f mongo qdrant

build:
	podman-compose build

restart:
	podman-compose restart

logs:
	podman-compose logs -f

clean-pod:
	podman-compose down
	podman pod rm -f pod_personal || true

init-db:
	cd backend && export PYTHONPATH=$$PYTHONPATH:. && .venv/bin/python src/api/main.py --init-db --email "$(USUARIO)" --password "$(SENHA)"

api:
	cd backend && export PYTHONPATH=$$PYTHONPATH:. && .venv/bin/python src/api/main.py

front:
	podman-compose --in-pod 0 up -d --no-deps frontend

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