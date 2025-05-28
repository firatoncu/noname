# Performance Optimization Guide

This guide documents the comprehensive performance optimizations implemented in the trading bot application to improve overall system performance, reduce latency, and optimize resource usage.

## Table of Contents

1. [Overview](#overview)
2. [Performance Improvements](#performance-improvements)
3. [Caching Mechanisms](#caching-mechanisms)
4. [Memory Optimization](#memory-optimization)
5. [CPU Optimization](#cpu-optimization)
6. [Database Optimization](#database-optimization)
7. [Profiling and Monitoring](#profiling-and-monitoring)
8. [Usage Guide](#usage-guide)
9. [Performance Metrics](#performance-metrics)
10. [Troubleshooting](#troubleshooting)

## Overview

The performance optimization system provides:

- **Multi-level caching** with LRU and TTL support
- **Memory usage optimization** and monitoring
- **CPU-intensive operation optimization** using thread/process pools
- **Database query optimization** with connection pooling and batching
- **Performance profiling** and bottleneck identification
- **Async operation batching** and pooling

## Performance Improvements

### Key Optimizations Implemented

1. **Data Fetching Optimization**
   - Cached API responses with intelligent TTL
   - Batch fetching for multiple symbols
   - Memory-optimized DataFrame operations
   - Compressed data storage

2. **Technical Indicator Optimization**
   - Cached indicator calculations
   - Vectorized operations using NumPy
   - CPU-optimized calculations
   - Batch processing capabilities

3. **Database Operation Optimization**
   - Connection pooling
   - Query result caching
   - Batch insert/update operations
   - Memory-efficient data handling

4. **Memory Management**
   - Automatic garbage collection
   - Memory usage monitoring
   - DataFrame memory optimization
   - Cache size management

## Caching Mechanisms

### Multi-Level Cache System

```python
from utils.performance_optimizer import get_cache_system

# Get the global cache system
cache = get_cache_system()

# Cache data
await cache.set("key", data)

# Retrieve cached data
cached_data = await cache.get("key")
```

### DataFrame Cache

Specialized cache for pandas DataFrames with compression:

```python
from utils.optimized_fetch_data import get_data_fetcher

fetcher = get_data_fetcher()
df, close_price = await fetcher.fetch_klines_data("BTCUSDT", client, 500, "1m")
```

### Indicator Cache

Cache technical indicators to avoid recalculation:

```python
from utils.optimized_indicators import cached_indicator

@cached_indicator("rsi", ttl_seconds=300)
def calculate_rsi(data, symbol=None, window=14):
    # RSI calculation
    return rsi_values
```

## Memory Optimization

### Memory Monitoring

```python
from utils.performance_optimizer import get_memory_optimizer

memory_optimizer = get_memory_optimizer()

# Start memory monitoring
await memory_optimizer.start_monitoring()

# Get memory usage statistics
stats = memory_optimizer.get_memory_usage()
print(f"Memory usage: {stats['rss_mb']:.1f}MB ({stats['percent']:.1f}%)")

# Force garbage collection
collected = memory_optimizer.force_garbage_collection()
```

### DataFrame Memory Optimization

```python
# Optimize DataFrame memory usage
optimized_df = memory_optimizer.optimize_dataframe(df)
```

## CPU Optimization

### Thread Pool Execution

```python
from utils.performance_optimizer import get_cpu_optimizer

cpu_optimizer = get_cpu_optimizer()

# Run CPU-intensive function in thread pool
result = await cpu_optimizer.run_in_thread(expensive_function, *args)

# Run in process pool for CPU-bound tasks
result = await cpu_optimizer.run_in_process(cpu_bound_function, *args)
```

### Vectorized Operations

```python
from utils.optimized_indicators import get_indicators

indicators = get_indicators()

# Vectorized MACD calculation
macd_data = indicators.calculate_macd(close_prices, symbol="BTCUSDT")

# Vectorized RSI calculation
rsi_values = indicators.calculate_rsi(close_prices, symbol="BTCUSDT")
```

## Database Optimization

### Connection Pooling

```python
from utils.optimized_database import get_optimized_database

db = get_optimized_database()

# Execute query with caching
result = await db.execute_query(
    "SELECT * FROM trades WHERE symbol = ?",
    params=("BTCUSDT",),
    use_cache=True
)
```

### Batch Operations

```python
# Batch insert
await db.batch_insert("trades", [
    {"symbol": "BTCUSDT", "price": 50000},
    {"symbol": "ETHUSDT", "price": 3000}
])

# Optimized DataFrame insertion
await db.optimize_dataframe_insert("trades", df, chunk_size=1000)
```

### InfluxDB Optimization

```python
from utils.optimized_database import get_optimized_influxdb

influxdb = get_optimized_influxdb()

# Start auto-flushing
await influxdb.start_auto_flush()

# Write point with batching
await influxdb.write_point(
    measurement="prices",
    fields={"close": 50000},
    tags={"symbol": "BTCUSDT"},
    batch=True
)
```

## Profiling and Monitoring

### Performance Profiling

```python
from utils.performance_optimizer import get_profiler

profiler = get_profiler()

# Profile async operation
async with profiler.profile_async("trading_operation"):
    await trading_function()

# Get performance report
report = profiler.get_performance_report()
print(f"Average duration: {report['trading_operation']['avg_duration']:.3f}s")

# Identify bottlenecks
bottlenecks = profiler.identify_bottlenecks(threshold_seconds=1.0)
```

### Function Profiling Decorator

```python
from utils.performance_optimizer import profiled

@profiled
async def trading_function():
    # Function implementation
    pass
```

### Performance Monitoring

```python
# Start performance monitoring loop
perf_monitor_task = asyncio.create_task(performance_monitoring_loop(logger))
```

## Usage Guide

### Running the Optimized Application

1. **Install performance dependencies:**
   ```bash
   pip install -r requirements-performance.txt
   ```

2. **Run the optimized version:**
   ```bash
   python optimized_n0name.py
   ```

3. **Monitor performance:**
   - Check logs for performance metrics
   - Monitor memory usage
   - Review cache hit rates

### Configuration

Configure performance settings in your application:

```python
from utils.performance_optimizer import CacheConfig, PerformanceMetrics

# Configure cache
cache_config = CacheConfig(
    max_size=1000,
    ttl_seconds=300,
    cleanup_interval=60,
    memory_threshold_mb=500
)

# Configure data fetching
data_config = DataFetchConfig(
    cache_ttl_seconds=60,
    max_cache_size=200,
    batch_size=10,
    concurrent_requests=5
)
```

## Performance Metrics

### Key Performance Indicators

1. **Cache Hit Rate**: Target >70%
2. **Memory Usage**: Keep <80% of available memory
3. **Average Fetch Time**: Target <1.0 second
4. **Database Query Time**: Target <0.5 seconds
5. **Trading Iteration Time**: Target <2.0 seconds

### Monitoring Dashboard

The application provides real-time performance metrics:

```
Performance Summary - Memory: 245.3MB, Cache Hit Rate: 85.2%, Avg Fetch Time: 0.234s
```

### Performance Health Check

```python
from src.optimized_open_position import performance_health_check

health_report = await performance_health_check(symbols, logger)
print(f"Overall health: {health_report['overall_health']}")
```

## Troubleshooting

### Common Performance Issues

1. **Low Cache Hit Rate**
   - Increase cache TTL
   - Increase cache size
   - Check data access patterns

2. **High Memory Usage**
   - Enable automatic garbage collection
   - Reduce cache sizes
   - Optimize DataFrame memory usage

3. **Slow Database Queries**
   - Enable query caching
   - Use batch operations
   - Optimize query structure

4. **CPU Bottlenecks**
   - Use thread/process pools
   - Enable vectorized operations
   - Optimize algorithm complexity

### Performance Tuning

1. **Cache Optimization**
   ```python
   # Adjust cache settings
   cache_config.max_size = 2000  # Increase cache size
   cache_config.ttl_seconds = 600  # Increase TTL
   ```

2. **Memory Optimization**
   ```python
   # Force memory cleanup
   await optimize_memory_usage(logger)
   ```

3. **Database Optimization**
   ```python
   # Increase batch size
   db_config.batch_size = 2000
   db_config.batch_timeout = 10.0
   ```

### Debugging Performance Issues

1. **Enable detailed profiling:**
   ```python
   # Profile specific operations
   @profiled
   async def problematic_function():
       pass
   ```

2. **Monitor resource usage:**
   ```python
   # Check memory usage
   memory_stats = memory_optimizer.get_memory_usage()
   
   # Check cache statistics
   cache_stats = cache.get_metrics()
   ```

3. **Analyze performance reports:**
   ```python
   # Generate detailed report
   report = profiler.get_performance_report()
   for operation, metrics in report.items():
       print(f"{operation}: {metrics['avg_duration']:.3f}s avg")
   ```

## Best Practices

1. **Use caching for frequently accessed data**
2. **Batch operations when possible**
3. **Monitor memory usage regularly**
4. **Profile critical code paths**
5. **Use vectorized operations for numerical computations**
6. **Implement proper cleanup procedures**
7. **Monitor performance metrics continuously**

## Advanced Features

### Background Optimization Tasks

```python
from src.optimized_open_position import start_background_optimizations

# Start background tasks
bg_tasks = await start_background_optimizations(symbols, client, logger)

# Stop background tasks when done
await stop_background_optimizations(bg_tasks, logger)
```

### Custom Performance Decorators

```python
from utils.performance_optimizer import cached, optimized_cpu

@cached(ttl_seconds=600, max_size=500)
@optimized_cpu(use_process_pool=True)
async def heavy_computation(data):
    # CPU-intensive computation
    return result
```

### Performance Testing

```python
import pytest
from utils.performance_optimizer import get_profiler

@pytest.mark.asyncio
async def test_trading_performance():
    profiler = get_profiler()
    
    async with profiler.profile_async("test_trading"):
        await trading_function()
    
    report = profiler.get_performance_report()
    assert report["test_trading"]["avg_duration"] < 1.0
```

## Conclusion

The performance optimization system provides comprehensive improvements to the trading bot application, including advanced caching, memory management, CPU optimization, and database performance enhancements. Regular monitoring and tuning of these systems will ensure optimal performance and resource utilization.

For additional support or questions about performance optimization, refer to the application logs and performance metrics dashboard. 