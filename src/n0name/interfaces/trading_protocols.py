"""
Trading-specific protocol definitions.

This module defines the protocols that trading-related components must implement.
"""

from abc import abstractmethod
from typing import Protocol, Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import pandas as pd

from ..types import (
    Symbol,
    Price,
    Quantity,
    OrderId,
    PositionId,
    SignalStrength,
    Timestamp,
)
from ..models.trading import (
    TradingSignal,
    MarketData,
    Position,
    Order,
    OrderType,
    OrderSide,
    OrderStatus,
    PositionSide,
    RiskMetrics,
)


class TradingStrategyProtocol(Protocol):
    """Protocol for trading strategies."""
    
    @property
    def name(self) -> str:
        """Strategy name."""
        ...
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """Strategy parameters."""
        ...
    
    @abstractmethod
    async def analyze_market(
        self, 
        market_data: MarketData, 
        symbol: Symbol
    ) -> TradingSignal:
        """
        Analyze market data and generate trading signals.
        
        Args:
            market_data: Market data for analysis
            symbol: Trading symbol
            
        Returns:
            Trading signal with buy/sell/hold recommendation
        """
        ...
    
    @abstractmethod
    def validate_signal(
        self, 
        signal: TradingSignal, 
        market_data: MarketData
    ) -> bool:
        """
        Validate a trading signal before execution.
        
        Args:
            signal: Trading signal to validate
            market_data: Current market data
            
        Returns:
            True if signal is valid, False otherwise
        """
        ...
    
    @abstractmethod
    def get_risk_parameters(self) -> Dict[str, Any]:
        """Get risk management parameters for this strategy."""
        ...


class PositionManagerProtocol(Protocol):
    """Protocol for position management."""
    
    @abstractmethod
    async def open_position(
        self,
        symbol: Symbol,
        side: PositionSide,
        quantity: Quantity,
        entry_price: Price,
        stop_loss: Optional[Price] = None,
        take_profit: Optional[Price] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PositionId:
        """
        Open a new position.
        
        Args:
            symbol: Trading symbol
            side: Position side (long/short)
            quantity: Position quantity
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            metadata: Additional position metadata
            
        Returns:
            Position ID
        """
        ...
    
    @abstractmethod
    async def close_position(
        self,
        position_id: PositionId,
        close_price: Price,
        reason: str = "Manual",
    ) -> bool:
        """
        Close an existing position.
        
        Args:
            position_id: Position to close
            close_price: Closing price
            reason: Reason for closing
            
        Returns:
            True if position was closed successfully
        """
        ...
    
    @abstractmethod
    async def update_position(
        self,
        position_id: PositionId,
        **updates: Any,
    ) -> bool:
        """
        Update position parameters.
        
        Args:
            position_id: Position to update
            **updates: Fields to update
            
        Returns:
            True if position was updated successfully
        """
        ...
    
    @abstractmethod
    def get_position(self, position_id: PositionId) -> Optional[Position]:
        """Get position by ID."""
        ...
    
    @abstractmethod
    def get_positions_by_symbol(self, symbol: Symbol) -> List[Position]:
        """Get all positions for a symbol."""
        ...
    
    @abstractmethod
    def get_all_positions(self) -> List[Position]:
        """Get all open positions."""
        ...
    
    @abstractmethod
    def calculate_unrealized_pnl(
        self, 
        position: Position, 
        current_price: Price
    ) -> Decimal:
        """Calculate unrealized P&L for a position."""
        ...


class OrderManagerProtocol(Protocol):
    """Protocol for order management."""
    
    @abstractmethod
    async def create_order(
        self,
        symbol: Symbol,
        side: OrderSide,
        order_type: OrderType,
        quantity: Quantity,
        price: Optional[Price] = None,
        stop_price: Optional[Price] = None,
        time_in_force: str = "GTC",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OrderId:
        """
        Create a new order.
        
        Args:
            symbol: Trading symbol
            side: Order side (buy/sell)
            order_type: Order type (market/limit/stop)
            quantity: Order quantity
            price: Order price (for limit orders)
            stop_price: Stop price (for stop orders)
            time_in_force: Time in force
            metadata: Additional order metadata
            
        Returns:
            Order ID
        """
        ...
    
    @abstractmethod
    async def cancel_order(self, order_id: OrderId) -> bool:
        """Cancel an existing order."""
        ...
    
    @abstractmethod
    async def modify_order(
        self,
        order_id: OrderId,
        **modifications: Any,
    ) -> bool:
        """Modify an existing order."""
        ...
    
    @abstractmethod
    def get_order(self, order_id: OrderId) -> Optional[Order]:
        """Get order by ID."""
        ...
    
    @abstractmethod
    def get_orders_by_symbol(self, symbol: Symbol) -> List[Order]:
        """Get all orders for a symbol."""
        ...
    
    @abstractmethod
    def get_open_orders(self) -> List[Order]:
        """Get all open orders."""
        ...


class MarketDataProviderProtocol(Protocol):
    """Protocol for market data providers."""
    
    @abstractmethod
    async def get_klines(
        self,
        symbol: Symbol,
        interval: str,
        limit: int = 500,
        start_time: Optional[Timestamp] = None,
        end_time: Optional[Timestamp] = None,
    ) -> pd.DataFrame:
        """
        Get historical kline/candlestick data.
        
        Args:
            symbol: Trading symbol
            interval: Kline interval (1m, 5m, 1h, etc.)
            limit: Number of klines to retrieve
            start_time: Start time for data
            end_time: End time for data
            
        Returns:
            DataFrame with OHLCV data
        """
        ...
    
    @abstractmethod
    async def get_ticker_price(self, symbol: Symbol) -> Price:
        """Get current ticker price for a symbol."""
        ...
    
    @abstractmethod
    async def get_order_book(
        self, 
        symbol: Symbol, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get order book data for a symbol."""
        ...
    
    @abstractmethod
    async def get_24hr_ticker(self, symbol: Symbol) -> Dict[str, Any]:
        """Get 24hr ticker statistics for a symbol."""
        ...


class RiskManagerProtocol(Protocol):
    """Protocol for risk management."""
    
    @abstractmethod
    async def validate_trade(
        self,
        signal: TradingSignal,
        position_size: Quantity,
        current_positions: List[Position],
    ) -> Tuple[bool, str]:
        """
        Validate a trade against risk parameters.
        
        Args:
            signal: Trading signal
            position_size: Proposed position size
            current_positions: Current open positions
            
        Returns:
            Tuple of (is_valid, reason)
        """
        ...
    
    @abstractmethod
    def calculate_position_size(
        self,
        signal: TradingSignal,
        account_balance: Decimal,
        risk_per_trade: float,
    ) -> Quantity:
        """
        Calculate appropriate position size based on risk parameters.
        
        Args:
            signal: Trading signal
            account_balance: Current account balance
            risk_per_trade: Risk percentage per trade
            
        Returns:
            Calculated position size
        """
        ...
    
    @abstractmethod
    def calculate_stop_loss(
        self,
        entry_price: Price,
        side: PositionSide,
        atr: Optional[float] = None,
    ) -> Price:
        """Calculate stop loss price."""
        ...
    
    @abstractmethod
    def calculate_take_profit(
        self,
        entry_price: Price,
        side: PositionSide,
        risk_reward_ratio: float = 2.0,
        stop_loss: Optional[Price] = None,
    ) -> Price:
        """Calculate take profit price."""
        ...
    
    @abstractmethod
    def get_risk_metrics(
        self, 
        positions: List[Position]
    ) -> RiskMetrics:
        """Calculate current risk metrics."""
        ... 