"""
n0name Trading Bot - Advanced Algorithmic Trading Platform

A modern, high-performance trading bot with comprehensive features including:
- Multiple trading strategies with pluggable architecture
- Real-time market data processing
- Risk management and position control
- Web-based monitoring interface
- Comprehensive logging and error handling
- Performance optimization and monitoring

Author: n0name Team
License: MIT
"""

from typing import Final

# Version information
__version__: Final[str] = "2.0.0"
__author__: Final[str] = "n0name Team"
__email__: Final[str] = "contact@n0name.com"
__license__: Final[str] = "MIT"

# Core exports
from .core.trading_engine import TradingEngine
from .core.base_strategy import BaseStrategy, TradingSignal, MarketData
from .core.position_manager import PositionManager
from .core.order_manager import OrderManager

# Configuration exports
from .config.models import TradingConfig, DatabaseConfig, SecurityConfig
from .config.manager import ConfigManager

# Service exports
from .services.binance_service import BinanceService
from .services.notification_service import NotificationService
from .services.monitoring_service import MonitoringService

# Dependency injection
from .di.container import Container

# Exceptions
from .exceptions import (
    TradingBotException,
    NetworkException,
    APIException,
    ConfigurationException,
    SystemException,
)

# Main application
from .main import TradingBotApplication

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    # Core components
    "TradingEngine",
    "BaseStrategy",
    "TradingSignal",
    "MarketData",
    "PositionManager",
    "OrderManager",
    # Configuration
    "TradingConfig",
    "DatabaseConfig",
    "SecurityConfig",
    "ConfigManager",
    # Services
    "BinanceService",
    "NotificationService",
    "MonitoringService",
    # Dependency injection
    "Container",
    # Exceptions
    "TradingBotException",
    "NetworkException",
    "APIException",
    "ConfigurationException",
    "SystemException",
    # Main application
    "TradingBotApplication",
] 