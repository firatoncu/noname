# Enhanced Logging and Exception Handling Migration Guide

This guide provides step-by-step instructions for migrating the existing codebase to use the new enhanced logging system and custom exception handling framework.

## Overview

The enhanced system provides:
- **Structured logging** with JSON format and multiple log levels
- **Log rotation** with size and time-based rotation
- **Error categorization** and severity levels
- **Custom exception classes** with recovery mechanisms
- **Performance monitoring** and metrics
- **Context-aware logging** with correlation IDs
- **Automatic retry mechanisms** and circuit breakers

## 1. Enhanced Logging System

### 1.1 Basic Migration

Replace existing logging imports:

```python
# OLD
from utils.app_logging import error_logger_func, logger_func

# NEW
from utils.enhanced_logging import get_logger, ErrorCategory, LogSeverity
```

### 1.2 Logger Initialization

```python
# OLD
logger = error_logger_func()

# NEW
logger = get_logger("trading_engine")  # Use descriptive names
```

### 1.3 Basic Logging

```python
# OLD
logger.error(f"Error in main loop: {e}")

# NEW
logger.error(
    "Error in main loop",
    category=ErrorCategory.TRADING,
    severity=LogSeverity.HIGH,
    extra={"symbol": symbol, "operation": "main_loop"}
)
```

### 1.4 Context-Aware Logging

```python
# Use context managers for related operations
with logger.context(symbol="BTCUSDT", strategy="bollinger_rsi"):
    logger.info("Starting position analysis")
    # All logs within this context will include symbol and strategy
    logger.warning("Low volume detected")
    logger.info("Position analysis completed")
```

### 1.5 Performance Logging

```python
# Using decorator
from utils.enhanced_logging import log_performance

@log_performance()
async def fetch_market_data(symbol: str):
    # Function implementation
    pass

# Manual performance logging
start_time = time.time()
result = await some_operation()
duration = time.time() - start_time
logger.performance("market_data_fetch", duration, symbol=symbol, records=len(result))
```

### 1.6 Exception Logging

```python
# OLD
try:
    result = await risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")

# NEW
try:
    result = await risky_operation()
except Exception as e:
    logger.exception(
        "Operation failed",
        category=ErrorCategory.API,
        severity=LogSeverity.HIGH,
        extra={"operation": "risky_operation", "symbol": symbol}
    )
```

## 2. Custom Exception Handling

### 2.1 Import Custom Exceptions

```python
from utils.exceptions import (
    TradingBotException,
    NetworkException,
    APIException,
    TradingException,
    DataValidationException,
    RecoveryManager,
    handle_exceptions,
    create_error_context
)
```

### 2.2 Replace Generic Exceptions

```python
# OLD
if balance < required_amount:
    raise ValueError("Insufficient balance")

# NEW
from utils.exceptions import InsufficientBalanceException

if balance < required_amount:
    raise InsufficientBalanceException(
        "Insufficient balance for trade",
        required_amount=required_amount,
        available_amount=balance,
        context=create_error_context(
            component="position_manager",
            operation="open_position",
            symbol=symbol
        )
    )
```

### 2.3 Network and API Error Handling

```python
# OLD
try:
    response = await client.get_account()
except Exception as e:
    logger.error(f"API call failed: {e}")
    return None

# NEW
try:
    response = await client.get_account()
except ConnectionError as e:
    raise NetworkException(
        "Failed to connect to Binance API",
        context=create_error_context(
            component="api_client",
            operation="get_account"
        ),
        original_exception=e
    )
except Exception as e:
    raise APIException(
        "API call failed",
        api_endpoint="/api/v3/account",
        context=create_error_context(
            component="api_client",
            operation="get_account"
        ),
        original_exception=e
    )
```

### 2.4 Using Exception Decorators

```python
from utils.exceptions import handle_exceptions, RecoveryManager

# Automatic exception handling with recovery
@handle_exceptions(
    recovery_manager=RecoveryManager(logger),
    fallback_value=None
)
async def fetch_market_data(symbol: str):
    # This function will automatically handle exceptions
    # and attempt recovery based on exception type
    pass
```

### 2.5 Data Validation

```python
from utils.exceptions import validate_data, DataValidationException

@validate_data({
    'symbol': lambda x: isinstance(x, str) and len(x) > 0,
    'quantity': lambda x: isinstance(x, (int, float)) and x > 0,
    'price': lambda x: isinstance(x, (int, float)) and x > 0
})
def create_order(symbol: str, quantity: float, price: float):
    # Function implementation
    pass
```

## 3. Migration Examples by Component

### 3.1 Trading Engine Migration

```python
# src/core/trading_engine.py

from utils.enhanced_logging import get_logger, ErrorCategory, LogSeverity
from utils.exceptions import (
    TradingException, 
    DataValidationException,
    handle_exceptions,
    create_error_context
)

class TradingEngine:
    def __init__(self, strategy, config=None):
        self.logger = get_logger("trading_engine")
        self.strategy = strategy
        # ... rest of initialization
    
    @handle_exceptions(fallback_value=False)
    async def process_symbol_signals(self, symbol: str, client, logger):
        with self.logger.context(symbol=symbol, component="trading_engine"):
            try:
                self.logger.info("Processing signals for symbol")
                
                # Validate inputs
                if not symbol or not isinstance(symbol, str):
                    raise DataValidationException(
                        "Invalid symbol provided",
                        field_name="symbol",
                        actual_value=symbol,
                        context=create_error_context(
                            component="trading_engine",
                            operation="process_symbol_signals"
                        )
                    )
                
                # Process signals
                result = await self._process_signals(symbol, client)
                
                self.logger.info("Signal processing completed successfully")
                return result
                
            except TradingException as e:
                self.logger.error(
                    "Trading error occurred",
                    category=ErrorCategory.TRADING,
                    severity=LogSeverity.HIGH,
                    extra=e.to_dict()
                )
                raise
            except Exception as e:
                self.logger.exception(
                    "Unexpected error in signal processing",
                    category=ErrorCategory.SYSTEM,
                    severity=LogSeverity.CRITICAL
                )
                raise TradingException(
                    "Signal processing failed",
                    original_exception=e,
                    context=create_error_context(
                        component="trading_engine",
                        operation="process_symbol_signals",
                        symbol=symbol
                    )
                )
```

### 3.2 API Client Migration

```python
# utils/api_client.py

from utils.enhanced_logging import get_logger, ErrorCategory, LogSeverity
from utils.exceptions import (
    NetworkException,
    APIException,
    RateLimitException,
    AuthenticationException,
    handle_exceptions
)

class BinanceClient:
    def __init__(self):
        self.logger = get_logger("binance_client")
    
    @handle_exceptions()
    async def get_account_info(self):
        with self.logger.context(component="binance_client", operation="get_account_info"):
            try:
                self.logger.debug("Fetching account information")
                
                response = await self._make_request("/api/v3/account")
                
                self.logger.info("Account information retrieved successfully")
                return response
                
            except aiohttp.ClientTimeout as e:
                raise NetworkException(
                    "Request timeout while fetching account info",
                    original_exception=e
                )
            except aiohttp.ClientResponseError as e:
                if e.status == 429:
                    raise RateLimitException(
                        "Rate limit exceeded",
                        retry_after=int(e.headers.get('Retry-After', 60))
                    )
                elif e.status == 401:
                    raise AuthenticationException(
                        "Invalid API credentials"
                    )
                else:
                    raise APIException(
                        f"API request failed with status {e.status}",
                        api_endpoint="/api/v3/account",
                        status_code=e.status
                    )
```

### 3.3 Main Application Migration

```python
# n0name.py

from utils.enhanced_logging import get_logger, ErrorCategory, LogSeverity
from utils.exceptions import (
    TradingBotException,
    SystemException,
    ConfigurationException,
    handle_exceptions,
    RecoveryManager
)

async def main():
    # Initialize enhanced logger
    logger = get_logger("main_application")
    recovery_manager = RecoveryManager(logger)
    
    with logger.context(component="main_application"):
        try:
            logger.info("Starting trading bot application")
            
            # Load configuration with validation
            config = await load_and_validate_config()
            
            # Initialize components
            client = await initialize_binance_client(config)
            
            logger.audit("Trading bot started successfully")
            
            # Main trading loop
            while True:
                try:
                    await trading_iteration(client, logger)
                    await asyncio.sleep(1)
                    
                except TradingBotException as e:
                    # Use recovery manager for known exceptions
                    await recovery_manager.handle_exception(
                        e, trading_iteration, client, logger
                    )
                    
                except Exception as e:
                    logger.exception(
                        "Unexpected error in main loop",
                        category=ErrorCategory.SYSTEM,
                        severity=LogSeverity.CRITICAL
                    )
                    break
                    
        except ConfigurationException as e:
            logger.critical(
                "Configuration error - cannot start application",
                category=ErrorCategory.CONFIGURATION,
                severity=LogSeverity.CRITICAL,
                extra=e.to_dict()
            )
            sys.exit(1)
            
        except Exception as e:
            logger.critical(
                "Fatal error during startup",
                category=ErrorCategory.SYSTEM,
                severity=LogSeverity.CRITICAL
            )
            sys.exit(1)
            
        finally:
            logger.audit("Trading bot shutdown completed")
            await cleanup_resources()

if __name__ == "__main__":
    asyncio.run(main())
```

## 4. Configuration

### 4.1 Logger Configuration

Create a logger configuration file:

```python
# config/logging_config.py

LOGGING_CONFIG = {
    "main_application": {
        "log_dir": "logs",
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "backup_count": 5,
        "enable_console": True,
        "enable_json": True,
        "enable_rotation": True
    },
    "trading_engine": {
        "log_dir": "logs/trading",
        "max_file_size": 5 * 1024 * 1024,   # 5MB
        "backup_count": 10,
        "enable_console": False,
        "enable_json": True,
        "enable_rotation": True
    },
    "api_client": {
        "log_dir": "logs/api",
        "max_file_size": 20 * 1024 * 1024,  # 20MB
        "backup_count": 3,
        "enable_console": False,
        "enable_json": True,
        "enable_rotation": True
    }
}
```

### 4.2 Exception Recovery Configuration

```python
# config/recovery_config.py

from utils.exceptions import RetryConfig, RecoveryAction

RECOVERY_CONFIG = {
    "network_errors": RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True,
        backoff_strategy="exponential"
    ),
    "api_errors": RetryConfig(
        max_attempts=5,
        base_delay=2.0,
        max_delay=60.0,
        exponential_base=1.5,
        jitter=True,
        backoff_strategy="exponential"
    ),
    "trading_errors": RetryConfig(
        max_attempts=2,
        base_delay=5.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=False,
        backoff_strategy="linear"
    )
}
```

## 5. Testing the Migration

### 5.1 Test Logging

```python
# tests/test_logging.py

import pytest
from utils.enhanced_logging import get_logger, ErrorCategory, LogSeverity

def test_enhanced_logging():
    logger = get_logger("test_logger")
    
    # Test basic logging
    logger.info("Test info message")
    logger.warning("Test warning message")
    logger.error("Test error message", category=ErrorCategory.TESTING)
    
    # Test context logging
    with logger.context(test_id="123", component="test"):
        logger.info("Message with context")
    
    # Test performance logging
    logger.performance("test_operation", 0.5, records=100)
    
    # Verify metrics
    metrics = logger.get_metrics()
    assert metrics['total_logs'] > 0
```

### 5.2 Test Exception Handling

```python
# tests/test_exceptions.py

import pytest
from utils.exceptions import (
    TradingBotException,
    NetworkException,
    handle_exceptions,
    RecoveryManager
)

def test_custom_exceptions():
    # Test exception creation
    exc = NetworkException("Test network error")
    assert exc.severity.value == "high"
    assert exc.recovery_action.value == "retry"
    
    # Test exception dictionary conversion
    exc_dict = exc.to_dict()
    assert exc_dict['error_type'] == 'NetworkException'
    assert exc_dict['message'] == 'Test network error'

@pytest.mark.asyncio
async def test_exception_handling():
    @handle_exceptions(fallback_value="fallback")
    async def failing_function():
        raise NetworkException("Test error")
    
    result = await failing_function()
    # Should return fallback value due to exception handling
    assert result == "fallback"
```

## 6. Monitoring and Metrics

### 6.1 Log Metrics Dashboard

```python
# utils/log_metrics.py

from utils.enhanced_logging import get_logger

def get_application_metrics():
    """Get comprehensive logging metrics"""
    loggers = ["main_application", "trading_engine", "api_client"]
    metrics = {}
    
    for logger_name in loggers:
        logger = get_logger(logger_name)
        metrics[logger_name] = logger.get_metrics()
    
    return metrics

def print_metrics_summary():
    """Print a summary of logging metrics"""
    metrics = get_application_metrics()
    
    print("=== Logging Metrics Summary ===")
    for logger_name, logger_metrics in metrics.items():
        print(f"\n{logger_name}:")
        print(f"  Total logs: {logger_metrics['total_logs']}")
        print(f"  Errors: {logger_metrics['error_count']}")
        print(f"  Warnings: {logger_metrics['warning_count']}")
        print(f"  Critical: {logger_metrics['critical_count']}")
        
        if logger_metrics['errors_by_category']:
            print("  Errors by category:")
            for category, count in logger_metrics['errors_by_category'].items():
                print(f"    {category}: {count}")
```

## 7. Best Practices

### 7.1 Logging Best Practices

1. **Use descriptive logger names**: `get_logger("trading_engine")` instead of `get_logger()`
2. **Include context**: Use context managers for related operations
3. **Categorize errors**: Always specify error category and severity
4. **Log performance**: Use performance logging for critical operations
5. **Structured data**: Include relevant data in the `extra` parameter

### 7.2 Exception Handling Best Practices

1. **Use specific exceptions**: Prefer `InsufficientBalanceException` over generic `Exception`
2. **Include context**: Always provide error context with relevant information
3. **Chain exceptions**: Use `original_exception` parameter to preserve the original error
4. **Recovery strategies**: Choose appropriate recovery actions for each exception type
5. **Validation**: Use validation decorators for input validation

### 7.3 Migration Checklist

- [ ] Replace all `error_logger_func()` calls with `get_logger()`
- [ ] Add error categorization to all error logs
- [ ] Replace generic exceptions with custom exception classes
- [ ] Add context managers for related operations
- [ ] Implement performance logging for critical functions
- [ ] Add exception handling decorators where appropriate
- [ ] Update configuration to use new logging settings
- [ ] Test logging and exception handling in development
- [ ] Monitor metrics in production
- [ ] Update documentation and team training

## 8. Rollback Plan

If issues arise during migration:

1. **Immediate rollback**: Keep the old `utils/app_logging.py` file as backup
2. **Gradual migration**: Migrate one component at a time
3. **Compatibility layer**: The new system provides backward compatibility functions
4. **Monitoring**: Monitor error rates and performance during migration
5. **Testing**: Thoroughly test each migrated component before moving to the next

## 9. Support and Troubleshooting

### Common Issues:

1. **Import errors**: Ensure all new modules are properly imported
2. **Context issues**: Make sure context managers are properly closed
3. **Performance impact**: Monitor logging performance in production
4. **File permissions**: Ensure log directory has proper write permissions
5. **Disk space**: Monitor disk usage with log rotation enabled

### Getting Help:

- Check the enhanced logging module documentation
- Review exception handling examples
- Test in development environment first
- Monitor application metrics during migration
