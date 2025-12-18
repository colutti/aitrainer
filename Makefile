.PHONY: up down build restart logs init-db api front clean-pod

up:
	podman-compose up -d

down:
	podman-compose down

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
	python -m backend.scripts.init_users --email "$(USUARIO)" --password "$(SENHA)"

api:
	cd backend && export PYTHONPATH=$$PYTHONPATH:. && .venv/bin/python src/api/main.py

front:
	cd frontend && npm run dev
