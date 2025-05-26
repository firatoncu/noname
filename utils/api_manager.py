"""
Advanced API Manager for Binance with sophisticated rate limiting.

This module provides:
- Advanced rate limiting with weight-based tracking
- Request queuing with priority management
- Automatic backoff strategies with circuit breaker
- Request batching and optimization
- Real-time rate limit monitoring
- Adaptive throttling based on API responses
"""

import asyncio
import aiohttp
import hmac
import hashlib
import time
import json
import logging
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from collections import deque, defaultdict
from urllib.parse import urlencode
import weakref
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)


class RequestPriority(IntEnum):
    """Request priority levels (higher number = higher priority)."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class RequestType(Enum):
    """Types of API requests for rate limiting."""
    GENERAL = "general"
    ORDER = "order"
    MARKET_DATA = "market_data"
    ACCOUNT = "account"
    WEBSOCKET = "websocket"


class BackoffStrategy(Enum):
    """Backoff strategies for rate limiting."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"
    ADAPTIVE = "adaptive"


@dataclass
class RequestWeight:
    """Weight configuration for different endpoints."""
    endpoint: str
    weight: int
    request_type: RequestType = RequestType.GENERAL
    max_per_minute: Optional[int] = None


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    # Binance rate limits
    requests_per_minute: int = 1200
    orders_per_second: int = 10
    orders_per_day: int = 200000
    
    # Weight limits
    weight_per_minute: int = 1200
    weight_per_second: int = 50
    
    # Backoff configuration
    backoff_strategy: BackoffStrategy = BackoffStrategy.ADAPTIVE
    initial_backoff: float = 1.0
    max_backoff: float = 300.0
    backoff_multiplier: float = 2.0
    
    # Circuit breaker
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    
    # Queue configuration
    max_queue_size: int = 10000
    queue_timeout: float = 30.0
    
    # Adaptive settings
    enable_adaptive_throttling: bool = True
    target_success_rate: float = 0.95
    monitoring_window: int = 100


@dataclass
class QueuedRequest:
    """Queued request with metadata."""
    method: str
    endpoint: str
    params: Dict[str, Any]
    signed: bool
    request_type: RequestType
    priority: RequestPriority
    weight: int
    future: asyncio.Future
    timestamp: float
    retries: int = 0
    max_retries: int = 3


@dataclass
class RateLimitState:
    """Current rate limit state."""
    requests_this_minute: int = 0
    requests_this_second: int = 0
    weight_this_minute: int = 0
    weight_this_second: int = 0
    orders_this_second: int = 0
    orders_this_day: int = 0
    last_reset_minute: float = 0
    last_reset_second: float = 0
    last_reset_day: float = 0


@dataclass
class APIMetrics:
    """API performance metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    average_response_time: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    success_rate: float = 1.0
    last_updated: float = field(default_factory=time.time)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class AdvancedRateLimiter:
    """Advanced rate limiter with weight tracking and adaptive throttling."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.state = RateLimitState()
        self.metrics = APIMetrics()
        self._lock = asyncio.Lock()
        
        # Circuit breaker
        self.circuit_state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        
        # Adaptive throttling
        self.current_throttle_factor = 1.0
        self.recent_responses = deque(maxlen=config.monitoring_window)
        
        # Weight tracking for endpoints
        self.endpoint_weights = self._initialize_endpoint_weights()
    
    def _initialize_endpoint_weights(self) -> Dict[str, RequestWeight]:
        """Initialize endpoint weight mappings."""
        weights = {
            # Market data endpoints
            '/fapi/v1/ping': RequestWeight('/fapi/v1/ping', 1, RequestType.MARKET_DATA),
            '/fapi/v1/time': RequestWeight('/fapi/v1/time', 1, RequestType.MARKET_DATA),
            '/fapi/v1/exchangeInfo': RequestWeight('/fapi/v1/exchangeInfo', 1, RequestType.MARKET_DATA),
            '/fapi/v1/depth': RequestWeight('/fapi/v1/depth', 2, RequestType.MARKET_DATA),
            '/fapi/v1/trades': RequestWeight('/fapi/v1/trades', 1, RequestType.MARKET_DATA),
            '/fapi/v1/historicalTrades': RequestWeight('/fapi/v1/historicalTrades', 5, RequestType.MARKET_DATA),
            '/fapi/v1/aggTrades': RequestWeight('/fapi/v1/aggTrades', 1, RequestType.MARKET_DATA),
            '/fapi/v1/klines': RequestWeight('/fapi/v1/klines', 1, RequestType.MARKET_DATA),
            '/fapi/v1/continuousKlines': RequestWeight('/fapi/v1/continuousKlines', 1, RequestType.MARKET_DATA),
            '/fapi/v1/indexPriceKlines': RequestWeight('/fapi/v1/indexPriceKlines', 1, RequestType.MARKET_DATA),
            '/fapi/v1/markPriceKlines': RequestWeight('/fapi/v1/markPriceKlines', 1, RequestType.MARKET_DATA),
            '/fapi/v1/premiumIndex': RequestWeight('/fapi/v1/premiumIndex', 1, RequestType.MARKET_DATA),
            '/fapi/v1/fundingRate': RequestWeight('/fapi/v1/fundingRate', 1, RequestType.MARKET_DATA),
            '/fapi/v1/ticker/24hr': RequestWeight('/fapi/v1/ticker/24hr', 1, RequestType.MARKET_DATA),
            '/fapi/v1/ticker/price': RequestWeight('/fapi/v1/ticker/price', 1, RequestType.MARKET_DATA),
            '/fapi/v1/ticker/bookTicker': RequestWeight('/fapi/v1/ticker/bookTicker', 1, RequestType.MARKET_DATA),
            
            # Account endpoints
            '/fapi/v2/account': RequestWeight('/fapi/v2/account', 5, RequestType.ACCOUNT),
            '/fapi/v2/balance': RequestWeight('/fapi/v2/balance', 5, RequestType.ACCOUNT),
            '/fapi/v2/positionRisk': RequestWeight('/fapi/v2/positionRisk', 5, RequestType.ACCOUNT),
            '/fapi/v1/userTrades': RequestWeight('/fapi/v1/userTrades', 5, RequestType.ACCOUNT),
            '/fapi/v1/income': RequestWeight('/fapi/v1/income', 30, RequestType.ACCOUNT),
            
            # Order endpoints
            '/fapi/v1/order': RequestWeight('/fapi/v1/order', 1, RequestType.ORDER),
            '/fapi/v1/batchOrders': RequestWeight('/fapi/v1/batchOrders', 5, RequestType.ORDER),
            '/fapi/v1/allOpenOrders': RequestWeight('/fapi/v1/allOpenOrders', 1, RequestType.ORDER),
            '/fapi/v1/openOrders': RequestWeight('/fapi/v1/openOrders', 1, RequestType.ORDER),
            '/fapi/v1/allOrders': RequestWeight('/fapi/v1/allOrders', 5, RequestType.ORDER),
            '/fapi/v1/countdownCancelAll': RequestWeight('/fapi/v1/countdownCancelAll', 10, RequestType.ORDER),
        }
        return weights
    
    async def acquire(self, endpoint: str, request_type: RequestType = RequestType.GENERAL) -> bool:
        """Acquire permission to make a request."""
        async with self._lock:
            # Check circuit breaker
            if not self._check_circuit_breaker():
                raise Exception("Circuit breaker is OPEN - too many failures")
            
            # Get request weight
            weight = self._get_endpoint_weight(endpoint)
            
            # Update rate limit counters
            self._update_counters()
            
            # Check if request can be made
            if not self._can_make_request(weight, request_type):
                return False
            
            # Apply adaptive throttling
            if self.config.enable_adaptive_throttling:
                throttle_delay = self._calculate_adaptive_delay()
                if throttle_delay > 0:
                    await asyncio.sleep(throttle_delay)
            
            # Record the request
            self._record_request(weight, request_type)
            return True
    
    def _get_endpoint_weight(self, endpoint: str) -> int:
        """Get weight for an endpoint."""
        if endpoint in self.endpoint_weights:
            return self.endpoint_weights[endpoint].weight
        return 1  # Default weight
    
    def _update_counters(self):
        """Update rate limit counters."""
        now = time.time()
        
        # Reset minute counters
        if now - self.state.last_reset_minute >= 60:
            self.state.requests_this_minute = 0
            self.state.weight_this_minute = 0
            self.state.last_reset_minute = now
        
        # Reset second counters
        if now - self.state.last_reset_second >= 1:
            self.state.requests_this_second = 0
            self.state.weight_this_second = 0
            self.state.orders_this_second = 0
            self.state.last_reset_second = now
        
        # Reset day counters
        if now - self.state.last_reset_day >= 86400:
            self.state.orders_this_day = 0
            self.state.last_reset_day = now
    
    def _can_make_request(self, weight: int, request_type: RequestType) -> bool:
        """Check if request can be made within rate limits."""
        # Check minute limits
        if (self.state.requests_this_minute >= self.config.requests_per_minute or
            self.state.weight_this_minute + weight > self.config.weight_per_minute):
            return False
        
        # Check second limits
        if self.state.weight_this_second + weight > self.config.weight_per_second:
            return False
        
        # Check order-specific limits
        if request_type == RequestType.ORDER:
            if (self.state.orders_this_second >= self.config.orders_per_second or
                self.state.orders_this_day >= self.config.orders_per_day):
                return False
        
        return True
    
    def _record_request(self, weight: int, request_type: RequestType):
        """Record a request in the rate limit counters."""
        self.state.requests_this_minute += 1
        self.state.requests_this_second += 1
        self.state.weight_this_minute += weight
        self.state.weight_this_second += weight
        
        if request_type == RequestType.ORDER:
            self.state.orders_this_second += 1
            self.state.orders_this_day += 1
    
    def _check_circuit_breaker(self) -> bool:
        """Check circuit breaker state."""
        now = time.time()
        
        if self.circuit_state == CircuitBreakerState.OPEN:
            if now - self.last_failure_time >= self.config.recovery_timeout:
                self.circuit_state = CircuitBreakerState.HALF_OPEN
                self.failure_count = 0
                return True
            return False
        
        return True
    
    def _calculate_adaptive_delay(self) -> float:
        """Calculate adaptive delay based on recent performance."""
        if len(self.recent_responses) < 10:
            return 0
        
        # Calculate current success rate
        recent_successes = sum(1 for success, _ in self.recent_responses if success)
        current_success_rate = recent_successes / len(self.recent_responses)
        
        # Adjust throttle factor based on success rate
        if current_success_rate < self.config.target_success_rate:
            self.current_throttle_factor = min(self.current_throttle_factor * 1.5, 5.0)
        else:
            self.current_throttle_factor = max(self.current_throttle_factor * 0.9, 1.0)
        
        # Calculate delay
        base_delay = 1.0 / self.config.requests_per_minute * 60
        return base_delay * (self.current_throttle_factor - 1.0)
    
    def record_response(self, success: bool, response_time: float, status_code: int = None):
        """Record API response for metrics and adaptive throttling."""
        self.metrics.total_requests += 1
        
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
            
            # Handle rate limiting
            if status_code == 429:
                self.metrics.rate_limited_requests += 1
                self._handle_rate_limit_exceeded()
            else:
                self._handle_failure()
        
        # Update response time metrics
        self.metrics.response_times.append(response_time)
        if self.metrics.response_times:
            self.metrics.average_response_time = statistics.mean(self.metrics.response_times)
        
        # Update success rate
        if self.metrics.total_requests > 0:
            self.metrics.success_rate = self.metrics.successful_requests / self.metrics.total_requests
        
        # Record for adaptive throttling
        self.recent_responses.append((success, response_time))
        self.metrics.last_updated = time.time()
    
    def _handle_rate_limit_exceeded(self):
        """Handle rate limit exceeded response."""
        # Increase throttle factor significantly
        self.current_throttle_factor = min(self.current_throttle_factor * 2.0, 10.0)
        
        # Record failure for circuit breaker
        self._handle_failure()
    
    def _handle_failure(self):
        """Handle request failure."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.circuit_state = CircuitBreakerState.OPEN
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return {
            'total_requests': self.metrics.total_requests,
            'successful_requests': self.metrics.successful_requests,
            'failed_requests': self.metrics.failed_requests,
            'rate_limited_requests': self.metrics.rate_limited_requests,
            'success_rate': self.metrics.success_rate,
            'average_response_time': self.metrics.average_response_time,
            'current_throttle_factor': self.current_throttle_factor,
            'circuit_state': self.circuit_state.value,
            'rate_limit_state': {
                'requests_this_minute': self.state.requests_this_minute,
                'weight_this_minute': self.state.weight_this_minute,
                'requests_this_second': self.state.requests_this_second,
                'weight_this_second': self.state.weight_this_second,
                'orders_this_second': self.state.orders_this_second,
                'orders_this_day': self.state.orders_this_day,
            }
        }


class RequestQueue:
    """Priority queue for API requests."""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.queues = {priority: deque() for priority in RequestPriority}
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Condition(self._lock)
        self._size = 0
    
    async def put(self, request: QueuedRequest) -> bool:
        """Add request to queue."""
        async with self._not_empty:
            if self._size >= self.max_size:
                return False
            
            self.queues[request.priority].append(request)
            self._size += 1
            self._not_empty.notify()
            return True
    
    async def get(self) -> Optional[QueuedRequest]:
        """Get highest priority request from queue."""
        async with self._not_empty:
            while self._size == 0:
                await self._not_empty.wait()
            
            # Get from highest priority queue first
            for priority in sorted(RequestPriority, reverse=True):
                if self.queues[priority]:
                    request = self.queues[priority].popleft()
                    self._size -= 1
                    return request
            
            return None
    
    async def get_nowait(self) -> Optional[QueuedRequest]:
        """Get request without waiting."""
        async with self._lock:
            if self._size == 0:
                return None
            
            for priority in sorted(RequestPriority, reverse=True):
                if self.queues[priority]:
                    request = self.queues[priority].popleft()
                    self._size -= 1
                    return request
            
            return None
    
    def size(self) -> int:
        """Get current queue size."""
        return self._size
    
    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        return {
            'total_size': self._size,
            'critical': len(self.queues[RequestPriority.CRITICAL]),
            'high': len(self.queues[RequestPriority.HIGH]),
            'normal': len(self.queues[RequestPriority.NORMAL]),
            'low': len(self.queues[RequestPriority.LOW]),
        }


class APIManager:
    """Sophisticated API Manager for Binance with advanced rate limiting."""
    
    def __init__(self, api_key: str, api_secret: str, config: RateLimitConfig = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.config = config or RateLimitConfig()
        
        # Core components
        self.rate_limiter = AdvancedRateLimiter(self.config)
        self.request_queue = RequestQueue(self.config.max_queue_size)
        
        # HTTP client
        self._session: Optional[aiohttp.ClientSession] = None
        self._base_url = "https://fapi.binance.com"
        
        # Request processing
        self._worker_tasks: List[asyncio.Task] = []
        self._is_running = False
        self._shutdown_event = asyncio.Event()
        
        # Batching
        self._batch_queues = defaultdict(list)
        self._batch_timers = {}
        self._batch_lock = asyncio.Lock()
        
        # Metrics
        self._start_time = time.time()
    
    async def start(self, num_workers: int = 5):
        """Start the API manager."""
        if self._is_running:
            return
        
        self._is_running = True
        self._shutdown_event.clear()
        
        # Create HTTP session
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'AdvancedTradingBot/1.0'}
        )
        
        # Start worker tasks
        for i in range(num_workers):
            task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._worker_tasks.append(task)
        
        logger.info(f"API Manager started with {num_workers} workers")
    
    async def stop(self):
        """Stop the API manager."""
        if not self._is_running:
            return
        
        self._is_running = False
        self._shutdown_event.set()
        
        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        
        # Close HTTP session
        if self._session:
            await self._session.close()
        
        self._worker_tasks.clear()
        logger.info("API Manager stopped")
    
    async def _worker_loop(self, worker_name: str):
        """Worker loop for processing requests."""
        logger.info(f"Worker {worker_name} started")
        
        try:
            while self._is_running:
                try:
                    # Get request from queue
                    request = await asyncio.wait_for(
                        self.request_queue.get(),
                        timeout=1.0
                    )
                    
                    if request is None:
                        continue
                    
                    # Check if request has timed out
                    if time.time() - request.timestamp > self.config.queue_timeout:
                        request.future.set_exception(
                            asyncio.TimeoutError("Request timed out in queue")
                        )
                        continue
                    
                    # Process the request
                    await self._process_request(request)
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Worker {worker_name} error: {e}")
                    await asyncio.sleep(1)
        
        except asyncio.CancelledError:
            pass
        finally:
            logger.info(f"Worker {worker_name} stopped")
    
    async def _process_request(self, request: QueuedRequest):
        """Process a single request."""
        try:
            # Wait for rate limiter
            while not await self.rate_limiter.acquire(request.endpoint, request.request_type):
                await asyncio.sleep(0.1)
            
            # Make the HTTP request
            start_time = time.time()
            response_data = await self._make_http_request(request)
            response_time = time.time() - start_time
            
            # Record successful response
            self.rate_limiter.record_response(True, response_time)
            
            # Set result
            if not request.future.done():
                request.future.set_result(response_data)
        
        except Exception as e:
            response_time = time.time() - start_time if 'start_time' in locals() else 0
            
            # Determine if this is a rate limit error
            status_code = getattr(e, 'status', None)
            is_rate_limit = status_code == 429
            
            # Record failed response
            self.rate_limiter.record_response(False, response_time, status_code)
            
            # Handle retries
            if request.retries < request.max_retries and (is_rate_limit or status_code in [500, 502, 503]):
                request.retries += 1
                
                # Calculate backoff delay
                delay = self._calculate_backoff_delay(request.retries)
                await asyncio.sleep(delay)
                
                # Re-queue the request
                await self.request_queue.put(request)
            else:
                # Set exception
                if not request.future.done():
                    request.future.set_exception(e)
    
    def _calculate_backoff_delay(self, retry_count: int) -> float:
        """Calculate backoff delay based on strategy."""
        if self.config.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.config.initial_backoff * (self.config.backoff_multiplier ** (retry_count - 1))
        elif self.config.backoff_strategy == BackoffStrategy.LINEAR:
            delay = self.config.initial_backoff * retry_count
        elif self.config.backoff_strategy == BackoffStrategy.FIBONACCI:
            fib = [1, 1]
            for i in range(2, retry_count + 1):
                fib.append(fib[i-1] + fib[i-2])
            delay = self.config.initial_backoff * fib[retry_count]
        else:  # ADAPTIVE
            # Use current throttle factor
            delay = self.config.initial_backoff * self.rate_limiter.current_throttle_factor * retry_count
        
        return min(delay, self.config.max_backoff)
    
    async def _make_http_request(self, request: QueuedRequest) -> Dict[str, Any]:
        """Make the actual HTTP request."""
        url = f"{self._base_url}{request.endpoint}"
        
        # Prepare headers
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Handle signed requests
        params = request.params.copy()
        if request.signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        # Make request
        if request.method.upper() == 'GET':
            async with self._session.get(url, params=params, headers=headers) as response:
                return await self._handle_response(response)
        elif request.method.upper() == 'POST':
            async with self._session.post(url, json=params, headers=headers) as response:
                return await self._handle_response(response)
        elif request.method.upper() == 'DELETE':
            async with self._session.delete(url, params=params, headers=headers) as response:
                return await self._handle_response(response)
        else:
            raise ValueError(f"Unsupported HTTP method: {request.method}")
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature."""
        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle HTTP response."""
        if response.status == 200:
            return await response.json()
        elif response.status == 429:
            # Rate limit exceeded
            retry_after = response.headers.get('Retry-After', '1')
            raise aiohttp.ClientResponseError(
                request_info=response.request_info,
                history=response.history,
                status=429,
                message=f"Rate limit exceeded. Retry after {retry_after} seconds"
            )
        else:
            error_text = await response.text()
            raise aiohttp.ClientResponseError(
                request_info=response.request_info,
                history=response.history,
                status=response.status,
                message=error_text
            )
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] = None,
        signed: bool = False,
        request_type: RequestType = RequestType.GENERAL,
        priority: RequestPriority = RequestPriority.NORMAL,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Make an API request."""
        if not self._is_running:
            raise RuntimeError("API Manager is not running. Call start() first.")
        
        # Create request
        future = asyncio.Future()
        weight = self.rate_limiter._get_endpoint_weight(endpoint)
        
        queued_request = QueuedRequest(
            method=method,
            endpoint=endpoint,
            params=params or {},
            signed=signed,
            request_type=request_type,
            priority=priority,
            weight=weight,
            future=future,
            timestamp=time.time()
        )
        
        # Add to queue
        if not await self.request_queue.put(queued_request):
            raise Exception("Request queue is full")
        
        # Wait for result
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            if not future.done():
                future.cancel()
            raise asyncio.TimeoutError(f"Request timed out after {timeout} seconds")
    
    async def batch_request(
        self,
        requests: List[Tuple[str, str, Dict[str, Any], bool, RequestType, RequestPriority]],
        timeout: float = 60.0
    ) -> List[Dict[str, Any]]:
        """Execute multiple requests in batch."""
        futures = []
        
        for method, endpoint, params, signed, request_type, priority in requests:
            future = asyncio.create_task(
                self.request(method, endpoint, params, signed, request_type, priority, timeout)
            )
            futures.append(future)
        
        # Wait for all requests to complete
        results = await asyncio.gather(*futures, return_exceptions=True)
        
        # Convert exceptions to proper format
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({'error': str(result)})
            else:
                processed_results.append(result)
        
        return processed_results
    
    # Convenience methods for common operations
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        return await self.request(
            'GET', '/fapi/v2/account',
            signed=True,
            request_type=RequestType.ACCOUNT,
            priority=RequestPriority.HIGH
        )
    
    async def get_position_info(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get position information."""
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return await self.request(
            'GET', '/fapi/v2/positionRisk',
            params=params,
            signed=True,
            request_type=RequestType.ACCOUNT,
            priority=RequestPriority.HIGH
        )
    
    async def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
        time_in_force: str = 'GTC',
        reduce_only: bool = False,
        close_position: bool = False
    ) -> Dict[str, Any]:
        """Create a new order."""
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity
        }
        
        if price:
            params['price'] = price
        if order_type in ['LIMIT', 'STOP', 'TAKE_PROFIT']:
            params['timeInForce'] = time_in_force
        if reduce_only:
            params['reduceOnly'] = 'true'
        if close_position:
            params['closePosition'] = 'true'
        
        return await self.request(
            'POST', '/fapi/v1/order',
            params=params,
            signed=True,
            request_type=RequestType.ORDER,
            priority=RequestPriority.CRITICAL
        )
    
    async def cancel_order(self, symbol: str, order_id: int = None, orig_client_order_id: str = None) -> Dict[str, Any]:
        """Cancel an order."""
        params = {'symbol': symbol}
        
        if order_id:
            params['orderId'] = order_id
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        
        return await self.request(
            'DELETE', '/fapi/v1/order',
            params=params,
            signed=True,
            request_type=RequestType.ORDER,
            priority=RequestPriority.HIGH
        )
    
    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: int = None,
        end_time: int = None
    ) -> List[List[Any]]:
        """Get kline/candlestick data."""
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        return await self.request(
            'GET', '/fapi/v1/klines',
            params=params,
            request_type=RequestType.MARKET_DATA,
            priority=RequestPriority.NORMAL
        )
    
    async def get_ticker_price(self, symbol: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get symbol price ticker."""
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return await self.request(
            'GET', '/fapi/v1/ticker/price',
            params=params,
            request_type=RequestType.MARKET_DATA,
            priority=RequestPriority.NORMAL
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics."""
        rate_limiter_metrics = self.rate_limiter.get_metrics()
        queue_stats = self.request_queue.get_stats()
        
        return {
            'uptime': time.time() - self._start_time,
            'is_running': self._is_running,
            'worker_count': len(self._worker_tasks),
            'rate_limiter': rate_limiter_metrics,
            'queue': queue_stats,
        }
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


# Global API manager instance
_api_manager: Optional[APIManager] = None


def get_api_manager() -> APIManager:
    """Get global API manager instance."""
    global _api_manager
    if _api_manager is None:
        raise RuntimeError("API Manager not initialized. Call initialize_api_manager() first.")
    return _api_manager


def initialize_api_manager(api_key: str, api_secret: str, config: RateLimitConfig = None) -> APIManager:
    """Initialize global API manager."""
    global _api_manager
    _api_manager = APIManager(api_key, api_secret, config)
    return _api_manager


async def cleanup_api_manager():
    """Clean up API manager resources."""
    global _api_manager
    if _api_manager:
        await _api_manager.stop()
        _api_manager = None 