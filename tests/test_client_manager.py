"""
Comprehensive test suite for the ClientManager.

Tests cover:
- Connection pool management
- Health monitoring and recovery
- Fallback mechanisms
- WebSocket connection management
- Error handling and circuit breakers
- Metrics and monitoring
"""

import asyncio
import pytest
import time
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

from utils.client_manager import (
    ClientManager, ClientConfig, ConnectionState, HealthStatus,
    ManagedClient, initialize_client_manager, cleanup_client_manager
)
from utils.async_binance_client import BinanceConfig, OptimizedBinanceClient


class TestClientManager:
    """Test suite for ClientManager."""
    
    @pytest.fixture
    def binance_config(self):
        """Create test Binance configuration."""
        return BinanceConfig(
            api_key="test_api_key",
            api_secret="test_api_secret",
            testnet=True,
            enable_rate_limiting=True
        )
    
    @pytest.fixture
    def client_config(self):
        """Create test client configuration."""
        return ClientConfig(
            min_connections=2,
            max_connections=5,
            health_check_interval=1.0,
            health_check_timeout=0.5,
            max_health_check_failures=2,
            enable_fallback_endpoints=True,
            enable_adaptive_scaling=True
        )
    
    @pytest.fixture
    async def client_manager(self, binance_config, client_config):
        """Create and start a test client manager."""
        manager = ClientManager(binance_config, client_config)
        yield manager
        if manager._is_running:
            await manager.stop()
    
    @pytest.mark.asyncio
    async def test_client_manager_initialization(self, binance_config, client_config):
        """Test ClientManager initialization."""
        manager = ClientManager(binance_config, client_config)
        
        assert manager.binance_config == binance_config
        assert manager.config == client_config
        assert not manager._is_running
        assert len(manager._clients) == 0
        assert len(manager._available_clients) == 0
        assert len(manager._busy_clients) == 0
    
    @pytest.mark.asyncio
    async def test_client_manager_start_stop(self, client_manager):
        """Test starting and stopping the client manager."""
        # Mock the client creation to avoid actual network calls
        with patch.object(client_manager, '_create_client', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = "test_client_1"
            
            # Start the manager
            await client_manager.start()
            assert client_manager._is_running
            assert client_manager._health_check_task is not None
            
            # Stop the manager
            await client_manager.stop()
            assert not client_manager._is_running
            assert client_manager._health_check_task.cancelled()
    
    @pytest.mark.asyncio
    async def test_connection_pool_initialization(self, client_manager):
        """Test connection pool initialization."""
        with patch.object(client_manager, '_create_client', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = ["client_1", "client_2"]
            
            await client_manager._initialize_connection_pool()
            
            # Should create minimum number of connections
            assert mock_create.call_count == client_manager.config.min_connections
    
    @pytest.mark.asyncio
    async def test_endpoint_selection_fallback(self, client_manager):
        """Test endpoint selection with fallback."""
        # Test normal selection
        endpoint = await client_manager._select_endpoint()
        assert endpoint in client_manager.config.fallback_endpoints
        
        # Test with all endpoints failing
        for endpoint in client_manager.config.fallback_endpoints:
            client_manager._endpoint_failures[endpoint] = 5
        
        fallback_endpoint = await client_manager._select_endpoint()
        assert fallback_endpoint == client_manager.config.fallback_endpoints[0]
    
    @pytest.mark.asyncio
    async def test_client_creation_and_management(self, client_manager):
        """Test client creation and management."""
        # Mock OptimizedBinanceClient
        mock_client = AsyncMock(spec=OptimizedBinanceClient)
        mock_client.connect = AsyncMock()
        mock_client.ping = AsyncMock()
        mock_client.close = AsyncMock()
        
        with patch('utils.client_manager.OptimizedBinanceClient', return_value=mock_client):
            client_id = await client_manager._create_client("test_client")
            
            assert client_id is not None
            assert client_id in client_manager._clients
            assert client_id in client_manager._available_clients
            assert client_manager._metrics.connection_count == 1
            assert client_manager._metrics.active_connections == 1
            
            # Test client removal
            await client_manager._remove_client(client_id)
            assert client_id not in client_manager._clients
            assert client_id not in client_manager._available_clients
            assert client_manager._metrics.active_connections == 0
    
    @pytest.mark.asyncio
    async def test_get_client_context_manager(self, client_manager):
        """Test getting client through context manager."""
        # Mock client
        mock_client = AsyncMock(spec=OptimizedBinanceClient)
        mock_client.connect = AsyncMock()
        mock_client.ping = AsyncMock()
        
        managed_client = ManagedClient(
            client=mock_client,
            state=ConnectionState.CONNECTED,
            client_id="test_client"
        )
        
        client_manager._clients["test_client"] = managed_client
        client_manager._available_clients.add("test_client")
        
        # Test context manager
        async with client_manager.get_client() as client:
            assert client == mock_client
            assert "test_client" in client_manager._busy_clients
            assert "test_client" not in client_manager._available_clients
        
        # After context, client should be back in available pool
        assert "test_client" in client_manager._available_clients
        assert "test_client" not in client_manager._busy_clients
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self, client_manager):
        """Test health monitoring functionality."""
        # Mock client
        mock_client = AsyncMock(spec=OptimizedBinanceClient)
        mock_client.ping = AsyncMock()
        
        managed_client = ManagedClient(
            client=mock_client,
            state=ConnectionState.CONNECTED,
            client_id="test_client"
        )
        
        client_manager._clients["test_client"] = managed_client
        
        # Test successful health check
        await client_manager._check_client_health("test_client", managed_client)
        
        assert managed_client.health_status == HealthStatus.HEALTHY
        assert managed_client.failure_count == 0
        assert managed_client.last_health_check > 0
        
        # Test failed health check
        mock_client.ping.side_effect = Exception("Connection failed")
        
        await client_manager._check_client_health("test_client", managed_client)
        
        assert managed_client.health_status == HealthStatus.UNHEALTHY
        assert managed_client.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_unhealthy_client_handling(self, client_manager):
        """Test handling of unhealthy clients."""
        # Mock client
        mock_client = AsyncMock(spec=OptimizedBinanceClient)
        mock_client.close = AsyncMock()
        
        managed_client = ManagedClient(
            client=mock_client,
            state=ConnectionState.CONNECTED,
            client_id="test_client",
            failure_count=client_manager.config.max_health_check_failures
        )
        
        client_manager._clients["test_client"] = managed_client
        client_manager._available_clients.add("test_client")
        client_manager._metrics.active_connections = 1
        
        # Mock client creation for replacement
        with patch.object(client_manager, '_create_client', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = "replacement_client"
            
            await client_manager._handle_unhealthy_client("test_client", managed_client)
            
            # Original client should be removed
            assert "test_client" not in client_manager._clients
            assert "test_client" not in client_manager._available_clients
            
            # Replacement should be created if below minimum
            if len(client_manager._clients) < client_manager.config.min_connections:
                mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_adaptive_scaling(self, client_manager):
        """Test adaptive scaling functionality."""
        # Setup initial state
        client_manager._clients = {f"client_{i}": Mock() for i in range(3)}
        client_manager._available_clients = {f"client_{i}" for i in range(1)}  # 1 available
        client_manager._busy_clients = {f"client_{i}" for i in range(1, 3)}  # 2 busy
        
        with patch.object(client_manager, '_create_client', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = "new_client"
            
            # Test scaling up (high utilization)
            await client_manager._perform_adaptive_scaling()
            
            # Should create new client due to high utilization (2/3 = 0.67 > 0.8 is false, but close)
            # Let's set it to definitely trigger scaling
            client_manager._busy_clients = {f"client_{i}" for i in range(3)}  # All busy
            client_manager._available_clients = set()
            
            await client_manager._perform_adaptive_scaling()
            mock_create.assert_called()
    
    @pytest.mark.asyncio
    async def test_websocket_connection_management(self, client_manager):
        """Test WebSocket connection management."""
        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.close = AsyncMock()
        
        # Mock session and connection
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.ws_connect = AsyncMock(return_value=mock_ws)
            mock_session_class.return_value = mock_session
            
            # Mock callback
            callback = AsyncMock()
            
            # Create WebSocket connection
            connection_id = await client_manager.create_websocket_connection(
                "btcusdt@ticker",
                callback,
                auto_reconnect=True
            )
            
            assert connection_id in client_manager._websocket_connections
            assert client_manager._websocket_connections[connection_id] == mock_ws
            
            # Close WebSocket connection
            await client_manager.close_websocket_connection(connection_id)
            
            assert connection_id not in client_manager._websocket_connections
            mock_ws.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_reconnection(self, client_manager):
        """Test WebSocket automatic reconnection."""
        callback = AsyncMock()
        
        with patch.object(client_manager, '_create_websocket', new_callable=AsyncMock) as mock_create_ws:
            mock_ws = AsyncMock()
            mock_create_ws.return_value = mock_ws
            
            # Test reconnection
            await client_manager._reconnect_websocket("ws-btcusdt@ticker-123", callback)
            
            # Should attempt to create new WebSocket
            mock_create_ws.assert_called_with("btcusdt@ticker")
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, client_manager):
        """Test metrics collection."""
        # Setup some test data
        client_manager._metrics.connection_count = 5
        client_manager._metrics.active_connections = 3
        client_manager._metrics.failed_connections = 1
        client_manager._metrics.average_response_time = 0.123
        
        client_manager._available_clients = {"client_1", "client_2"}
        client_manager._busy_clients = {"client_3"}
        client_manager._websocket_connections = {"ws_1": Mock(), "ws_2": Mock()}
        
        metrics = client_manager.get_metrics()
        
        assert metrics["connection_metrics"]["total_connections"] == 5
        assert metrics["connection_metrics"]["active_connections"] == 3
        assert metrics["connection_metrics"]["available_connections"] == 2
        assert metrics["connection_metrics"]["busy_connections"] == 1
        assert metrics["connection_metrics"]["failed_connections"] == 1
        assert metrics["connection_metrics"]["average_response_time"] == 0.123
        assert metrics["websocket_connections"] == 2
    
    @pytest.mark.asyncio
    async def test_health_status_determination(self, client_manager):
        """Test health status determination."""
        # Test healthy status
        client_manager._metrics.consecutive_failures = 0
        client_manager._metrics.active_connections = 2
        assert client_manager.get_health_status() == HealthStatus.HEALTHY
        
        # Test degraded status
        client_manager._metrics.consecutive_failures = 1
        assert client_manager.get_health_status() == HealthStatus.DEGRADED
        
        # Test unhealthy status
        client_manager._metrics.consecutive_failures = client_manager.config.max_health_check_failures
        assert client_manager.get_health_status() == HealthStatus.UNHEALTHY
        
        # Test unknown status
        client_manager._metrics.consecutive_failures = 0
        client_manager._metrics.active_connections = 0
        assert client_manager.get_health_status() == HealthStatus.UNKNOWN
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, client_manager):
        """Test circuit breaker integration."""
        # Initialize circuit breakers
        await client_manager.start()
        
        # Test that circuit breakers are created for each endpoint
        for endpoint in client_manager.config.fallback_endpoints:
            assert endpoint in client_manager._circuit_breakers
        
        await client_manager.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_client_access(self, client_manager):
        """Test concurrent access to client pool."""
        # Create multiple clients
        mock_clients = []
        for i in range(3):
            mock_client = AsyncMock(spec=OptimizedBinanceClient)
            managed_client = ManagedClient(
                client=mock_client,
                state=ConnectionState.CONNECTED,
                client_id=f"client_{i}"
            )
            client_manager._clients[f"client_{i}"] = managed_client
            client_manager._available_clients.add(f"client_{i}")
            mock_clients.append(mock_client)
        
        # Test concurrent access
        async def use_client(client_id):
            async with client_manager.get_client() as client:
                await asyncio.sleep(0.1)  # Simulate work
                return client
        
        # Run multiple concurrent tasks
        tasks = [use_client(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All tasks should complete successfully
        assert len([r for r in results if not isinstance(r, Exception)]) == 5
    
    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self, client_manager):
        """Test connection timeout handling."""
        # Test timeout when no clients available
        with pytest.raises(Exception, match="No available clients"):
            async with client_manager.get_client(timeout=0.1):
                pass
    
    @pytest.mark.asyncio
    async def test_global_client_manager_functions(self, binance_config, client_config):
        """Test global client manager functions."""
        # Test initialization
        manager = initialize_client_manager(binance_config, client_config)
        assert manager is not None
        
        # Test getting global instance
        from utils.client_manager import get_client_manager
        global_manager = get_client_manager()
        assert global_manager == manager
        
        # Test cleanup
        await cleanup_client_manager()
        
        # Should raise error after cleanup
        with pytest.raises(RuntimeError, match="Client manager not initialized"):
            get_client_manager()


class TestClientConfig:
    """Test ClientConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = ClientConfig()
        
        assert config.min_connections == 2
        assert config.max_connections == 10
        assert config.health_check_interval == 30.0
        assert config.enable_fallback_endpoints is True
        assert config.enable_adaptive_scaling is True
        assert len(config.fallback_endpoints) == 3
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = ClientConfig(
            min_connections=5,
            max_connections=20,
            health_check_interval=60.0,
            enable_fallback_endpoints=False
        )
        
        assert config.min_connections == 5
        assert config.max_connections == 20
        assert config.health_check_interval == 60.0
        assert config.enable_fallback_endpoints is False


class TestManagedClient:
    """Test ManagedClient dataclass."""
    
    def test_managed_client_creation(self):
        """Test ManagedClient creation."""
        mock_client = Mock(spec=OptimizedBinanceClient)
        
        managed_client = ManagedClient(
            client=mock_client,
            client_id="test_client"
        )
        
        assert managed_client.client == mock_client
        assert managed_client.client_id == "test_client"
        assert managed_client.state == ConnectionState.DISCONNECTED
        assert managed_client.health_status == HealthStatus.UNKNOWN
        assert managed_client.failure_count == 0
        assert managed_client.created_at > 0
        assert managed_client.last_used > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 