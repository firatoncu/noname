"""
Async utilities for optimized asynchronous operations.

This module provides:
- Connection pooling for HTTP requests
- Request batching and rate limiting
- Retry mechanisms with exponential backoff
- Common async patterns and utilities
- Error handling and circuit breaker patterns
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import json
from datetime import datetime, timedelta
import weakref
import functools

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy types."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"


@dataclass
class RetryConfig:
    """Configuration for retry mechanisms."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retry_on_exceptions: Tuple[Exception, ...] = (
        aiohttp.ClientError,
        asyncio.TimeoutError,
        ConnectionError
    )


@dataclass
class ConnectionPoolConfig:
    """Configuration for HTTP connection pools."""
    connector_limit: int = 100
    connector_limit_per_host: int = 30
    timeout_total: float = 30.0
    timeout_connect: float = 10.0
    timeout_sock_read: float = 10.0
    keepalive_timeout: float = 30.0
    enable_cleanup_closed: bool = True


@dataclass
class BatchConfig:
    """Configuration for request batching."""
    batch_size: int = 10
    batch_timeout: float = 1.0
    max_concurrent_batches: int = 5


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: Tuple[Exception, ...] = (Exception,)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                await self._on_success()
                return result
            except self.config.expected_exception as e:
                await self._on_failure()
                raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
    
    async def _on_success(self):
        """Handle successful execution."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count += 1
    
    async def _on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class AsyncHTTPClient:
    """Optimized async HTTP client with connection pooling and retry logic."""
    
    def __init__(self, config: ConnectionPoolConfig = None):
        self.config = config or ConnectionPoolConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        self._timeout: Optional[aiohttp.ClientTimeout] = None
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    async def __aenter__(self):
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def _ensure_session(self):
        """Ensure HTTP session is created."""
        if self._session is None or self._session.closed:
            # Create connector with optimized settings
            self._connector = aiohttp.TCPConnector(
                limit=self.config.connector_limit,
                limit_per_host=self.config.connector_limit_per_host,
                keepalive_timeout=self.config.keepalive_timeout,
                enable_cleanup_closed=self.config.enable_cleanup_closed,
                use_dns_cache=True,
                ttl_dns_cache=300,
                family=0  # Allow both IPv4 and IPv6
            )
            
            # Create timeout configuration
            self._timeout = aiohttp.ClientTimeout(
                total=self.config.timeout_total,
                connect=self.config.timeout_connect,
                sock_read=self.config.timeout_sock_read
            )
            
            # Create session
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=self._timeout,
                headers={'User-Agent': 'AsyncTradingBot/1.0'}
            )
    
    def _get_circuit_breaker(self, host: str) -> CircuitBreaker:
        """Get or create circuit breaker for host."""
        if host not in self._circuit_breakers:
            config = CircuitBreakerConfig()
            self._circuit_breakers[host] = CircuitBreaker(config)
        return self._circuit_breakers[host]
    
    async def request(
        self,
        method: str,
        url: str,
        retry_config: RetryConfig = None,
        use_circuit_breaker: bool = True,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """Make HTTP request with retry and circuit breaker."""
        await self._ensure_session()
        retry_config = retry_config or RetryConfig()
        
        # Extract host for circuit breaker
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        
        async def _make_request():
            return await self._session.request(method, url, **kwargs)
        
        if use_circuit_breaker:
            circuit_breaker = self._get_circuit_breaker(host)
            return await self._retry_with_backoff(
                lambda: circuit_breaker.call(_make_request),
                retry_config
            )
        else:
            return await self._retry_with_backoff(_make_request, retry_config)
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make GET request."""
        return await self.request('GET', url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make POST request."""
        return await self.request('POST', url, **kwargs)
    
    async def put(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make PUT request."""
        return await self.request('PUT', url, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make DELETE request."""
        return await self.request('DELETE', url, **kwargs)
    
    async def _retry_with_backoff(
        self,
        func: Callable,
        retry_config: RetryConfig
    ):
        """Execute function with retry and backoff logic."""
        last_exception = None
        
        for attempt in range(retry_config.max_retries + 1):
            try:
                return await func()
            except retry_config.retry_on_exceptions as e:
                last_exception = e
                
                if attempt == retry_config.max_retries:
                    break
                
                delay = self._calculate_delay(attempt, retry_config)
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{retry_config.max_retries + 1}): {e}. "
                    f"Retrying in {delay:.2f}s"
                )
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for retry attempt."""
        if config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier ** attempt)
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (attempt + 1)
        elif config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay
        else:  # IMMEDIATE
            delay = 0
        
        # Apply maximum delay limit
        delay = min(delay, config.max_delay)
        
        # Add jitter to prevent thundering herd
        if config.jitter and delay > 0:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    async def close(self):
        """Close HTTP session and connector."""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._connector:
            await self._connector.close()


class RequestBatcher:
    """Batch multiple requests for efficient processing."""
    
    def __init__(self, config: BatchConfig = None):
        self.config = config or BatchConfig()
        self._pending_requests: List[Tuple[Callable, asyncio.Future]] = []
        self._batch_lock = asyncio.Lock()
        self._batch_task: Optional[asyncio.Task] = None
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_batches)
    
    async def add_request(self, request_func: Callable) -> Any:
        """Add request to batch and return future result."""
        future = asyncio.Future()
        
        async with self._batch_lock:
            self._pending_requests.append((request_func, future))
            
            # Start batch processing if not already running
            if self._batch_task is None or self._batch_task.done():
                self._batch_task = asyncio.create_task(self._process_batches())
        
        return await future
    
    async def _process_batches(self):
        """Process pending requests in batches."""
        while True:
            async with self._batch_lock:
                if not self._pending_requests:
                    break
                
                # Extract batch
                batch_size = min(len(self._pending_requests), self.config.batch_size)
                batch = self._pending_requests[:batch_size]
                self._pending_requests = self._pending_requests[batch_size:]
            
            # Process batch
            await self._execute_batch(batch)
            
            # Small delay between batches
            if self._pending_requests:
                await asyncio.sleep(0.01)
    
    async def _execute_batch(self, batch: List[Tuple[Callable, asyncio.Future]]):
        """Execute a batch of requests."""
        async with self._semaphore:
            tasks = []
            futures = []
            
            for request_func, future in batch:
                task = asyncio.create_task(request_func())
                tasks.append(task)
                futures.append(future)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Set results on futures
            for future, result in zip(futures, results):
                if isinstance(result, Exception):
                    future.set_exception(result)
                else:
                    future.set_result(result)


class RateLimiter:
    """Rate limiter for controlling request frequency."""
    
    def __init__(self, max_requests: int, time_window: float):
        self.max_requests = max_requests
        self.time_window = time_window
        self._requests: List[float] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request."""
        async with self._lock:
            now = time.time()
            
            # Remove old requests outside time window
            self._requests = [req_time for req_time in self._requests 
                           if now - req_time < self.time_window]
            
            # Check if we can make a request
            if len(self._requests) >= self.max_requests:
                # Calculate wait time
                oldest_request = min(self._requests)
                wait_time = self.time_window - (now - oldest_request)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    return await self.acquire()  # Recursive call after waiting
            
            # Record this request
            self._requests.append(now)


class AsyncTaskManager:
    """Manager for async tasks with lifecycle control."""
    
    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        self._task_groups: Dict[str, List[str]] = {}
        self._shutdown_event = asyncio.Event()
    
    def create_task(
        self,
        coro,
        name: str = None,
        group: str = None
    ) -> asyncio.Task:
        """Create and register a task."""
        task = asyncio.create_task(coro, name=name)
        task_id = name or f"task_{id(task)}"
        
        self._tasks[task_id] = task
        
        if group:
            if group not in self._task_groups:
                self._task_groups[group] = []
            self._task_groups[group].append(task_id)
        
        # Add done callback for cleanup
        task.add_done_callback(lambda t: self._cleanup_task(task_id))
        
        return task
    
    def _cleanup_task(self, task_id: str):
        """Clean up completed task."""
        if task_id in self._tasks:
            del self._tasks[task_id]
        
        # Remove from groups
        for group_tasks in self._task_groups.values():
            if task_id in group_tasks:
                group_tasks.remove(task_id)
    
    async def cancel_task(self, task_id: str):
        """Cancel a specific task."""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    async def cancel_group(self, group: str):
        """Cancel all tasks in a group."""
        if group in self._task_groups:
            tasks_to_cancel = self._task_groups[group].copy()
            for task_id in tasks_to_cancel:
                await self.cancel_task(task_id)
    
    async def cancel_all(self):
        """Cancel all managed tasks."""
        tasks_to_cancel = list(self._tasks.keys())
        for task_id in tasks_to_cancel:
            await self.cancel_task(task_id)
    
    def get_task_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all tasks."""
        status = {}
        for task_id, task in self._tasks.items():
            status[task_id] = {
                'done': task.done(),
                'cancelled': task.cancelled(),
                'exception': task.exception() if task.done() and not task.cancelled() else None
            }
        return status


# Utility functions for common async patterns

async def gather_with_concurrency(
    tasks: List[Callable],
    max_concurrency: int = 10,
    return_exceptions: bool = True
) -> List[Any]:
    """Execute tasks with limited concurrency."""
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def _execute_with_semaphore(task):
        async with semaphore:
            return await task()
    
    wrapped_tasks = [_execute_with_semaphore(task) for task in tasks]
    return await asyncio.gather(*wrapped_tasks, return_exceptions=return_exceptions)


async def timeout_after(seconds: float, coro):
    """Execute coroutine with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {seconds} seconds")
        raise


def async_cache(ttl_seconds: int = 300):
    """Decorator for caching async function results."""
    def decorator(func):
        cache = {}
        cache_times = {}
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            # Check if cached result is still valid
            if (key in cache and 
                key in cache_times and 
                current_time - cache_times[key] < ttl_seconds):
                return cache[key]
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache[key] = result
            cache_times[key] = current_time
            
            # Clean old cache entries
            expired_keys = [
                k for k, t in cache_times.items()
                if current_time - t >= ttl_seconds
            ]
            for k in expired_keys:
                cache.pop(k, None)
                cache_times.pop(k, None)
            
            return result
        
        return wrapper
    return decorator


@asynccontextmanager
async def async_resource_pool(
    create_resource: Callable,
    destroy_resource: Callable,
    max_size: int = 10
):
    """Context manager for async resource pooling."""
    pool = asyncio.Queue(maxsize=max_size)
    created_resources = []
    
    try:
        # Pre-populate pool
        for _ in range(max_size):
            resource = await create_resource()
            created_resources.append(resource)
            await pool.put(resource)
        
        yield pool
        
    finally:
        # Clean up all resources
        for resource in created_resources:
            try:
                await destroy_resource(resource)
            except Exception as e:
                logger.error(f"Error destroying resource: {e}")


# Global instances
_http_client: Optional[AsyncHTTPClient] = None
_task_manager: Optional[AsyncTaskManager] = None
_request_batcher: Optional[RequestBatcher] = None


def get_http_client() -> AsyncHTTPClient:
    """Get global HTTP client instance."""
    global _http_client
    if _http_client is None:
        _http_client = AsyncHTTPClient()
    return _http_client


def get_task_manager() -> AsyncTaskManager:
    """Get global task manager instance."""
    global _task_manager
    if _task_manager is None:
        _task_manager = AsyncTaskManager()
    return _task_manager


def get_request_batcher() -> RequestBatcher:
    """Get global request batcher instance."""
    global _request_batcher
    if _request_batcher is None:
        _request_batcher = RequestBatcher()
    return _request_batcher


async def cleanup_async_utils():
    """Clean up global async utilities."""
    global _http_client, _task_manager, _request_batcher
    
    if _http_client:
        await _http_client.close()
        _http_client = None
    
    if _task_manager:
        await _task_manager.cancel_all()
        _task_manager = None
    
    _request_batcher = None 