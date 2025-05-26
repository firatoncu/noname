"""
Optimized async main application with enhanced performance.

This module demonstrates:
- Async initialization and cleanup
- Concurrent task management
- Optimized API operations
- Proper error handling and retry mechanisms
"""

import asyncio
import logging
import signal
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

# Import async utilities
from utils.async_utils import (
    get_http_client, get_task_manager, cleanup_async_utils,
    gather_with_concurrency, timeout_after
)
from utils.async_influxdb_client import (
    initialize_influxdb, cleanup_influxdb, InfluxDBConfig
)
from utils.async_binance_client import (
    initialize_binance_client, cleanup_binance_client, 
    BinanceConfig, get_binance_client
)
from utils.async_signal_manager import (
    initialize_async_signal_manager, cleanup_async_signal_manager,
    get_async_signal_manager
)
from utils.client_manager import (
    ClientManager, ClientConfig, initialize_client_manager, 
    get_client_manager, cleanup_client_manager
)

# Import existing modules
from utils.config_loader import load_config
from utils.error_logger import error_logger_func
from utils.state_manager import get_state_manager, initialize_state_manager
from utils.web_ui.project.api.main import start_server_and_updater
from utils.add_to_hosts import add_to_hosts
from utils.start_frontend import start_frontend

logger = logging.getLogger(__name__)


class AsyncTradingApplication:
    """Main async trading application with optimized operations."""
    
    def __init__(self):
        self.config: Optional[Dict[str, Any]] = None
        self.logger: Optional[logging.Logger] = None
        self.binance_client = None
        self.influxdb_client = None
        self.signal_manager = None
        self.state_manager = None
        self.task_manager = None
        self.shutdown_event = asyncio.Event()
        self.running_tasks: List[asyncio.Task] = []
        self.client_manager = None
    
    async def initialize(self):
        """Initialize all application components asynchronously."""
        try:
            logger.info("Starting async trading application initialization...")
            
            # Load configuration
            self.config = load_config()
            self.logger = error_logger_func()
            
            # Initialize state manager
            self.state_manager = initialize_state_manager("async_state.json")
            
            # Initialize task manager
            self.task_manager = get_task_manager()
            
            # Initialize async signal manager
            self.signal_manager = initialize_async_signal_manager(
                persistence_file="async_signals.json",
                auto_cleanup=True
            )
            
            # Initialize InfluxDB if enabled
            if self.config.get('db_status', False):
                await self._initialize_influxdb()
            
            # Initialize Binance client manager
            await self._initialize_binance_client()
            
            # Set up signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            logger.info("Async trading application initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            raise
    
    async def _initialize_influxdb(self):
        """Initialize InfluxDB asynchronously."""
        try:
            influxdb_config = InfluxDBConfig(
                database=self.config.get('influxdb_database', 'n0namedb'),
                batch_size=1000,
                flush_interval=2.0
            )
            
            self.influxdb_client = await initialize_influxdb(influxdb_config)
            logger.info("InfluxDB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB: {e}")
            # Continue without InfluxDB if it fails
            self.influxdb_client = None
    
    async def _initialize_binance_client(self):
        """Initialize Binance client manager asynchronously."""
        try:
            api_keys = self.config['api_keys']
            
            # Configure Binance client
            binance_config = BinanceConfig(
                api_key=api_keys['api_key'],
                api_secret=api_keys['api_secret'],
                testnet=self.config.get('testnet', False),
                enable_rate_limiting=True,
                enable_request_batching=True,
                batch_size=10,
                max_requests_per_minute=1200,
                max_order_requests_per_second=5
            )
            
            # Configure client manager for robust connection handling
            client_config = ClientConfig(
                min_connections=2,
                max_connections=8,
                health_check_interval=30.0,
                health_check_timeout=10.0,
                max_health_check_failures=3,
                enable_fallback_endpoints=True,
                enable_adaptive_scaling=True,
                enable_connection_warming=True,
                fallback_endpoints=[
                    "https://fapi.binance.com",
                    "https://fapi1.binance.com", 
                    "https://fapi2.binance.com"
                ]
            )
            
            # Initialize and start client manager
            self.client_manager = initialize_client_manager(binance_config, client_config)
            await self.client_manager.start()
            
            # Keep reference to old interface for compatibility
            self.binance_client = get_client_manager()
            
            logger.info("Binance ClientManager initialized successfully")
            
            # Log initial metrics
            metrics = self.client_manager.get_metrics()
            health_status = self.client_manager.get_health_status()
            logger.info(f"ClientManager health: {health_status.value}")
            logger.info(f"Active connections: {metrics['connection_metrics']['active_connections']}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Binance ClientManager: {e}")
            raise
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """Run the main trading application."""
        try:
            # Perform initial setup
            await self._perform_initial_setup()
            
            # Start core trading tasks
            await self._start_trading_tasks()
            
            # Start web interface
            await self._start_web_interface()
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Error in main application loop: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def _perform_initial_setup(self):
        """Perform initial setup operations concurrently."""
        setup_tasks = []
        
        # Add host entry
        setup_tasks.append(self._add_host_entry())
        
        # Set leverage for symbols
        if self.config.get('symbols'):
            setup_tasks.append(self._set_leverage_for_symbols())
        
        # Load existing signals
        setup_tasks.append(self.signal_manager.load_signals_async())
        
        # Execute setup tasks concurrently
        results = await gather_with_concurrency(
            setup_tasks,
            max_concurrency=5,
            return_exceptions=True
        )
        
        # Log any setup errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Setup task {i} failed: {result}")
    
    async def _add_host_entry(self):
        """Add host entry asynchronously."""
        try:
            # Run in executor since it's a blocking operation
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                add_to_hosts,
                "n0name",
                "127.0.0.1"
            )
            logger.info("Host entry added successfully")
        except Exception as e:
            logger.warning(f"Failed to add host entry: {e}")
    
    async def _set_leverage_for_symbols(self):
        """Set leverage for all symbols concurrently using ClientManager."""
        try:
            symbols = self.config['symbols']['symbols']
            leverage = self.config['symbols']['leverage']
            
            # Use client manager for robust connection handling
            async with self.client_manager.get_client() as client:
                # Create batch requests for setting leverage
                batch_requests = []
                for symbol in symbols:
                    batch_requests.append({
                        'method': 'POST',
                        'endpoint': '/fapi/v1/leverage',
                        'params': {'symbol': symbol, 'leverage': leverage},
                        'signed': True
                    })
                
                # Execute batch requests
                results = await client.batch_request(batch_requests)
            
            logger.info(f"Leverage set to {leverage} for {len(symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")
    
    async def _start_trading_tasks(self):
        """Start core trading tasks."""
        symbols = self.config['symbols']['symbols']
        max_open_positions = self.config['symbols']['max_open_positions']
        leverage = self.config['symbols']['leverage']
        
        # Start position monitoring task
        position_task = self.task_manager.create_task(
            self._position_monitoring_loop(symbols, max_open_positions, leverage),
            name="position_monitoring",
            group="trading"
        )
        self.running_tasks.append(position_task)
        
        # Start trend checking task
        trend_task = self.task_manager.create_task(
            self._trend_checking_loop(symbols),
            name="trend_checking",
            group="trading"
        )
        self.running_tasks.append(trend_task)
        
        # Start signal processing task
        signal_task = self.task_manager.create_task(
            self._signal_processing_loop(symbols),
            name="signal_processing",
            group="trading"
        )
        self.running_tasks.append(signal_task)
        
        logger.info("Trading tasks started successfully")
    
    async def _start_web_interface(self):
        """Start web interface components."""
        try:
            symbols = self.config['symbols']['symbols']
            
            # Start frontend
            frontend_task = self.task_manager.create_task(
                self._start_frontend_async(),
                name="frontend",
                group="web"
            )
            self.running_tasks.append(frontend_task)
            
            # Start API server and updater
            server_task, updater_task = await start_server_and_updater(
                symbols, self.binance_client
            )
            
            self.running_tasks.extend([server_task, updater_task])
            
            logger.info("Web interface started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start web interface: {e}")
    
    async def _start_frontend_async(self):
        """Start frontend asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            process = await loop.run_in_executor(None, start_frontend)
            return process
        except Exception as e:
            logger.error(f"Failed to start frontend: {e}")
            return None
    
    async def _position_monitoring_loop(self, symbols: List[str], max_positions: int, leverage: int):
        """Main position monitoring loop."""
        while not self.shutdown_event.is_set():
            try:
                # Process all symbols concurrently
                tasks = [
                    self._process_symbol_positions(symbol, max_positions, leverage)
                    for symbol in symbols
                ]
                
                await gather_with_concurrency(
                    tasks,
                    max_concurrency=10,
                    return_exceptions=True
                )
                
                # Check error counter
                error_count = self.state_manager.get_error_counter()
                if error_count >= 3:
                    logger.error("Too many errors occurred. Shutting down...")
                    await self.shutdown()
                    break
                
                # Wait before next iteration
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in position monitoring loop: {e}")
                self.state_manager.increment_error_counter()
                await asyncio.sleep(5)
    
    async def _process_symbol_positions(self, symbol: str, max_positions: int, leverage: int):
        """Process positions for a specific symbol using ClientManager."""
        try:
            async with self.client_manager.get_client() as client:
                # Get current positions
                positions = await client.get_position_info(symbol)
                
                # Get pending signals for this symbol
                signals = await self.signal_manager.get_pending_signals_async(symbol)
                
                if signals:
                    await self._execute_signal_based_orders(symbol, signals, positions, client)
                
                # Control existing positions
                await self._control_existing_positions(symbol, positions, client)
                
        except Exception as e:
            logger.error(f"Error processing positions for {symbol}: {e}")
    
    async def _execute_signal_based_orders(self, symbol: str, signals: Dict, positions: List[Dict], client):
        """Execute orders based on signals using provided client."""
        try:
            # Check if we can open new positions
            open_positions = [p for p in positions if float(p['positionAmt']) != 0]
            
            if len(open_positions) >= self.config['symbols']['max_open_positions']:
                logger.info(f"Max positions reached for {symbol}, skipping new orders")
                return
            
            # Process each signal
            for signal_id, signal_data in signals.items():
                try:
                    # Determine order parameters
                    side = 'BUY' if signal_data['action'] == 'long' else 'SELL'
                    quantity = await self._calculate_position_size(symbol, signal_data, client)
                    
                    if quantity > 0:
                        # Create market order
                        order_result = await client.create_order(
                            symbol=symbol,
                            side=side,
                            order_type='MARKET',
                            quantity=quantity,
                            reduce_only=False
                        )
                        
                        logger.info(f"Order executed for {symbol}: {order_result['orderId']}")
                        
                        # Mark signal as processed
                        await self.signal_manager.mark_signal_processed_async(signal_id)
                        
                        # Store order in InfluxDB if available
                        if self.influxdb_client:
                            await self._store_order_metrics(symbol, order_result, signal_data)
                
                except Exception as e:
                    logger.error(f"Failed to execute order for signal {signal_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error executing signal-based orders for {symbol}: {e}")
    
    async def _control_existing_positions(self, symbol: str, positions: List[Dict], client):
        """Control existing positions using provided client."""
        try:
            for position in positions:
                position_amt = float(position['positionAmt'])
                
                if position_amt != 0:
                    # Check if position should be closed based on PnL or other criteria
                    unrealized_pnl = float(position['unRealizedProfit'])
                    
                    # Simple PnL-based exit (customize as needed)
                    if unrealized_pnl < -100:  # Close if loss > $100
                        await self._close_position(symbol, position, client)
                    elif unrealized_pnl > 200:  # Close if profit > $200
                        await self._close_position(symbol, position, client)
                        
        except Exception as e:
            logger.error(f"Error controlling positions for {symbol}: {e}")
    
    async def _close_position(self, symbol: str, position: Dict, client):
        """Close a position using provided client."""
        try:
            position_amt = float(position['positionAmt'])
            side = 'SELL' if position_amt > 0 else 'BUY'
            quantity = abs(position_amt)
            
            order_result = await client.create_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=quantity,
                reduce_only=True
            )
            
            logger.info(f"Position closed for {symbol}: {order_result['orderId']}")
            
        except Exception as e:
            logger.error(f"Failed to close position for {symbol}: {e}")
    
    async def _calculate_position_size(self, symbol: str, signal_data: Dict, client) -> float:
        """Calculate position size based on account balance and risk management."""
        try:
            # Get account information
            account_info = await client.get_account_info()
            available_balance = float(account_info['availableBalance'])
            
            # Use 1% of available balance per trade (customize as needed)
            risk_amount = available_balance * 0.01
            
            # Get current price
            ticker = await client.get_ticker_price(symbol)
            current_price = float(ticker['price'])
            
            # Calculate quantity based on risk amount
            quantity = risk_amount / current_price
            
            # Round to appropriate precision (implement precision logic)
            return round(quantity, 3)  # Simplified rounding
            
        except Exception as e:
            logger.error(f"Error calculating position size for {symbol}: {e}")
            return 0.0
    
    async def _trend_checking_loop(self, symbols: List[str]):
        """Trend checking loop."""
        while not self.shutdown_event.is_set():
            try:
                # Process trend checking for all symbols concurrently
                tasks = [
                    self._check_symbol_trend(symbol)
                    for symbol in symbols
                ]
                
                await gather_with_concurrency(
                    tasks,
                    max_concurrency=5,
                    return_exceptions=True
                )
                
                # Wait 5 minutes before next check
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in trend checking loop: {e}")
                await asyncio.sleep(60)
    
    async def _check_symbol_trend(self, symbol: str):
        """Check trend for a specific symbol using ClientManager."""
        try:
            async with self.client_manager.get_client() as client:
                # Get recent klines
                klines = await client.get_klines(
                    symbol=symbol,
                    interval='1h',
                    limit=50
                )
                
                # Analyze trend
                is_uptrend = self._analyze_trend(klines)
                
                if is_uptrend is not None:
                    # Store trend data if InfluxDB is available
                    if self.influxdb_client:
                        await self._store_trend_data(symbol, is_uptrend, klines[-1])
                
        except Exception as e:
            logger.error(f"Error checking trend for {symbol}: {e}")
    
    def _analyze_trend(self, klines: List[List]) -> Optional[bool]:
        """Analyze trend from kline data."""
        # Implement your trend analysis logic here
        # This is a placeholder
        if len(klines) < 10:
            return None
        
        # Simple trend analysis based on price movement
        recent_closes = [float(kline[4]) for kline in klines[-10:]]
        return recent_closes[-1] > recent_closes[0]
    
    async def _signal_processing_loop(self, symbols: List[str]):
        """Signal processing loop."""
        while not self.shutdown_event.is_set():
            try:
                # Clean up expired signals
                await self.signal_manager.cleanup_expired_signals_async()
                
                # Process signals for all symbols
                all_signals = await self.signal_manager.get_signals_for_multiple_symbols_async(symbols)
                
                # Log signal statistics
                for symbol, signals in all_signals.items():
                    if signals:
                        stats = await self.signal_manager.get_signal_statistics_async(symbol)
                        logger.debug(f"Signal stats for {symbol}: {stats}")
                
                # Wait before next processing
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in signal processing loop: {e}")
                await asyncio.sleep(30)
    
    async def shutdown(self):
        """Gracefully shutdown the application."""
        if self.shutdown_event.is_set():
            return
        
        logger.info("Initiating graceful shutdown...")
        self.shutdown_event.set()
        
        try:
            # Cancel all running tasks
            for task in self.running_tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete with timeout
            if self.running_tasks:
                await timeout_after(10, asyncio.gather(*self.running_tasks, return_exceptions=True))
            
            logger.info("All tasks stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during task shutdown: {e}")
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Starting cleanup...")
        
        try:
            # Cancel all running tasks
            for task in self.running_tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete
            if self.running_tasks:
                await asyncio.gather(*self.running_tasks, return_exceptions=True)
            
            # Cancel task manager tasks
            await self.task_manager.cancel_all()
            
            # Cleanup ClientManager
            if hasattr(self, 'client_manager'):
                await cleanup_client_manager()
                logger.info("ClientManager cleaned up")
            
            # Cleanup InfluxDB
            if self.influxdb_client:
                await cleanup_influxdb()
                logger.info("InfluxDB cleaned up")
            
            # Cleanup async utilities
            await cleanup_async_utils()
            logger.info("Async utilities cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        finally:
            logger.info("Cleanup completed")


async def main():
    """Main entry point for the async trading application."""
    app = AsyncTradingApplication()
    
    try:
        # Initialize application
        await app.initialize()
        
        # Run application
        await app.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    finally:
        await app.cleanup()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the async application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1) 