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

# Import available modules
try:
    from .cli import main as cli_main
except ImportError:
    cli_main = None

try:
    from .exceptions import (
        TradingBotException,
        NetworkException,
        APIException,
        ConfigurationException,
        SystemException,
    )
except ImportError:
    # Define basic exceptions if the module doesn't exist
    class TradingBotException(Exception):
        """Base exception for trading bot errors."""
        pass

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    # Available functions
    "cli_main",
    # Exceptions
    "TradingBotException",
] 