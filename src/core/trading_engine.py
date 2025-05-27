"""
Trading Engine - Main Trading Orchestrator

This module provides the main trading engine that orchestrates all trading operations,
implementing the strategy pattern and coordinating between different components.

The TradingEngine class serves as the central coordinator for:
- Strategy execution and signal processing
- Position management and monitoring
- Order execution and lifecycle management
- Risk management and validation
- Performance monitoring and metrics collection

Architecture:
    The trading engine follows a modular design with clear separation of concerns:
    
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   Strategy      │    │  Position       │    │  Order          │
    │   Manager       │◄──►│  Manager        │◄──►│  Manager        │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
            ▲                        ▲                        ▲
            │                        │                        │
            └────────────────────────┼────────────────────────┘
                                     │
                            ┌─────────────────┐
                            │  Trading        │
                            │  Engine         │
                            │  (Coordinator)  │
                            └─────────────────┘

Example:
    Basic usage of the trading engine:
    
    >>> from src.core.trading_engine import TradingEngine, TradingConfig
    >>> from src.strategies.bollinger_rsi import BollingerRSIStrategy
    >>> 
    >>> # Create strategy and configuration
    >>> strategy = BollingerRSIStrategy()
    >>> config = TradingConfig(max_open_positions=5, leverage=10)
    >>> 
    >>> # Initialize trading engine
    >>> engine = TradingEngine(strategy, config)
    >>> await engine.initialize(symbols, client, logger)
    >>> 
    >>> # Start trading
    >>> await engine.start_trading(client, logger)

Author: n0name Development Team
Version: 2.0.0
Last Modified: 2024-01-01
"""

import asyncio
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import time

# Core trading components
from .base_strategy import BaseStrategy, MarketData, SignalType, PositionSide
from .position_manager import PositionManager, PositionConfig, Position
from .order_manager import OrderManager, OrderConfig, Order

# Utility imports
from utils.fetch_data import binance_fetch_data
from utils.calculate_quantity import calculate_quantity
from utils.stepsize_precision import stepsize_precision
from utils.globals import get_capital_tbu, get_db_status
from utils.influxdb.csv_writer import write_to_daily_csv
from utils.influxdb.inf_send_data import write_live_conditions

# Type imports
from src.n0name.types import Symbol, Price, Quantity, Leverage, Percentage
from src.n0name.exceptions import (
    TradingException, 
    SystemException, 
    ValidationException,
    ErrorCategory, 
    ErrorSeverity,
    create_error_context
)

# Enhanced logging
from utils.enhanced_logging import PerformanceLogger, log_performance


class TradingEngineState(str, Enum):
    """
    Enumeration of possible trading engine states.
    
    States:
        IDLE: Engine is initialized but not running
        STARTING: Engine is in the process of starting up
        RUNNING: Engine is actively trading
        STOPPING: Engine is in the process of stopping
        STOPPED: Engine has been stopped
        ERROR: Engine encountered a critical error
    """
    IDLE = "idle"
    STARTING = "starting" 
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class TradingConfig:
    """
    Configuration class for the trading engine.
    
    This dataclass encapsulates all configuration parameters needed for
    trading operations, providing sensible defaults and validation.
    
    Attributes:
        max_open_positions: Maximum number of concurrent open positions
        leverage: Trading leverage multiplier (1-125 for Binance)
        lookback_period: Number of historical candles for analysis
        position_value_percentage: Percentage of capital to use per position (0.0-1.0)
        enable_database_logging: Whether to log trading data to database
        enable_notifications: Whether to send trading notifications
        risk_management_enabled: Whether to apply risk management rules
        max_daily_trades: Maximum number of trades per day (0 = unlimited)
        stop_loss_percentage: Default stop loss percentage (0.0-1.0)
        take_profit_percentage: Default take profit percentage (0.0-1.0)
        min_profit_threshold: Minimum profit threshold to close positions
        max_position_hold_time: Maximum time to hold a position (in hours)
        
    Example:
        >>> config = TradingConfig(
        ...     max_open_positions=3,
        ...     leverage=5,
        ...     position_value_percentage=0.1,
        ...     stop_loss_percentage=0.02
        ... )
    """
    max_open_positions: int = 5
    leverage: Leverage = Leverage(10)
    lookback_period: int = 500
    position_value_percentage: Percentage = 0.2  # 20% of capital per position
    enable_database_logging: bool = True
    enable_notifications: bool = True
    risk_management_enabled: bool = True
    max_daily_trades: int = 0  # 0 = unlimited
    stop_loss_percentage: Percentage = 0.02  # 2% stop loss
    take_profit_percentage: Percentage = 0.05  # 5% take profit
    min_profit_threshold: Percentage = 0.001  # 0.1% minimum profit
    max_position_hold_time: int = 24  # 24 hours
    
    # Performance and monitoring settings
    signal_processing_interval: float = 1.0  # seconds
    position_monitoring_interval: float = 1.0  # seconds
    performance_logging_interval: int = 300  # 5 minutes
    
    def __post_init__(self) -> None:
        """Validate configuration parameters after initialization."""
        self._validate_config()
    
    def _validate_config(self) -> None:
        """
        Validate configuration parameters.
        
        Raises:
            ValidationException: If any configuration parameter is invalid
        """
        errors = []
        
        # Validate numeric ranges
        if self.max_open_positions <= 0:
            errors.append("max_open_positions must be positive")
        
        if not (1 <= self.leverage <= 125):
            errors.append("leverage must be between 1 and 125")
        
        if self.lookback_period < 50:
            errors.append("lookback_period must be at least 50")
        
        if not (0.0 < self.position_value_percentage <= 1.0):
            errors.append("position_value_percentage must be between 0.0 and 1.0")
        
        if not (0.0 <= self.stop_loss_percentage <= 1.0):
            errors.append("stop_loss_percentage must be between 0.0 and 1.0")
        
        if not (0.0 <= self.take_profit_percentage <= 1.0):
            errors.append("take_profit_percentage must be between 0.0 and 1.0")
        
        if self.max_position_hold_time <= 0:
            errors.append("max_position_hold_time must be positive")
        
        if errors:
            raise ValidationException(
                f"Invalid trading configuration: {'; '.join(errors)}",
                context=create_error_context(
                    component="trading_config",
                    operation="validate_config"
                )
            )


@dataclass
class TradingMetrics:
    """
    Container for trading performance metrics.
    
    This class tracks various performance metrics for monitoring
    and analysis of trading operations.
    
    Attributes:
        total_trades: Total number of trades executed
        winning_trades: Number of profitable trades
        losing_trades: Number of losing trades
        total_pnl: Total profit/loss across all trades
        max_drawdown: Maximum drawdown experienced
        win_rate: Percentage of winning trades
        average_trade_duration: Average time positions are held
        sharpe_ratio: Risk-adjusted return metric
        last_updated: Timestamp of last metrics update
    """
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    average_trade_duration: float = 0.0
    sharpe_ratio: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def update_metrics(self, trade_pnl: float, trade_duration: float) -> None:
        """
        Update metrics with new trade data.
        
        Args:
            trade_pnl: Profit/loss of the completed trade
            trade_duration: Duration of the trade in hours
        """
        self.total_trades += 1
        self.total_pnl += trade_pnl
        
        if trade_pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # Update win rate
        self.win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0.0
        
        # Update average trade duration
        self.average_trade_duration = (
            (self.average_trade_duration * (self.total_trades - 1) + trade_duration) 
            / self.total_trades
        )
        
        self.last_updated = datetime.utcnow()


class TradingEngine:
    """
    Main trading engine that orchestrates all trading operations.
    
    This class implements the strategy pattern and coordinates between
    strategies, position management, and order execution. It serves as
    the central hub for all trading activities.
    
    The engine operates in an event-driven manner, continuously processing
    market data, generating signals, and executing trades based on the
    configured strategy.
    
    Attributes:
        strategy: The trading strategy instance
        config: Trading configuration parameters
        position_manager: Position lifecycle manager
        order_manager: Order execution manager
        state: Current engine state
        metrics: Performance metrics tracker
        
    Example:
        >>> strategy = BollingerRSIStrategy()
        >>> config = TradingConfig(max_open_positions=5)
        >>> engine = TradingEngine(strategy, config)
        >>> 
        >>> await engine.initialize(symbols, client, logger)
        >>> await engine.start_trading(client, logger)
    """
    
    def __init__(
        self,
        strategy: BaseStrategy,
        trading_config: Optional[TradingConfig] = None,
        position_config: Optional[PositionConfig] = None,
        order_config: Optional[OrderConfig] = None
    ) -> None:
        """
        Initialize the trading engine.
        
        Args:
            strategy: Trading strategy to use for signal generation
            trading_config: Configuration for trading operations
            position_config: Configuration for position management
            order_config: Configuration for order management
            
        Raises:
            ValidationException: If strategy or configuration is invalid
        """
        # Validate strategy
        if not isinstance(strategy, BaseStrategy):
            raise ValidationException(
                "Strategy must be an instance of BaseStrategy",
                field_name="strategy",
                context=create_error_context(
                    component="trading_engine",
                    operation="initialize"
                )
            )
        
        # Initialize core components
        self.strategy = strategy
        self.config = trading_config or TradingConfig()
        
        # Initialize managers with configurations
        self.position_manager = PositionManager(position_config)
        self.order_manager = OrderManager(order_config)
        
        # Engine state management
        self.state = TradingEngineState.IDLE
        self.metrics = TradingMetrics()
        
        # Trading state variables
        self._is_running = False
        self._symbols: List[Symbol] = []
        self._step_sizes: Dict[Symbol, float] = {}
        self._quantity_precisions: Dict[Symbol, int] = {}
        self._price_precisions: Dict[Symbol, int] = {}
        
        # Performance tracking
        self._last_performance_log = time.time()
        self._iteration_count = 0
        self._start_time: Optional[datetime] = None
        
        # Task management
        self._running_tasks: List[asyncio.Task] = []
    
    @log_performance()
    async def initialize(
        self, 
        symbols: List[Union[str, Symbol]], 
        client, 
        logger: PerformanceLogger
    ) -> None:
        """
        Initialize the trading engine with symbols and market data.
        
        This method prepares the engine for trading by:
        1. Validating and storing trading symbols
        2. Fetching market precision data from the exchange
        3. Initializing strategy with historical data
        4. Setting up monitoring and logging
        
        Args:
            symbols: List of trading symbols to monitor
            client: Binance API client instance
            logger: Enhanced logger for structured logging
            
        Raises:
            ValidationException: If symbols list is invalid
            SystemException: If initialization fails
            
        Example:
            >>> symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
            >>> await engine.initialize(symbols, client, logger)
        """
        try:
            self.state = TradingEngineState.STARTING
            
            # Validate symbols
            if not symbols or not isinstance(symbols, list):
                raise ValidationException(
                    "Symbols must be a non-empty list",
                    field_name="symbols",
                    context=create_error_context(
                        component="trading_engine",
                        operation="initialize"
                    )
                )
            
            # Convert to Symbol type and validate
            validated_symbols = []
            for symbol in symbols:
                if isinstance(symbol, str):
                    symbol = Symbol(symbol)
                validated_symbols.append(symbol)
            
            self._symbols = validated_symbols
            
            logger.info(
                f"Initializing trading engine with {len(self._symbols)} symbols",
                extra={
                    "symbols": [str(s) for s in self._symbols],
                    "strategy": self.strategy.name,
                    "max_positions": self.config.max_open_positions
                }
            )
            
            # Fetch market precision data for accurate order placement
            logger.info("Fetching market precision data...")
            step_sizes, quantity_precisions, price_precisions = await stepsize_precision(
                client, [str(s) for s in self._symbols]
            )
            
            self._step_sizes = {Symbol(k): v for k, v in step_sizes.items()}
            self._quantity_precisions = {Symbol(k): v for k, v in quantity_precisions.items()}
            self._price_precisions = {Symbol(k): v for k, v in price_precisions.items()}
            
            # Initialize strategy with market data
            logger.info("Initializing strategy with historical data...")
            await self._initialize_strategy_data(client, logger)
            
            # Initialize managers
            await self.position_manager.initialize(logger)
            await self.order_manager.initialize(client, logger)
            
            self.state = TradingEngineState.IDLE
            
            logger.info(
                "Trading engine initialized successfully",
                extra={
                    "symbols_count": len(self._symbols),
                    "strategy": self.strategy.name,
                    "precision_data_loaded": True
                }
            )
            
        except Exception as e:
            self.state = TradingEngineState.ERROR
            logger.error(
                "Failed to initialize trading engine",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                extra={"error": str(e)}
            )
            
            if isinstance(e, (ValidationException, SystemException)):
                raise
            else:
                raise SystemException(
                    "Trading engine initialization failed",
                    original_exception=e,
                    context=create_error_context(
                        component="trading_engine",
                        operation="initialize"
                    )
                )
    
    async def _initialize_strategy_data(self, client, logger: PerformanceLogger) -> None:
        """
        Initialize strategy with historical market data.
        
        Args:
            client: Binance API client
            logger: Enhanced logger instance
        """
        for symbol in self._symbols:
            try:
                # Fetch historical data for strategy initialization
                df, current_price = await binance_fetch_data(
                    self.config.lookback_period, 
                    str(symbol), 
                    client
                )
                
                market_data = MarketData(
                    df=df,
                    close_price=current_price,
                    symbol=str(symbol),
                    timestamp=int(time.time() * 1000)
                )
                
                # Validate data with strategy
                if not self.strategy.validate_market_data(market_data):
                    logger.warning(
                        f"Insufficient market data for {symbol}",
                        extra={"symbol": str(symbol), "data_length": len(df)}
                    )
                
            except Exception as e:
                logger.warning(
                    f"Failed to initialize data for {symbol}: {e}",
                    extra={"symbol": str(symbol)}
                )
    
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