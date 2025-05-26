"""
Optimized async Binance client with advanced features.

This module provides:
- Enhanced connection pooling for Binance API
- Request batching and rate limiting
- Automatic retry mechanisms
- WebSocket connection management
- Order execution optimization
"""

import asyncio
import aiohttp
import hmac
import hashlib
import time
import json
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlencode
import weakref

from .async_utils import (
    AsyncHTTPClient, RetryConfig, RetryStrategy, RateLimiter,
    RequestBatcher, get_http_client, get_request_batcher,
    gather_with_concurrency, async_cache
)

logger = logging.getLogger(__name__)


@dataclass
class BinanceConfig:
    """Configuration for Binance client."""
    api_key: str
    api_secret: str
    base_url: str = "https://fapi.binance.com"
    testnet: bool = False
    max_requests_per_minute: int = 1200
    max_requests_per_second: int = 10
    max_order_requests_per_second: int = 5
    enable_rate_limiting: bool = True
    enable_request_batching: bool = True
    batch_size: int = 10
    connection_pool_size: int = 50


class RequestType(Enum):
    """Types of API requests for rate limiting."""
    GENERAL = "general"
    ORDER = "order"
    MARKET_DATA = "market_data"


@dataclass
class BatchRequest:
    """Batched request data."""
    method: str
    endpoint: str
    params: Dict[str, Any] = field(default_factory=dict)
    signed: bool = False
    request_type: RequestType = RequestType.GENERAL


class OptimizedBinanceClient:
    """Optimized async Binance client with advanced features."""
    
    def __init__(self, config: BinanceConfig):
        self.config = config
        self._http_client: Optional[AsyncHTTPClient] = None
        self._rate_limiters: Dict[RequestType, RateLimiter] = {}
        self._request_batcher: Optional[RequestBatcher] = None
        self._websocket_connections: Dict[str, aiohttp.ClientWebSocketResponse] = {}
        self._closed = False
        
        # Initialize rate limiters
        self._setup_rate_limiters()
    
    def _setup_rate_limiters(self):
        """Setup rate limiters for different request types."""
        if self.config.enable_rate_limiting:
            self._rate_limiters[RequestType.GENERAL] = RateLimiter(
                max_requests=self.config.max_requests_per_minute,
                time_window=60.0
            )
            self._rate_limiters[RequestType.ORDER] = RateLimiter(
                max_requests=self.config.max_order_requests_per_second,
                time_window=1.0
            )
            self._rate_limiters[RequestType.MARKET_DATA] = RateLimiter(
                max_requests=self.config.max_requests_per_second,
                time_window=1.0
            )
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def connect(self):
        """Initialize client connections."""
        if self._http_client is None:
            self._http_client = get_http_client()
        
        if self.config.enable_request_batching:
            self._request_batcher = get_request_batcher()
        
        logger.info("Binance client connected")
    
    async def close(self):
        """Close client connections."""
        if self._closed:
            return
        
        self._closed = True
        
        # Close WebSocket connections
        for ws in self._websocket_connections.values():
            if not ws.closed:
                await ws.close()
        self._websocket_connections.clear()
        
        logger.info("Binance client closed")
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for signed requests."""
        query_string = urlencode(params)
        return hmac.new(
            self.config.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _prepare_signed_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare parameters for signed requests."""
        params = params.copy()
        params['timestamp'] = int(time.time() * 1000)
        params['signature'] = self._generate_signature(params)
        return params
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] = None,
        signed: bool = False,
        request_type: RequestType = RequestType.GENERAL
    ) -> Dict[str, Any]:
        """Make HTTP request to Binance API."""
        params = params or {}
        
        # Apply rate limiting
        if request_type in self._rate_limiters:
            await self._rate_limiters[request_type].acquire()
        
        # Prepare URL
        url = f"{self.config.base_url}{endpoint}"
        
        # Prepare headers
        headers = {
            'X-MBX-APIKEY': self.config.api_key,
            'Content-Type': 'application/json'
        }
        
        # Handle signed requests
        if signed:
            params = self._prepare_signed_params(params)
        
        # Configure retry
        retry_config = RetryConfig(
            max_retries=3,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=10.0
        )
        
        try:
            if method.upper() == 'GET':
                async with self._http_client.get(
                    url,
                    params=params,
                    headers=headers,
                    retry_config=retry_config
                ) as response:
                    return await self._handle_response(response)
            else:
                async with self._http_client.request(
                    method,
                    url,
                    json=params if method.upper() in ['POST', 'PUT'] else None,
                    params=params if method.upper() not in ['POST', 'PUT'] else None,
                    headers=headers,
                    retry_config=retry_config
                ) as response:
                    return await self._handle_response(response)
                    
        except Exception as e:
            logger.error(f"Request failed: {method} {endpoint} - {e}")
            raise
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle API response."""
        if response.status == 200:
            return await response.json()
        else:
            error_text = await response.text()
            raise Exception(f"API request failed with status {response.status}: {error_text}")
    
    async def batch_request(self, requests: List[BatchRequest]) -> List[Dict[str, Any]]:
        """Execute multiple requests in batch."""
        if not self.config.enable_request_batching:
            # Execute requests sequentially
            results = []
            for req in requests:
                result = await self._make_request(
                    req.method, req.endpoint, req.params, req.signed, req.request_type
                )
                results.append(result)
            return results
        
        # Use request batcher
        async def make_batched_request(req: BatchRequest):
            return await self._make_request(
                req.method, req.endpoint, req.params, req.signed, req.request_type
            )
        
        tasks = [
            lambda req=req: make_batched_request(req)
            for req in requests
        ]
        
        return await gather_with_concurrency(tasks, max_concurrency=self.config.batch_size)
    
    # Market Data Methods
    
    @async_cache(ttl_seconds=60)
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information."""
        return await self._make_request(
            'GET', '/fapi/v1/exchangeInfo',
            request_type=RequestType.MARKET_DATA
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
        
        return await self._make_request(
            'GET', '/fapi/v1/klines',
            params=params,
            request_type=RequestType.MARKET_DATA
        )
    
    async def get_ticker_price(self, symbol: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get symbol price ticker."""
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return await self._make_request(
            'GET', '/fapi/v1/ticker/price',
            params=params,
            request_type=RequestType.MARKET_DATA
        )
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get order book."""
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        return await self._make_request(
            'GET', '/fapi/v1/depth',
            params=params,
            request_type=RequestType.MARKET_DATA
        )
    
    # Account Methods
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        return await self._make_request(
            'GET', '/fapi/v2/account',
            signed=True
        )
    
    async def get_position_info(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get position information."""
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return await self._make_request(
            'GET', '/fapi/v2/positionRisk',
            params=params,
            signed=True
        )
    
    async def get_balance(self) -> List[Dict[str, Any]]:
        """Get account balance."""
        return await self._make_request(
            'GET', '/fapi/v2/balance',
            signed=True
        )
    
    # Trading Methods
    
    async def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
        time_in_force: str = 'GTC',
        reduce_only: bool = False,
        close_position: bool = False,
        position_side: str = 'BOTH'
    ) -> Dict[str, Any]:
        """Create a new order."""
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
            'positionSide': position_side
        }
        
        if price:
            params['price'] = price
        if order_type in ['LIMIT', 'STOP', 'TAKE_PROFIT']:
            params['timeInForce'] = time_in_force
        if reduce_only:
            params['reduceOnly'] = 'true'
        if close_position:
            params['closePosition'] = 'true'
        
        return await self._make_request(
            'POST', '/fapi/v1/order',
            params=params,
            signed=True,
            request_type=RequestType.ORDER
        )
    
    async def cancel_order(self, symbol: str, order_id: int = None, orig_client_order_id: str = None) -> Dict[str, Any]:
        """Cancel an order."""
        params = {'symbol': symbol}
        
        if order_id:
            params['orderId'] = order_id
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        
        return await self._make_request(
            'DELETE', '/fapi/v1/order',
            params=params,
            signed=True,
            request_type=RequestType.ORDER
        )
    
    async def cancel_all_orders(self, symbol: str) -> Dict[str, Any]:
        """Cancel all open orders for a symbol."""
        params = {'symbol': symbol}
        
        return await self._make_request(
            'DELETE', '/fapi/v1/allOpenOrders',
            params=params,
            signed=True,
            request_type=RequestType.ORDER
        )
    
    async def get_order(self, symbol: str, order_id: int = None, orig_client_order_id: str = None) -> Dict[str, Any]:
        """Get order information."""
        params = {'symbol': symbol}
        
        if order_id:
            params['orderId'] = order_id
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        
        return await self._make_request(
            'GET', '/fapi/v1/order',
            params=params,
            signed=True
        )
    
    async def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get all open orders."""
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return await self._make_request(
            'GET', '/fapi/v1/openOrders',
            params=params,
            signed=True
        )
    
    async def get_order_history(
        self,
        symbol: str,
        start_time: int = None,
        end_time: int = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Get order history."""
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        return await self._make_request(
            'GET', '/fapi/v1/allOrders',
            params=params,
            signed=True
        )
    
    # Batch Trading Methods
    
    async def create_batch_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple orders in batch."""
        batch_requests = []
        
        for order in orders:
            batch_requests.append(BatchRequest(
                method='POST',
                endpoint='/fapi/v1/order',
                params=order,
                signed=True,
                request_type=RequestType.ORDER
            ))
        
        return await self.batch_request(batch_requests)
    
    async def get_multiple_symbols_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get data for multiple symbols efficiently."""
        batch_requests = []
        
        for symbol in symbols:
            # Get ticker price
            batch_requests.append(BatchRequest(
                method='GET',
                endpoint='/fapi/v1/ticker/price',
                params={'symbol': symbol},
                request_type=RequestType.MARKET_DATA
            ))
        
        results = await self.batch_request(batch_requests)
        
        # Organize results by symbol
        symbol_data = {}
        for i, symbol in enumerate(symbols):
            symbol_data[symbol] = results[i]
        
        return symbol_data
    
    # WebSocket Methods
    
    async def create_websocket_connection(self, stream: str) -> aiohttp.ClientWebSocketResponse:
        """Create WebSocket connection for real-time data."""
        ws_url = f"wss://fstream.binance.com/ws/{stream}"
        
        session = aiohttp.ClientSession()
        ws = await session.ws_connect(ws_url)
        
        self._websocket_connections[stream] = ws
        return ws
    
    async def subscribe_to_ticker(self, symbol: str, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to ticker updates via WebSocket."""
        stream = f"{symbol.lower()}@ticker"
        ws = await self.create_websocket_connection(stream)
        
        async def message_handler():
            try:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        await callback(data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f"WebSocket error: {ws.exception()}")
                        break
            except Exception as e:
                logger.error(f"WebSocket message handler error: {e}")
            finally:
                if not ws.closed:
                    await ws.close()
                if stream in self._websocket_connections:
                    del self._websocket_connections[stream]
        
        # Start message handler task
        asyncio.create_task(message_handler())
    
    async def subscribe_to_klines(
        self,
        symbol: str,
        interval: str,
        callback: Callable[[Dict[str, Any]], None]
    ):
        """Subscribe to kline updates via WebSocket."""
        stream = f"{symbol.lower()}@kline_{interval}"
        ws = await self.create_websocket_connection(stream)
        
        async def message_handler():
            try:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        await callback(data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f"WebSocket error: {ws.exception()}")
                        break
            except Exception as e:
                logger.error(f"WebSocket message handler error: {e}")
            finally:
                if not ws.closed:
                    await ws.close()
                if stream in self._websocket_connections:
                    del self._websocket_connections[stream]
        
        # Start message handler task
        asyncio.create_task(message_handler())
    
    # Utility Methods
    
    async def get_server_time(self) -> Dict[str, Any]:
        """Get server time."""
        return await self._make_request(
            'GET', '/fapi/v1/time',
            request_type=RequestType.MARKET_DATA
        )
    
    async def ping(self) -> Dict[str, Any]:
        """Test connectivity."""
        return await self._make_request(
            'GET', '/fapi/v1/ping',
            request_type=RequestType.MARKET_DATA
        )


# Global client instance
_binance_client: Optional[OptimizedBinanceClient] = None


def get_binance_client() -> OptimizedBinanceClient:
    """Get global Binance client instance."""
    global _binance_client
    if _binance_client is None:
        raise RuntimeError("Binance client not initialized. Call initialize_binance_client() first.")
    return _binance_client


def initialize_binance_client(config: BinanceConfig) -> OptimizedBinanceClient:
    """Initialize global Binance client."""
    global _binance_client
    _binance_client = OptimizedBinanceClient(config)
    return _binance_client


async def cleanup_binance_client():
    """Clean up Binance client resources."""
    global _binance_client
    if _binance_client:
        await _binance_client.close()
        _binance_client = None 