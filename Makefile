.PHONY: dev stop reset logs verify verify-all test-once e2e test-backend-cov deploy-preflight deploy-build deploy-prod deploy-prod-fast deploy-smoke deploy-prod-env

dev:
	./scripts/dev/dev.sh

stop:
	./scripts/dev/stop.sh

reset:
	./scripts/dev/reset.sh

logs:
	./scripts/dev/logs.sh

verify:
	./scripts/verify/quick.sh

verify-all:
	./scripts/verify/all.sh

test-once:
	./scripts/verify/quick.sh
	./scripts/verify/e2e.sh

e2e:
	./scripts/verify/e2e.sh

test-backend-cov:
	./scripts/compose.sh -f docker-compose.test.yml run --rm backend-tests pytest --cov=src --cov-report=html --cov-report=term-missing

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
