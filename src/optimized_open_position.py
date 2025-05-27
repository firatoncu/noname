"""
Optimized Open Position Module with Performance Enhancements

This module provides:
- Batch processing for multiple symbols
- Cached data fetching and indicator calculations
- Memory-optimized operations
- Performance monitoring and profiling
"""

import asyncio
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
from src.create_order import check_create_order
from src.position_value import position_val
from src.control_position import position_checker
from utils.calculate_quantity import calculate_quantity
from utils.stepsize_precision import stepsize_precision
from utils.globals import get_capital_tbu, get_db_status
from utils.position_opt import funding_fee_controller
from utils.influxdb.csv_writer import write_to_daily_csv
from utils.influxdb.inf_send_data import write_live_conditions

# Performance optimization imports
from utils.performance_optimizer import profiled, cached, get_memory_optimizer
from utils.optimized_fetch_data import batch_fetch_symbols_data, get_data_fetcher
from utils.optimized_indicators import get_indicators
from utils.optimized_database import get_optimized_influxdb

import logging
import time
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)


@cached(ttl_seconds=300, max_size=100)  # Cache for 5 minutes
@profiled
async def get_cached_stepsize_precision(client, symbols):
    """Cached version of stepsize_precision to avoid repeated API calls."""
    return await stepsize_precision(client, symbols)


@profiled
async def optimized_process_symbol(
    symbol: str,
    client,
    logger,
    stepSizes: Dict[str, float],
    quantityPrecisions: Dict[str, int],
    position_value: float,
    data_cache: Dict[str, Tuple],
    indicators_cache: Dict[str, Any]
):
    """
    Optimized symbol processing with caching and error handling.
    
    Args:
        symbol: Trading symbol
        client: Binance client
        logger: Logger instance
        stepSizes: Step sizes for symbols
        quantityPrecisions: Quantity precisions for symbols
        position_value: Position value for calculations
        data_cache: Cached market data
        indicators_cache: Cached indicator data
    """
    try:
        # Check funding fee (cached internally)
        funding_fee = await funding_fee_controller(symbol, client, logger)
        if funding_fee == False:
            logger.debug(f"Funding fee check failed for {symbol}")
            return
        
        # Get cached data
        if symbol in data_cache:
            df, close_price = data_cache[symbol]
        else:
            logger.warning(f"No cached data available for {symbol}")
            return
        
        # Calculate quantity with optimized precision
        Q = calculate_quantity(
            position_value, 
            close_price, 
            stepSizes[symbol], 
            quantityPrecisions[symbol]
        )
        
        # Process order with cached data
        await check_create_order(symbol, Q, df, client, logger)
        
        # Write to database if enabled (batched)
        if get_db_status() == True:
            influxdb = get_optimized_influxdb()
            await influxdb.write_point(
                measurement="live_conditions",
                fields={
                    "close_price": close_price,
                    "quantity": Q,
                    "symbol": symbol
                },
                tags={"symbol": symbol},
                timestamp=df['timestamp'].iloc[-1] if hasattr(df['timestamp'].iloc[-1], 'to_pydatetime') 
                         else df['timestamp'].iloc[-1]
            )
        
        logger.debug(f"Successfully processed {symbol}")
        
    except Exception as e:
        logger.error(f"Error processing {symbol}: {e}")


@profiled
async def batch_process_symbols(
    symbols: List[str],
    client,
    logger,
    stepSizes: Dict[str, float],
    quantityPrecisions: Dict[str, int],
    position_value: float,
    batch_size: int = 5
):
    """
    Process symbols in batches for better performance.
    
    Args:
        symbols: List of trading symbols
        client: Binance client
        logger: Logger instance
        stepSizes: Step sizes for symbols
        quantityPrecisions: Quantity precisions for symbols
        position_value: Position value for calculations
        batch_size: Number of symbols to process concurrently
    """
    # Fetch all data in batch
    logger.debug(f"Batch fetching data for {len(symbols)} symbols")
    data_cache = await batch_fetch_symbols_data(symbols, client, 500, '1m')
    
    # Pre-calculate indicators for all symbols
    indicators = get_indicators()
    indicators_cache = {}
    
    # Process symbols in batches
    for i in range(0, len(symbols), batch_size):
        batch_symbols = symbols[i:i + batch_size]
        
        # Create tasks for concurrent processing
        tasks = []
        for symbol in batch_symbols:
            if symbol in data_cache:  # Only process if we have data
                task = optimized_process_symbol(
                    symbol, client, logger, stepSizes, quantityPrecisions,
                    position_value, data_cache, indicators_cache
                )
                tasks.append(task)
        
        # Execute batch concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Small delay between batches to prevent overwhelming the system
        if i + batch_size < len(symbols):
            await asyncio.sleep(0.1)


@profiled
async def optimized_open_position(max_open_positions, symbols, logger, client, leverage):
    """
    Optimized main function for opening positions with performance enhancements.
    
    This function includes:
    - Cached static data fetching
    - Batch processing of symbols
    - Memory optimization
    - Performance monitoring
    """
    start_time = time.time()
    memory_optimizer = get_memory_optimizer()
    
    try:
        logger.debug(f"Starting optimized position opening for {len(symbols)} symbols")
        
        # Fetch static data once with caching
        stepSizes, quantityPrecisions, pricePrecisions = await get_cached_stepsize_precision(client, symbols)
        
        # Get capital and position value
        capital_tbu = get_capital_tbu()
        position_value = await position_val(leverage, capital_tbu, max_open_positions, logger, client)
        
        # Check existing positions
        await position_checker(client, pricePrecisions, logger)
        
        # Process symbols in optimized batches
        await batch_process_symbols(
            symbols, client, logger, stepSizes, quantityPrecisions, position_value
        )
        
        # Force garbage collection to free memory
        memory_optimizer.force_garbage_collection()
        
        execution_time = time.time() - start_time
        logger.debug(f"Optimized position opening completed in {execution_time:.3f}s")
        
    except Exception as e:
        logger.error(f"Error in optimized open position: {e}")
        await asyncio.sleep(2)


# Additional optimization functions

@profiled
async def preload_market_data(symbols: List[str], client, logger):
    """
    Preload market data for all symbols to warm up the cache.
    
    Args:
        symbols: List of trading symbols
        client: Binance client
        logger: Logger instance
    """
    try:
        logger.info(f"Preloading market data for {len(symbols)} symbols")
        data_fetcher = get_data_fetcher()
        
        # Batch fetch data to warm up cache
        await data_fetcher.batch_fetch_data(symbols, client, 500, '1m')
        
        logger.info("Market data preloading completed")
        
    except Exception as e:
        logger.error(f"Error preloading market data: {e}")


@profiled
async def optimize_memory_usage(logger):
    """
    Optimize memory usage by clearing caches and forcing garbage collection.
    
    Args:
        logger: Logger instance
    """
    try:
        memory_optimizer = get_memory_optimizer()
        data_fetcher = get_data_fetcher()
        
        # Get memory stats before optimization
        before_stats = memory_optimizer.get_memory_usage()
        
        # Clear old cache entries
        data_fetcher.clear_cache()
        
        # Force garbage collection
        collected = memory_optimizer.force_garbage_collection()
        
        # Get memory stats after optimization
        after_stats = memory_optimizer.get_memory_usage()
        
        memory_saved = before_stats['rss_mb'] - after_stats['rss_mb']
        
        logger.info(
            f"Memory optimization completed - "
            f"Freed {collected} objects, "
            f"Saved {memory_saved:.1f}MB memory"
        )
        
    except Exception as e:
        logger.error(f"Error optimizing memory usage: {e}")


@profiled
async def performance_health_check(symbols: List[str], logger):
    """
    Perform a health check on performance systems.
    
    Args:
        symbols: List of trading symbols
        logger: Logger instance
    
    Returns:
        Dict with health check results
    """
    try:
        data_fetcher = get_data_fetcher()
        memory_optimizer = get_memory_optimizer()
        
        # Get performance stats
        data_stats = data_fetcher.get_performance_stats()
        memory_stats = memory_optimizer.get_memory_usage()
        
        # Check cache hit rate
        cache_health = "good" if data_stats['cache_hit_rate'] > 0.7 else "poor"
        
        # Check memory usage
        memory_health = "good" if memory_stats['percent'] < 80 else "high"
        
        # Check average fetch time
        fetch_health = "good" if data_stats['avg_fetch_time'] < 1.0 else "slow"
        
        health_report = {
            'overall_health': 'good' if all(h == 'good' for h in [cache_health, memory_health, fetch_health]) else 'degraded',
            'cache_health': cache_health,
            'memory_health': memory_health,
            'fetch_health': fetch_health,
            'cache_hit_rate': data_stats['cache_hit_rate'],
            'memory_usage_percent': memory_stats['percent'],
            'avg_fetch_time': data_stats['avg_fetch_time'],
            'symbols_count': len(symbols)
        }
        
        logger.info(f"Performance health check: {health_report['overall_health']}")
        
        return health_report
        
    except Exception as e:
        logger.error(f"Error in performance health check: {e}")
        return {'overall_health': 'error', 'error': str(e)}


# Background optimization tasks

async def background_cache_warmer(symbols: List[str], client, logger, interval: int = 300):
    """
    Background task to keep cache warm by periodically fetching data.
    
    Args:
        symbols: List of trading symbols
        client: Binance client
        logger: Logger instance
        interval: Interval in seconds between cache warming
    """
    while True:
        try:
            await preload_market_data(symbols, client, logger)
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in background cache warmer: {e}")
            await asyncio.sleep(60)


async def background_memory_optimizer(logger, interval: int = 600):
    """
    Background task to periodically optimize memory usage.
    
    Args:
        logger: Logger instance
        interval: Interval in seconds between memory optimization
    """
    while True:
        try:
            await optimize_memory_usage(logger)
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in background memory optimizer: {e}")
            await asyncio.sleep(60)


async def start_background_optimizations(symbols: List[str], client, logger):
    """
    Start background optimization tasks.
    
    Args:
        symbols: List of trading symbols
        client: Binance client
        logger: Logger instance
    
    Returns:
        List of background tasks
    """
    tasks = []
    
    # Start cache warmer
    cache_warmer_task = asyncio.create_task(
        background_cache_warmer(symbols, client, logger)
    )
    tasks.append(cache_warmer_task)
    
    # Start memory optimizer
    memory_optimizer_task = asyncio.create_task(
        background_memory_optimizer(logger)
    )
    tasks.append(memory_optimizer_task)
    
    logger.info("Background optimization tasks started")
    
    return tasks


async def stop_background_optimizations(tasks: List[asyncio.Task], logger):
    """
    Stop background optimization tasks.
    
    Args:
        tasks: List of background tasks to stop
        logger: Logger instance
    """
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    logger.info("Background optimization tasks stopped") 