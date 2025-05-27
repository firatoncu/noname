# Makefile for n0name Trading Bot v2.0.0
# Provides convenient shortcuts for development, testing, building, and deployment

.PHONY: help install install-dev test test-unit test-integration test-performance test-security test-all coverage lint format clean docs build deploy

# Default target
help:
	@echo "n0name Trading Bot v2.0.0 - Development Commands"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  dev              Start development environment"
	@echo "  setup            Complete development setup"
	@echo "  quick-test       Run quick validation tests"
	@echo ""
	@echo "📦 Setup Commands:"
	@echo "  install          Install package in production mode"
	@echo "  install-dev      Install package in development mode with all dependencies"
	@echo "  setup-dev        Complete development environment setup"
	@echo "  setup-hooks      Install pre-commit hooks"
	@echo ""
	@echo "🧪 Testing Commands:"
	@echo "  test             Run unit tests (default)"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-performance Run performance tests"
	@echo "  test-security    Run security tests"
	@echo "  test-smoke       Run smoke tests for quick validation"
	@echo "  test-all         Run all tests"
	@echo "  test-parallel    Run tests in parallel"
	@echo ""
	@echo "📊 Coverage Commands:"
	@echo "  coverage         Run tests with coverage reporting"
	@echo "  coverage-unit    Run unit tests with coverage"
	@echo "  coverage-html    Generate HTML coverage report"
	@echo "  coverage-report  Generate comprehensive test report"
	@echo ""
	@echo "🔍 Code Quality Commands:"
	@echo "  lint             Run all linting tools"
	@echo "  format           Format code with black and isort"
	@echo "  type-check       Run type checking with mypy"
	@echo "  security-scan    Run security analysis"
	@echo "  validate         Run all validation checks"
	@echo ""
	@echo "🏗️ Build Commands:"
	@echo "  build            Build package for distribution"
	@echo "  build-dev        Build for development"
	@echo "  build-prod       Build for production"
	@echo "  build-exe        Build standalone executable"
	@echo "  build-docker     Build Docker images"
	@echo "  build-release    Build complete release package"
	@echo ""
	@echo "🚀 Deployment Commands:"
	@echo "  deploy-dev       Deploy to development environment"
	@echo "  deploy-staging   Deploy to staging environment"
	@echo "  deploy-prod      Deploy to production environment"
	@echo "  deploy-rollback  Rollback deployment"
	@echo "  deploy-dry-run   Test deployment without changes"
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  docker-build     Build Docker images"
	@echo "  docker-up        Start Docker services"
	@echo "  docker-down      Stop Docker services"
	@echo "  docker-logs      View Docker logs"
	@echo "  docker-clean     Clean Docker resources"
	@echo "  docker-dev       Start development Docker environment"
	@echo ""
	@echo "📚 Documentation Commands:"
	@echo "  docs             Build documentation"
	@echo "  docs-serve       Serve documentation locally"
	@echo "  docs-clean       Clean documentation build"
	@echo ""
	@echo "🛠️ Maintenance Commands:"
	@echo "  clean            Clean up build artifacts and cache files"
	@echo "  clean-all        Deep clean including dependencies"
	@echo "  backup           Backup important data"
	@echo "  check-deps       Check if all dependencies are installed"
	@echo "  update-deps      Update dependencies"
	@echo ""
	@echo "🔄 CI/CD Commands:"
	@echo "  ci-test          Run the same tests as CI pipeline"
	@echo "  pre-commit       Run pre-commit checks"
	@echo "  validate-setup   Validate project setup"

# Quick Start Commands
dev:
	@echo "🚀 Starting development environment..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ Development environment started!"
	@echo "📊 Grafana: http://localhost:3000"
	@echo "📈 InfluxDB: http://localhost:8086"
	@echo "🔍 Logs: make docker-dev-logs"

setup: install-dev setup-hooks
	@echo "✅ Development setup complete!"

quick-test: test-smoke lint
	@echo "✅ Quick validation passed!"

# Setup Commands
install:
	pip install -e .

install-dev:
	pip install -e .[dev,performance,monitoring,security]
	pip install -r requirements-dev.txt

setup-dev: install-dev setup-hooks
	@echo "Setting up development environment..."
	mkdir -p logs data/market data/backtest data/cache
	cp -n .env.example .env || true
	@echo "✅ Development environment setup complete!"
	@echo "📝 Please edit .env with your configuration"

setup-hooks:
	pre-commit install
	pre-commit install --hook-type commit-msg

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
	python tests/run_tests.py --coverage --html
	@echo "📊 Coverage report: htmlcov/index.html"

coverage-report:
	python tests/run_tests.py --report
	@echo "📋 Comprehensive test report generated"

# Code Quality Commands
lint:
	python tests/run_tests.py --lint

format:
	python tests/run_tests.py --format

type-check:
	python -m mypy src/ --config-file pyproject.toml

security-scan:
	@echo "🔍 Running security scans..."
	bandit -r src/ -f json -o reports/bandit-report.json
	safety check --json --output reports/safety-report.json
	@echo "📋 Security reports: reports/bandit-report.json, reports/safety-report.json"

validate: lint type-check security-scan test-smoke
	@echo "✅ All validation checks passed!"

# Build Commands
build:
	python scripts/build/build.py --type prod

build-dev:
	python scripts/build/build.py --type dev

build-prod:
	python scripts/build/build.py --type prod --test --lint

build-exe:
	python scripts/build/build.py --type exe --onefile

build-docker:
	python scripts/build/build.py --type docker

build-release:
	@read -p "Enter version (e.g., 2.1.0): " version; \
	python scripts/build/build.py --type release --version $$version

# Deployment Commands
deploy-dev:
	scripts/deployment/deploy.sh -e development

deploy-staging:
	scripts/deployment/deploy.sh -e staging

deploy-prod:
	@echo "⚠️  WARNING: This will deploy to PRODUCTION!"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		scripts/deployment/deploy.sh -e production; \
	else \
		echo "❌ Deployment cancelled."; \
	fi

deploy-rollback:
	scripts/deployment/deploy.sh --rollback

deploy-dry-run:
	scripts/deployment/deploy.sh --dry-run -e production

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

docker-dev:
	docker-compose -f docker-compose.dev.yml up -d

docker-dev-down:
	docker-compose -f docker-compose.dev.yml down

docker-dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

docker-dev-shell:
	docker-compose -f docker-compose.dev.yml exec n0name-bot bash

# Documentation Commands
docs:
	@echo "📚 Building documentation..."
	mkdir -p docs/_build
	@echo "✅ Documentation built!"

docs-serve:
	@echo "🌐 Serving documentation at http://localhost:8000"
	cd docs && python -m http.server 8000

docs-clean:
	rm -rf docs/_build

# Maintenance Commands
clean:
	@echo "🧹 Cleaning up build artifacts and cache files..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "✅ Cleanup complete!"

clean-all: clean
	@echo "🧹 Deep cleaning..."
	rm -rf venv/
	rm -rf .venv/
	rm -rf node_modules/
	docker system prune -a -f
	@echo "✅ Deep cleanup complete!"

backup:
	@echo "💾 Creating backup..."
	scripts/maintenance/backup.sh
	@echo "✅ Backup complete!"

check-deps:
	@echo "🔍 Checking dependencies..."
	python scripts/utilities/validate-setup.py --deps
	@echo "✅ Dependencies check complete!"

update-deps:
	@echo "📦 Updating dependencies..."
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-dev.txt
	@echo "✅ Dependencies updated!"

# CI/CD Commands
ci-test:
	@echo "🔄 Running CI pipeline tests..."
	python tests/run_tests.py --ci
	@echo "✅ CI tests complete!"

pre-commit:
	pre-commit run --all-files

validate-setup:
	@echo "🔍 Validating project setup..."
	python scripts/utilities/validate-setup.py --all
	@echo "✅ Setup validation complete!"

# Monitoring Commands
monitor:
	@echo "📊 Opening monitoring dashboard..."
	@echo "Grafana: http://localhost:3000"
	@echo "InfluxDB: http://localhost:8086"

logs:
	tail -f logs/n0name.log

logs-error:
	tail -f logs/error.log

# Development Utilities
shell:
	python -c "from n0name import *; import IPython; IPython.embed()"

debug:
	python -m pdb n0name.py

profile:
	python -m cProfile -o profile.stats n0name.py
	@echo "📊 Profile saved to profile.stats"

# Database Commands
db-migrate:
	python scripts/utilities/migrate-data.py

db-backup:
	scripts/maintenance/backup.sh --database-only

db-restore:
	@read -p "Enter backup file path: " backup_file; \
	scripts/maintenance/backup.sh --restore $$backup_file

# Security Commands
security-audit:
	@echo "🔒 Running security audit..."
	python tools/security/audit.py
	@echo "✅ Security audit complete!"

encrypt-config:
	python tools/security/encrypt_config.py

decrypt-config:
	python tools/security/decrypt_config.py

# Performance Commands
benchmark:
	python tests/performance/test_benchmarks.py

load-test:
	python tests/performance/test_load.py

# Release Commands
tag-release:
	@read -p "Enter version (e.g., v2.1.0): " version; \
	git tag -a $$version -m "Release $$version"; \
	git push origin $$version

changelog:
	@echo "📝 Updating changelog..."
	@echo "Please update CHANGELOG.md manually"

# Help for specific categories
help-dev:
	@echo "🔧 Development Commands:"
	@echo "  dev              Start development environment"
	@echo "  setup-dev        Setup development environment"
	@echo "  test             Run tests"
	@echo "  lint             Check code quality"
	@echo "  format           Format code"

help-deploy:
	@echo "🚀 Deployment Commands:"
	@echo "  deploy-dev       Deploy to development"
	@echo "  deploy-staging   Deploy to staging"
	@echo "  deploy-prod      Deploy to production"
	@echo "  deploy-rollback  Rollback deployment"

help-docker:
	@echo "🐳 Docker Commands:"
	@echo "  docker-dev       Start development containers"
	@echo "  docker-up        Start production containers"
	@echo "  docker-logs      View container logs"
	@echo "  docker-clean     Clean Docker resources" 