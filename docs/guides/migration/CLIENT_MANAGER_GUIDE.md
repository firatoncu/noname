# Binance Client Manager Guide

## Overview

The `ClientManager` is a robust connection management system for Binance API clients that provides:

- **Connection Pooling**: Automatic scaling of connection pools based on demand
- **Health Monitoring**: Continuous health checks with automatic recovery
- **Fallback Mechanisms**: Multiple endpoint support with automatic failover
- **Circuit Breaker Pattern**: Fault tolerance for network issues
- **WebSocket Management**: Managed WebSocket connections with auto-reconnection
- **Comprehensive Metrics**: Detailed monitoring and performance metrics

## Key Features

### 🔄 Connection Pooling
- Maintains a pool of ready-to-use Binance clients
- Automatic scaling based on demand (min/max connections)
- Efficient resource utilization with connection reuse

### 🏥 Health Monitoring
- Continuous health checks using ping requests
- Automatic removal and replacement of unhealthy clients
- Configurable failure thresholds and recovery timeouts

### 🔀 Fallback Mechanisms
- Multiple Binance endpoint support
- Automatic failover when primary endpoints fail
- Circuit breaker pattern for fault tolerance

### 📡 WebSocket Management
- Managed WebSocket connections with automatic reconnection
- Multiple endpoint fallback for WebSocket connections
- Graceful handling of connection drops

### 📊 Metrics & Monitoring
- Real-time connection metrics
- Performance monitoring (response times, failure rates)
- Health status reporting

## Quick Start

### Basic Setup

```python
import asyncio
from utils.client_manager import (
    ClientManager, ClientConfig, initialize_client_manager, 
    get_client_manager, cleanup_client_manager
)
from utils.async_binance_client import BinanceConfig

async def main():
    # Configure Binance client
    binance_config = BinanceConfig(
        api_key="your_api_key",
        api_secret="your_api_secret",
        testnet=True,  # Use testnet for testing
        enable_rate_limiting=True
    )
    
    # Configure client manager
    client_config = ClientConfig(
        min_connections=2,
        max_connections=10,
        health_check_interval=30.0,
        enable_fallback_endpoints=True
    )
    
    # Initialize and start client manager
    client_manager = initialize_client_manager(binance_config, client_config)
    await client_manager.start()
    
    try:
        # Use the client manager
        async with client_manager.get_client() as client:
            account_info = await client.get_account_info()
            print(f"Account assets: {len(account_info.get('assets', []))}")
            
        # Get metrics
        metrics = client_manager.get_metrics()
        print(f"Active connections: {metrics['connection_metrics']['active_connections']}")
        
    finally:
        await cleanup_client_manager()

if __name__ == "__main__":
    asyncio.run(main())
```

### Using the Context Manager

The recommended way to use clients is through the context manager:

```python
async with client_manager.get_client() as client:
    # Client is automatically acquired from pool
    server_time = await client.get_server_time()
    account_info = await client.get_account_info()
    
    # Multiple operations with the same client
    positions = await client.get_position_info()
    balance = await client.get_balance()
# Client is automatically returned to pool
```

## Configuration

### BinanceConfig

```python
binance_config = BinanceConfig(
    api_key="your_api_key",
    api_secret="your_api_secret",
    base_url="https://fapi.binance.com",  # Primary endpoint
    testnet=False,
    max_requests_per_minute=1200,
    max_requests_per_second=10,
    max_order_requests_per_second=5,
    enable_rate_limiting=True,
    enable_request_batching=True,
    batch_size=10,
    connection_pool_size=50
)
```

### ClientConfig

```python
client_config = ClientConfig(
    # Connection pool settings
    min_connections=2,              # Minimum connections to maintain
    max_connections=10,             # Maximum connections allowed
    connection_timeout=30.0,        # Timeout for getting a client
    idle_timeout=300.0,             # Idle timeout for connections
    
    # Health check settings
    health_check_interval=30.0,     # Interval between health checks
    health_check_timeout=10.0,      # Timeout for health check requests
    max_health_check_failures=3,    # Max failures before removing client
    
    # Reconnection settings
    max_reconnection_attempts=5,    # Max reconnection attempts
    reconnection_delay=5.0,         # Initial reconnection delay
    reconnection_backoff_multiplier=2.0,  # Backoff multiplier
    max_reconnection_delay=300.0,   # Maximum reconnection delay
    
    # Fallback settings
    enable_fallback_endpoints=True,
    fallback_endpoints=[
        "https://fapi.binance.com",
        "https://fapi1.binance.com",
        "https://fapi2.binance.com"
    ],
    
    # Circuit breaker settings
    circuit_breaker_failure_threshold=5,
    circuit_breaker_recovery_timeout=60.0,
    
    # Performance settings
    enable_connection_warming=True,
    connection_warm_up_requests=3,
    enable_adaptive_scaling=True
)
```

## Advanced Usage

### WebSocket Connections

```python
async def ticker_callback(data):
    if 'c' in data:  # Current price
        symbol = data.get('s', 'UNKNOWN')
        price = data.get('c', '0')
        print(f"Price update - {symbol}: ${price}")

# Create managed WebSocket connection
connection_id = await client_manager.create_websocket_connection(
    "btcusdt@ticker",
    ticker_callback,
    auto_reconnect=True
)

# Connection will automatically reconnect if dropped
await asyncio.sleep(60)  # Let it run for a minute

# Close when done
await client_manager.close_websocket_connection(connection_id)
```

### Concurrent Operations

```python
async def make_multiple_requests():
    """Example of concurrent API requests."""
    
    async def get_symbol_data(symbol):
        async with client_manager.get_client() as client:
            ticker = await client.get_ticker_price(symbol)
            return {symbol: ticker['price']}
    
    # Make concurrent requests for multiple symbols
    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT']
    tasks = [get_symbol_data(symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks)
    
    # Combine results
    prices = {}
    for result in results:
        prices.update(result)
    
    return prices
```

### Error Handling

```python
async def robust_trading_operation():
    """Example with comprehensive error handling."""
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with client_manager.get_client(timeout=10.0) as client:
                # Perform trading operations
                account_info = await client.get_account_info()
                positions = await client.get_position_info()
                
                # Create order if conditions are met
                if should_place_order(account_info, positions):
                    order = await client.create_order(
                        symbol='BTCUSDT',
                        side='BUY',
                        order_type='MARKET',
                        quantity=0.001
                    )
                    return order
                    
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Monitoring and Metrics

### Getting Metrics

```python
metrics = client_manager.get_metrics()

print("Connection Metrics:")
print(f"  Total connections: {metrics['connection_metrics']['total_connections']}")
print(f"  Active connections: {metrics['connection_metrics']['active_connections']}")
print(f"  Available connections: {metrics['connection_metrics']['available_connections']}")
print(f"  Failed connections: {metrics['connection_metrics']['failed_connections']}")
print(f"  Average response time: {metrics['connection_metrics']['average_response_time']:.3f}s")

print("\nEndpoint Status:")
for endpoint, status in metrics['endpoint_status'].items():
    print(f"  {endpoint}: {status['failures']} failures, {status['circuit_breaker_state']}")

print(f"\nWebSocket connections: {metrics['websocket_connections']}")
print(f"Background tasks: {metrics['background_tasks']}")
```

### Health Status

```python
health_status = client_manager.get_health_status()
print(f"Overall health: {health_status.value}")

# Health status can be: HEALTHY, DEGRADED, UNHEALTHY, UNKNOWN
if health_status == HealthStatus.UNHEALTHY:
    print("Warning: Client manager is unhealthy!")
    # Take corrective action
```

## Best Practices

### 1. Connection Pool Sizing

```python
# For low-traffic applications
client_config = ClientConfig(
    min_connections=1,
    max_connections=3
)

# For high-traffic applications
client_config = ClientConfig(
    min_connections=5,
    max_connections=20
)
```

### 2. Health Check Configuration

```python
# Aggressive health checking for critical applications
client_config = ClientConfig(
    health_check_interval=15.0,     # Check every 15 seconds
    health_check_timeout=5.0,       # 5 second timeout
    max_health_check_failures=2     # Remove after 2 failures
)

# Relaxed health checking for stable environments
client_config = ClientConfig(
    health_check_interval=60.0,     # Check every minute
    health_check_timeout=10.0,      # 10 second timeout
    max_health_check_failures=5     # Remove after 5 failures
)
```

### 3. Fallback Configuration

```python
# Enable fallback for production
client_config = ClientConfig(
    enable_fallback_endpoints=True,
    fallback_endpoints=[
        "https://fapi.binance.com",
        "https://fapi1.binance.com",
        "https://fapi2.binance.com"
    ]
)

# Disable fallback for testing with specific endpoint
client_config = ClientConfig(
    enable_fallback_endpoints=False
)
```

### 4. Resource Management

```python
async def application_lifecycle():
    """Proper resource management."""
    
    # Initialize
    client_manager = initialize_client_manager(binance_config, client_config)
    
    try:
        await client_manager.start()
        
        # Application logic here
        await run_trading_application()
        
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        # Always cleanup
        await cleanup_client_manager()
```

## Troubleshooting

### Common Issues

1. **No Available Clients**
   ```
   Exception: No available clients
   ```
   - Increase `max_connections` in ClientConfig
   - Check if health checks are failing
   - Verify API credentials

2. **High Connection Failures**
   ```
   High number of failed_connections in metrics
   ```
   - Check network connectivity
   - Verify API endpoints are accessible
   - Review API key permissions

3. **WebSocket Disconnections**
   ```
   WebSocket connections frequently dropping
   ```
   - Enable auto-reconnection
   - Check network stability
   - Verify WebSocket endpoint availability

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('utils.client_manager')
logger.setLevel(logging.DEBUG)
```

### Metrics Monitoring

Set up periodic metrics monitoring:

```python
async def monitor_client_manager():
    """Monitor client manager health."""
    while True:
        metrics = client_manager.get_metrics()
        health = client_manager.get_health_status()
        
        if health != HealthStatus.HEALTHY:
            print(f"Warning: Client manager health is {health.value}")
        
        conn_metrics = metrics['connection_metrics']
        if conn_metrics['failed_connections'] > 10:
            print("Warning: High number of connection failures")
        
        await asyncio.sleep(30)  # Check every 30 seconds
```

## Migration from Existing Code

### From Direct Client Usage

**Before:**
```python
client = OptimizedBinanceClient(config)
await client.connect()

try:
    account_info = await client.get_account_info()
finally:
    await client.close()
```

**After:**
```python
client_manager = initialize_client_manager(binance_config, client_config)
await client_manager.start()

try:
    async with client_manager.get_client() as client:
        account_info = await client.get_account_info()
finally:
    await cleanup_client_manager()
```

### From APIManager

**Before:**
```python
api_manager = APIManager(api_key, api_secret)
await api_manager.start()

try:
    account_info = await api_manager.get_account_info()
finally:
    await api_manager.stop()
```

**After:**
```python
client_manager = initialize_client_manager(binance_config, client_config)
await client_manager.start()

try:
    async with client_manager.get_client() as client:
        account_info = await client.get_account_info()
finally:
    await cleanup_client_manager()
```

## Performance Considerations

### Connection Pool Optimization

- Set `min_connections` based on baseline load
- Set `max_connections` based on peak load
- Enable `adaptive_scaling` for dynamic workloads

### Health Check Optimization

- Balance `health_check_interval` vs. resource usage
- Adjust `health_check_timeout` based on network latency
- Set `max_health_check_failures` based on tolerance for false positives

### WebSocket Optimization

- Use auto-reconnection for critical data streams
- Implement proper error handling in callbacks
- Monitor connection metrics for stability

## Security Considerations

1. **API Key Management**
   - Store API keys securely (environment variables, key management systems)
   - Use testnet for development and testing
   - Rotate API keys regularly

2. **Network Security**
   - Use HTTPS endpoints only
   - Implement proper certificate validation
   - Consider VPN or private networks for production

3. **Error Handling**
   - Don't log sensitive information (API keys, secrets)
   - Implement proper exception handling
   - Monitor for suspicious activity

## Conclusion

The ClientManager provides a robust, production-ready solution for managing Binance API connections. It handles the complexity of connection pooling, health monitoring, and error recovery, allowing you to focus on your trading logic.

For more examples and advanced usage patterns, see the `examples/client_manager_example.py` file. 