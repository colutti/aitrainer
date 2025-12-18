.PHONY: up down logs init-db hash-user

up:
	podman-compose up -d

down:
	podman-compose down

logs:
	podman-compose logs -f

init-db:
	python -m backend.scripts.init_users --email "$(USUARIO)" --password "$(SENHA)"

api:
	cd backend && uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

front:
	cd frontend && npx ng serve --host 0.0.0.0 --port 4200
