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
            
            # Initialize Binance client
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
        """Initialize Binance client asynchronously."""
        try:
            api_keys = self.config['api_keys']
            
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
            
            self.binance_client = initialize_binance_client(binance_config)
            await self.binance_client.connect()
            
            logger.info("Binance client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
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
        """Set leverage for all symbols concurrently."""
        try:
            symbols = self.config['symbols']['symbols']
            leverage = self.config['symbols']['leverage']
            
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
            results = await self.binance_client.batch_request(batch_requests)
            
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
        """Process positions for a single symbol."""
        try:
            # Get current position
            positions = await self.binance_client.get_position_info(symbol)
            
            # Get trading signals
            signals = await self.signal_manager.get_all_active_signals_async(symbol)
            
            # Process position logic here
            # This would include your existing position management logic
            # but optimized for async operations
            
            # Example: Check for buy/sell signals and execute orders
            if signals:
                await self._execute_signal_based_orders(symbol, signals, positions)
            
        except Exception as e:
            logger.error(f"Error processing positions for {symbol}: {e}")
            raise
    
    async def _execute_signal_based_orders(self, symbol: str, signals: Dict, positions: List[Dict]):
        """Execute orders based on signals."""
        try:
            # This is a simplified example - implement your actual trading logic
            from utils.async_binance_client import RequestType
            
            buy_signal = signals.get('BUY')
            sell_signal = signals.get('SELL')
            
            if buy_signal and buy_signal.value > 0:
                # Execute buy order
                order_result = await self.binance_client.create_order(
                    symbol=symbol,
                    side='BUY',
                    order_type='MARKET',
                    quantity=0.001  # Calculate appropriate quantity
                )
                
                logger.info(f"Buy order executed for {symbol}: {order_result}")
                
                # Confirm signal
                await self.signal_manager.confirm_signal_async(
                    symbol, buy_signal.signal_type, "Order executed"
                )
            
            elif sell_signal and sell_signal.value > 0:
                # Execute sell order
                order_result = await self.binance_client.create_order(
                    symbol=symbol,
                    side='SELL',
                    order_type='MARKET',
                    quantity=0.001  # Calculate appropriate quantity
                )
                
                logger.info(f"Sell order executed for {symbol}: {order_result}")
                
                # Confirm signal
                await self.signal_manager.confirm_signal_async(
                    symbol, sell_signal.signal_type, "Order executed"
                )
            
        except Exception as e:
            logger.error(f"Error executing orders for {symbol}: {e}")
            raise
    
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
        """Check trend for a single symbol."""
        try:
            # Get kline data
            klines = await self.binance_client.get_klines(
                symbol=symbol,
                interval='1h',
                limit=100
            )
            
            # Analyze trend (implement your trend analysis logic)
            trend_signal = self._analyze_trend(klines)
            
            # Create trend signal
            if trend_signal is not None:
                await self.signal_manager.create_signal_async(
                    symbol=symbol,
                    signal_type='TREND',
                    value=trend_signal,
                    confidence=0.7,
                    source_indicator='trend_analysis'
                )
            
        except Exception as e:
            logger.error(f"Error checking trend for {symbol}: {e}")
            raise
    
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
        """Clean up all resources."""
        try:
            logger.info("Cleaning up application resources...")
            
            # Clean up async utilities
            await cleanup_async_utils()
            
            # Clean up Binance client
            await cleanup_binance_client()
            
            # Clean up InfluxDB
            await cleanup_influxdb()
            
            # Clean up signal manager
            await cleanup_async_signal_manager()
            
            logger.info("Application cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


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