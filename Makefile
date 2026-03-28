.PHONY: dev stop reset logs verify verify-all test-once e2e test-backend-cov

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
