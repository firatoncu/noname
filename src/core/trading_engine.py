"""
Trading Engine - Main Trading Orchestrator

This module provides the main trading engine that orchestrates all trading operations,
implementing the strategy pattern and coordinating between different components.
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .base_strategy import BaseStrategy, MarketData, SignalType, PositionSide
from .position_manager import PositionManager, PositionConfig
from .order_manager import OrderManager, OrderConfig
from utils.fetch_data import binance_fetch_data
from utils.calculate_quantity import calculate_quantity
from utils.stepsize_precision import stepsize_precision
from utils.globals import get_capital_tbu, get_db_status
from utils.influxdb.csv_writer import write_to_daily_csv
from utils.influxdb.inf_send_data import write_live_conditions


@dataclass
class TradingConfig:
    """Configuration for the trading engine"""
    max_open_positions: int = 5
    leverage: int = 10
    lookback_period: int = 500
    position_value_percentage: float = 0.2  # 20% of capital per position
    enable_database_logging: bool = True
    enable_notifications: bool = True


class TradingEngine:
    """
    Main trading engine that orchestrates all trading operations.
    
    This class implements the strategy pattern and coordinates between
    strategies, position management, and order execution.
    """
    
    def __init__(
        self,
        strategy: BaseStrategy,
        trading_config: TradingConfig = None,
        position_config: PositionConfig = None,
        order_config: OrderConfig = None
    ):
        """
        Initialize the trading engine.
        
        Args:
            strategy: Trading strategy to use
            trading_config: Trading engine configuration
            position_config: Position management configuration
            order_config: Order management configuration
        """
        self.strategy = strategy
        self.config = trading_config or TradingConfig()
        
        # Initialize managers
        self.position_manager = PositionManager(position_config)
        self.order_manager = OrderManager(order_config)
        
        # Trading state
        self._is_running = False
        self._symbols: List[str] = []
        self._step_sizes: Dict[str, float] = {}
        self._quantity_precisions: Dict[str, int] = {}
        self._price_precisions: Dict[str, int] = {}
    
    async def initialize(self, symbols: List[str], client, logger):
        """
        Initialize the trading engine with symbols and market data.
        
        Args:
            symbols: List of trading symbols
            client: Binance client
            logger: Logger instance
        """
        try:
            self._symbols = symbols
            
            # Get market precision data
            step_sizes, quantity_precisions, price_precisions = await stepsize_precision(client, symbols)
            self._step_sizes = step_sizes
            self._quantity_precisions = quantity_precisions
            self._price_precisions = price_precisions
            
            logger.info(f"Trading engine initialized with {len(symbols)} symbols")
            logger.info(f"Strategy: {self.strategy.name}")
            
        except Exception as e:
            logger.error(f"Error initializing trading engine: {e}")
            raise
    
    async def start_trading(self, client, logger):
        """
        Start the main trading loop.
        
        Args:
            client: Binance client
            logger: Logger instance
        """
        if self._is_running:
            logger.warning("Trading engine is already running")
            return
        
        self._is_running = True
        logger.info("Starting trading engine...")
        
        try:
            # Start position monitoring task
            position_task = asyncio.create_task(
                self._position_monitoring_loop(client, logger)
            )
            
            # Start signal processing task
            signal_task = asyncio.create_task(
                self._signal_processing_loop(client, logger)
            )
            
            # Wait for both tasks
            await asyncio.gather(position_task, signal_task)
            
        except Exception as e:
            logger.error(f"Error in trading engine: {e}")
        finally:
            self._is_running = False
            logger.info("Trading engine stopped")
    
    async def stop_trading(self):
        """Stop the trading engine"""
        self._is_running = False
    
    async def _signal_processing_loop(self, client, logger):
        """Main signal processing loop"""
        while self._is_running:
            try:
                # Process each symbol
                tasks = [
                    self._process_symbol_signals(symbol, client, logger)
                    for symbol in self._symbols
                ]
                
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(1)  # Small delay between iterations
                
            except Exception as e:
                logger.error(f"Error in signal processing loop: {e}")
                await asyncio.sleep(5)
    
    async def _position_monitoring_loop(self, client, logger):
        """Position monitoring loop"""
        while self._is_running:
            try:
                # Monitor all open positions
                positions = self.position_manager.get_all_positions()
                
                for symbol, position in positions.items():
                    await self._monitor_position(symbol, client, logger)
                
                await asyncio.sleep(1)  # Monitor positions every second
                
            except Exception as e:
                logger.error(f"Error in position monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _process_symbol_signals(self, symbol: str, client, logger):
        """
        Process trading signals for a single symbol.
        
        Args:
            symbol: Trading symbol
            client: Binance client
            logger: Logger instance
        """
        try:
            # Skip if already have position
            if self.position_manager.has_position(symbol):
                return
            
            # Check if we can open new positions
            current_positions = len(self.position_manager.get_all_positions())
            if current_positions >= self.config.max_open_positions:
                return
            
            # Fetch market data
            df, close_price = await binance_fetch_data(
                self.config.lookback_period, symbol, client
            )
            
            market_data = MarketData(
                df=df,
                close_price=close_price,
                symbol=symbol
            )
            
            # Validate market data
            if not self.strategy.validate_market_data(market_data):
                logger.warning(f"Insufficient market data for {symbol}")
                return
            
            # Check trading signals
            buy_signal = self.strategy.check_buy_conditions(market_data, symbol, logger)
            sell_signal = self.strategy.check_sell_conditions(market_data, symbol, logger)
            
            # Process signals
            await self._process_trading_signals(
                symbol, buy_signal, sell_signal, market_data, client, logger
            )
            
            # Log to database if enabled
            if self.config.enable_database_logging and get_db_status():
                await write_live_conditions(df['timestamp'].iloc[-1], symbol)
            
        except Exception as e:
            logger.error(f"Error processing signals for {symbol}: {e}")
    
    async def _process_trading_signals(
        self,
        symbol: str,
        buy_signal,
        sell_signal,
        market_data: MarketData,
        client,
        logger
    ):
        """
        Process buy and sell signals for a symbol.
        
        Args:
            symbol: Trading symbol
            buy_signal: Buy signal from strategy
            sell_signal: Sell signal from strategy
            market_data: Market data
            client: Binance client
            logger: Logger instance
        """
        try:
            # Calculate position size
            capital_tbu = get_capital_tbu()
            position_value = (capital_tbu * self.config.position_value_percentage)
            
            quantity = calculate_quantity(
                position_value,
                market_data.close_price,
                self._step_sizes[symbol],
                self._quantity_precisions[symbol]
            )
            
            # Process buy signal
            if (hasattr(buy_signal, 'signal_type') and 
                buy_signal.signal_type == SignalType.BUY and
                all(buy_signal.conditions.values())):
                
                await self._execute_trade(
                    symbol, PositionSide.LONG, quantity, client, logger, buy_signal
                )
            
            # Process sell signal
            elif (hasattr(sell_signal, 'signal_type') and 
                  sell_signal.signal_type == SignalType.SELL and
                  all(sell_signal.conditions.values())):
                
                await self._execute_trade(
                    symbol, PositionSide.SHORT, quantity, client, logger, sell_signal
                )
            
        except Exception as e:
            logger.error(f"Error processing trading signals for {symbol}: {e}")
    
    async def _execute_trade(
        self,
        symbol: str,
        side: PositionSide,
        quantity: float,
        client,
        logger,
        signal
    ):
        """
        Execute a trade.
        
        Args:
            symbol: Trading symbol
            side: Position side
            quantity: Trade quantity
            client: Binance client
            logger: Logger instance
            signal: Trading signal
        """
        try:
            # Create market order
            order_result = await self.order_manager.create_market_order(
                symbol, side, quantity, client, logger, signal
            )
            
            if order_result.success:
                # Open position in position manager
                await self.position_manager.open_position(
                    symbol, side, quantity, client, logger
                )
                
                logger.info(
                    f"Trade executed: {symbol} {side.value} {quantity} "
                    f"(Signal strength: {signal.strength:.2f})"
                )
            else:
                logger.error(f"Failed to execute trade for {symbol}: {order_result.error_message}")
            
        except Exception as e:
            logger.error(f"Error executing trade for {symbol}: {e}")
    
    async def _monitor_position(self, symbol: str, client, logger):
        """
        Monitor a single position.
        
        Args:
            symbol: Trading symbol
            client: Binance client
            logger: Logger instance
        """
        try:
            # Fetch current market data
            df, close_price = await binance_fetch_data(300, symbol, client)
            
            market_data = MarketData(
                df=df,
                close_price=close_price,
                symbol=symbol
            )
            
            # Monitor position
            position_closed = await self.position_manager.monitor_position(
                symbol, market_data, client, logger, self._price_precisions
            )
            
            if position_closed:
                logger.info(f"Position closed for {symbol}")
            
        except Exception as e:
            logger.error(f"Error monitoring position for {symbol}: {e}")
    
    def switch_strategy(self, new_strategy: BaseStrategy, logger):
        """
        Switch to a new trading strategy.
        
        Args:
            new_strategy: New strategy to use
            logger: Logger instance
        """
        old_strategy_name = self.strategy.name
        self.strategy = new_strategy
        logger.info(f"Switched strategy from {old_strategy_name} to {new_strategy.name}")
    
    def get_trading_status(self) -> Dict[str, Any]:
        """
        Get current trading status.
        
        Returns:
            Dictionary with trading status information
        """
        positions = self.position_manager.get_position_summary()
        order_stats = self.order_manager.get_statistics()
        
        return {
            "is_running": self._is_running,
            "strategy": self.strategy.name,
            "symbols": self._symbols,
            "config": {
                "max_open_positions": self.config.max_open_positions,
                "leverage": self.config.leverage,
                "lookback_period": self.config.lookback_period,
                "position_value_percentage": self.config.position_value_percentage
            },
            "positions": positions,
            "orders": order_stats
        }
    
    def update_config(self, new_config: TradingConfig):
        """Update trading configuration"""
        self.config = new_config
    
    async def close_all_positions(self, client, logger, reason: str = "Manual"):
        """
        Close all open positions.
        
        Args:
            client: Binance client
            logger: Logger instance
            reason: Reason for closing positions
        """
        positions = self.position_manager.get_all_positions()
        
        for symbol in positions.keys():
            await self.position_manager.close_position(symbol, client, logger, reason)
        
        logger.info(f"Closed all positions. Reason: {reason}")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about the current strategy"""
        return self.strategy.get_strategy_info() 