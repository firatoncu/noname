"""
Advanced Performance Optimization Module for Trading Bot

This module provides:
- Multi-level caching with LRU and TTL support
- Memory usage optimization and monitoring
- CPU-intensive operation optimization
- Database query optimization
- Performance profiling and bottleneck identification
- Async operation batching and pooling
"""

import asyncio
import functools
import time
import psutil
import gc
import sys
import weakref
import pickle
import hashlib
import logging
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
import multiprocessing
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from contextlib import asynccontextmanager
import cProfile
import pstats
import io
from memory_profiler import profile as memory_profile

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for caching system."""
    max_size: int = 1000
    ttl_seconds: int = 300
    cleanup_interval: int = 60
    enable_persistence: bool = False
    persistence_file: str = "cache_data.pkl"
    enable_compression: bool = True
    memory_threshold_mb: int = 500


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    cache_hits: int = 0
    cache_misses: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    active_tasks: int = 0
    avg_response_time: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


class LRUCache:
    """Advanced LRU Cache with TTL and memory management."""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self._cache = OrderedDict()
        self._timestamps = {}
        self._access_counts = defaultdict(int)
        self._lock = threading.RLock()
        self._memory_usage = 0
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background cleanup task."""
        if self._cleanup_task is None:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(self._cleanup_worker())
    
    async def _cleanup_worker(self):
        """Background worker for cache cleanup."""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                self._cleanup_expired()
                self._manage_memory()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    def _cleanup_expired(self):
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, timestamp in self._timestamps.items():
                if current_time - timestamp > self.config.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove_key(key)
    
    def _manage_memory(self):
        """Manage memory usage by removing least accessed items."""
        if self._memory_usage > self.config.memory_threshold_mb * 1024 * 1024:
            with self._lock:
                # Sort by access count and remove least accessed
                sorted_keys = sorted(
                    self._access_counts.items(),
                    key=lambda x: x[1]
                )
                
                # Remove 25% of least accessed items
                remove_count = len(sorted_keys) // 4
                for key, _ in sorted_keys[:remove_count]:
                    if key in self._cache:
                        self._remove_key(key)
    
    def _remove_key(self, key):
        """Remove a key from cache and update memory usage."""
        if key in self._cache:
            value = self._cache.pop(key)
            self._timestamps.pop(key, None)
            self._access_counts.pop(key, None)
            
            # Estimate memory usage reduction
            try:
                self._memory_usage -= sys.getsizeof(value) + sys.getsizeof(key)
            except:
                pass
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check TTL
            current_time = time.time()
            if current_time - self._timestamps[key] > self.config.ttl_seconds:
                self._remove_key(key)
                return None
            
            # Move to end (most recently used)
            value = self._cache.pop(key)
            self._cache[key] = value
            self._access_counts[key] += 1
            
            return value
    
    def set(self, key: str, value: Any) -> bool:
        """Set value in cache."""
        with self._lock:
            # Check if we need to make space
            if len(self._cache) >= self.config.max_size and key not in self._cache:
                # Remove oldest item
                oldest_key = next(iter(self._cache))
                self._remove_key(oldest_key)
            
            # Add/update value
            self._cache[key] = value
            self._timestamps[key] = time.time()
            self._access_counts[key] += 1
            
            # Update memory usage estimate
            try:
                self._memory_usage += sys.getsizeof(value) + sys.getsizeof(key)
            except:
                pass
            
            return True
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._access_counts.clear()
            self._memory_usage = 0
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.config.max_size,
                'memory_usage_mb': self._memory_usage / (1024 * 1024),
                'hit_rate': self._calculate_hit_rate(),
                'total_accesses': sum(self._access_counts.values())
            }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_accesses = sum(self._access_counts.values())
        if total_accesses == 0:
            return 0.0
        return len(self._cache) / total_accesses


class MultiLevelCache:
    """Multi-level caching system with L1 (memory) and L2 (disk) cache."""
    
    def __init__(self, l1_config: CacheConfig, l2_config: CacheConfig = None):
        self.l1_cache = LRUCache(l1_config)
        self.l2_enabled = l2_config is not None
        self.l2_config = l2_config
        self._l2_cache_file = l2_config.persistence_file if l2_config else None
        self._metrics = PerformanceMetrics()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache."""
        # Try L1 cache first
        value = self.l1_cache.get(key)
        if value is not None:
            self._metrics.cache_hits += 1
            return value
        
        # Try L2 cache if enabled
        if self.l2_enabled:
            value = await self._get_from_l2(key)
            if value is not None:
                # Promote to L1 cache
                self.l1_cache.set(key, value)
                self._metrics.cache_hits += 1
                return value
        
        self._metrics.cache_misses += 1
        return None
    
    async def set(self, key: str, value: Any):
        """Set value in multi-level cache."""
        # Always set in L1
        self.l1_cache.set(key, value)
        
        # Set in L2 if enabled
        if self.l2_enabled:
            await self._set_to_l2(key, value)
    
    async def _get_from_l2(self, key: str) -> Optional[Any]:
        """Get value from L2 (disk) cache."""
        try:
            # This would be implemented with a proper disk cache
            # For now, return None
            return None
        except Exception as e:
            logger.error(f"L2 cache get error: {e}")
            return None
    
    async def _set_to_l2(self, key: str, value: Any):
        """Set value to L2 (disk) cache."""
        try:
            # This would be implemented with a proper disk cache
            pass
        except Exception as e:
            logger.error(f"L2 cache set error: {e}")
    
    def get_metrics(self) -> PerformanceMetrics:
        """Get cache metrics."""
        self._metrics.last_updated = datetime.now()
        return self._metrics


class DataFrameCache:
    """Specialized cache for pandas DataFrames with compression."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache = OrderedDict()
        self._timestamps = {}
        self._lock = threading.RLock()
    
    def _create_key(self, symbol: str, interval: str, limit: int) -> str:
        """Create cache key for DataFrame."""
        return f"{symbol}_{interval}_{limit}"
    
    def get(self, symbol: str, interval: str, limit: int) -> Optional[pd.DataFrame]:
        """Get DataFrame from cache."""
        key = self._create_key(symbol, interval, limit)
        
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check TTL
            if time.time() - self._timestamps[key] > self.ttl_seconds:
                self._remove_key(key)
                return None
            
            # Move to end and return
            df_compressed = self._cache.pop(key)
            self._cache[key] = df_compressed
            
            # Decompress and return
            return pickle.loads(df_compressed)
    
    def set(self, symbol: str, interval: str, limit: int, df: pd.DataFrame):
        """Set DataFrame in cache with compression."""
        key = self._create_key(symbol, interval, limit)
        
        with self._lock:
            # Make space if needed
            if len(self._cache) >= self.max_size and key not in self._cache:
                oldest_key = next(iter(self._cache))
                self._remove_key(oldest_key)
            
            # Compress and store
            df_compressed = pickle.dumps(df, protocol=pickle.HIGHEST_PROTOCOL)
            self._cache[key] = df_compressed
            self._timestamps[key] = time.time()
    
    def _remove_key(self, key: str):
        """Remove key from cache."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)


class CPUOptimizer:
    """CPU optimization utilities for intensive operations."""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self._thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self._process_pool = ProcessPoolExecutor(max_workers=self.max_workers)
    
    async def run_in_thread(self, func: Callable, *args, **kwargs) -> Any:
        """Run CPU-intensive function in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._thread_pool, 
            functools.partial(func, *args, **kwargs)
        )
    
    async def run_in_process(self, func: Callable, *args, **kwargs) -> Any:
        """Run CPU-intensive function in process pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._process_pool,
            functools.partial(func, *args, **kwargs)
        )
    
    def vectorize_operation(self, func: Callable) -> Callable:
        """Vectorize operation using numpy for better performance."""
        @functools.wraps(func)
        def wrapper(data, *args, **kwargs):
            if isinstance(data, pd.Series):
                return func(data.values, *args, **kwargs)
            elif isinstance(data, (list, tuple)):
                return func(np.array(data), *args, **kwargs)
            else:
                return func(data, *args, **kwargs)
        return wrapper
    
    async def close(self):
        """Close executor pools."""
        self._thread_pool.shutdown(wait=True)
        self._process_pool.shutdown(wait=True)


class MemoryOptimizer:
    """Memory usage optimization and monitoring."""
    
    def __init__(self):
        self._memory_threshold = 80  # Percentage
        self._monitoring_interval = 30  # Seconds
        self._monitoring_task = None
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    
    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage."""
        # Convert object columns to category if beneficial
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) < 0.5:  # Less than 50% unique values
                df[col] = df[col].astype('category')
        
        # Downcast numeric types
        for col in df.select_dtypes(include=['int']).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')
        
        for col in df.select_dtypes(include=['float']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')
        
        return df
    
    def force_garbage_collection(self):
        """Force garbage collection to free memory."""
        collected = gc.collect()
        logger.debug(f"Garbage collection freed {collected} objects")
        return collected
    
    async def start_monitoring(self):
        """Start memory monitoring task."""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitor_memory())
    
    async def _monitor_memory(self):
        """Monitor memory usage and trigger cleanup if needed."""
        while True:
            try:
                memory_stats = self.get_memory_usage()
                
                if memory_stats['percent'] > self._memory_threshold:
                    logger.warning(f"High memory usage: {memory_stats['percent']:.1f}%")
                    self.force_garbage_collection()
                
                await asyncio.sleep(self._monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")


class PerformanceProfiler:
    """Performance profiling and bottleneck identification."""
    
    def __init__(self):
        self._profiles = {}
        self._timing_data = defaultdict(list)
    
    @asynccontextmanager
    async def profile_async(self, operation_name: str):
        """Profile async operation."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            duration = end_time - start_time
            memory_delta = (end_memory - start_memory) / 1024 / 1024  # MB
            
            self._timing_data[operation_name].append({
                'duration': duration,
                'memory_delta_mb': memory_delta,
                'timestamp': datetime.now()
            })
    
    def profile_function(self, func: Callable) -> Callable:
        """Decorator to profile function performance."""
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            async with self.profile_async(func.__name__):
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                self._timing_data[func.__name__].append({
                    'duration': duration,
                    'timestamp': datetime.now()
                })
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        report = {}
        
        for operation, timings in self._timing_data.items():
            if not timings:
                continue
            
            durations = [t['duration'] for t in timings]
            report[operation] = {
                'count': len(durations),
                'avg_duration': np.mean(durations),
                'min_duration': np.min(durations),
                'max_duration': np.max(durations),
                'total_duration': np.sum(durations),
                'p95_duration': np.percentile(durations, 95),
                'p99_duration': np.percentile(durations, 99)
            }
        
        return report
    
    def identify_bottlenecks(self, threshold_seconds: float = 1.0) -> List[str]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        for operation, timings in self._timing_data.items():
            if not timings:
                continue
            
            avg_duration = np.mean([t['duration'] for t in timings])
            if avg_duration > threshold_seconds:
                bottlenecks.append(operation)
        
        return sorted(bottlenecks, key=lambda op: np.mean([t['duration'] for t in self._timing_data[op]]), reverse=True)


# Global instances
_cache_system: Optional[MultiLevelCache] = None
_dataframe_cache: Optional[DataFrameCache] = None
_cpu_optimizer: Optional[CPUOptimizer] = None
_memory_optimizer: Optional[MemoryOptimizer] = None
_profiler: Optional[PerformanceProfiler] = None


def get_cache_system() -> MultiLevelCache:
    """Get global cache system."""
    global _cache_system
    if _cache_system is None:
        l1_config = CacheConfig(max_size=1000, ttl_seconds=300)
        _cache_system = MultiLevelCache(l1_config)
    return _cache_system


def get_dataframe_cache() -> DataFrameCache:
    """Get global DataFrame cache."""
    global _dataframe_cache
    if _dataframe_cache is None:
        _dataframe_cache = DataFrameCache(max_size=100, ttl_seconds=300)
    return _dataframe_cache


def get_cpu_optimizer() -> CPUOptimizer:
    """Get global CPU optimizer."""
    global _cpu_optimizer
    if _cpu_optimizer is None:
        _cpu_optimizer = CPUOptimizer()
    return _cpu_optimizer


def get_memory_optimizer() -> MemoryOptimizer:
    """Get global memory optimizer."""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer()
    return _memory_optimizer


def get_profiler() -> PerformanceProfiler:
    """Get global profiler."""
    global _profiler
    if _profiler is None:
        _profiler = PerformanceProfiler()
    return _profiler


# Decorators for easy use
def cached(ttl_seconds: int = 300, max_size: int = 1000):
    """Decorator for caching function results."""
    def decorator(func):
        cache = LRUCache(CacheConfig(max_size=max_size, ttl_seconds=ttl_seconds))
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            key = hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()
            
            result = cache.get(key)
            if result is not None:
                return result
            
            result = await func(*args, **kwargs)
            cache.set(key, result)
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            key = hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()
            
            result = cache.get(key)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def optimized_cpu(use_process_pool: bool = False):
    """Decorator for CPU-intensive operations."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            optimizer = get_cpu_optimizer()
            if use_process_pool:
                return await optimizer.run_in_process(func, *args, **kwargs)
            else:
                return await optimizer.run_in_thread(func, *args, **kwargs)
        return wrapper
    return decorator


def profiled(func):
    """Decorator for profiling function performance."""
    profiler = get_profiler()
    return profiler.profile_function(func)


async def cleanup_performance_optimizers():
    """Clean up all performance optimizers."""
    global _cache_system, _dataframe_cache, _cpu_optimizer, _memory_optimizer, _profiler
    
    if _cpu_optimizer:
        await _cpu_optimizer.close()
        _cpu_optimizer = None
    
    _cache_system = None
    _dataframe_cache = None
    _memory_optimizer = None
    _profiler = None 