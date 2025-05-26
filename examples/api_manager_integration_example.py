"""
Example integration of the new APIManager into the existing trading system.

This example shows how to:
1. Initialize the APIManager
2. Replace existing API calls
3. Handle different request priorities
4. Monitor performance metrics
5. Implement proper error handling
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

# Import the new APIManager
from utils.api_manager import (
    APIManager, initialize_api_manager, get_api_manager,
    RateLimitConfig, RequestPriority, RequestType, BackoffStrategy
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedTradingBot:
    """Enhanced trading bot using the new APIManager."""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_manager = None
        self.is_running = False
        
        # Trading state
        self.positions = {}
        self.open_orders = {}
        self.market_data = {}
        
        # Performance tracking
        self.trade_count = 0
        self.last_metrics_update = datetime.now()
    
    async def initialize(self):
        """Initialize the trading bot with optimized APIManager configuration."""
        
        # Configure rate limiting for optimal performance
        config = RateLimitConfig(
            # Conservative rate limits to avoid hitting Binance limits
            requests_per_minute=1000,  # Below Binance's 1200 limit
            orders_per_second=8,       # Below Binance's 10 limit
            orders_per_day=150000,     # Below Binance's 200k limit
            
            # Weight management
            weight_per_minute=1000,    # Conservative weight usage
            weight_per_second=40,      # Conservative per-second weight
            
            # Adaptive backoff for reliability
            backoff_strategy=BackoffStrategy.ADAPTIVE,
            initial_backoff=0.5,
            max_backoff=120.0,
            backoff_multiplier=1.5,
            
            # Circuit breaker for fault tolerance
            failure_threshold=3,
            recovery_timeout=30.0,
            
            # Large queue for burst handling
            max_queue_size=20000,
            queue_timeout=45.0,
            
            # Adaptive throttling for optimal performance
            enable_adaptive_throttling=True,
            target_success_rate=0.97,
            monitoring_window=100
        )
        
        # Initialize the global APIManager
        self.api_manager = initialize_api_manager(
            self.api_key, 
            self.api_secret, 
            config
        )
        
        # Start with multiple workers for concurrent processing
        await self.api_manager.start(num_workers=8)
        
        logger.info("Enhanced Trading Bot initialized with APIManager")
    
    async def start_trading(self):
        """Start the main trading loop."""
        if self.is_running:
            logger.warning("Trading bot is already running")
            return
        
        self.is_running = True
        logger.info("Starting enhanced trading bot...")
        
        try:
            # Start concurrent tasks
            await asyncio.gather(
                self.monitor_positions(),
                self.process_market_data(),
                self.manage_orders(),
                self.monitor_performance(),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
        finally:
            self.is_running = False
    
    async def stop_trading(self):
        """Stop the trading bot."""
        logger.info("Stopping trading bot...")
        self.is_running = False
        
        if self.api_manager:
            await self.api_manager.stop()
    
    async def monitor_positions(self):
        """Monitor positions with high priority requests."""
        logger.info("Starting position monitoring...")
        
        while self.is_running:
            try:
                # Get position info with HIGH priority (critical for risk management)
                positions = await self.api_manager.get_position_info()
                
                # Update internal position tracking
                self.positions = {
                    pos['symbol']: pos for pos in positions 
                    if float(pos['positionAmt']) != 0
                }
                
                # Check for position changes that require action
                await self.handle_position_changes()
                
                # No manual sleep needed - rate limiting handled automatically
                await asyncio.sleep(0.5)  # Minimal delay for loop control
                
            except Exception as e:
                logger.error(f"Position monitoring error: {e}")
                await asyncio.sleep(2)  # Brief pause on error
    
    async def process_market_data(self):
        """Process market data with optimized batch requests."""
        logger.info("Starting market data processing...")
        
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"]
        
        while self.is_running:
            try:
                # Batch request for multiple symbols (efficient API usage)
                requests = []
                for symbol in symbols:
                    # Get ticker price
                    requests.append((
                        'GET', '/fapi/v1/ticker/price',
                        {'symbol': symbol},
                        False,  # not signed
                        RequestType.MARKET_DATA,
                        RequestPriority.NORMAL
                    ))
                    
                    # Get recent klines
                    requests.append((
                        'GET', '/fapi/v1/klines',
                        {
                            'symbol': symbol,
                            'interval': '1m',
                            'limit': 20
                        },
                        False,  # not signed
                        RequestType.MARKET_DATA,
                        RequestPriority.NORMAL
                    ))
                
                # Execute batch request
                results = await self.api_manager.batch_request(requests, timeout=30.0)
                
                # Process results
                await self.update_market_data(symbols, results)
                
                # Process trading signals
                await self.process_trading_signals()
                
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"Market data processing error: {e}")
                await asyncio.sleep(5)
    
    async def manage_orders(self):
        """Manage open orders with high priority."""
        logger.info("Starting order management...")
        
        while self.is_running:
            try:
                # Get open orders with HIGH priority
                open_orders = await self.api_manager.request(
                    'GET', '/fapi/v1/openOrders',
                    signed=True,
                    request_type=RequestType.ORDER,
                    priority=RequestPriority.HIGH
                )
                
                self.open_orders = {order['orderId']: order for order in open_orders}
                
                # Check for orders that need management
                await self.handle_order_management()
                
                await asyncio.sleep(2)  # Check orders every 2 seconds
                
            except Exception as e:
                logger.error(f"Order management error: {e}")
                await asyncio.sleep(5)
    
    async def monitor_performance(self):
        """Monitor APIManager performance and adjust if needed."""
        logger.info("Starting performance monitoring...")
        
        while self.is_running:
            try:
                metrics = self.api_manager.get_metrics()
                
                # Log performance metrics every 30 seconds
                if (datetime.now() - self.last_metrics_update).seconds >= 30:
                    await self.log_performance_metrics(metrics)
                    self.last_metrics_update = datetime.now()
                
                # Check for performance issues
                await self.handle_performance_issues(metrics)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def create_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """Create a market order with CRITICAL priority."""
        try:
            logger.info(f"Creating {side} market order: {quantity} {symbol}")
            
            result = await self.api_manager.create_order(
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=quantity
            )
            
            self.trade_count += 1
            logger.info(f"Order created successfully: {result['orderId']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create market order: {e}")
            raise
    
    async def create_limit_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float, 
        price: float
    ) -> Dict[str, Any]:
        """Create a limit order with HIGH priority."""
        try:
            logger.info(f"Creating {side} limit order: {quantity} {symbol} @ {price}")
            
            result = await self.api_manager.create_order(
                symbol=symbol,
                side=side,
                order_type="LIMIT",
                quantity=quantity,
                price=price,
                time_in_force="GTC"
            )
            
            self.trade_count += 1
            logger.info(f"Limit order created: {result['orderId']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create limit order: {e}")
            raise
    
    async def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an order with HIGH priority."""
        try:
            logger.info(f"Cancelling order {order_id} for {symbol}")
            
            result = await self.api_manager.cancel_order(
                symbol=symbol,
                order_id=order_id
            )
            
            logger.info(f"Order cancelled successfully: {order_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
    
    async def get_account_balance(self) -> List[Dict[str, Any]]:
        """Get account balance with HIGH priority."""
        try:
            balance = await self.api_manager.request(
                'GET', '/fapi/v2/balance',
                signed=True,
                request_type=RequestType.ACCOUNT,
                priority=RequestPriority.HIGH
            )
            return balance
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            raise
    
    async def handle_position_changes(self):
        """Handle position changes and risk management."""
        for symbol, position in self.positions.items():
            position_amt = float(position['positionAmt'])
            unrealized_pnl = float(position['unRealizedProfit'])
            
            # Example: Close position if unrealized loss exceeds threshold
            if unrealized_pnl < -100:  # $100 loss threshold
                logger.warning(f"Large unrealized loss detected for {symbol}: ${unrealized_pnl}")
                
                # Close position with market order (CRITICAL priority)
                side = "SELL" if position_amt > 0 else "BUY"
                await self.create_market_order(symbol, side, abs(position_amt))
    
    async def update_market_data(self, symbols: List[str], results: List[Dict[str, Any]]):
        """Update internal market data from batch results."""
        idx = 0
        for symbol in symbols:
            # Process ticker data
            if idx < len(results) and 'error' not in results[idx]:
                ticker_data = results[idx]
                if symbol not in self.market_data:
                    self.market_data[symbol] = {}
                self.market_data[symbol]['price'] = float(ticker_data['price'])
            idx += 1
            
            # Process kline data
            if idx < len(results) and 'error' not in results[idx]:
                kline_data = results[idx]
                if symbol not in self.market_data:
                    self.market_data[symbol] = {}
                self.market_data[symbol]['klines'] = kline_data
            idx += 1
    
    async def process_trading_signals(self):
        """Process trading signals based on market data."""
        for symbol, data in self.market_data.items():
            if 'price' in data and 'klines' in data:
                # Simple example: buy if price increased significantly
                current_price = data['price']
                klines = data['klines']
                
                if len(klines) >= 5:
                    # Get price from 5 minutes ago
                    old_price = float(klines[-5][4])  # Close price
                    price_change = (current_price - old_price) / old_price
                    
                    # Example signal: buy if price increased by more than 1%
                    if price_change > 0.01 and symbol not in self.positions:
                        logger.info(f"Buy signal for {symbol}: {price_change:.2%} increase")
                        # Could create order here based on your strategy
    
    async def handle_order_management(self):
        """Handle order management logic."""
        for order_id, order in self.open_orders.items():
            # Example: Cancel orders that are too old
            order_time = int(order['time'])
            current_time = int(datetime.now().timestamp() * 1000)
            
            # Cancel orders older than 5 minutes
            if current_time - order_time > 300000:  # 5 minutes in milliseconds
                logger.info(f"Cancelling old order: {order_id}")
                await self.cancel_order(order['symbol'], order_id)
    
    async def log_performance_metrics(self, metrics: Dict[str, Any]):
        """Log detailed performance metrics."""
        rate_limiter = metrics['rate_limiter']
        queue = metrics['queue']
        
        logger.info("=== API Performance Metrics ===")
        logger.info(f"Uptime: {metrics['uptime']:.1f}s")
        logger.info(f"Workers: {metrics['worker_count']}")
        logger.info(f"Success Rate: {rate_limiter['success_rate']:.2%}")
        logger.info(f"Avg Response Time: {rate_limiter['average_response_time']:.3f}s")
        logger.info(f"Throttle Factor: {rate_limiter['current_throttle_factor']:.2f}")
        logger.info(f"Circuit State: {rate_limiter['circuit_state']}")
        logger.info(f"Queue Size: {queue['total_size']}")
        logger.info(f"Trades Executed: {self.trade_count}")
        
        # Rate limit usage
        state = rate_limiter['rate_limit_state']
        logger.info(f"Rate Limits - Requests/min: {state['requests_this_minute']}/1000")
        logger.info(f"Rate Limits - Weight/min: {state['weight_this_minute']}/1000")
        logger.info(f"Rate Limits - Orders/day: {state['orders_this_day']}/150000")
    
    async def handle_performance_issues(self, metrics: Dict[str, Any]):
        """Handle performance issues automatically."""
        rate_limiter = metrics['rate_limiter']
        
        # Check for low success rate
        if rate_limiter['success_rate'] < 0.90:
            logger.warning(f"Low success rate detected: {rate_limiter['success_rate']:.2%}")
        
        # Check for high response times
        if rate_limiter['average_response_time'] > 2.0:
            logger.warning(f"High response times: {rate_limiter['average_response_time']:.3f}s")
        
        # Check circuit breaker state
        if rate_limiter['circuit_state'] == 'open':
            logger.error("Circuit breaker is OPEN - API requests are being blocked")
        
        # Check queue size
        if metrics['queue']['total_size'] > 1000:
            logger.warning(f"Large queue size: {metrics['queue']['total_size']}")


async def main():
    """Main function demonstrating the enhanced trading bot."""
    
    # Replace with your actual API credentials
    API_KEY = "your_binance_api_key"
    API_SECRET = "your_binance_api_secret"
    
    # Create and initialize the enhanced trading bot
    bot = EnhancedTradingBot(API_KEY, API_SECRET)
    
    try:
        # Initialize the bot
        await bot.initialize()
        
        # Start trading (this will run indefinitely)
        await bot.start_trading()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, stopping bot...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Clean shutdown
        await bot.stop_trading()
        logger.info("Bot stopped successfully")


if __name__ == "__main__":
    # Run the enhanced trading bot
    asyncio.run(main()) 