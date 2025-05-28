"""
Utilities package for the n0name trading bot.

This package contains various utility modules for:
- Enhanced logging
- Async operations and connection management
- Database operations
- API management
- Windows-specific fixes
- Configuration management
- Exception handling
"""

# Import key utilities for easy access
from .enhanced_logging import get_logger, get_default_logger
from .exceptions import TradingBotException, NetworkException, APIException

# Windows-specific imports (only on Windows)
import sys
if sys.platform.startswith('win'):
    from .windows_asyncio_fixes import initialize_windows_asyncio, windows_asyncio_safe

__version__ = "1.0.0"
__all__ = [
    'get_logger',
    'get_default_logger', 
    'TradingBotException',
    'NetworkException',
    'APIException'
]

# Add Windows-specific exports if on Windows
if sys.platform.startswith('win'):
    __all__.extend(['initialize_windows_asyncio', 'windows_asyncio_safe']) 