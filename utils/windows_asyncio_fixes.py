"""
Windows-specific asyncio fixes and error suppression.

This module provides utilities to handle common Windows asyncio issues:
- Connection reset errors (WinError 10054)
- Connection aborted errors (WinError 10053)
- Broken pipe errors
- Resource warnings

These errors are typically harmless and occur due to normal network behavior
but can clutter logs and cause unnecessary alarm.
"""

import asyncio
import logging
import sys
import warnings
from typing import Dict, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class WindowsAsyncioErrorSuppressor:
    """Handles suppression of harmless Windows asyncio errors."""
    
    def __init__(self, suppress_resource_warnings: bool = True):
        self.suppress_resource_warnings = suppress_resource_warnings
        self.suppressed_errors = {
            'ConnectionResetError': 0,
            'ConnectionAbortedError': 0,
            'BrokenPipeError': 0,
            'ResourceWarning': 0,
            'ConnectionMessage': 0
        }
        
    def setup_error_suppression(self):
        """Set up error suppression for Windows asyncio."""
        if not sys.platform.startswith('win'):
            logger.debug("Not on Windows, skipping asyncio error suppression")
            return
            
        logger.info("Setting up Windows asyncio error suppression")
        
        # Suppress resource warnings if requested
        if self.suppress_resource_warnings:
            warnings.filterwarnings("ignore", category=ResourceWarning)
            
        # Set up custom exception handler
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(self.exception_handler)
        
    def exception_handler(self, loop: asyncio.AbstractEventLoop, context: Dict[str, Any]):
        """Custom exception handler for asyncio loop."""
        exception = context.get('exception')
        message = context.get('message', '')
        
        if exception:
            exception_type = type(exception).__name__
            
            # Check if this is a harmless connection error
            if self._is_harmless_connection_error(exception):
                self.suppressed_errors[exception_type] += 1
                
                # Log at debug level for monitoring (only occasionally to avoid spam)
                if self.suppressed_errors[exception_type] % 10 == 1:  # Log every 10th occurrence
                    logger.debug(
                        f"Suppressed {self.suppressed_errors[exception_type]} harmless {exception_type} errors",
                        extra={
                            'suppressed_error_type': exception_type,
                            'total_suppressed': self.suppressed_errors[exception_type]
                        }
                    )
                return
        
        # Check for harmless connection messages in the context
        if any(phrase in message.lower() for phrase in [
            'connection lost', 'connection reset', 'connection aborted',
            'broken pipe', 'forcibly closed'
        ]):
            self.suppressed_errors['ConnectionMessage'] = self.suppressed_errors.get('ConnectionMessage', 0) + 1
            return
        
        # For other exceptions, use default handler
        loop.default_exception_handler(context)
        
    def _is_harmless_connection_error(self, exception: Exception) -> bool:
        """Check if an exception is a harmless connection error."""
        harmless_types = (
            ConnectionResetError,    # WinError 10054
            ConnectionAbortedError,  # WinError 10053
            BrokenPipeError,        # Broken pipe
        )
        
        if isinstance(exception, harmless_types):
            # Additional checks for specific error codes
            if hasattr(exception, 'winerror'):
                # WinError 10054: Connection reset by peer
                # WinError 10053: Connection aborted by software
                if exception.winerror in (10054, 10053):
                    return True
            return True
            
        return False
        
    def get_suppression_stats(self) -> Dict[str, int]:
        """Get statistics on suppressed errors."""
        return self.suppressed_errors.copy()
        
    def log_suppression_summary(self):
        """Log a summary of suppressed errors."""
        total_suppressed = sum(self.suppressed_errors.values())
        if total_suppressed > 0:
            logger.info(
                f"Suppressed {total_suppressed} harmless connection errors",
                extra={'suppression_stats': self.suppressed_errors}
            )


def setup_windows_asyncio_fixes(suppress_resource_warnings: bool = True) -> WindowsAsyncioErrorSuppressor:
    """
    Set up Windows asyncio fixes and error suppression.
    
    Args:
        suppress_resource_warnings: Whether to suppress ResourceWarning messages
        
    Returns:
        WindowsAsyncioErrorSuppressor instance for monitoring
    """
    suppressor = WindowsAsyncioErrorSuppressor(suppress_resource_warnings)
    suppressor.setup_error_suppression()
    return suppressor


def windows_asyncio_safe(func):
    """
    Decorator to make async functions safer on Windows by catching harmless errors.
    
    This decorator catches and logs (at debug level) common Windows connection errors
    that don't affect functionality but can clutter error logs.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
            logger.debug(
                f"Caught harmless connection error in {func.__name__}: {e}",
                extra={
                    'function': func.__name__,
                    'error_type': type(e).__name__,
                    'error_code': getattr(e, 'winerror', None)
                }
            )
            # Re-raise if it's not a harmless Windows error
            if not (hasattr(e, 'winerror') and e.winerror in (10054, 10053)):
                raise
        except Exception:
            # Re-raise all other exceptions
            raise
            
    return wrapper


def configure_windows_event_loop():
    """Configure asyncio event loop for optimal Windows performance."""
    if not sys.platform.startswith('win'):
        return
        
    # Use ProactorEventLoop for better Windows compatibility
    if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        logger.debug("Set Windows ProactorEventLoop policy")
    
    # Configure event loop settings
    try:
        loop = asyncio.get_event_loop()
        
        # Set debug mode if in development
        if __debug__:
            loop.set_debug(False)  # Disable debug mode to reduce noise
            
    except RuntimeError:
        # No event loop running yet
        pass


# Global suppressor instance
_global_suppressor: Optional[WindowsAsyncioErrorSuppressor] = None


def get_global_suppressor() -> Optional[WindowsAsyncioErrorSuppressor]:
    """Get the global error suppressor instance."""
    return _global_suppressor


def initialize_windows_asyncio():
    """Initialize Windows asyncio fixes and return suppressor for monitoring."""
    global _global_suppressor
    
    if sys.platform.startswith('win'):
        configure_windows_event_loop()
        _global_suppressor = setup_windows_asyncio_fixes()
        logger.info("Windows asyncio fixes initialized")
        return _global_suppressor
    else:
        logger.debug("Not on Windows, skipping asyncio fixes")
        return None 