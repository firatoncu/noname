# Makefile for n0name Trading Bot
# Provides convenient shortcuts for development, testing, building, and deployment

.PHONY: help install install-dev test test-unit test-integration test-performance test-security test-all coverage lint format clean docs build deploy

# Default target
help:
	@echo "n0name Trading Bot - Development Commands"
	@echo ""
	@echo "Setup Commands:"
	@echo "  install          Install package in production mode"
	@echo "  install-dev      Install package in development mode with all dependencies"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test             Run unit tests (default)"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-performance Run performance tests"
	@echo "  test-security    Run security tests"
	@echo "  test-smoke       Run smoke tests for quick validation"
	@echo "  test-all         Run all tests"
	@echo "  test-parallel    Run tests in parallel"
	@echo ""
	@echo "Coverage Commands:"
	@echo "  coverage         Run tests with coverage reporting"
	@echo "  coverage-unit    Run unit tests with coverage"
	@echo "  coverage-html    Generate HTML coverage report"
	@echo "  coverage-report  Generate comprehensive test report"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  lint             Run all linting tools"
	@echo "  format           Format code with black and isort"
	@echo "  type-check       Run type checking with mypy"
	@echo "  security-scan    Run security analysis"
	@echo ""
	@echo "Build Commands:"
	@echo "  build            Build package for distribution"
	@echo "  build-dev        Build for development"
	@echo "  build-prod       Build for production"
	@echo "  build-exe        Build standalone executable"
	@echo "  build-docker     Build Docker images"
	@echo "  build-release    Build complete release package"
	@echo ""
	@echo "Deployment Commands:"
	@echo "  deploy-dev       Deploy to development environment"
	@echo "  deploy-staging   Deploy to staging environment"
	@echo "  deploy-prod      Deploy to production environment"
	@echo "  deploy-rollback  Rollback deployment"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build     Build Docker images"
	@echo "  docker-up        Start Docker services"
	@echo "  docker-down      Stop Docker services"
	@echo "  docker-logs      View Docker logs"
	@echo "  docker-clean     Clean Docker resources"
	@echo ""
	@echo "Development Commands:"
	@echo "  clean            Clean up build artifacts and cache files"
	@echo "  docs             Build documentation"
	@echo "  check-deps       Check if all dependencies are installed"
	@echo ""
	@echo "CI/CD Commands:"
	@echo "  ci-test          Run the same tests as CI pipeline"
	@echo "  pre-commit       Run pre-commit checks"

# Setup Commands
install:
	pip install -e .

install-dev:
	pip install -e .[dev,performance,monitoring]

# Testing Commands
test:
	python tests/run_tests.py --unit

test-unit:
	python tests/run_tests.py --unit --verbose

test-integration:
	python tests/run_tests.py --integration --verbose

test-performance:
	python tests/run_tests.py --performance --verbose

test-security:
	python tests/run_tests.py --security --verbose

test-smoke:
	python tests/run_tests.py --smoke --verbose

test-all:
	python tests/run_tests.py --all --verbose

test-parallel:
	python tests/run_tests.py --all --parallel --verbose

# Coverage Commands
coverage:
	python tests/run_tests.py --coverage --verbose

coverage-unit:
	python tests/run_tests.py --unit --coverage --verbose

coverage-html:
	python tests/run_tests.py --coverage
	@echo "Coverage report generated at: htmlcov/index.html"

coverage-report:
	python tests/run_tests.py --report
	@echo "Comprehensive test report generated"

# Code Quality Commands
lint:
	python tests/run_tests.py --lint

format:
	python tests/run_tests.py --format

type-check:
	python -m mypy src/

security-scan:
	bandit -r src/ -f json -o bandit-report.json
	safety check --json --output safety-report.json
	@echo "Security reports generated: bandit-report.json, safety-report.json"

# Build Commands
build:
	python scripts/build.py --type prod

build-dev:
	python scripts/build.py --type dev

build-prod:
	python scripts/build.py --type prod --test --lint

build-exe:
	python scripts/build.py --type exe --onefile

build-docker:
	python scripts/build.py --type docker

build-release:
	@read -p "Enter version (e.g., 2.0.0): " version; \
	python scripts/build.py --type release --version $$version

# Deployment Commands
deploy-dev:
	./scripts/deploy.sh -e development

deploy-staging:
	./scripts/deploy.sh -e staging

deploy-prod:
	@echo "WARNING: This will deploy to PRODUCTION!"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		./scripts/deploy.sh -e production; \
	else \
		echo "Deployment cancelled."; \
	fi

deploy-rollback:
	./scripts/deploy.sh --rollback

deploy-dry-run:
	./scripts/deploy.sh --dry-run -e production

# Docker Commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker system prune -a -f
	docker volume prune -f

docker-dev-up:
	docker-compose -f docker-compose.dev.yml up -d

docker-dev-down:
	docker-compose -f docker-compose.dev.yml down

docker-dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

# Development Commands
clean:
	@echo "Cleaning up build artifacts and cache files..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete
	@echo "Cleanup complete!"

docs:
	@echo "Building documentation..."
	# Add documentation build commands here when docs are added
	@echo "Documentation build would run here"

check-deps:
	python tests/run_tests.py --check-deps

# CI/CD Commands
ci-test: lint test-unit test-integration coverage
	@echo "CI test pipeline completed"

pre-commit: format lint test-unit
	@echo "Pre-commit checks completed"

# Advanced Testing Commands
test-custom:
	@read -p "Enter test pattern: " pattern; \
	python tests/run_tests.py --custom "$$pattern" --verbose

test-debug:
	pytest -v -s --tb=long --pdb

test-profile:
	pytest --durations=10 --verbose

# Database Commands
db-migrate:
	@echo "Running database migrations..."
	# Add database migration commands here

db-reset:
	@echo "Resetting database..."
	docker-compose exec postgres psql -U n0name -d n0name_trading -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

db-backup:
	@echo "Creating database backup..."
	mkdir -p backups
	docker-compose exec postgres pg_dump -U n0name n0name_trading > backups/db_backup_$(shell date +%Y%m%d_%H%M%S).sql

# Performance Monitoring
benchmark:
	pytest --benchmark-only --benchmark-sort=mean

benchmark-compare:
	pytest --benchmark-compare=0001 --benchmark-sort=mean

# Continuous Testing
watch-tests:
	@echo "Watching for file changes and running tests..."
	# Requires entr or similar tool
	find src/ tests/ -name "*.py" | entr -c make test-unit

# Release Commands
release-check: clean lint test-all coverage security-scan
	@echo "Release checks completed successfully!"

release-tag:
	@read -p "Enter version tag (e.g., v2.0.0): " tag; \
	git tag -a $$tag -m "Release $$tag"; \
	git push origin $$tag

# Environment Commands
env-check:
	@echo "Python version: $$(python --version)"
	@echo "Pip version: $$(pip --version)"
	@echo "Virtual environment: $$VIRTUAL_ENV"
	python -c "import sys; print(f'Python path: {sys.path}')"

env-setup:
	@echo "Setting up development environment..."
	cp env.example .env
	@echo "Please edit .env with your configuration"

# Quick Commands for Development
quick-test:
	pytest tests/unit/ -x -v

quick-lint:
	ruff check src/ tests/
	black --check src/ tests/

# Monitoring Commands
logs:
	tail -f logs/trading_bot.log

logs-error:
	grep ERROR logs/trading_bot.log | tail -20

status:
	@echo "=== Service Status ==="
	docker-compose ps
	@echo ""
	@echo "=== Health Checks ==="
	curl -s http://localhost:8080/health || echo "Application not responding"

# Utility Commands
install-hooks:
	pre-commit install
	@echo "Pre-commit hooks installed"

update-deps:
	pip install -e .[dev,performance,monitoring] --upgrade
	pip freeze > requirements-frozen.txt

generate-requirements:
	pip-compile requirements.in
	pip-compile requirements-dev.in

# Help for specific categories
help-build:
	@echo "Build Commands:"
	@echo "  build            Build package for distribution"
	@echo "  build-dev        Build for development"
	@echo "  build-prod       Build for production with tests"
	@echo "  build-exe        Build standalone executable"
	@echo "  build-docker     Build Docker images"
	@echo "  build-release    Build complete release package"

help-deploy:
	@echo "Deployment Commands:"
	@echo "  deploy-dev       Deploy to development environment"
	@echo "  deploy-staging   Deploy to staging environment"
	@echo "  deploy-prod      Deploy to production environment (with confirmation)"
	@echo "  deploy-rollback  Rollback to previous deployment"
	@echo "  deploy-dry-run   Show what would be deployed without executing"

help-docker:
	@echo "Docker Commands:"
	@echo "  docker-build     Build Docker images"
	@echo "  docker-up        Start production Docker services"
	@echo "  docker-down      Stop Docker services"
	@echo "  docker-logs      View Docker logs"
	@echo "  docker-clean     Clean Docker resources"
	@echo "  docker-dev-up    Start development Docker services"
	@echo "  docker-dev-down  Stop development Docker services" 