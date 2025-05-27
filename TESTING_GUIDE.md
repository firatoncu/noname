# Testing Infrastructure Guide

This guide provides comprehensive information about the testing infrastructure for the n0name trading bot project.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Coverage Reporting](#coverage-reporting)
- [Continuous Integration](#continuous-integration)
- [Writing Tests](#writing-tests)
- [Mock Objects](#mock-objects)
- [Performance Testing](#performance-testing)
- [Security Testing](#security-testing)
- [Troubleshooting](#troubleshooting)

## Overview

The testing infrastructure is designed to ensure code quality, reliability, and performance of the trading bot. It includes:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions and workflows
- **Performance Tests**: Measure and validate system performance
- **Security Tests**: Validate security measures and detect vulnerabilities
- **Coverage Reporting**: Track test coverage and identify gaps
- **CI/CD Pipeline**: Automated testing on multiple platforms and Python versions

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── run_tests.py               # Test runner script
├── unit/                      # Unit tests
│   ├── test_trading_engine.py
│   ├── test_position_manager.py
│   ├── test_order_manager.py
│   └── test_base_strategy.py
├── integration/               # Integration tests
│   ├── test_trading_integration.py
│   └── test_api_integration.py
├── performance/               # Performance tests
│   └── test_performance.py
└── security/                  # Security tests
    └── test_security.py
```

## Running Tests

### Prerequisites

Install development dependencies:

```bash
pip install -e .[dev]
```

### Basic Test Execution

```bash
# Run all tests
python tests/run_tests.py --all

# Run unit tests only
python tests/run_tests.py --unit

# Run integration tests only
python tests/run_tests.py --integration

# Run with verbose output
python tests/run_tests.py --unit --verbose

# Run tests in parallel
python tests/run_tests.py --all --parallel
```

### Advanced Test Execution

```bash
# Run with coverage reporting
python tests/run_tests.py --coverage

# Run performance tests
python tests/run_tests.py --performance

# Run security tests
python tests/run_tests.py --security

# Run smoke tests (quick validation)
python tests/run_tests.py --smoke

# Run custom test pattern
python tests/run_tests.py --custom "test_trading"

# Generate comprehensive report
python tests/run_tests.py --report
```

### Direct pytest Usage

```bash
# Run specific test file
pytest tests/unit/test_trading_engine.py -v

# Run specific test method
pytest tests/unit/test_trading_engine.py::TestTradingEngine::test_initialization -v

# Run tests with markers
pytest -m "unit" -v
pytest -m "integration" -v
pytest -m "slow" -v

# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

Test individual components in isolation:

- **TradingEngine**: Core trading logic and orchestration
- **PositionManager**: Position tracking and risk management
- **OrderManager**: Order creation and execution
- **BaseStrategy**: Strategy interface and base functionality

**Characteristics:**
- Fast execution (< 1 second per test)
- No external dependencies
- Extensive use of mocks
- High coverage of edge cases

### Integration Tests (`@pytest.mark.integration`)

Test component interactions and end-to-end workflows:

- Complete trading workflows
- Multi-component interactions
- Error propagation and recovery
- Database and API integration (mocked)

**Characteristics:**
- Moderate execution time (1-10 seconds per test)
- Test realistic scenarios
- Use comprehensive mocking
- Focus on component boundaries

### Performance Tests (`@pytest.mark.performance` or `@pytest.mark.slow`)

Measure and validate system performance:

- High-frequency signal processing
- Memory usage stability
- Concurrent operation handling
- Scalability testing

**Characteristics:**
- Longer execution time (10+ seconds)
- Resource usage monitoring
- Benchmark comparisons
- Load testing scenarios

### Security Tests (`@pytest.mark.security`)

Validate security measures:

- Input validation and sanitization
- Authentication and authorization
- Encryption and data protection
- Vulnerability detection

## Coverage Reporting

### Generating Coverage Reports

```bash
# Generate HTML coverage report
python tests/run_tests.py --coverage

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Targets

- **Minimum Coverage**: 80%
- **Target Coverage**: 90%+
- **Critical Components**: 95%+

### Coverage Configuration

Coverage settings are configured in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/venv/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
show_missing = true
fail_under = 80
```

## Continuous Integration

### GitHub Actions Workflow

The CI/CD pipeline runs automatically on:

- Push to `main` or `develop` branches
- Pull requests
- Daily scheduled runs (2 AM UTC)

### CI Jobs

1. **Code Quality**: Linting and formatting checks
2. **Unit Tests**: Cross-platform and multi-Python version testing
3. **Integration Tests**: Component interaction testing
4. **Coverage Analysis**: Coverage reporting and tracking
5. **Performance Tests**: Performance regression detection
6. **Security Tests**: Security vulnerability scanning
7. **Documentation Tests**: Documentation build validation

### Viewing CI Results

- Check the "Actions" tab in GitHub
- View detailed logs for each job
- Download artifacts for reports and coverage

### CI Configuration

The workflow is defined in `.github/workflows/ci.yml` and includes:

- Matrix testing across Python 3.9-3.12
- Multi-platform testing (Ubuntu, Windows, macOS)
- Artifact collection and retention
- Automated reporting and notifications

## Writing Tests

### Test Structure

Follow this structure for new tests:

```python
"""
Test module docstring explaining what is being tested.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.module_under_test import ClassUnderTest


@pytest.mark.unit  # or integration, performance, etc.
class TestClassUnderTest:
    """Test suite for ClassUnderTest."""
    
    def test_method_name_scenario(self, fixture_name):
        """Test method docstring explaining the scenario."""
        # Arrange
        setup_code()
        
        # Act
        result = method_under_test()
        
        # Assert
        assert result == expected_value
    
    @pytest.mark.asyncio
    async def test_async_method(self, async_fixture):
        """Test async method."""
        result = await async_method_under_test()
        assert result is not None
```

### Test Naming Conventions

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<method_name>_<scenario>`

Examples:
- `test_trading_engine_initialization_success`
- `test_position_manager_close_position_not_found`
- `test_order_manager_create_order_insufficient_balance`

### Using Fixtures

Leverage the comprehensive fixtures in `conftest.py`:

```python
def test_trading_engine_with_mock_strategy(trading_engine, mock_logger):
    """Test using pre-configured fixtures."""
    result = trading_engine.get_trading_status()
    assert isinstance(result, dict)

def test_position_calculation(sample_position):
    """Test using factory-generated test data."""
    pnl = sample_position.calculate_pnl(sample_position.entry_price * 1.01)
    assert pnl > 0
```

### Async Testing

For async code, use `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_async_trading_operation(trading_engine, mock_binance_client):
    """Test async trading operation."""
    result = await trading_engine.process_signals(mock_binance_client)
    assert result is True
```

## Mock Objects

### Available Mock Fixtures

- `mock_binance_client`: Mock Binance API client
- `mock_logger`: Mock logger instance
- `mock_database`: Mock database connection
- `mock_http_responses`: Mock HTTP responses
- `mock_influxdb`: Mock InfluxDB client

### Creating Custom Mocks

```python
from unittest.mock import Mock, AsyncMock, patch

# Simple mock
mock_service = Mock()
mock_service.method.return_value = "expected_result"

# Async mock
async_mock = AsyncMock()
async_mock.async_method.return_value = "async_result"

# Patch decorator
@patch('module.external_dependency')
def test_with_patch(mock_dependency):
    mock_dependency.return_value = "mocked_value"
    # Test code here

# Context manager patch
def test_with_context_patch():
    with patch('module.external_dependency') as mock_dep:
        mock_dep.return_value = "mocked_value"
        # Test code here
```

### Mock Best Practices

1. **Mock at the boundary**: Mock external dependencies, not internal logic
2. **Use realistic data**: Make mock responses realistic
3. **Verify interactions**: Assert that mocks were called correctly
4. **Reset mocks**: Use `mock.reset_mock()` when needed
5. **Avoid over-mocking**: Don't mock everything; test real logic

## Performance Testing

### Writing Performance Tests

```python
@pytest.mark.performance
def test_signal_processing_performance(benchmark, trading_engine):
    """Benchmark signal processing performance."""
    def process_signals():
        return trading_engine.process_multiple_signals(test_data)
    
    result = benchmark(process_signals)
    assert result is not None

@pytest.mark.slow
async def test_memory_usage_stability():
    """Test memory usage over extended operation."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Run operations
    for _ in range(1000):
        await perform_operation()
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Allow some increase but detect leaks
    assert memory_increase < 50 * 1024 * 1024  # 50MB limit
```

### Performance Benchmarks

Use `pytest-benchmark` for performance testing:

```bash
# Run benchmarks
pytest --benchmark-only

# Compare benchmarks
pytest --benchmark-compare=0001

# Save benchmark results
pytest --benchmark-save=baseline
```

## Security Testing

### Security Test Categories

1. **Input Validation**: Test malicious input handling
2. **Authentication**: Test auth mechanisms
3. **Encryption**: Test data protection
4. **Dependencies**: Check for vulnerable packages

### Example Security Tests

```python
@pytest.mark.security
def test_input_sanitization(security_test_data):
    """Test that malicious inputs are properly sanitized."""
    for malicious_input in security_test_data['malicious_inputs']:
        with pytest.raises(ValueError):
            process_user_input(malicious_input)

@pytest.mark.security
def test_api_authentication():
    """Test API authentication mechanisms."""
    # Test with invalid token
    with pytest.raises(AuthenticationError):
        api_client.authenticate("invalid_token")
```

### Security Tools Integration

The CI pipeline includes:

- **Bandit**: Static security analysis
- **Safety**: Dependency vulnerability checking
- **pip-audit**: Package vulnerability scanning

## Troubleshooting

### Common Issues

#### Import Errors

```bash
# Ensure package is installed in development mode
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

#### Async Test Issues

```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Use proper async markers
@pytest.mark.asyncio
async def test_async_function():
    pass
```

#### Coverage Issues

```bash
# Ensure source path is correct
pytest --cov=src --cov-report=term-missing

# Check coverage configuration in pyproject.toml
```

#### Mock Issues

```python
# Reset mocks between tests
@pytest.fixture(autouse=True)
def reset_mocks():
    yield
    mock_object.reset_mock()

# Use proper mock assertions
mock_object.assert_called_once_with(expected_args)
```

### Debug Mode

Run tests in debug mode:

```bash
# Verbose output with debug info
pytest -v -s --tb=long

# Drop into debugger on failure
pytest --pdb

# Debug specific test
pytest tests/unit/test_trading_engine.py::test_specific -v -s
```

### Performance Issues

```bash
# Profile test execution
pytest --durations=10

# Run tests in parallel
pytest -n auto

# Skip slow tests
pytest -m "not slow"
```

### Getting Help

1. Check this documentation
2. Review test examples in the codebase
3. Check pytest documentation: https://docs.pytest.org/
4. Review CI logs for detailed error information
5. Create an issue with detailed error information

## Best Practices Summary

1. **Write tests first**: Follow TDD when possible
2. **Test behavior, not implementation**: Focus on what, not how
3. **Use descriptive names**: Make test intent clear
4. **Keep tests independent**: Tests should not depend on each other
5. **Use appropriate markers**: Categorize tests properly
6. **Mock external dependencies**: Keep tests fast and reliable
7. **Maintain high coverage**: Aim for 90%+ coverage
8. **Review test failures**: Don't ignore failing tests
9. **Update tests with code changes**: Keep tests in sync
10. **Document complex test scenarios**: Explain non-obvious test logic

## Contributing to Tests

When contributing new features:

1. Write tests for new functionality
2. Update existing tests if behavior changes
3. Ensure all tests pass locally
4. Check coverage reports
5. Follow existing test patterns
6. Add appropriate test markers
7. Update documentation if needed

The testing infrastructure is a critical part of maintaining code quality and reliability. Well-written tests help catch bugs early, enable confident refactoring, and serve as documentation for expected behavior. 