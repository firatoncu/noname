"""
Advanced Binance Client Manager with robust connection management.

This module provides:
- Connection pooling with automatic scaling
- Health monitoring and automatic reconnection
- Fallback mechanisms for network issues
- Circuit breaker patterns for fault tolerance
- Comprehensive error handling and recovery
- WebSocket connection management
- Performance monitoring and metrics
"""

import asyncio
import aiohttp
import time
import logging
import weakref
from typing import Dict, List, Optional, Any, Callable, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import json
from datetime import datetime, timedelta
import random
from collections import defaultdict, deque

from .async_utils import (
    AsyncHTTPClient, RetryConfig, RetryStrategy, RateLimiter,
    CircuitBreaker, CircuitBreakerConfig, ConnectionPoolConfig
)
from .async_binance_client import OptimizedBinanceClient, BinanceConfig
from .api_manager import APIManager, RateLimitConfig

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection states for client management."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


class HealthStatus(Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ConnectionMetrics:
    """Metrics for connection monitoring."""
    connection_count: int = 0
    active_connections: int = 0
    failed_connections: int = 0
    reconnection_attempts: int = 0
    last_successful_connection: Optional[float] = None
    last_failed_connection: Optional[float] = None
    average_response_time: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    health_check_failures: int = 0
    consecutive_failures: int = 0


@dataclass
class ClientConfig:
    """Configuration for client management."""
    # Connection pool settings
    min_connections: int = 2
    max_connections: int = 10
    connection_timeout: float = 30.0
    idle_timeout: float = 300.0
    
    # Health check settings
    health_check_interval: float = 30.0
    health_check_timeout: float = 10.0
    max_health_check_failures: int = 3
    
    # Reconnection settings
    max_reconnection_attempts: int = 5
    reconnection_delay: float = 5.0
    reconnection_backoff_multiplier: float = 2.0
    max_reconnection_delay: float = 300.0
    
    # Fallback settings
    enable_fallback_endpoints: bool = True
    fallback_endpoints: List[str] = field(default_factory=lambda: [
        "https://fapi.binance.com",
        "https://fapi1.binance.com",
        "https://fapi2.binance.com"
    ])
    
    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: float = 60.0
    
    # Performance settings
    enable_connection_warming: bool = True
    connection_warm_up_requests: int = 3
    enable_adaptive_scaling: bool = True


@dataclass
class ManagedClient:
    """Wrapper for managed Binance client."""
    client: OptimizedBinanceClient
    state: ConnectionState = ConnectionState.DISCONNECTED
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    last_health_check: float = 0.0
    health_status: HealthStatus = HealthStatus.UNKNOWN
    failure_count: int = 0
    endpoint_url: str = ""
    client_id: str = ""


class ClientManager:
    """Advanced client manager with robust connection handling."""
    
    def __init__(self, binance_config: BinanceConfig, client_config: ClientConfig = None):
        self.binance_config = binance_config
        self.config = client_config or ClientConfig()
        
        # Client pool management
        self._clients: Dict[str, ManagedClient] = {}
        self._available_clients: Set[str] = set()
        self._busy_clients: Set[str] = set()
        self._client_lock = asyncio.Lock()
        
        # Connection management
        self._connection_semaphore = asyncio.Semaphore(self.config.max_connections)
        self._is_running = False
        self._shutdown_event = asyncio.Event()
        
        # Health monitoring
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics = ConnectionMetrics()
        
        # Circuit breakers per endpoint
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Fallback management
        self._current_endpoint_index = 0
        self._endpoint_failures: Dict[str, int] = defaultdict(int)
        
        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()
        
        # WebSocket connections
        self._websocket_connections: Dict[str, aiohttp.ClientWebSocketResponse] = {}
        self._websocket_reconnect_tasks: Dict[str, asyncio.Task] = {}
    
    async def start(self) -> None:
        """Start the client manager."""
        if self._is_running:
            return
        
        self._is_running = True
        self._shutdown_event.clear()
        
        logger.info("Starting ClientManager...")
        
        # Initialize circuit breakers for each endpoint
        for endpoint in self.config.fallback_endpoints:
            circuit_config = CircuitBreakerConfig(
                failure_threshold=self.config.circuit_breaker_failure_threshold,
                recovery_timeout=self.config.circuit_breaker_recovery_timeout
            )
            self._circuit_breakers[endpoint] = CircuitBreaker(circuit_config)
        
        # Create initial connection pool
        await self._initialize_connection_pool()
        
        # Start health monitoring
        self._health_check_task = asyncio.create_task(self._health_monitor_loop())
        
        # Start connection scaling if enabled
        if self.config.enable_adaptive_scaling:
            scaling_task = asyncio.create_task(self._adaptive_scaling_loop())
            self._background_tasks.add(scaling_task)
        
        logger.info(f"ClientManager started with {len(self._clients)} initial connections")
    
    async def stop(self) -> None:
        """Stop the client manager and cleanup resources."""
        if not self._is_running:
            return
        
        logger.info("Stopping ClientManager...")
        
        self._is_running = False
        self._shutdown_event.set()
        
        # Cancel health monitoring
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Cancel WebSocket reconnection tasks
        for task in self._websocket_reconnect_tasks.values():
            task.cancel()
        
        # Close all WebSocket connections
        for ws in self._websocket_connections.values():
            if not ws.closed:
                await ws.close()
        
        # Close all clients
        async with self._client_lock:
            for managed_client in self._clients.values():
                try:
                    await managed_client.client.close()
                except Exception as e:
                    logger.error(f"Error closing client: {e}")
            
            self._clients.clear()
            self._available_clients.clear()
            self._busy_clients.clear()
        
        logger.info("ClientManager stopped")
    
    async def _initialize_connection_pool(self) -> None:
        """Initialize the connection pool with minimum connections."""
        tasks = []
        for i in range(self.config.min_connections):
            task = asyncio.create_task(self._create_client(f"initial-{i}"))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _create_client(self, client_id: str = None) -> Optional[str]:
        """Create a new managed client."""
        if not client_id:
            client_id = f"client-{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
        
        try:
            # Select endpoint (with fallback support)
            endpoint_url = await self._select_endpoint()
            
            # Create client config with selected endpoint
            client_config = BinanceConfig(
                api_key=self.binance_config.api_key,
                api_secret=self.binance_config.api_secret,
                base_url=endpoint_url,
                testnet=self.binance_config.testnet,
                max_requests_per_minute=self.binance_config.max_requests_per_minute,
                max_requests_per_second=self.binance_config.max_requests_per_second,
                max_order_requests_per_second=self.binance_config.max_order_requests_per_second,
                enable_rate_limiting=self.binance_config.enable_rate_limiting,
                enable_request_batching=self.binance_config.enable_request_batching,
                batch_size=self.binance_config.batch_size,
                connection_pool_size=self.binance_config.connection_pool_size
            )
            
            # Create client
            client = OptimizedBinanceClient(client_config)
            await client.connect()
            
            # Create managed client wrapper
            managed_client = ManagedClient(
                client=client,
                state=ConnectionState.CONNECTED,
                endpoint_url=endpoint_url,
                client_id=client_id
            )
            
            # Warm up connection if enabled
            if self.config.enable_connection_warming:
                await self._warm_up_connection(managed_client)
            
            # Add to pool
            async with self._client_lock:
                self._clients[client_id] = managed_client
                self._available_clients.add(client_id)
                self._metrics.connection_count += 1
                self._metrics.active_connections += 1
                self._metrics.last_successful_connection = time.time()
            
            logger.info(f"Created client {client_id} using endpoint {endpoint_url}")
            return client_id
            
        except Exception as e:
            logger.error(f"Failed to create client {client_id}: {e}")
            self._metrics.failed_connections += 1
            self._metrics.last_failed_connection = time.time()
            
            # Mark endpoint as failed
            if 'endpoint_url' in locals():
                self._endpoint_failures[endpoint_url] += 1
            
            return None
    
    async def _select_endpoint(self) -> str:
        """Select the best available endpoint with fallback support."""
        if not self.config.enable_fallback_endpoints:
            return self.binance_config.base_url
        
        # Try endpoints in order, skipping failed ones
        for _ in range(len(self.config.fallback_endpoints)):
            endpoint = self.config.fallback_endpoints[self._current_endpoint_index]
            
            # Check circuit breaker
            circuit_breaker = self._circuit_breakers.get(endpoint)
            if circuit_breaker and circuit_breaker.state.value != "open":
                # Check failure count
                if self._endpoint_failures[endpoint] < 3:
                    return endpoint
            
            # Move to next endpoint
            self._current_endpoint_index = (self._current_endpoint_index + 1) % len(self.config.fallback_endpoints)
        
        # If all endpoints are failing, use the primary one
        logger.warning("All endpoints are failing, using primary endpoint")
        return self.config.fallback_endpoints[0]
    
    async def _warm_up_connection(self, managed_client: ManagedClient) -> None:
        """Warm up a connection with test requests."""
        try:
            for _ in range(self.config.connection_warm_up_requests):
                await managed_client.client.ping()
                await asyncio.sleep(0.1)
            
            logger.debug(f"Warmed up connection {managed_client.client_id}")
            
        except Exception as e:
            logger.warning(f"Failed to warm up connection {managed_client.client_id}: {e}")
    
    @asynccontextmanager
    async def get_client(self, timeout: float = None) -> OptimizedBinanceClient:
        """Get a client from the pool with automatic management."""
        timeout = timeout or self.config.connection_timeout
        client_id = None
        
        try:
            # Acquire connection semaphore
            await asyncio.wait_for(
                self._connection_semaphore.acquire(),
                timeout=timeout
            )
            
            # Get available client
            client_id = await self._get_available_client(timeout)
            if not client_id:
                raise Exception("No available clients")
            
            managed_client = self._clients[client_id]
            managed_client.last_used = time.time()
            
            yield managed_client.client
            
        except Exception as e:
            logger.error(f"Error getting client: {e}")
            raise
        finally:
            # Release client back to pool
            if client_id:
                await self._release_client(client_id)
            
            # Release semaphore
            self._connection_semaphore.release()
    
    async def _get_available_client(self, timeout: float) -> Optional[str]:
        """Get an available client from the pool."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            async with self._client_lock:
                # Try to get an available client
                if self._available_clients:
                    client_id = self._available_clients.pop()
                    self._busy_clients.add(client_id)
                    return client_id
                
                # Check if we can create a new client
                if len(self._clients) < self.config.max_connections:
                    # Release lock temporarily to create client
                    pass
            
            # Try to create a new client
            new_client_id = await self._create_client()
            if new_client_id:
                async with self._client_lock:
                    if new_client_id in self._available_clients:
                        self._available_clients.remove(new_client_id)
                        self._busy_clients.add(new_client_id)
                        return new_client_id
            
            # Wait a bit before retrying
            await asyncio.sleep(0.1)
        
        return None
    
    async def _release_client(self, client_id: str) -> None:
        """Release a client back to the available pool."""
        async with self._client_lock:
            if client_id in self._busy_clients:
                self._busy_clients.remove(client_id)
                
                # Check if client is still healthy
                managed_client = self._clients.get(client_id)
                if managed_client and managed_client.state == ConnectionState.CONNECTED:
                    self._available_clients.add(client_id)
                else:
                    # Remove unhealthy client
                    if client_id in self._clients:
                        await self._remove_client(client_id)
    
    async def _remove_client(self, client_id: str) -> None:
        """Remove a client from the pool."""
        managed_client = self._clients.pop(client_id, None)
        if managed_client:
            try:
                await managed_client.client.close()
            except Exception as e:
                logger.error(f"Error closing client {client_id}: {e}")
            
            self._available_clients.discard(client_id)
            self._busy_clients.discard(client_id)
            self._metrics.active_connections -= 1
            
            logger.info(f"Removed client {client_id}")
    
    async def _health_monitor_loop(self) -> None:
        """Background task for health monitoring."""
        logger.info("Health monitor started")
        
        try:
            while self._is_running:
                await self._perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Health monitor error: {e}")
        finally:
            logger.info("Health monitor stopped")
    
    async def _perform_health_checks(self) -> None:
        """Perform health checks on all clients."""
        current_time = time.time()
        clients_to_check = []
        
        async with self._client_lock:
            for client_id, managed_client in self._clients.items():
                # Check if health check is due
                if (current_time - managed_client.last_health_check) >= self.config.health_check_interval:
                    clients_to_check.append((client_id, managed_client))
        
        # Perform health checks concurrently
        if clients_to_check:
            tasks = [
                self._check_client_health(client_id, managed_client)
                for client_id, managed_client in clients_to_check
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_client_health(self, client_id: str, managed_client: ManagedClient) -> None:
        """Check health of a specific client."""
        try:
            start_time = time.time()
            
            # Perform health check (ping)
            await asyncio.wait_for(
                managed_client.client.ping(),
                timeout=self.config.health_check_timeout
            )
            
            response_time = time.time() - start_time
            
            # Update metrics
            self._metrics.response_times.append(response_time)
            if self._metrics.response_times:
                self._metrics.average_response_time = sum(self._metrics.response_times) / len(self._metrics.response_times)
            
            # Update client health
            managed_client.last_health_check = time.time()
            managed_client.health_status = HealthStatus.HEALTHY
            managed_client.failure_count = 0
            self._metrics.consecutive_failures = 0
            
            # Reset endpoint failure count on success
            self._endpoint_failures[managed_client.endpoint_url] = 0
            
        except Exception as e:
            logger.warning(f"Health check failed for client {client_id}: {e}")
            
            managed_client.failure_count += 1
            managed_client.health_status = HealthStatus.UNHEALTHY
            self._metrics.health_check_failures += 1
            self._metrics.consecutive_failures += 1
            
            # Mark endpoint as failed
            self._endpoint_failures[managed_client.endpoint_url] += 1
            
            # Remove client if it has too many failures
            if managed_client.failure_count >= self.config.max_health_check_failures:
                await self._handle_unhealthy_client(client_id, managed_client)
    
    async def _handle_unhealthy_client(self, client_id: str, managed_client: ManagedClient) -> None:
        """Handle an unhealthy client."""
        logger.warning(f"Removing unhealthy client {client_id}")
        
        async with self._client_lock:
            await self._remove_client(client_id)
        
        # Try to create a replacement client
        if len(self._clients) < self.config.min_connections:
            replacement_task = asyncio.create_task(self._create_client())
            self._background_tasks.add(replacement_task)
    
    async def _adaptive_scaling_loop(self) -> None:
        """Background task for adaptive connection scaling."""
        logger.info("Adaptive scaling started")
        
        try:
            while self._is_running:
                await self._perform_adaptive_scaling()
                await asyncio.sleep(60)  # Check every minute
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Adaptive scaling error: {e}")
        finally:
            logger.info("Adaptive scaling stopped")
    
    async def _perform_adaptive_scaling(self) -> None:
        """Perform adaptive scaling based on usage patterns."""
        async with self._client_lock:
            total_clients = len(self._clients)
            busy_clients = len(self._busy_clients)
            available_clients = len(self._available_clients)
        
        # Calculate utilization
        utilization = busy_clients / max(total_clients, 1)
        
        # Scale up if utilization is high
        if utilization > 0.8 and total_clients < self.config.max_connections:
            logger.info(f"Scaling up: utilization={utilization:.2f}, creating new client")
            await self._create_client()
        
        # Scale down if utilization is low and we have more than minimum
        elif utilization < 0.2 and total_clients > self.config.min_connections and available_clients > 1:
            # Remove an idle client
            async with self._client_lock:
                if self._available_clients:
                    client_id = self._available_clients.pop()
                    await self._remove_client(client_id)
                    logger.info(f"Scaling down: utilization={utilization:.2f}, removed client {client_id}")
    
    async def create_websocket_connection(
        self,
        stream: str,
        callback: Callable[[Dict[str, Any]], None],
        auto_reconnect: bool = True
    ) -> str:
        """Create a managed WebSocket connection."""
        connection_id = f"ws-{stream}-{int(time.time() * 1000)}"
        
        try:
            ws = await self._create_websocket(stream)
            self._websocket_connections[connection_id] = ws
            
            # Start message handler
            handler_task = asyncio.create_task(
                self._websocket_message_handler(connection_id, ws, callback, auto_reconnect)
            )
            self._background_tasks.add(handler_task)
            
            logger.info(f"Created WebSocket connection {connection_id} for stream {stream}")
            return connection_id
            
        except Exception as e:
            logger.error(f"Failed to create WebSocket connection for {stream}: {e}")
            raise
    
    async def _create_websocket(self, stream: str) -> aiohttp.ClientWebSocketResponse:
        """Create a WebSocket connection."""
        # Try different WebSocket endpoints
        ws_endpoints = [
            "wss://fstream.binance.com/ws/",
            "wss://fstream1.binance.com/ws/",
            "wss://fstream2.binance.com/ws/"
        ]
        
        for endpoint in ws_endpoints:
            try:
                session = aiohttp.ClientSession()
                ws = await session.ws_connect(f"{endpoint}{stream}")
                return ws
            except Exception as e:
                logger.warning(f"Failed to connect to {endpoint}: {e}")
                await session.close()
        
        raise Exception("Failed to connect to any WebSocket endpoint")
    
    async def _websocket_message_handler(
        self,
        connection_id: str,
        ws: aiohttp.ClientWebSocketResponse,
        callback: Callable[[Dict[str, Any]], None],
        auto_reconnect: bool
    ) -> None:
        """Handle WebSocket messages with automatic reconnection."""
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await callback(data)
                    except Exception as e:
                        logger.error(f"Error in WebSocket callback: {e}")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    break
        
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        
        finally:
            # Clean up connection
            if connection_id in self._websocket_connections:
                del self._websocket_connections[connection_id]
            
            if not ws.closed:
                await ws.close()
            
            # Attempt reconnection if enabled
            if auto_reconnect and self._is_running:
                reconnect_task = asyncio.create_task(
                    self._reconnect_websocket(connection_id, callback)
                )
                self._websocket_reconnect_tasks[connection_id] = reconnect_task
    
    async def _reconnect_websocket(
        self,
        connection_id: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Reconnect a WebSocket connection."""
        stream = connection_id.split('-')[1]  # Extract stream from connection_id
        delay = 5.0
        max_delay = 300.0
        
        for attempt in range(self.config.max_reconnection_attempts):
            try:
                await asyncio.sleep(delay)
                
                logger.info(f"Attempting to reconnect WebSocket {connection_id} (attempt {attempt + 1})")
                
                ws = await self._create_websocket(stream)
                self._websocket_connections[connection_id] = ws
                
                # Start new message handler
                handler_task = asyncio.create_task(
                    self._websocket_message_handler(connection_id, ws, callback, True)
                )
                self._background_tasks.add(handler_task)
                
                logger.info(f"Successfully reconnected WebSocket {connection_id}")
                return
                
            except Exception as e:
                logger.error(f"WebSocket reconnection attempt {attempt + 1} failed: {e}")
                delay = min(delay * 2, max_delay)
        
        logger.error(f"Failed to reconnect WebSocket {connection_id} after {self.config.max_reconnection_attempts} attempts")
    
    async def close_websocket_connection(self, connection_id: str) -> None:
        """Close a WebSocket connection."""
        ws = self._websocket_connections.pop(connection_id, None)
        if ws and not ws.closed:
            await ws.close()
        
        # Cancel reconnection task if exists
        reconnect_task = self._websocket_reconnect_tasks.pop(connection_id, None)
        if reconnect_task:
            reconnect_task.cancel()
        
        logger.info(f"Closed WebSocket connection {connection_id}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics."""
        return {
            "connection_metrics": {
                "total_connections": self._metrics.connection_count,
                "active_connections": self._metrics.active_connections,
                "available_connections": len(self._available_clients),
                "busy_connections": len(self._busy_clients),
                "failed_connections": self._metrics.failed_connections,
                "reconnection_attempts": self._metrics.reconnection_attempts,
                "average_response_time": self._metrics.average_response_time,
                "health_check_failures": self._metrics.health_check_failures,
                "consecutive_failures": self._metrics.consecutive_failures
            },
            "endpoint_status": {
                endpoint: {
                    "failures": self._endpoint_failures[endpoint],
                    "circuit_breaker_state": self._circuit_breakers[endpoint].state.value
                }
                for endpoint in self.config.fallback_endpoints
            },
            "websocket_connections": len(self._websocket_connections),
            "background_tasks": len(self._background_tasks),
            "uptime": time.time() - (self._metrics.last_successful_connection or time.time())
        }
    
    def get_health_status(self) -> HealthStatus:
        """Get overall health status."""
        if self._metrics.consecutive_failures >= self.config.max_health_check_failures:
            return HealthStatus.UNHEALTHY
        elif self._metrics.consecutive_failures > 0:
            return HealthStatus.DEGRADED
        elif self._metrics.active_connections > 0:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN


# Global client manager instance
_client_manager: Optional[ClientManager] = None


def get_client_manager() -> ClientManager:
    """Get global client manager instance."""
    global _client_manager
    if _client_manager is None:
        raise RuntimeError("Client manager not initialized. Call initialize_client_manager() first.")
    return _client_manager


def initialize_client_manager(
    binance_config: BinanceConfig,
    client_config: ClientConfig = None
) -> ClientManager:
    """Initialize global client manager."""
    global _client_manager
    _client_manager = ClientManager(binance_config, client_config)
    return _client_manager


async def cleanup_client_manager():
    """Clean up client manager resources."""
    global _client_manager
    if _client_manager:
        await _client_manager.stop()
        _client_manager = None 