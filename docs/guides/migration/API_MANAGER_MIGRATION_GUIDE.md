# API Manager Migration Guide

## Overview

This guide explains how to migrate from the current sleep-based rate limiting approach to the new sophisticated `APIManager` class that provides advanced rate limiting, request queuing, weight management, and automatic backoff strategies.

## Key Features of the New APIManager

### 1. Advanced Rate Limiting
- **Weight-based tracking**: Each endpoint has a specific weight that counts against rate limits
- **Multiple time windows**: Tracks requests per second, minute, and day
- **Endpoint-specific limits**: Different limits for orders, market data, and account endpoints

### 2. Request Queuing with Priority
- **Priority levels**: CRITICAL, HIGH, NORMAL, LOW
- **Queue management**: Automatic queuing when rate limits are reached
- **Timeout handling**: Requests timeout if queued too long

### 3. Automatic Backoff Strategies
- **Multiple strategies**: Exponential, Linear, Fibonacci, Adaptive
- **Circuit breaker**: Automatically stops requests when too many failures occur
- **Adaptive throttling**: Adjusts request rate based on success rate

### 4. Request Batching and Optimization
- **Batch processing**: Multiple requests can be processed together
- **Worker pool**: Configurable number of workers for concurrent processing
- **Connection pooling**: Optimized HTTP connections

## Migration Steps

### Step 1: Replace Current Binance Client

**Before (using existing client):**
```python
from utils.async_binance_client import get_binance_client

client = get_binance_client()
result = await client.get_account_info()
```

**After (using new APIManager):**
```python
from utils.api_manager import get_api_manager, initialize_api_manager, RateLimitConfig

# Initialize once at startup
config = RateLimitConfig(
    requests_per_minute=1200,
    orders_per_second=10,
    enable_adaptive_throttling=True
)
api_manager = initialize_api_manager(api_key, api_secret, config)
await api_manager.start()

# Use throughout application
api_manager = get_api_manager()
result = await api_manager.get_account_info()
```

### Step 2: Update Order Management

**Before:**
```python
# Old approach with manual sleep
import asyncio

async def create_order_with_retry(client, order_params):
    for attempt in range(3):
        try:
            return await client.futures_create_order(**order_params)
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

**After:**
```python
# New approach with automatic retry and priority
from utils.api_manager import RequestPriority

async def create_order_with_priority(api_manager, order_params):
    return await api_manager.create_order(
        symbol=order_params['symbol'],
        side=order_params['side'],
        order_type=order_params['type'],
        quantity=order_params['quantity'],
        price=order_params.get('price')
    )
    # Automatic retry, backoff, and priority handling built-in
```

### Step 3: Update Market Data Fetching

**Before:**
```python
async def fetch_multiple_symbols(client, symbols):
    results = []
    for symbol in symbols:
        try:
            data = await client.futures_klines(symbol=symbol, interval='1m', limit=100)
            results.append(data)
            await asyncio.sleep(0.1)  # Manual rate limiting
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
    return results
```

**After:**
```python
async def fetch_multiple_symbols(api_manager, symbols):
    # Batch request with automatic rate limiting
    requests = []
    for symbol in symbols:
        requests.append((
            'GET', '/fapi/v1/klines',
            {'symbol': symbol, 'interval': '1m', 'limit': 100},
            False,  # not signed
            RequestType.MARKET_DATA,
            RequestPriority.NORMAL
        ))
    
    return await api_manager.batch_request(requests)
```

### Step 4: Update Position Monitoring

**Before:**
```python
async def monitor_positions(client):
    while True:
        try:
            positions = await client.futures_position_information()
            # Process positions
            await asyncio.sleep(1)  # Fixed delay
        except Exception as e:
            await asyncio.sleep(5)  # Error backoff
```

**After:**
```python
async def monitor_positions(api_manager):
    while True:
        try:
            positions = await api_manager.get_position_info()
            # Process positions
            # No manual sleep needed - rate limiting handled automatically
        except Exception as e:
            # Automatic backoff and retry handled by APIManager
            await asyncio.sleep(1)  # Minimal delay for loop control
```

## Configuration Options

### Basic Configuration
```python
from utils.api_manager import RateLimitConfig, BackoffStrategy

config = RateLimitConfig(
    # Binance rate limits
    requests_per_minute=1200,
    orders_per_second=10,
    orders_per_day=200000,
    
    # Weight limits
    weight_per_minute=1200,
    weight_per_second=50,
    
    # Backoff strategy
    backoff_strategy=BackoffStrategy.ADAPTIVE,
    initial_backoff=1.0,
    max_backoff=300.0,
    
    # Queue settings
    max_queue_size=10000,
    queue_timeout=30.0,
    
    # Adaptive throttling
    enable_adaptive_throttling=True,
    target_success_rate=0.95
)
```

### Advanced Configuration for High-Frequency Trading
```python
config = RateLimitConfig(
    # More aggressive limits
    requests_per_minute=1000,  # Conservative
    orders_per_second=8,       # Below Binance limit
    weight_per_second=40,      # Conservative weight usage
    
    # Faster backoff recovery
    backoff_strategy=BackoffStrategy.EXPONENTIAL,
    initial_backoff=0.5,
    max_backoff=60.0,
    
    # Larger queue for burst handling
    max_queue_size=50000,
    queue_timeout=60.0,
    
    # Strict adaptive throttling
    enable_adaptive_throttling=True,
    target_success_rate=0.98,
    monitoring_window=50
)
```

## Usage Examples

### Example 1: Trading Bot Integration

```python
import asyncio
from utils.api_manager import (
    initialize_api_manager, get_api_manager, 
    RateLimitConfig, RequestPriority, RequestType
)

class TradingBot:
    def __init__(self, api_key, api_secret):
        # Initialize API manager
        config = RateLimitConfig(
            enable_adaptive_throttling=True,
            target_success_rate=0.95
        )
        self.api_manager = initialize_api_manager(api_key, api_secret, config)
    
    async def start(self):
        await self.api_manager.start(num_workers=10)
        
        # Start trading tasks
        await asyncio.gather(
            self.monitor_positions(),
            self.process_signals(),
            self.update_orders()
        )
    
    async def monitor_positions(self):
        while True:
            try:
                positions = await self.api_manager.get_position_info()
                await self.process_positions(positions)
            except Exception as e:
                print(f"Position monitoring error: {e}")
                await asyncio.sleep(1)
    
    async def process_signals(self):
        while True:
            try:
                # Get market data with normal priority
                ticker_data = await self.api_manager.get_ticker_price()
                
                # Process signals and create orders with high priority
                if self.should_trade(ticker_data):
                    await self.api_manager.create_order(
                        symbol="BTCUSDT",
                        side="BUY",
                        order_type="MARKET",
                        quantity=0.001
                    )
            except Exception as e:
                print(f"Signal processing error: {e}")
    
    async def update_orders(self):
        while True:
            try:
                # Get open orders with high priority
                orders = await self.api_manager.request(
                    'GET', '/fapi/v1/openOrders',
                    signed=True,
                    request_type=RequestType.ORDER,
                    priority=RequestPriority.HIGH
                )
                await self.manage_orders(orders)
            except Exception as e:
                print(f"Order management error: {e}")
    
    async def stop(self):
        await self.api_manager.stop()
```

### Example 2: Batch Data Collection

```python
async def collect_market_data(symbols, intervals):
    api_manager = get_api_manager()
    
    # Prepare batch requests
    requests = []
    for symbol in symbols:
        for interval in intervals:
            requests.append((
                'GET', '/fapi/v1/klines',
                {
                    'symbol': symbol,
                    'interval': interval,
                    'limit': 1000
                },
                False,  # not signed
                RequestType.MARKET_DATA,
                RequestPriority.LOW  # Low priority for bulk data
            ))
    
    # Execute batch with automatic rate limiting
    results = await api_manager.batch_request(requests, timeout=120.0)
    
    # Process results
    processed_data = {}
    idx = 0
    for symbol in symbols:
        processed_data[symbol] = {}
        for interval in intervals:
            if 'error' not in results[idx]:
                processed_data[symbol][interval] = results[idx]
            idx += 1
    
    return processed_data
```

### Example 3: Monitoring and Metrics

```python
async def monitor_api_performance():
    api_manager = get_api_manager()
    
    while True:
        metrics = api_manager.get_metrics()
        
        print(f"API Performance Metrics:")
        print(f"  Uptime: {metrics['uptime']:.2f} seconds")
        print(f"  Success Rate: {metrics['rate_limiter']['success_rate']:.2%}")
        print(f"  Average Response Time: {metrics['rate_limiter']['average_response_time']:.3f}s")
        print(f"  Throttle Factor: {metrics['rate_limiter']['current_throttle_factor']:.2f}")
        print(f"  Circuit State: {metrics['rate_limiter']['circuit_state']}")
        print(f"  Queue Size: {metrics['queue']['total_size']}")
        print(f"  Rate Limits:")
        print(f"    Requests this minute: {metrics['rate_limiter']['rate_limit_state']['requests_this_minute']}")
        print(f"    Weight this minute: {metrics['rate_limiter']['rate_limit_state']['weight_this_minute']}")
        print(f"    Orders today: {metrics['rate_limiter']['rate_limit_state']['orders_this_day']}")
        
        await asyncio.sleep(30)  # Update every 30 seconds
```

## Migration Checklist

- [ ] Install new APIManager dependencies
- [ ] Update imports to use new APIManager
- [ ] Replace manual sleep calls with APIManager requests
- [ ] Configure rate limiting parameters
- [ ] Update error handling to work with new retry mechanisms
- [ ] Test with low-priority requests first
- [ ] Monitor metrics and adjust configuration
- [ ] Gradually migrate high-priority trading operations
- [ ] Remove old sleep-based rate limiting code

## Benefits After Migration

1. **Improved Performance**: No more unnecessary delays from fixed sleep times
2. **Better Rate Limit Compliance**: Precise tracking of Binance rate limits
3. **Automatic Recovery**: Circuit breaker and adaptive throttling handle failures
4. **Priority Management**: Critical orders get processed first
5. **Comprehensive Monitoring**: Real-time metrics and performance tracking
6. **Scalability**: Worker pool can handle high request volumes
7. **Reliability**: Automatic retries and backoff strategies

## Troubleshooting

### Common Issues

1. **Queue Full Error**
   - Increase `max_queue_size` in configuration
   - Add more workers with `start(num_workers=N)`

2. **Circuit Breaker Open**
   - Check network connectivity
   - Verify API credentials
   - Monitor error logs for root cause

3. **High Response Times**
   - Enable adaptive throttling
   - Reduce `target_success_rate` temporarily
   - Check Binance API status

4. **Rate Limit Exceeded**
   - Verify endpoint weights are correct
   - Reduce request frequency
   - Check for concurrent API usage

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('utils.api_manager')
logger.setLevel(logging.DEBUG)

# Monitor detailed request flow
api_manager = get_api_manager()
metrics = api_manager.get_metrics()
print(f"Detailed metrics: {metrics}")
```

This migration will significantly improve your trading bot's API efficiency and reliability while ensuring compliance with Binance rate limits. 