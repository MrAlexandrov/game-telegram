# Game Telegram - Development Makefile
# Provides common development tasks and shortcuts

.PHONY: help install install-dev test test-unit test-integration test-e2e test-performance
.PHONY: lint format security-scan clean build start stop restart logs
.PHONY: db-migrate db-reset demo-data verify deploy-staging deploy-prod
.PHONY: docker-build docker-push release

# Default target
help: ## Show this help message
	@echo "Game Telegram - Development Commands"
	@echo "===================================="
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation
install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install

# Testing
test: test-unit test-integration ## Run all tests

test-unit: ## Run unit tests
	pytest tests/unit/ -v --cov=. --cov-report=html --cov-report=term

test-integration: ## Run integration tests
	pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests
	pytest tests/e2e/ -v

test-performance: ## Run performance tests
	pytest tests/performance/ -v

test-all: ## Run all test suites
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

# Code Quality
lint: ## Run linting checks
	flake8 services/ shared/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 services/ shared/ --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

format: ## Format code with black and isort
	black services/ shared/ tests/ demo/ scripts/
	isort services/ shared/ tests/ demo/ scripts/

format-check: ## Check code formatting
	black --check services/ shared/ tests/ demo/ scripts/
	isort --check-only services/ shared/ tests/ demo/ scripts/

type-check: ## Run type checking with mypy
	mypy services/ shared/ --ignore-missing-imports

security-scan: ## Run security scans
	bandit -r services/ shared/ -f json -o bandit-report.json
	safety check --json --output safety-report.json || true

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

# Docker Operations
build: ## Build all Docker images
	docker-compose build

start: ## Start all services
	docker-compose up -d

stop: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-service: ## Show logs from specific service (usage: make logs-service SERVICE=game-engine)
	docker-compose logs -f $(SERVICE)

# Database Operations
db-migrate: ## Run database migrations
	cd services/game-engine && alembic upgrade head
	cd services/user-manager && alembic upgrade head

db-reset: ## Reset database (WARNING: destroys all data)
	docker-compose down -v
	docker-compose up -d postgres redis
	sleep 10
	$(MAKE) db-migrate

db-shell: ## Open database shell
	docker-compose exec postgres psql -U gameuser -d gamedb

redis-shell: ## Open Redis shell
	docker-compose exec redis redis-cli

# Demo and Development Data
demo-data: ## Load demo data
	python demo/scripts/load_sample_games.py --all
	python demo/scripts/create_test_users.py --count 10 --admin

demo-reset: ## Reset and reload demo data
	$(MAKE) db-reset
	sleep 5
	$(MAKE) demo-data

# System Verification
verify: ## Run system verification
	python scripts/verify_system.py

quick-check: ## Run quick system health check
	./scripts/quick_check.sh

health: ## Check service health
	@echo "Checking service health..."
	@curl -f http://localhost:8002/health && echo " ✅ Game Engine"
	@curl -f http://localhost:8003/health && echo " ✅ Session Manager"
	@curl -f http://localhost:8004/health && echo " ✅ User Manager"
	@curl -f http://localhost:8005/health && echo " ✅ Analytics Service"
	@curl -f http://localhost:8006/health && echo " ✅ Notification Service"

# Development Environment
dev-setup: ## Set up development environment
	cp .env.example .env
	@echo "Please edit .env with your configuration"
	$(MAKE) install-dev
	$(MAKE) build
	$(MAKE) start
	sleep 30
	$(MAKE) db-migrate
	$(MAKE) demo-data
	$(MAKE) verify

dev-clean: ## Clean development environment
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

# Production Operations
docker-build: ## Build production Docker images
	docker-compose -f docker-compose.prod.yml build

docker-push: ## Push Docker images to registry
	docker-compose -f docker-compose.prod.yml push

deploy-staging: ## Deploy to staging environment
	@echo "Deploying to staging..."
	# Add staging deployment commands here

deploy-prod: ## Deploy to production environment
	@echo "Deploying to production..."
	# Add production deployment commands here

# Release Management
release: ## Create release package
	@echo "🚀 Creating release package..."
	python3 scripts/release.py

release-version: ## Show current version
	@echo "📋 Current version: $$(cat VERSION)"

release-patch: ## Create a patch release
	@echo "🔢 Creating patch release..."
	@major=$$(cat VERSION | cut -d. -f1); \
	minor=$$(cat VERSION | cut -d. -f2); \
	current=$$(cat VERSION | cut -d. -f3); \
	new=$$((current + 1)); \
	echo "$$major.$$minor.$$new" > VERSION; \
	python3 scripts/release.py --version "$$major.$$minor.$$new" --update-version

release-minor: ## Create a minor release
	@echo "🔢 Creating minor release..."
	@major=$$(cat VERSION | cut -d. -f1); \
	current=$$(cat VERSION | cut -d. -f2); \
	new=$$((current + 1)); \
	echo "$$major.$$new.0" > VERSION; \
	python3 scripts/release.py --version "$$major.$$new.0" --update-version

release-major: ## Create a major release
	@echo "🔢 Creating major release..."
	@current=$$(cat VERSION | cut -d. -f1); \
	new=$$((current + 1)); \
	echo "$$new.0.0" > VERSION; \
	python3 scripts/release.py --version "$$new.0.0" --update-version

release-beta: ## Create beta release
	@echo "🧪 Creating beta release..."
	@version=$$(cat VERSION); \
	python3 scripts/release.py --version "$$version-beta" --type beta

release-clean: ## Clean release artifacts
	@echo "🧹 Cleaning release artifacts..."
	rm -rf releases/

# Monitoring and Maintenance
monitor: ## Start monitoring stack
	docker-compose -f docker-compose.monitoring.yml up -d

backup: ## Create system backup
	./scripts/backup.sh

restore: ## Restore from backup (usage: make restore BACKUP_DATE=20240101_120000)
	./scripts/restore.sh $(BACKUP_DATE)

# Cleanup
clean: ## Clean up temporary files and caches
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

clean-docker: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -af
	docker volume prune -f

# Documentation
docs-serve: ## Serve documentation locally
	@echo "Documentation available at:"
	@echo "  README: file://$(PWD)/README.md"
	@echo "  API Docs: http://localhost:8002/docs"
	@echo "  User Guide: file://$(PWD)/docs/user-guide/"
	@echo "  Developer Guide: file://$(PWD)/docs/developer-guide/"

docs-build: ## Build documentation
	@echo "Building documentation..."
	# Add documentation build commands if using tools like Sphinx

# CI/CD
ci-test: ## Run CI test suite locally
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) security-scan
	$(MAKE) test-all

ci-build: ## Build for CI/CD
	docker-compose -f docker-compose.test.yml build

ci-up: ## Start CI test environment
	docker-compose -f docker-compose.test.yml up -d
	sleep 30

ci-down: ## Stop CI test environment
	docker-compose -f docker-compose.test.yml down -v

ci-verify: ## Run CI verification
	docker-compose -f docker-compose.test.yml exec game-engine python scripts/verify_system.py

# Environment Variables
env-check: ## Check environment configuration
	@echo "Checking environment variables..."
	@python -c "import os; print('✅ DATABASE_URL' if os.getenv('DATABASE_URL') else '❌ DATABASE_URL missing')"
	@python -c "import os; print('✅ REDIS_URL' if os.getenv('REDIS_URL') else '❌ REDIS_URL missing')"
	@python -c "import os; print('✅ SECRET_KEY' if os.getenv('SECRET_KEY') else '❌ SECRET_KEY missing')"
	@python -c "import os; print('✅ ADMIN_BOT_TOKEN' if os.getenv('ADMIN_BOT_TOKEN') else '❌ ADMIN_BOT_TOKEN missing')"
	@python -c "import os; print('✅ PLAYER_BOT_TOKEN' if os.getenv('PLAYER_BOT_TOKEN') else '❌ PLAYER_BOT_TOKEN missing')"

# Performance and Load Testing
load-test: ## Run load tests
	locust -f tests/performance/locustfile.py --host=http://localhost:8002

stress-test: ## Run stress tests
	pytest tests/performance/test_load_testing.py::test_stress_testing -v

benchmark: ## Run performance benchmarks
	pytest tests/performance/ -v --benchmark-only

# Utilities
shell: ## Open Python shell with project context
	python -c "import sys; sys.path.append('.'); from services.game_engine.app.main import app; print('Game Telegram shell ready')"

psql: ## Open PostgreSQL shell
	$(MAKE) db-shell

redis-cli: ## Open Redis CLI
	$(MAKE) redis-shell

# Default environment file check
.env:
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo "Please edit .env with your configuration"; \
	fi

# Ensure .env exists for targets that need it
start stop restart logs db-migrate demo-data verify: .env