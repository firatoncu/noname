"""
Optimized Database Operations Module

This module provides:
- Connection pooling for database operations
- Query optimization and caching
- Batch insert/update operations
- Memory-efficient data handling
- Performance monitoring and optimization
"""

import asyncio
import asyncpg
# Make aioredis optional to avoid compatibility issues
try:
    import aioredis
    REDIS_AVAILABLE = True
except (ImportError, TypeError) as e:
    REDIS_AVAILABLE = False
    aioredis = None

import time
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import pickle
import hashlib
from contextlib import asynccontextmanager
import pandas as pd
import numpy as np

from .performance_optimizer import (
    cached, profiled, get_cache_system, get_memory_optimizer
)

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Configuration for database optimization."""
    # Connection pool settings
    min_pool_size: int = 5
    max_pool_size: int = 20
    pool_timeout: float = 30.0
    
    # Query optimization
    enable_query_cache: bool = True
    query_cache_ttl: int = 300
    max_cached_queries: int = 1000
    
    # Batch operations
    batch_size: int = 1000
    batch_timeout: float = 5.0
    
    # Performance monitoring
    enable_slow_query_log: bool = True
    slow_query_threshold: float = 1.0


@dataclass
class QueryMetrics:
    """Query performance metrics."""
    query_hash: str
    execution_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    max_time: float = 0.0
    min_time: float = float('inf')
    last_executed: datetime = field(default_factory=datetime.now)


class ConnectionPool:
    """Optimized database connection pool."""
    
    def __init__(self, config: DatabaseConfig, connection_string: str):
        self.config = config
        self.connection_string = connection_string
        self._pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()
        self._connection_count = 0
        self._active_connections = 0
    
    async def initialize(self):
        """Initialize the connection pool."""
        if self._pool is None:
            async with self._lock:
                if self._pool is None:
                    self._pool = await asyncpg.create_pool(
                        self.connection_string,
                        min_size=self.config.min_pool_size,
                        max_size=self.config.max_pool_size,
                        command_timeout=self.config.pool_timeout
                    )
                    logger.info(f"Database connection pool initialized with {self.config.max_pool_size} max connections")
    
    @asynccontextmanager
    async def acquire_connection(self):
        """Acquire a connection from the pool."""
        if self._pool is None:
            await self.initialize()
        
        self._active_connections += 1
        try:
            async with self._pool.acquire() as connection:
                yield connection
        finally:
            self._active_connections -= 1
    
    async def close(self):
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            'active_connections': self._active_connections,
            'pool_size': len(self._pool._holders) if self._pool else 0,
            'max_size': self.config.max_pool_size,
            'min_size': self.config.min_pool_size
        }


class QueryCache:
    """Cache for database query results."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._cache = {}
        self._timestamps = {}
        self._access_counts = {}
        self._lock = asyncio.Lock()
    
    def _create_cache_key(self, query: str, params: Tuple = None) -> str:
        """Create cache key for query and parameters."""
        key_data = f"{query}_{params}" if params else query
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, query: str, params: Tuple = None) -> Optional[Any]:
        """Get cached query result."""
        if not self.config.enable_query_cache:
            return None
        
        key = self._create_cache_key(query, params)
        
        async with self._lock:
            if key not in self._cache:
                return None
            
            # Check TTL
            if time.time() - self._timestamps[key] > self.config.query_cache_ttl:
                self._remove_key(key)
                return None
            
            # Update access count
            self._access_counts[key] = self._access_counts.get(key, 0) + 1
            
            return self._cache[key]
    
    async def set(self, query: str, result: Any, params: Tuple = None):
        """Cache query result."""
        if not self.config.enable_query_cache:
            return
        
        key = self._create_cache_key(query, params)
        
        async with self._lock:
            # Make space if needed
            if len(self._cache) >= self.config.max_cached_queries and key not in self._cache:
                # Remove least recently used
                lru_key = min(self._timestamps.keys(), key=lambda k: self._timestamps[k])
                self._remove_key(lru_key)
            
            self._cache[key] = result
            self._timestamps[key] = time.time()
            self._access_counts[key] = 1
    
    def _remove_key(self, key: str):
        """Remove key from cache."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._access_counts.pop(key, None)
    
    async def clear(self):
        """Clear the cache."""
        async with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._access_counts.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'size': len(self._cache),
            'max_size': self.config.max_cached_queries,
            'total_accesses': sum(self._access_counts.values()),
            'unique_queries': len(self._cache)
        }


class BatchProcessor:
    """Batch processor for database operations."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._insert_batches = {}
        self._update_batches = {}
        self._batch_locks = {}
        self._flush_tasks = {}
    
    async def add_insert(self, table: str, data: Dict[str, Any]):
        """Add data to insert batch."""
        if table not in self._insert_batches:
            self._insert_batches[table] = []
            self._batch_locks[table] = asyncio.Lock()
        
        async with self._batch_locks[table]:
            self._insert_batches[table].append(data)
            
            # Auto-flush if batch is full
            if len(self._insert_batches[table]) >= self.config.batch_size:
                await self._flush_insert_batch(table)
    
    async def add_update(self, table: str, data: Dict[str, Any], where_clause: str):
        """Add data to update batch."""
        if table not in self._update_batches:
            self._update_batches[table] = []
            self._batch_locks[table] = asyncio.Lock()
        
        async with self._batch_locks[table]:
            self._update_batches[table].append((data, where_clause))
            
            # Auto-flush if batch is full
            if len(self._update_batches[table]) >= self.config.batch_size:
                await self._flush_update_batch(table)
    
    async def _flush_insert_batch(self, table: str):
        """Flush insert batch for a table."""
        if table not in self._insert_batches or not self._insert_batches[table]:
            return
        
        batch_data = self._insert_batches[table].copy()
        self._insert_batches[table].clear()
        
        # Execute batch insert
        try:
            await self._execute_batch_insert(table, batch_data)
            logger.debug(f"Flushed {len(batch_data)} inserts for table {table}")
        except Exception as e:
            logger.error(f"Error flushing insert batch for {table}: {e}")
    
    async def _flush_update_batch(self, table: str):
        """Flush update batch for a table."""
        if table not in self._update_batches or not self._update_batches[table]:
            return
        
        batch_data = self._update_batches[table].copy()
        self._update_batches[table].clear()
        
        # Execute batch update
        try:
            await self._execute_batch_update(table, batch_data)
            logger.debug(f"Flushed {len(batch_data)} updates for table {table}")
        except Exception as e:
            logger.error(f"Error flushing update batch for {table}: {e}")
    
    async def _execute_batch_insert(self, table: str, batch_data: List[Dict[str, Any]]):
        """Execute batch insert operation."""
        # This would be implemented with actual database connection
        # For now, just log the operation
        logger.debug(f"Batch insert: {len(batch_data)} records to {table}")
    
    async def _execute_batch_update(self, table: str, batch_data: List[Tuple[Dict[str, Any], str]]):
        """Execute batch update operation."""
        # This would be implemented with actual database connection
        # For now, just log the operation
        logger.debug(f"Batch update: {len(batch_data)} records in {table}")
    
    async def flush_all(self):
        """Flush all pending batches."""
        for table in list(self._insert_batches.keys()):
            await self._flush_insert_batch(table)
        
        for table in list(self._update_batches.keys()):
            await self._flush_update_batch(table)


class OptimizedDatabase:
    """Optimized database operations with caching and performance improvements."""
    
    def __init__(self, config: DatabaseConfig = None, connection_string: str = None):
        self.config = config or DatabaseConfig()
        self._connection_pool = ConnectionPool(self.config, connection_string) if connection_string else None
        self._query_cache = QueryCache(self.config)
        self._batch_processor = BatchProcessor(self.config)
        self._query_metrics = {}
        self._memory_optimizer = get_memory_optimizer()
    
    @profiled
    async def execute_query(
        self,
        query: str,
        params: Tuple = None,
        fetch_all: bool = True,
        use_cache: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute optimized database query with caching.
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch_all: Whether to fetch all results
            use_cache: Whether to use query cache
        
        Returns:
            Query results or None
        """
        start_time = time.time()
        
        # Try cache first
        if use_cache:
            cached_result = await self._query_cache.get(query, params)
            if cached_result is not None:
                logger.debug("Query cache hit")
                return cached_result
        
        # Execute query
        try:
            if self._connection_pool:
                async with self._connection_pool.acquire_connection() as conn:
                    if fetch_all:
                        if params:
                            result = await conn.fetch(query, *params)
                        else:
                            result = await conn.fetch(query)
                    else:
                        if params:
                            result = await conn.fetchrow(query, *params)
                        else:
                            result = await conn.fetchrow(query)
                    
                    # Convert to list of dicts for consistency
                    if result:
                        if fetch_all:
                            result = [dict(row) for row in result]
                        else:
                            result = dict(result)
                    
                    # Cache result
                    if use_cache and result:
                        await self._query_cache.set(query, result, params)
                    
                    # Record metrics
                    execution_time = time.time() - start_time
                    await self._record_query_metrics(query, execution_time)
                    
                    return result
            else:
                logger.warning("No database connection pool available")
                return None
                
        except Exception as e:
            logger.error(f"Database query error: {e}")
            raise
    
    async def _record_query_metrics(self, query: str, execution_time: float):
        """Record query performance metrics."""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        if query_hash not in self._query_metrics:
            self._query_metrics[query_hash] = QueryMetrics(query_hash)
        
        metrics = self._query_metrics[query_hash]
        metrics.execution_count += 1
        metrics.total_time += execution_time
        metrics.avg_time = metrics.total_time / metrics.execution_count
        metrics.max_time = max(metrics.max_time, execution_time)
        metrics.min_time = min(metrics.min_time, execution_time)
        metrics.last_executed = datetime.now()
        
        # Log slow queries
        if (self.config.enable_slow_query_log and 
            execution_time > self.config.slow_query_threshold):
            logger.warning(f"Slow query detected: {execution_time:.3f}s - {query[:100]}...")
    
    @profiled
    async def batch_insert(self, table: str, data: List[Dict[str, Any]]):
        """Optimized batch insert operation."""
        for record in data:
            await self._batch_processor.add_insert(table, record)
    
    @profiled
    async def batch_update(self, table: str, updates: List[Tuple[Dict[str, Any], str]]):
        """Optimized batch update operation."""
        for data, where_clause in updates:
            await self._batch_processor.add_update(table, data, where_clause)
    
    async def optimize_dataframe_insert(
        self,
        table: str,
        df: pd.DataFrame,
        chunk_size: int = 1000
    ):
        """
        Optimize DataFrame insertion with memory management.
        
        Args:
            table: Target table name
            df: DataFrame to insert
            chunk_size: Size of chunks for processing
        """
        # Optimize DataFrame memory usage
        df = self._memory_optimizer.optimize_dataframe(df)
        
        # Process in chunks to manage memory
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i + chunk_size]
            records = chunk.to_dict('records')
            await self.batch_insert(table, records)
            
            # Force garbage collection after each chunk
            if i % (chunk_size * 10) == 0:
                self._memory_optimizer.force_garbage_collection()
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics."""
        # Query metrics summary
        query_stats = {}
        if self._query_metrics:
            total_queries = sum(m.execution_count for m in self._query_metrics.values())
            avg_execution_time = sum(m.avg_time for m in self._query_metrics.values()) / len(self._query_metrics)
            
            query_stats = {
                'total_queries': total_queries,
                'unique_queries': len(self._query_metrics),
                'avg_execution_time': avg_execution_time,
                'slow_queries': len([m for m in self._query_metrics.values() 
                                   if m.avg_time > self.config.slow_query_threshold])
            }
        
        return {
            'connection_pool': self._connection_pool.get_stats() if self._connection_pool else {},
            'query_cache': self._query_cache.get_stats(),
            'query_metrics': query_stats,
            'memory_usage': self._memory_optimizer.get_memory_usage()
        }
    
    async def cleanup(self):
        """Clean up database resources."""
        await self._batch_processor.flush_all()
        await self._query_cache.clear()
        
        if self._connection_pool:
            await self._connection_pool.close()


# InfluxDB optimizations
class OptimizedInfluxDB:
    """Optimized InfluxDB operations."""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self._batch_points = []
        self._batch_lock = asyncio.Lock()
        self._flush_task = None
    
    async def write_point(
        self,
        measurement: str,
        fields: Dict[str, Any],
        tags: Dict[str, str] = None,
        timestamp: datetime = None,
        batch: bool = True
    ):
        """Write a point to InfluxDB with batching."""
        point = {
            'measurement': measurement,
            'fields': fields,
            'tags': tags or {},
            'timestamp': timestamp or datetime.now()
        }
        
        if batch:
            async with self._batch_lock:
                self._batch_points.append(point)
                
                if len(self._batch_points) >= self.config.batch_size:
                    await self._flush_batch()
        else:
            await self._write_points_direct([point])
    
    async def _flush_batch(self):
        """Flush batch points to InfluxDB."""
        if not self._batch_points:
            return
        
        points_to_write = self._batch_points.copy()
        self._batch_points.clear()
        
        try:
            await self._write_points_direct(points_to_write)
            logger.debug(f"Flushed {len(points_to_write)} points to InfluxDB")
        except Exception as e:
            logger.error(f"Error flushing InfluxDB batch: {e}")
    
    async def _write_points_direct(self, points: List[Dict[str, Any]]):
        """Write points directly to InfluxDB."""
        # This would be implemented with actual InfluxDB client
        # For now, just log the operation
        logger.debug(f"Writing {len(points)} points to InfluxDB")
    
    async def start_auto_flush(self):
        """Start automatic batch flushing."""
        if self._flush_task is None:
            self._flush_task = asyncio.create_task(self._auto_flush_worker())
    
    async def _auto_flush_worker(self):
        """Worker for automatic batch flushing."""
        while True:
            try:
                await asyncio.sleep(self.config.batch_timeout)
                async with self._batch_lock:
                    if self._batch_points:
                        await self._flush_batch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-flush worker: {e}")
    
    async def cleanup(self):
        """Clean up InfluxDB resources."""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        await self._flush_batch()


# Global instances
_database: Optional[OptimizedDatabase] = None
_influxdb: Optional[OptimizedInfluxDB] = None


def get_optimized_database() -> OptimizedDatabase:
    """Get global optimized database instance."""
    global _database
    if _database is None:
        _database = OptimizedDatabase()
    return _database


def get_optimized_influxdb() -> OptimizedInfluxDB:
    """Get global optimized InfluxDB instance."""
    global _influxdb
    if _influxdb is None:
        _influxdb = OptimizedInfluxDB()
    return _influxdb


async def cleanup_database_optimizers():
    """Clean up all database optimizers."""
    global _database, _influxdb
    
    if _database:
        await _database.cleanup()
        _database = None
    
    if _influxdb:
        await _influxdb.cleanup()
        _influxdb = None 