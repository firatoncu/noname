# Makefile for n0name Trading Bot
# Provides convenient shortcuts for development and testing tasks

.PHONY: help install install-dev test test-unit test-integration test-performance test-security test-all coverage lint format clean docs build

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
	@echo "Development Commands:"
	@echo "  clean            Clean up build artifacts and cache files"
	@echo "  docs             Build documentation"
	@echo "  build            Build package for distribution"
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

build:
	@echo "Building package for distribution..."
	python -m build
	@echo "Package built in dist/"

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

# Docker Commands (if using Docker)
docker-test:
	docker build -t n0name-test .
	docker run --rm n0name-test make test-all

# Database Commands (if using database)
db-test:
	@echo "Setting up test database..."
	# Add database setup commands here
	python tests/run_tests.py --integration --verbose
	@echo "Database tests completed"

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

# Environment Commands
env-check:
	@echo "Python version: $$(python --version)"
	@echo "Pip version: $$(pip --version)"
	@echo "Virtual environment: $$VIRTUAL_ENV"
	python -c "import sys; print(f'Python path: {sys.path}')"

# Quick Commands for Development
quick-test:
	pytest tests/unit/ -x -v

quick-lint:
	ruff check src/ tests/
	black --check src/ tests/

# Help for specific categories
help-test:
	@echo "Testing Commands Help:"
	@echo ""
	@echo "  test             - Run unit tests (fastest, for development)"
	@echo "  test-unit        - Run all unit tests with verbose output"
	@echo "  test-integration - Run integration tests (slower, more comprehensive)"
	@echo "  test-performance - Run performance benchmarks"
	@echo "  test-security    - Run security vulnerability tests"
	@echo "  test-all         - Run all test categories"
	@echo "  test-parallel    - Run tests in parallel (faster on multi-core)"
	@echo ""
	@echo "Coverage:"
	@echo "  coverage         - Run tests with coverage reporting"
	@echo "  coverage-html    - Generate HTML coverage report"
	@echo ""
	@echo "Custom:"
	@echo "  test-custom      - Run tests matching a custom pattern"
	@echo "  test-debug       - Run tests with debugger on failure"

help-quality:
	@echo "Code Quality Commands Help:"
	@echo ""
	@echo "  lint             - Run ruff, mypy, and black checks"
	@echo "  format           - Auto-format code with black and isort"
	@echo "  type-check       - Run mypy type checking"
	@echo "  security-scan    - Run bandit and safety security scans"
	@echo ""
	@echo "Quick checks:"
	@echo "  quick-lint       - Fast linting for development"
	@echo "  pre-commit       - Run all pre-commit checks"

# Aliases for common commands
t: test
tu: test-unit
ti: test-integration
ta: test-all
c: coverage
l: lint
f: format
cl: clean 