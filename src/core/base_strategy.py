"""
Base Strategy Class for Trading Strategies

This module provides the abstract base class for all trading strategies,
implementing the Strategy Pattern for flexible strategy switching.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
import pandas as pd
from dataclasses import dataclass
from enum import Enum


class SignalType(Enum):
    """Enumeration for trading signals"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class PositionSide(Enum):
    """Enumeration for position sides"""
    LONG = "long"
    SHORT = "short"
    NONE = "none"


@dataclass
class TradingSignal:
    """Data class for trading signals"""
    signal_type: SignalType
    strength: float  # Signal strength (0.0 to 1.0)
    conditions: Dict[str, bool]  # Individual condition results
    metadata: Dict[str, Any] = None  # Additional signal metadata
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class MarketData:
    """Data class for market data"""
    df: pd.DataFrame
    close_price: float
    symbol: str
    timeframe: str = "5m"
    
    @property
    def close_prices(self) -> pd.Series:
        return self.df['close'].astype(float)
    
    @property
    def high_prices(self) -> pd.Series:
        return self.df['high'].astype(float)
    
    @property
    def low_prices(self) -> pd.Series:
        return self.df['low'].astype(float)
    
    @property
    def volume(self) -> pd.Series:
        return self.df['volume'].astype(float)


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    This class defines the interface that all trading strategies must implement,
    following the Strategy Pattern for flexible strategy switching.
    """
    
    def __init__(self, name: str, parameters: Dict[str, Any] = None):
        """
        Initialize the strategy.
        
        Args:
            name: Strategy name
            parameters: Strategy-specific parameters
        """
        self.name = name
        self.parameters = parameters or {}
        self._signal_state = {}  # Internal state for multi-step signals
    
    @abstractmethod
    def check_buy_conditions(self, market_data: MarketData, symbol: str, logger) -> TradingSignal:
        """
        Check if buy conditions are met.
        
        Args:
            market_data: Market data for analysis
            symbol: Trading symbol
            logger: Logger instance
            
        Returns:
            TradingSignal with buy signal information
        """
        pass
    
    @abstractmethod
    def check_sell_conditions(self, market_data: MarketData, symbol: str, logger) -> TradingSignal:
        """
        Check if sell conditions are met.
        
        Args:
            market_data: Market data for analysis
            symbol: Trading symbol
            logger: Logger instance
            
        Returns:
            TradingSignal with sell signal information
        """
        pass
    
    def get_signal_state(self, symbol: str) -> Dict[str, Any]:
        """Get the current signal state for a symbol"""
        return self._signal_state.get(symbol, {})
    
    def set_signal_state(self, symbol: str, state: Dict[str, Any]):
        """Set the signal state for a symbol"""
        self._signal_state[symbol] = state
    
    def reset_signal_state(self, symbol: str):
        """Reset the signal state for a symbol"""
        if symbol in self._signal_state:
            del self._signal_state[symbol]
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get a strategy parameter"""
        return self.parameters.get(key, default)
    
    def set_parameter(self, key: str, value: Any):
        """Set a strategy parameter"""
        self.parameters[key] = value
    
    @abstractmethod
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get strategy information and parameters.
        
        Returns:
            Dictionary with strategy information
        """
        pass
    
    def validate_market_data(self, market_data: MarketData, min_periods: int = 50) -> bool:
        """
        Validate that market data has sufficient periods for analysis.
        
        Args:
            market_data: Market data to validate
            min_periods: Minimum required periods
            
        Returns:
            True if data is sufficient, False otherwise
        """
        return len(market_data.df) >= min_periods
    
    def __str__(self) -> str:
        return f"{self.name} Strategy"
    
    def __repr__(self) -> str:
        return f"BaseStrategy(name='{self.name}', parameters={self.parameters})" 