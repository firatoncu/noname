"""
Trading strategies for the n0name trading bot.

This module provides a comprehensive collection of trading strategies
with a factory pattern for easy instantiation and management.
"""

from .factory import StrategyFactory
from .base import BaseStrategy
from .bollinger_rsi import BollingerRSIStrategy
from .macd_fibonacci import MACDFibonacciStrategy
from .registry import StrategyRegistry

__all__ = [
    "StrategyFactory",
    "BaseStrategy",
    "BollingerRSIStrategy",
    "MACDFibonacciStrategy",
    "StrategyRegistry",
] 