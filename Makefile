.PHONY: dev stop reset logs user-reset user-reset-dry-run verify verify-all test-once e2e test-backend-cov test-conversation deploy-preflight deploy-build deploy-prod deploy-prod-fast deploy-smoke deploy-prod-env

test-backend-cov:
	./scripts/compose.sh -f docker-compose.test.yml run --rm backend-tests pytest --cov=src --cov-report=html --cov-report=term-missing

test-conversation:
	cd backend && .venv/bin/pytest tests/conversation/ -v --tb=short

deploy-preflight:
	./scripts/deploy/preflight.sh

deploy-build: deploy-preflight
	./scripts/deploy/build_images.sh

deploy-prod: deploy-build
	./scripts/deploy/deploy_prod.sh
	./scripts/deploy/smoke_test.sh

deploy-prod-fast: deploy-preflight
	AUTO_DETECT_CHANGED=true ./scripts/deploy/build_images.sh
	./scripts/deploy/deploy_prod.sh
	./scripts/deploy/smoke_test.sh

deploy-smoke:
	./scripts/deploy/smoke_test.sh

deploy-prod-env:
	./scripts/deploy/deploy_prod_env.sh
