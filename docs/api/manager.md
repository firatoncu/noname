# Advanced API Manager for Binance Trading

## Overview

This implementation provides a sophisticated rate limiting system for Binance API calls that replaces the current sleep-based approach. The `APIManager` class handles request queuing, rate limit tracking, weight management, and automatic backoff strategies to optimize API usage efficiency.

## Key Features

### 🚀 Advanced Rate Limiting
- **Weight-based tracking**: Each endpoint has specific weights that count against Binance rate limits
- **Multiple time windows**: Tracks requests per second, minute, and day
- **Endpoint-specific limits**: Different limits for orders, market data, and account endpoints
- **Real-time monitoring**: Continuous tracking of rate limit usage

### 📋 Request Queuing with Priority
- **Priority levels**: CRITICAL, HIGH, NORMAL, LOW
- **Intelligent queuing**: Automatic queuing when rate limits are reached
- **Timeout handling**: Requests timeout if queued too long
- **Fair scheduling**: Higher priority requests are processed first

### 🔄 Automatic Backoff Strategies
- **Multiple strategies**: Exponential, Linear, Fibonacci, Adaptive
- **Circuit breaker**: Automatically stops requests when too many failures occur
- **Adaptive throttling**: Adjusts request rate based on success rate
- **Smart recovery**: Automatic recovery from rate limit violations

### ⚡ Request Batching and Optimization
- **Batch processing**: Multiple requests can be processed together
- **Worker pool**: Configurable number of workers for concurrent processing
- **Connection pooling**: Optimized HTTP connections with keep-alive
- **Request optimization**: Intelligent request scheduling

### 📊 Performance Monitoring
- **Real-time metrics**: Success rates, response times, queue sizes
- **Performance tracking**: Historical data and trend analysis
- **Alerting**: Automatic detection of performance issues
- **Debugging support**: Detailed logging and metrics

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Trading Bot   │───▶│   API Manager    │───▶│  Binance API    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Rate Limiter    │
                    │  - Weight Track  │
                    │  - Time Windows  │
                    │  - Circuit Break │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Request Queue    │
                    │  - Priority      │
                    │  - FIFO/Priority │
                    │  - Timeout       │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Worker Pool     │
                    │  - Concurrent    │
                    │  - HTTP Client   │
                    │  - Retry Logic   │
                    └──────────────────┘
```

## Installation

1. **Copy the APIManager files**:
   ```bash
   cp utils/api_manager.py /path/to/your/project/utils/
   ```

2. **Install dependencies** (if not already installed):
   ```bash
   pip install aiohttp asyncio
   ```

3. **Update your imports**:
   ```python
   from utils.api_manager import initialize_api_manager, get_api_manager
   ```

## Quick Start

### Basic Usage

```python
import asyncio
from utils.api_manager import initialize_api_manager, RateLimitConfig

async def main():
    # Initialize API Manager
    config = RateLimitConfig(
        requests_per_minute=1000,
        orders_per_second=8,
        enable_adaptive_throttling=True
    )
    
    api_manager = initialize_api_manager(
        api_key="your_api_key",
        api_secret="your_api_secret",
        config=config
    )
    
    # Start the manager
    await api_manager.start(num_workers=5)
    
    try:
        # Make API calls
        account_info = await api_manager.get_account_info()
        positions = await api_manager.get_position_info()
        
        # Create orders with priority
        order = await api_manager.create_order(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity=0.001
        )
        
    finally:
        # Clean shutdown
        await api_manager.stop()

asyncio.run(main())
```

### Advanced Configuration

```python
from utils.api_manager import RateLimitConfig, BackoffStrategy

# High-frequency trading configuration
config = RateLimitConfig(
    # Conservative rate limits
    requests_per_minute=1000,
    orders_per_second=8,
    weight_per_minute=1000,
    weight_per_second=40,
    
    # Adaptive backoff
    backoff_strategy=BackoffStrategy.ADAPTIVE,
    initial_backoff=0.5,
    max_backoff=120.0,
    
    # Circuit breaker
    failure_threshold=3,
    recovery_timeout=30.0,
    
    # Large queue for bursts
    max_queue_size=20000,
    queue_timeout=45.0,
    
    # Adaptive throttling
    enable_adaptive_throttling=True,
    target_success_rate=0.97,
    monitoring_window=100
)
```

## API Reference

### Core Classes

#### `APIManager`
Main class for managing API requests.

**Methods:**
- `start(num_workers=5)`: Start the API manager
- `stop()`: Stop the API manager
- `request(method, endpoint, params, signed, request_type, priority)`: Make a request
- `batch_request(requests)`: Execute multiple requests in batch
- `get_metrics()`: Get performance metrics

#### `RateLimitConfig`
Configuration for rate limiting behavior.

**Parameters:**
- `requests_per_minute`: Maximum requests per minute (default: 1200)
- `orders_per_second`: Maximum orders per second (default: 10)
- `weight_per_minute`: Maximum weight per minute (default: 1200)
- `enable_adaptive_throttling`: Enable adaptive throttling (default: True)

#### `RequestPriority`
Priority levels for requests.

**Levels:**
- `CRITICAL`: Highest priority (order cancellations, emergency stops)
- `HIGH`: High priority (order creation, position monitoring)
- `NORMAL`: Normal priority (market data, account info)
- `LOW`: Low priority (historical data, bulk operations)

### Convenience Methods

```python
# Account operations
account_info = await api_manager.get_account_info()
positions = await api_manager.get_position_info(symbol="BTCUSDT")

# Trading operations
order = await api_manager.create_order(
    symbol="BTCUSDT",
    side="BUY",
    order_type="LIMIT",
    quantity=0.001,
    price=50000.0
)

cancel_result = await api_manager.cancel_order(
    symbol="BTCUSDT",
    order_id=12345
)

# Market data
klines = await api_manager.get_klines(
    symbol="BTCUSDT",
    interval="1m",
    limit=100
)

ticker = await api_manager.get_ticker_price(symbol="BTCUSDT")
```

## Performance Benefits

### Before (Sleep-based)
```python
# Old approach
for symbol in symbols:
    data = await client.get_ticker(symbol)
    await asyncio.sleep(0.1)  # Fixed delay
    
# Problems:
# - Unnecessary delays
# - No priority handling
# - Poor error recovery
# - No rate limit tracking
```

### After (APIManager)
```python
# New approach
requests = [(
    'GET', '/fapi/v1/ticker/price',
    {'symbol': symbol},
    False, RequestType.MARKET_DATA, RequestPriority.NORMAL
) for symbol in symbols]

results = await api_manager.batch_request(requests)

# Benefits:
# - Optimal timing
# - Priority handling
# - Automatic retry
# - Rate limit compliance
```

## Monitoring and Metrics

### Real-time Metrics

```python
metrics = api_manager.get_metrics()

print(f"Success Rate: {metrics['rate_limiter']['success_rate']:.2%}")
print(f"Avg Response Time: {metrics['rate_limiter']['average_response_time']:.3f}s")
print(f"Queue Size: {metrics['queue']['total_size']}")
print(f"Circuit State: {metrics['rate_limiter']['circuit_state']}")
```

### Performance Dashboard

```python
async def monitor_performance():
    while True:
        metrics = api_manager.get_metrics()
        
        # Log key metrics
        logger.info(f"API Performance:")
        logger.info(f"  Success Rate: {metrics['rate_limiter']['success_rate']:.2%}")
        logger.info(f"  Response Time: {metrics['rate_limiter']['average_response_time']:.3f}s")
        logger.info(f"  Throttle Factor: {metrics['rate_limiter']['current_throttle_factor']:.2f}")
        logger.info(f"  Requests/min: {metrics['rate_limiter']['rate_limit_state']['requests_this_minute']}")
        
        await asyncio.sleep(30)
```

## Error Handling

### Automatic Retry
```python
# Automatic retry with exponential backoff
try:
    result = await api_manager.request(
        'GET', '/fapi/v1/account',
        signed=True,
        request_type=RequestType.ACCOUNT,
        priority=RequestPriority.HIGH
    )
except Exception as e:
    # All retries exhausted
    logger.error(f"Request failed after retries: {e}")
```

### Circuit Breaker
```python
# Circuit breaker prevents cascade failures
if metrics['rate_limiter']['circuit_state'] == 'open':
    logger.warning("Circuit breaker is open - API is temporarily unavailable")
    # Implement fallback logic
```

## Testing

Run the test suite to validate functionality:

```bash
python tests/test_api_manager.py
```

The test suite includes:
- Basic initialization
- Rate limiting
- Request prioritization
- Batch processing
- Error handling
- Performance metrics
- Circuit breaker
- Adaptive throttling

## Migration Guide

See `API_MANAGER_MIGRATION_GUIDE.md` for detailed migration instructions from the current sleep-based approach.

## Examples

See `examples/api_manager_integration_example.py` for a complete trading bot implementation using the new APIManager.

## Configuration Recommendations

### Conservative Trading Bot
```python
config = RateLimitConfig(
    requests_per_minute=800,
    orders_per_second=5,
    enable_adaptive_throttling=True,
    target_success_rate=0.98
)
```

### High-Frequency Trading
```python
config = RateLimitConfig(
    requests_per_minute=1000,
    orders_per_second=8,
    weight_per_second=40,
    backoff_strategy=BackoffStrategy.EXPONENTIAL,
    enable_adaptive_throttling=True,
    target_success_rate=0.95
)
```

### Data Collection Bot
```python
config = RateLimitConfig(
    requests_per_minute=600,
    weight_per_minute=800,
    max_queue_size=50000,
    enable_adaptive_throttling=True
)
```

## Troubleshooting

### Common Issues

1. **Queue Full Error**
   - Increase `max_queue_size`
   - Add more workers
   - Reduce request frequency

2. **Circuit Breaker Open**
   - Check network connectivity
   - Verify API credentials
   - Monitor error logs

3. **High Response Times**
   - Enable adaptive throttling
   - Check Binance API status
   - Reduce concurrent requests

4. **Rate Limit Exceeded**
   - Verify endpoint weights
   - Check for other API usage
   - Reduce request frequency

### Debug Mode

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('utils.api_manager')
logger.setLevel(logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This implementation is part of the trading bot project and follows the same license terms.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the migration guide
3. Run the test suite
4. Check the example implementation

---

**Note**: This APIManager significantly improves API efficiency and reliability while ensuring compliance with Binance rate limits. The sophisticated rate limiting, request queuing, and automatic backoff strategies provide a robust foundation for high-performance trading applications. 