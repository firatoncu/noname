# Contributing to n0name Trading Bot

Thank you for your interest in contributing to the n0name trading bot! This document provides guidelines and information for contributors.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Contribution Workflow](#contribution-workflow)
5. [Coding Standards](#coding-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Documentation Guidelines](#documentation-guidelines)
8. [Pull Request Process](#pull-request-process)
9. [Issue Reporting](#issue-reporting)
10. [Security Considerations](#security-considerations)

## Code of Conduct

### Our Pledge

We are committed to making participation in this project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team. All complaints will be reviewed and investigated promptly and fairly.

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.9 or higher
- Git
- Node.js 16+ (for frontend development)
- Basic understanding of:
  - Async/await programming in Python
  - Trading concepts and financial markets
  - REST APIs and WebSocket connections

### Areas for Contribution

We welcome contributions in the following areas:

1. **Core Trading Logic**
   - New trading strategies
   - Risk management improvements
   - Performance optimizations

2. **Infrastructure**
   - Monitoring and alerting
   - Database optimizations
   - Security enhancements

3. **User Interface**
   - Web interface improvements
   - Mobile responsiveness
   - Data visualization

4. **Documentation**
   - API documentation
   - User guides
   - Code examples

5. **Testing**
   - Unit tests
   - Integration tests
   - Performance tests

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/noname.git
cd noname

# Add the original repository as upstream
git remote add upstream https://github.com/ORIGINAL_OWNER/noname.git
```

### 2. Environment Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Configuration

```bash
# Copy example configuration
cp env.example .env

# Edit .env with your settings (use testnet for development)
# Never commit real API keys or sensitive data
```

### 4. Verify Setup

```bash
# Run tests to verify setup
pytest tests/

# Run linting
flake8 src/
black --check src/
mypy src/

# Start the application in development mode
python n0name.py --debug
```

## Contribution Workflow

### 1. Create a Feature Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write clean, well-documented code
- Follow the coding standards (see below)
- Add tests for new functionality
- Update documentation as needed

### 3. Commit Changes

We use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages:

```bash
# Examples of good commit messages
git commit -m "feat: add MACD strategy implementation"
git commit -m "fix: resolve position calculation bug"
git commit -m "docs: update API documentation"
git commit -m "test: add unit tests for order manager"
```

### 4. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
```

## Coding Standards

### Python Code Style

We follow [PEP 8](https://pep8.org/) with these specific guidelines:

#### Formatting
- Use Black for code formatting (line length: 88 characters)
- Use isort for import sorting
- Use double quotes for strings
- Use trailing commas in multi-line structures

#### Type Hints
All functions must have type hints:

```python
from typing import Dict, List, Optional, Union
from src.n0name.types import Symbol, Price, Quantity

def calculate_position_size(
    symbol: Symbol,
    price: Price,
    risk_percentage: float,
    account_balance: Quantity
) -> Optional[Quantity]:
    """Calculate position size based on risk management rules."""
    # Implementation here
    pass
```

#### Docstrings
Use Google-style docstrings for all public functions and classes:

```python
def process_market_data(
    data: Dict[str, Any], 
    symbol: str
) -> MarketData:
    """
    Process raw market data into structured format.
    
    This function takes raw market data from the exchange API and converts
    it into a standardized MarketData object for strategy analysis.
    
    Args:
        data: Raw market data from exchange API
        symbol: Trading symbol (e.g., "BTCUSDT")
        
    Returns:
        MarketData: Processed market data object
        
    Raises:
        ValidationException: If data format is invalid
        
    Example:
        >>> raw_data = {"close": 45000, "volume": 1000}
        >>> market_data = process_market_data(raw_data, "BTCUSDT")
        >>> print(market_data.close_price)
        45000.0
    """
    # Implementation here
    pass
```

#### Error Handling
Use the custom exception hierarchy:

```python
from src.n0name.exceptions import TradingException, ErrorCategory, ErrorSeverity

try:
    result = risky_operation()
except Exception as e:
    raise TradingException(
        "Operation failed",
        category=ErrorCategory.TRADING,
        severity=ErrorSeverity.HIGH,
        original_exception=e,
        recoverable=True,
        retry_after=30
    )
```

#### Async/Await
- Use async/await for all I/O operations
- Avoid blocking operations in async functions
- Use proper exception handling in async code

```python
async def fetch_market_data(symbol: str, client: AsyncClient) -> MarketData:
    """Fetch market data asynchronously."""
    try:
        response = await client.get_klines(symbol=symbol, interval="1m")
        return process_response(response)
    except Exception as e:
        logger.error(f"Failed to fetch data for {symbol}: {e}")
        raise
```

### File Organization

```
src/
├── n0name/              # Core application
│   ├── __init__.py
│   ├── types.py         # Type definitions
│   ├── exceptions.py    # Exception hierarchy
│   └── interfaces/      # Abstract interfaces
├── core/                # Business logic
│   ├── trading_engine.py
│   ├── position_manager.py
│   └── order_manager.py
├── strategies/          # Trading strategies
├── indicators/          # Technical indicators
└── utils/              # Utility functions
```

### Naming Conventions

- **Classes**: PascalCase (`TradingEngine`, `PositionManager`)
- **Functions/Methods**: snake_case (`calculate_position_size`, `get_market_data`)
- **Variables**: snake_case (`current_price`, `order_id`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_POSITIONS`, `DEFAULT_LEVERAGE`)
- **Files/Modules**: snake_case (`trading_engine.py`, `market_data.py`)

## Testing Guidelines

### Test Structure

```
tests/
├── unit/               # Unit tests
│   ├── test_trading_engine.py
│   ├── test_strategies.py
│   └── test_utils.py
├── integration/        # Integration tests
│   ├── test_api_integration.py
│   └── test_database_integration.py
├── e2e/               # End-to-end tests
│   └── test_trading_workflow.py
├── fixtures/          # Test data
│   ├── market_data.json
│   └── config_samples.yml
└── conftest.py        # Pytest configuration
```

### Writing Tests

#### Unit Tests
```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.core.trading_engine import TradingEngine

class TestTradingEngine:
    @pytest.fixture
    def mock_strategy(self):
        strategy = Mock()
        strategy.generate_signals = AsyncMock(return_value={
            "buy_signal": True,
            "confidence": 0.8
        })
        return strategy
    
    @pytest.fixture
    def trading_engine(self, mock_strategy):
        return TradingEngine(mock_strategy)
    
    async def test_initialize_success(self, trading_engine):
        """Test successful initialization."""
        symbols = ["BTCUSDT", "ETHUSDT"]
        client = AsyncMock()
        logger = Mock()
        
        await trading_engine.initialize(symbols, client, logger)
        
        assert trading_engine._symbols == symbols
        assert trading_engine._is_running is False
    
    async def test_initialize_failure(self, trading_engine):
        """Test initialization failure handling."""
        with pytest.raises(SystemException):
            await trading_engine.initialize([], None, None)
```

#### Integration Tests
```python
@pytest.mark.integration
async def test_complete_trading_workflow():
    """Test complete trading workflow from signal to execution."""
    # Setup test environment
    config = load_test_config()
    client = create_test_client()
    
    # Execute workflow
    result = await execute_trading_cycle(config, client)
    
    # Verify results
    assert result.success is True
    assert len(result.orders) > 0
```

### Test Coverage

- Maintain minimum 80% test coverage
- All new features must include tests
- Critical paths require 100% coverage

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html
```

## Documentation Guidelines

### Code Documentation

1. **Docstrings**: All public functions, classes, and modules must have docstrings
2. **Type Hints**: All function parameters and return values must be typed
3. **Inline Comments**: Use sparingly, only for complex logic
4. **Examples**: Include usage examples in docstrings

### API Documentation

When adding new APIs:

1. Update `API_DOCUMENTATION.md`
2. Include request/response examples
3. Document error conditions
4. Add usage examples

### User Documentation

For user-facing features:

1. Update relevant guides in the docs folder
2. Add screenshots for UI changes
3. Include configuration examples
4. Update the main README if needed

## Pull Request Process

### Before Submitting

1. **Run all checks locally**:
   ```bash
   # Code formatting
   black src/ tests/
   isort src/ tests/
   
   # Linting
   flake8 src/ tests/
   mypy src/
   
   # Tests
   pytest tests/
   
   # Security check
   bandit -r src/
   ```

2. **Update documentation**:
   - Add/update docstrings
   - Update API documentation
   - Update user guides if needed

3. **Add tests**:
   - Unit tests for new functions
   - Integration tests for new features
   - Update existing tests if needed

### Pull Request Template

When creating a pull request, include:

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No breaking changes (or clearly documented)
```

### Review Process

1. **Automated Checks**: All CI checks must pass
2. **Code Review**: At least one maintainer review required
3. **Testing**: Reviewer will test functionality
4. **Documentation**: Verify documentation is complete and accurate

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Bug Description**
Clear description of the bug.

**Steps to Reproduce**
1. Step one
2. Step two
3. Step three

**Expected Behavior**
What should happen.

**Actual Behavior**
What actually happens.

**Environment**
- OS: [e.g., Windows 10, Ubuntu 20.04]
- Python version: [e.g., 3.9.7]
- Bot version: [e.g., 2.0.0]

**Additional Context**
Any other relevant information.
```

### Feature Requests

Use the feature request template:

```markdown
**Feature Description**
Clear description of the proposed feature.

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should this feature work?

**Alternatives Considered**
Other approaches you've considered.

**Additional Context**
Any other relevant information.
```

## Security Considerations

### Security Guidelines

1. **Never commit sensitive data**:
   - API keys
   - Private keys
   - Passwords
   - Personal information

2. **Use environment variables** for configuration
3. **Validate all inputs** from external sources
4. **Use secure communication** (HTTPS, WSS)
5. **Follow principle of least privilege**

### Reporting Security Issues

For security vulnerabilities:

1. **Do not** create public issues
2. Email security concerns to: [security@example.com]
3. Include detailed description and reproduction steps
4. Allow time for fix before public disclosure

### Security Review

All contributions involving:
- Authentication/authorization
- Cryptography
- External API integration
- File system access
- Network communication

Will receive additional security review.

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Discord**: Real-time chat (link in README)
- **Email**: Direct contact for sensitive issues

### Resources

- [Developer Guide](DEVELOPER_GUIDE.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Testing Guide](TESTING_GUIDE.md)

## Recognition

Contributors will be recognized in:

- `CONTRIBUTORS.md` file
- Release notes for significant contributions
- Annual contributor highlights

Thank you for contributing to the n0name trading bot! 🚀 