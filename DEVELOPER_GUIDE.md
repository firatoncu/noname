# Developer Guide - n0name Trading Bot

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Development Setup](#development-setup)
3. [Code Structure](#code-structure)
4. [Development Workflow](#development-workflow)
5. [Testing Guidelines](#testing-guidelines)
6. [Code Style and Standards](#code-style-and-standards)
7. [Contribution Guidelines](#contribution-guidelines)
8. [API Documentation](#api-documentation)
9. [Debugging and Troubleshooting](#debugging-and-troubleshooting)
10. [Performance Considerations](#performance-considerations)

## Architecture Overview

The n0name trading bot is built using a modular, event-driven architecture that emphasizes:

- **Separation of Concerns**: Each module has a specific responsibility
- **Async/Await Pattern**: Non-blocking operations for high performance
- **Strategy Pattern**: Pluggable trading strategies
- **Dependency Injection**: Loose coupling between components
- **Comprehensive Error Handling**: Structured exception hierarchy
- **Type Safety**: Extensive use of type hints and custom types

### Core Components

```
n0name/
├── src/
│   ├── n0name/           # Core application module
│   │   ├── cli.py        # Command-line interface
│   │   ├── exceptions.py # Exception hierarchy
│   │   ├── types.py      # Type definitions
│   │   └── interfaces/   # Abstract interfaces
│   ├── core/             # Business logic
│   │   ├── trading_engine.py    # Main trading orchestrator
│   │   ├── position_manager.py  # Position management
│   │   ├── order_manager.py     # Order execution
│   │   └── base_strategy.py     # Strategy interface
│   ├── strategies/       # Trading strategies
│   ├── indicators/       # Technical indicators
│   ├── utils/           # Utility functions
│   └── monitoring/      # System monitoring
├── auth/                # Authentication and security
├── config/              # Configuration management
├── tests/               # Test suite
└── utils/               # Shared utilities
```

### Data Flow

1. **Market Data Ingestion**: Real-time data from Binance API
2. **Signal Generation**: Strategies analyze data and generate signals
3. **Risk Management**: Positions and orders are validated
4. **Order Execution**: Orders are placed through the exchange
5. **Position Monitoring**: Continuous monitoring of open positions
6. **Logging and Analytics**: All activities are logged and analyzed

## Development Setup

### Prerequisites

- Python 3.9+
- Node.js 16+ (for frontend)
- Git
- Docker (optional, for containerized development)

### Environment Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd noname
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

5. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

6. **Setup database** (if using InfluxDB):
   ```bash
   # Follow MONITORING_SYSTEM_GUIDE.md for database setup
   ```

### IDE Configuration

#### VS Code
Recommended extensions:
- Python
- Pylance
- Black Formatter
- isort
- mypy

#### PyCharm
- Enable type checking
- Configure Black as formatter
- Setup pytest as test runner

## Code Structure

### Module Organization

#### `src/n0name/` - Core Application
- **`types.py`**: Type definitions and validators
- **`exceptions.py`**: Exception hierarchy and error handling
- **`cli.py`**: Command-line interface
- **`interfaces/`**: Abstract base classes and protocols

#### `src/core/` - Business Logic
- **`trading_engine.py`**: Main trading orchestrator
- **`position_manager.py`**: Position lifecycle management
- **`order_manager.py`**: Order execution and management
- **`base_strategy.py`**: Strategy interface and base implementation

#### `src/strategies/` - Trading Strategies
- Strategy implementations following the Strategy pattern
- Each strategy inherits from `BaseStrategy`

#### `src/indicators/` - Technical Indicators
- Technical analysis indicators
- Reusable indicator calculations

#### `utils/` - Utilities
- **`enhanced_logging.py`**: Structured logging
- **`config/`**: Configuration management
- **`web_ui/`**: Web interface components

### Design Patterns Used

1. **Strategy Pattern**: For trading strategies
2. **Observer Pattern**: For event handling
3. **Factory Pattern**: For creating components
4. **Dependency Injection**: For loose coupling
5. **Command Pattern**: For order execution
6. **State Pattern**: For position states

## Development Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: Feature development
- `hotfix/*`: Critical fixes
- `release/*`: Release preparation

### Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Pull Request Process

1. Create feature branch from `develop`
2. Implement changes with tests
3. Update documentation
4. Run full test suite
5. Create pull request
6. Code review and approval
7. Merge to `develop`

## Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
├── fixtures/      # Test data
└── conftest.py    # Pytest configuration
```

### Writing Tests

#### Unit Tests
```python
import pytest
from unittest.mock import Mock, patch
from src.core.trading_engine import TradingEngine

class TestTradingEngine:
    @pytest.fixture
    def trading_engine(self):
        strategy = Mock()
        return TradingEngine(strategy)
    
    async def test_initialize_success(self, trading_engine):
        # Test implementation
        pass
    
    async def test_initialize_failure(self, trading_engine):
        # Test error handling
        pass
```

#### Integration Tests
```python
@pytest.mark.integration
async def test_trading_workflow():
    # Test complete trading workflow
    pass
```

### Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test type
pytest tests/unit/
pytest tests/integration/

# Run with markers
pytest -m "not slow"
```

## Code Style and Standards

### Python Style Guide

Follow [PEP 8](https://pep8.org/) with these additions:

#### Formatting
- Use Black for code formatting
- Line length: 88 characters
- Use double quotes for strings
- Use trailing commas in multi-line structures

#### Type Hints
```python
from typing import Dict, List, Optional, Union
from src.n0name.types import Symbol, Price, Quantity

def calculate_position_size(
    symbol: Symbol,
    price: Price,
    risk_percentage: float,
    account_balance: Quantity
) -> Optional[Quantity]:
    """
    Calculate position size based on risk management rules.
    
    Args:
        symbol: Trading symbol
        price: Current price
        risk_percentage: Risk as percentage of account
        account_balance: Available account balance
        
    Returns:
        Calculated position size or None if invalid
        
    Raises:
        ValidationException: If parameters are invalid
    """
    # Implementation
    pass
```

#### Docstring Format
Use Google-style docstrings:

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    Brief description of the function.
    
    Longer description if needed. Explain the purpose,
    behavior, and any important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: Description of when this exception is raised
        
    Example:
        >>> result = function_name("value1", 42)
        >>> print(result)
        expected_output
    """
    pass
```

#### Error Handling
```python
from src.n0name.exceptions import TradingException, ErrorCategory, ErrorSeverity

try:
    # Risky operation
    result = await risky_operation()
except Exception as e:
    raise TradingException(
        "Operation failed",
        category=ErrorCategory.TRADING,
        severity=ErrorSeverity.HIGH,
        original_exception=e
    )
```

### Code Quality Tools

#### Linting and Formatting
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Security check
bandit -r src/
```

#### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
```

## Contribution Guidelines

### Getting Started

1. **Fork the repository**
2. **Create a feature branch**
3. **Set up development environment**
4. **Make your changes**
5. **Add tests**
6. **Update documentation**
7. **Submit pull request**

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Type hints are provided
- [ ] Error handling is appropriate
- [ ] Performance impact is considered
- [ ] Security implications are reviewed

### Documentation Requirements

- Update relevant `.md` files
- Add docstrings to new functions/classes
- Update API documentation
- Add examples for new features

## API Documentation

### Core APIs

#### Trading Engine API
```python
from src.core.trading_engine import TradingEngine, TradingConfig

# Initialize trading engine
config = TradingConfig(
    max_open_positions=5,
    leverage=10,
    position_value_percentage=0.2
)
engine = TradingEngine(strategy, config)

# Start trading
await engine.initialize(symbols, client, logger)
await engine.start_trading(client, logger)
```

#### Strategy API
```python
from src.core.base_strategy import BaseStrategy, MarketData, SignalType

class CustomStrategy(BaseStrategy):
    async def generate_signals(self, market_data: MarketData) -> Dict[str, Any]:
        # Strategy implementation
        return {
            "buy_signal": True,
            "sell_signal": False,
            "confidence": 0.8
        }
```

### REST API Endpoints

The web interface provides REST API endpoints:

- `GET /api/status` - Get trading status
- `GET /api/positions` - Get open positions
- `POST /api/strategy/switch` - Switch trading strategy
- `POST /api/trading/start` - Start trading
- `POST /api/trading/stop` - Stop trading

## Debugging and Troubleshooting

### Logging

The application uses structured logging:

```python
from utils.enhanced_logging import get_logger, ErrorCategory, LogSeverity

logger = get_logger(__name__)

# Different log levels
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", category=ErrorCategory.TRADING, severity=LogSeverity.HIGH)
logger.audit("Audit trail", extra={"user_id": "123", "action": "trade"})
```

### Common Issues

#### Connection Issues
- Check API keys and permissions
- Verify network connectivity
- Check rate limits

#### Trading Issues
- Verify account balance
- Check symbol precision
- Validate order parameters

#### Performance Issues
- Monitor memory usage
- Check async task management
- Review database queries

### Debug Mode

Enable debug mode in configuration:

```yaml
# config.yml
debug:
  enabled: true
  log_level: DEBUG
  detailed_errors: true
```

## Performance Considerations

### Async Programming

- Use `asyncio` for I/O operations
- Avoid blocking operations in async functions
- Use connection pooling for database/API calls

### Memory Management

- Monitor memory usage with large datasets
- Use generators for large data processing
- Clean up resources properly

### Database Optimization

- Use appropriate indexes
- Batch database operations
- Monitor query performance

### Monitoring

- Use performance decorators
- Monitor key metrics
- Set up alerts for anomalies

```python
from utils.enhanced_logging import log_performance

@log_performance()
async def expensive_operation():
    # Operation implementation
    pass
```

---

For more specific guides, see:
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Comprehensive testing documentation
- [SECURITY.md](SECURITY.md) - Security guidelines
- [PERFORMANCE_OPTIMIZATION_GUIDE.md](PERFORMANCE_OPTIMIZATION_GUIDE.md) - Performance optimization
- [MONITORING_SYSTEM_GUIDE.md](MONITORING_SYSTEM_GUIDE.md) - Monitoring and observability 