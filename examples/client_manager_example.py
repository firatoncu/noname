"""
Example usage of the robust ClientManager for Binance connections.

This example demonstrates:
- Basic client manager setup and usage
- Connection pooling and automatic scaling
- Health monitoring and metrics
- WebSocket connection management
- Error handling and fallback mechanisms
"""

import asyncio
import logging
import json
from typing import Dict, Any

from utils.client_manager import (
    ClientManager, ClientConfig, initialize_client_manager, 
    get_client_manager, cleanup_client_manager
)
from utils.async_binance_client import BinanceConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def basic_client_manager_example():
    """Basic example of using the ClientManager."""
    logger.info("=== Basic ClientManager Example ===")
    
    # Configure Binance client
    binance_config = BinanceConfig(
        api_key="your_api_key_here",
        api_secret="your_api_secret_here",
        testnet=True,  # Use testnet for examples
        enable_rate_limiting=True,
        enable_request_batching=True
    )
    
    # Configure client manager
    client_config = ClientConfig(
        min_connections=2,
        max_connections=5,
        health_check_interval=30.0,
        enable_fallback_endpoints=True,
        enable_adaptive_scaling=True
    )
    
    # Initialize client manager
    client_manager = initialize_client_manager(binance_config, client_config)
    
    try:
        # Start the client manager
        await client_manager.start()
        logger.info("ClientManager started successfully")
        
        # Use the client manager to make API calls
        async with client_manager.get_client() as client:
            # Test connectivity
            server_time = await client.get_server_time()
            logger.info(f"Server time: {server_time}")
            
            # Get account information
            account_info = await client.get_account_info()
            logger.info(f"Account balance count: {len(account_info.get('assets', []))}")
            
            # Get ticker prices for multiple symbols
            symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
            ticker_data = await client.get_multiple_symbols_data(symbols)
            for symbol, data in ticker_data.items():
                logger.info(f"{symbol}: ${data.get('price', 'N/A')}")
        
        # Get metrics
        metrics = client_manager.get_metrics()
        logger.info(f"Connection metrics: {json.dumps(metrics['connection_metrics'], indent=2)}")
        
    except Exception as e:
        logger.error(f"Error in basic example: {e}")
    finally:
        await cleanup_client_manager()


async def websocket_example():
    """Example of using WebSocket connections with automatic reconnection."""
    logger.info("=== WebSocket Example ===")
    
    # Configure and start client manager
    binance_config = BinanceConfig(
        api_key="your_api_key_here",
        api_secret="your_api_secret_here",
        testnet=True
    )
    
    client_manager = initialize_client_manager(binance_config)
    await client_manager.start()
    
    try:
        # WebSocket callback for ticker updates
        async def ticker_callback(data: Dict[str, Any]):
            if 'c' in data:  # Current price
                symbol = data.get('s', 'UNKNOWN')
                price = data.get('c', '0')
                logger.info(f"Ticker update - {symbol}: ${price}")
        
        # WebSocket callback for kline updates
        async def kline_callback(data: Dict[str, Any]):
            if 'k' in data:
                kline = data['k']
                symbol = kline.get('s', 'UNKNOWN')
                close_price = kline.get('c', '0')
                logger.info(f"Kline update - {symbol}: ${close_price}")
        
        # Create WebSocket connections
        ticker_connection = await client_manager.create_websocket_connection(
            "btcusdt@ticker",
            ticker_callback,
            auto_reconnect=True
        )
        
        kline_connection = await client_manager.create_websocket_connection(
            "ethusdt@kline_1m",
            kline_callback,
            auto_reconnect=True
        )
        
        logger.info("WebSocket connections established")
        
        # Let it run for a while to see updates
        await asyncio.sleep(30)
        
        # Close WebSocket connections
        await client_manager.close_websocket_connection(ticker_connection)
        await client_manager.close_websocket_connection(kline_connection)
        
        logger.info("WebSocket connections closed")
        
    except Exception as e:
        logger.error(f"Error in WebSocket example: {e}")
    finally:
        await cleanup_client_manager()


async def error_handling_example():
    """Example demonstrating error handling and fallback mechanisms."""
    logger.info("=== Error Handling Example ===")
    
    # Configure with aggressive settings to trigger fallbacks
    binance_config = BinanceConfig(
        api_key="your_api_key_here",
        api_secret="your_api_secret_here",
        testnet=True
    )
    
    client_config = ClientConfig(
        min_connections=1,
        max_connections=3,
        health_check_interval=10.0,
        max_health_check_failures=2,
        enable_fallback_endpoints=True,
        fallback_endpoints=[
            "https://fapi.binance.com",
            "https://fapi1.binance.com",
            "https://fapi2.binance.com"
        ]
    )
    
    client_manager = initialize_client_manager(binance_config, client_config)
    
    try:
        await client_manager.start()
        
        # Simulate multiple concurrent requests to test connection pooling
        async def make_request(request_id: int):
            try:
                async with client_manager.get_client(timeout=10.0) as client:
                    server_time = await client.get_server_time()
                    logger.info(f"Request {request_id} completed: {server_time['serverTime']}")
                    return True
            except Exception as e:
                logger.error(f"Request {request_id} failed: {e}")
                return False
        
        # Make concurrent requests
        tasks = [make_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_requests = sum(1 for r in results if r is True)
        logger.info(f"Completed {successful_requests}/{len(tasks)} requests successfully")
        
        # Check health status
        health_status = client_manager.get_health_status()
        logger.info(f"Overall health status: {health_status.value}")
        
        # Get detailed metrics
        metrics = client_manager.get_metrics()
        logger.info("=== Detailed Metrics ===")
        logger.info(f"Connection metrics: {json.dumps(metrics['connection_metrics'], indent=2)}")
        logger.info(f"Endpoint status: {json.dumps(metrics['endpoint_status'], indent=2)}")
        
    except Exception as e:
        logger.error(f"Error in error handling example: {e}")
    finally:
        await cleanup_client_manager()


async def load_testing_example():
    """Example demonstrating load testing and adaptive scaling."""
    logger.info("=== Load Testing Example ===")
    
    binance_config = BinanceConfig(
        api_key="your_api_key_here",
        api_secret="your_api_secret_here",
        testnet=True,
        enable_rate_limiting=True,
        max_requests_per_minute=1200
    )
    
    client_config = ClientConfig(
        min_connections=2,
        max_connections=8,
        enable_adaptive_scaling=True,
        health_check_interval=15.0
    )
    
    client_manager = initialize_client_manager(binance_config, client_config)
    
    try:
        await client_manager.start()
        
        # Function to simulate trading activity
        async def simulate_trading_activity(session_id: int, duration: int):
            logger.info(f"Starting trading session {session_id}")
            start_time = asyncio.get_event_loop().time()
            request_count = 0
            
            while (asyncio.get_event_loop().time() - start_time) < duration:
                try:
                    async with client_manager.get_client() as client:
                        # Simulate various API calls
                        if request_count % 3 == 0:
                            await client.get_ticker_price('BTCUSDT')
                        elif request_count % 3 == 1:
                            await client.get_account_info()
                        else:
                            await client.get_position_info()
                        
                        request_count += 1
                        
                        # Small delay between requests
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    logger.error(f"Session {session_id} request failed: {e}")
                    await asyncio.sleep(1)  # Back off on error
            
            logger.info(f"Session {session_id} completed {request_count} requests")
            return request_count
        
        # Start multiple concurrent trading sessions
        sessions = [
            simulate_trading_activity(i, 60)  # 60 seconds each
            for i in range(5)
        ]
        
        # Monitor metrics during load test
        async def monitor_metrics():
            for _ in range(12):  # Monitor for 60 seconds
                await asyncio.sleep(5)
                metrics = client_manager.get_metrics()
                conn_metrics = metrics['connection_metrics']
                logger.info(
                    f"Metrics - Active: {conn_metrics['active_connections']}, "
                    f"Available: {conn_metrics['available_connections']}, "
                    f"Busy: {conn_metrics['busy_connections']}, "
                    f"Avg Response: {conn_metrics['average_response_time']:.3f}s"
                )
        
        # Run sessions and monitoring concurrently
        monitor_task = asyncio.create_task(monitor_metrics())
        session_results = await asyncio.gather(*sessions, return_exceptions=True)
        monitor_task.cancel()
        
        total_requests = sum(r for r in session_results if isinstance(r, int))
        logger.info(f"Load test completed: {total_requests} total requests")
        
        # Final metrics
        final_metrics = client_manager.get_metrics()
        logger.info("=== Final Load Test Metrics ===")
        logger.info(json.dumps(final_metrics, indent=2))
        
    except Exception as e:
        logger.error(f"Error in load testing example: {e}")
    finally:
        await cleanup_client_manager()


async def main():
    """Run all examples."""
    logger.info("Starting ClientManager examples...")
    
    try:
        # Run examples sequentially
        await basic_client_manager_example()
        await asyncio.sleep(2)
        
        await websocket_example()
        await asyncio.sleep(2)
        
        await error_handling_example()
        await asyncio.sleep(2)
        
        await load_testing_example()
        
    except KeyboardInterrupt:
        logger.info("Examples interrupted by user")
    except Exception as e:
        logger.error(f"Error running examples: {e}")
    finally:
        logger.info("Examples completed")


if __name__ == "__main__":
    # Note: Replace API keys with your actual keys before running
    asyncio.run(main()) 