"""
Optimized Data Fetching Module with Advanced Caching

This module provides:
- Cached data fetching with intelligent cache management
- Memory-optimized DataFrame operations
- Batch data fetching for multiple symbols
- Compressed data storage
- Performance monitoring and optimization
"""

import asyncio
import pandas as pd
import numpy as np
import time
import logging
import functools
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import hashlib

from .performance_optimizer import (
    get_dataframe_cache, get_memory_optimizer, get_profiler,
    cached, profiled, DataFrameCache
)

logger = logging.getLogger(__name__)


@dataclass
class DataFetchConfig:
    """Configuration for data fetching optimization."""
    cache_ttl_seconds: int = 60  # Cache for 1 minute for real-time data
    max_cache_size: int = 200
    enable_compression: bool = True
    batch_size: int = 10
    concurrent_requests: int = 5
    memory_optimization: bool = True


class OptimizedDataFetcher:
    """Optimized data fetcher with caching and performance improvements."""
    
    def __init__(self, config: DataFetchConfig = None):
        self.config = config or DataFetchConfig()
        self._cache = DataFrameCache(
            max_size=self.config.max_cache_size,
            ttl_seconds=self.config.cache_ttl_seconds
        )
        self._memory_optimizer = get_memory_optimizer()
        self._profiler = get_profiler()
        self._request_semaphore = asyncio.Semaphore(self.config.concurrent_requests)
        
        # Performance tracking
        self._fetch_stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_requests': 0,
            'avg_fetch_time': 0.0,
            'memory_saved_mb': 0.0
        }
    
    @profiled
    async def fetch_klines_data(
        self,
        symbol: str,
        client,
        lookback_period: int = 500,
        interval: str = '1m'
    ) -> Tuple[pd.DataFrame, float]:
        """
        Fetch klines data with caching and optimization.
        
        Returns:
            Tuple of (DataFrame, close_price)
        """
        start_time = time.time()
        
        # Try to get from cache first
        cached_df = self._cache.get(symbol, interval, lookback_period)
        if cached_df is not None:
            self._fetch_stats['cache_hits'] += 1
            close_price = cached_df['close'].iloc[-1]
            logger.debug(f"Cache hit for {symbol} {interval} {lookback_period}")
            return cached_df, close_price
        
        # Cache miss - fetch from API
        self._fetch_stats['cache_misses'] += 1
        self._fetch_stats['total_requests'] += 1
        
        async with self._request_semaphore:
            try:
                # Fetch data from Binance
                klines = await client.futures_klines(
                    symbol=symbol,
                    interval=interval,
                    limit=lookback_period
                )
                
                # Create optimized DataFrame
                df = self._create_optimized_dataframe(klines)
                close_price = df['close'].iloc[-1]
                
                # Cache the result
                self._cache.set(symbol, interval, lookback_period, df)
                
                # Update performance stats
                fetch_time = time.time() - start_time
                self._update_fetch_stats(fetch_time)
                
                logger.debug(f"Fetched and cached {symbol} {interval} {lookback_period} in {fetch_time:.3f}s")
                
                return df, close_price
                
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                raise
    
    def _create_optimized_dataframe(self, klines: List[List]) -> pd.DataFrame:
        """Create memory-optimized DataFrame from klines data."""
        # Define columns
        columns = [
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ]
        
        # Create DataFrame
        df = pd.DataFrame(klines, columns=columns)
        
        # Optimize data types for memory efficiency
        if self.config.memory_optimization:
            df = self._optimize_dataframe_memory(df)
        
        return df
    
    def _optimize_dataframe_memory(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage."""
        # Convert numeric columns to appropriate types
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 
                          'quote_asset_volume', 'taker_buy_base_asset_volume', 
                          'taker_buy_quote_asset_volume']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], downcast='float')
        
        # Convert integer columns
        int_columns = ['timestamp', 'close_time', 'number_of_trades']
        for col in int_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], downcast='integer')
        
        # Drop unnecessary columns to save memory
        if 'ignore' in df.columns:
            df = df.drop('ignore', axis=1)
        
        return df
    
    @profiled
    async def batch_fetch_data(
        self,
        symbols: List[str],
        client,
        lookback_period: int = 500,
        interval: str = '1m'
    ) -> Dict[str, Tuple[pd.DataFrame, float]]:
        """
        Batch fetch data for multiple symbols with optimized concurrency.
        
        Returns:
            Dictionary mapping symbol to (DataFrame, close_price)
        """
        # Create tasks for concurrent fetching
        tasks = []
        for symbol in symbols:
            task = self.fetch_klines_data(symbol, client, lookback_period, interval)
            tasks.append((symbol, task))
        
        # Execute with controlled concurrency
        results = {}
        for i in range(0, len(tasks), self.config.batch_size):
            batch = tasks[i:i + self.config.batch_size]
            batch_results = await asyncio.gather(
                *[task for _, task in batch],
                return_exceptions=True
            )
            
            # Process batch results
            for j, (symbol, _) in enumerate(batch):
                result = batch_results[j]
                if isinstance(result, Exception):
                    logger.error(f"Error fetching data for {symbol}: {result}")
                    continue
                results[symbol] = result
        
        return results
    
    def _update_fetch_stats(self, fetch_time: float):
        """Update fetch performance statistics."""
        # Update average fetch time using exponential moving average
        alpha = 0.1  # Smoothing factor
        if self._fetch_stats['avg_fetch_time'] == 0:
            self._fetch_stats['avg_fetch_time'] = fetch_time
        else:
            self._fetch_stats['avg_fetch_time'] = (
                alpha * fetch_time + 
                (1 - alpha) * self._fetch_stats['avg_fetch_time']
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        total_requests = self._fetch_stats['cache_hits'] + self._fetch_stats['cache_misses']
        cache_hit_rate = (
            self._fetch_stats['cache_hits'] / total_requests 
            if total_requests > 0 else 0
        )
        
        return {
            'cache_hit_rate': cache_hit_rate,
            'total_requests': total_requests,
            'cache_hits': self._fetch_stats['cache_hits'],
            'cache_misses': self._fetch_stats['cache_misses'],
            'avg_fetch_time': self._fetch_stats['avg_fetch_time'],
            'cache_size': len(self._cache._cache),
            'memory_usage': self._memory_optimizer.get_memory_usage()
        }
    
    def clear_cache(self):
        """Clear the data cache."""
        self._cache._cache.clear()
        self._cache._timestamps.clear()
        logger.info("Data cache cleared")


# Global instance
_data_fetcher: Optional[OptimizedDataFetcher] = None


def get_data_fetcher() -> OptimizedDataFetcher:
    """Get global optimized data fetcher instance."""
    global _data_fetcher
    if _data_fetcher is None:
        _data_fetcher = OptimizedDataFetcher()
    return _data_fetcher


# Optimized version of the original binance_fetch_data function
@cached(ttl_seconds=60, max_size=200)
@profiled
async def binance_fetch_data(
    lookback_period: int,
    symbol: str,
    client,
    interval: str = '1m'
) -> Tuple[pd.DataFrame, float]:
    """
    Optimized version of binance_fetch_data with caching.
    
    This function maintains compatibility with the original API while
    adding performance optimizations.
    """
    fetcher = get_data_fetcher()
    return await fetcher.fetch_klines_data(symbol, client, lookback_period, interval)


# Batch fetching function for improved performance
@profiled
async def batch_fetch_symbols_data(
    symbols: List[str],
    client,
    lookback_period: int = 500,
    interval: str = '1m'
) -> Dict[str, Tuple[pd.DataFrame, float]]:
    """
    Fetch data for multiple symbols concurrently with optimization.
    
    Args:
        symbols: List of trading symbols
        client: Binance client
        lookback_period: Number of periods to fetch
        interval: Time interval for klines
    
    Returns:
        Dictionary mapping symbol to (DataFrame, close_price)
    """
    fetcher = get_data_fetcher()
    return await fetcher.batch_fetch_data(symbols, client, lookback_period, interval)


# Technical indicator caching
class IndicatorCache:
    """Cache for technical indicators to avoid recalculation."""
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 500):
        self._cache = {}
        self._timestamps = {}
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
    
    def _create_key(self, symbol: str, indicator_name: str, params: Dict) -> str:
        """Create cache key for indicator."""
        params_str = str(sorted(params.items()))
        key_str = f"{symbol}_{indicator_name}_{params_str}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, symbol: str, indicator_name: str, params: Dict) -> Optional[Any]:
        """Get cached indicator value."""
        key = self._create_key(symbol, indicator_name, params)
        
        if key not in self._cache:
            return None
        
        # Check TTL
        if time.time() - self._timestamps[key] > self.ttl_seconds:
            self._remove_key(key)
            return None
        
        return self._cache[key]
    
    def set(self, symbol: str, indicator_name: str, params: Dict, value: Any):
        """Set cached indicator value."""
        key = self._create_key(symbol, indicator_name, params)
        
        # Make space if needed
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest_key = min(self._timestamps.keys(), key=lambda k: self._timestamps[k])
            self._remove_key(oldest_key)
        
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def _remove_key(self, key: str):
        """Remove key from cache."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)


# Global indicator cache
_indicator_cache = IndicatorCache()


def cached_indicator(indicator_name: str, ttl_seconds: int = 300):
    """Decorator for caching technical indicators."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(data, symbol: str = None, **kwargs):
            if symbol is None:
                # If no symbol provided, execute without caching
                return func(data, **kwargs)
            
            # Try to get from cache
            cached_result = _indicator_cache.get(symbol, indicator_name, kwargs)
            if cached_result is not None:
                return cached_result
            
            # Calculate and cache result
            result = func(data, **kwargs)
            _indicator_cache.set(symbol, indicator_name, kwargs, result)
            
            return result
        return wrapper
    return decorator


# Performance monitoring function
async def monitor_data_performance():
    """Monitor and log data fetching performance."""
    fetcher = get_data_fetcher()
    
    while True:
        try:
            stats = fetcher.get_performance_stats()
            
            logger.info(
                f"Data Performance - Cache Hit Rate: {stats['cache_hit_rate']:.2%}, "
                f"Avg Fetch Time: {stats['avg_fetch_time']:.3f}s, "
                f"Memory Usage: {stats['memory_usage']['rss_mb']:.1f}MB"
            )
            
            # Log warning if performance is degrading
            if stats['cache_hit_rate'] < 0.5:
                logger.warning("Low cache hit rate detected - consider adjusting cache settings")
            
            if stats['avg_fetch_time'] > 2.0:
                logger.warning("High fetch times detected - possible network issues")
            
            await asyncio.sleep(60)  # Monitor every minute
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in performance monitoring: {e}")
            await asyncio.sleep(60)


# Cleanup function
async def cleanup_data_fetcher():
    """Clean up data fetcher resources."""
    global _data_fetcher
    if _data_fetcher:
        _data_fetcher.clear_cache()
        _data_fetcher = None
    
    # Clear indicator cache
    _indicator_cache._cache.clear()
    _indicator_cache._timestamps.clear() 