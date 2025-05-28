"""
Enhanced Logging System with Structured Logging and Log Rotation

This module provides:
- Structured logging with JSON format support
- Multiple log levels with proper categorization
- Log rotation with size and time-based rotation
- Performance monitoring and metrics
- Context-aware logging with correlation IDs
- Error categorization and severity levels
- Async-safe logging operations
"""

import logging
import logging.handlers
import json
import os
import sys
import time
import asyncio
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import traceback
import uuid
from contextlib import contextmanager
import functools


class LogLevel(Enum):
    """Enhanced log levels with specific use cases"""
    TRACE = 5      # Very detailed debugging
    DEBUG = 10     # Debugging information
    INFO = 20      # General information
    WARNING = 30   # Warning messages
    ERROR = 40     # Error messages
    CRITICAL = 50  # Critical errors
    AUDIT = 60     # Audit trail events


class ErrorCategory(Enum):
    """Error categorization for better analysis"""
    NETWORK = "network"
    API = "api"
    DATA = "data"
    TRADING = "trading"
    SYSTEM = "system"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    CONFIGURATION = "configuration"
    PERFORMANCE = "performance"
    UNKNOWN = "unknown"


class LogSeverity(Enum):
    """Log severity levels for prioritization"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LogContext:
    """Context information for structured logging"""
    correlation_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    symbol: Optional[str] = None
    strategy: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class LogMetrics:
    """Logging metrics for monitoring"""
    total_logs: int = 0
    error_count: int = 0
    warning_count: int = 0
    critical_count: int = 0
    last_error_time: Optional[datetime] = None
    last_critical_time: Optional[datetime] = None
    errors_by_category: Dict[str, int] = None
    
    def __post_init__(self):
        if self.errors_by_category is None:
            self.errors_by_category = {}


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields if enabled
        if self.include_extra:
            for key, value in record.__dict__.items():
                if key not in log_data and not key.startswith('_'):
                    try:
                        # Ensure value is JSON serializable
                        json.dumps(value)
                        log_data[key] = value
                    except (TypeError, ValueError):
                        log_data[key] = str(value)
        
        return json.dumps(log_data, ensure_ascii=False)


class EnhancedLogger:
    """Enhanced logger with structured logging and advanced features"""
    
    def __init__(
        self,
        name: str,
        log_dir: str = "logs",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        enable_console: bool = True,
        enable_json: bool = True,
        enable_rotation: bool = True,
        log_level: str = "INFO"  # Add log_level parameter
    ):
        """
        Initialize enhanced logger
        
        Args:
            name: Logger name
            log_dir: Directory for log files
            max_file_size: Maximum size per log file in bytes
            backup_count: Number of backup files to keep
            enable_console: Enable console output
            enable_json: Enable JSON structured logging
            enable_rotation: Enable log rotation
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.enable_console = enable_console
        self.enable_json = enable_json
        self.enable_rotation = enable_rotation
        
        # Create log directory
        self.log_dir.mkdir(exist_ok=True)
        
        # Initialize logger
        self.logger = logging.getLogger(name)
        # Set log level from config instead of hardcoded TRACE
        self.set_log_level(log_level)
        self.logger.handlers.clear()
        
        # Initialize metrics
        self.metrics = LogMetrics()
        self._metrics_lock = threading.Lock()
        
        # Context storage
        self._context_storage = threading.local()
        
        # Setup handlers
        self._setup_handlers()
        
        # Add custom log levels
        self._add_custom_levels()
    
    def set_log_level(self, level: str):
        """Set the log level from string"""
        level_map = {
            "TRACE": LogLevel.TRACE.value,
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
            "AUDIT": LogLevel.AUDIT.value
        }
        
        numeric_level = level_map.get(level.upper(), logging.INFO)
        self.logger.setLevel(numeric_level)
        
        # Update console handler level if it exists
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream.name == '<stdout>':
                handler.setLevel(numeric_level)
    
    def _add_custom_levels(self):
        """Add custom log levels"""
        logging.addLevelName(LogLevel.TRACE.value, "TRACE")
        logging.addLevelName(LogLevel.AUDIT.value, "AUDIT")
        
        # Add methods to logger
        def trace(self, message, *args, **kwargs):
            if self.isEnabledFor(LogLevel.TRACE.value):
                self._log(LogLevel.TRACE.value, message, args, **kwargs)
        
        def audit(self, message, *args, **kwargs):
            if self.isEnabledFor(LogLevel.AUDIT.value):
                self._log(LogLevel.AUDIT.value, message, args, **kwargs)
        
        logging.Logger.trace = trace
        logging.Logger.audit = audit
    
    def _setup_handlers(self):
        """Setup log handlers"""
        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.logger.level)
            
            if self.enable_json:
                console_handler.setFormatter(StructuredFormatter())
            else:
                console_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                console_handler.setFormatter(console_formatter)
            
            self.logger.addHandler(console_handler)
        
        # File handlers for different log levels
        self._setup_file_handlers()
    
    def _setup_file_handlers(self):
        """Setup file handlers for different log levels"""
        handlers_config = [
            ("all", logging.NOTSET, "all.log"),
            ("error", logging.ERROR, "error.log"),
            ("warning", logging.WARNING, "warning.log"),
            ("audit", LogLevel.AUDIT.value, "audit.log"),
            ("performance", LogLevel.TRACE.value, "performance.log"),
        ]
        
        for handler_name, level, filename in handlers_config:
            file_path = self.log_dir / filename
            
            if self.enable_rotation:
                handler = logging.handlers.RotatingFileHandler(
                    file_path,
                    maxBytes=self.max_file_size,
                    backupCount=self.backup_count,
                    encoding='utf-8'
                )
            else:
                handler = logging.FileHandler(file_path, encoding='utf-8')
            
            handler.setLevel(level)
            
            if self.enable_json:
                handler.setFormatter(StructuredFormatter())
            else:
                formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
                )
                handler.setFormatter(formatter)
            
            # Add filter for specific handlers
            if handler_name == "performance":
                handler.addFilter(lambda record: hasattr(record, 'performance_metric'))
            elif handler_name == "audit":
                handler.addFilter(lambda record: record.levelno == LogLevel.AUDIT.value)
            
            self.logger.addHandler(handler)
    
    @contextmanager
    def context(self, **kwargs):
        """Context manager for adding context to logs"""
        old_context = getattr(self._context_storage, 'context', {})
        new_context = {**old_context, **kwargs}
        
        # Generate correlation ID if not provided
        if 'correlation_id' not in new_context:
            new_context['correlation_id'] = str(uuid.uuid4())
        
        self._context_storage.context = new_context
        try:
            yield new_context
        finally:
            self._context_storage.context = old_context
    
    def _get_context(self) -> Dict[str, Any]:
        """Get current logging context"""
        return getattr(self._context_storage, 'context', {})
    
    def _update_metrics(self, level: int, category: Optional[ErrorCategory] = None):
        """Update logging metrics"""
        with self._metrics_lock:
            self.metrics.total_logs += 1
            
            if level >= logging.ERROR:
                self.metrics.error_count += 1
                self.metrics.last_error_time = datetime.now(timezone.utc)
                
                if category:
                    cat_name = category.value
                    self.metrics.errors_by_category[cat_name] = (
                        self.metrics.errors_by_category.get(cat_name, 0) + 1
                    )
            
            if level >= logging.WARNING:
                self.metrics.warning_count += 1
            
            if level >= logging.CRITICAL:
                self.metrics.critical_count += 1
                self.metrics.last_critical_time = datetime.now(timezone.utc)
    
    def _log_with_context(
        self,
        level: int,
        message: str,
        *args,
        category: Optional[ErrorCategory] = None,
        severity: Optional[LogSeverity] = None,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log message with context and metadata"""
        # Get current context
        context = self._get_context()
        
        # Prepare extra data
        log_extra = {
            **context,
            **(extra or {}),
        }
        
        if category:
            log_extra['error_category'] = category.value
        
        if severity:
            log_extra['severity'] = severity.value
        
        # Update metrics
        self._update_metrics(level, category)
        
        # Log the message
        self.logger.log(level, message, *args, extra=log_extra, **kwargs)
    
    # Convenience methods for different log levels
    def trace(self, message: str, *args, **kwargs):
        """Log trace message"""
        self._log_with_context(LogLevel.TRACE.value, message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        self._log_with_context(logging.DEBUG, message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message"""
        self._log_with_context(logging.INFO, message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        self._log_with_context(logging.WARNING, message, *args, **kwargs)
    
    def error(
        self,
        message: str,
        *args,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: LogSeverity = LogSeverity.MEDIUM,
        **kwargs
    ):
        """Log error message with categorization"""
        self._log_with_context(
            logging.ERROR, message, *args,
            category=category, severity=severity, **kwargs
        )
    
    def critical(
        self,
        message: str,
        *args,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: LogSeverity = LogSeverity.CRITICAL,
        **kwargs
    ):
        """Log critical message"""
        self._log_with_context(
            logging.CRITICAL, message, *args,
            category=category, severity=severity, **kwargs
        )
    
    def audit(self, message: str, *args, **kwargs):
        """Log audit message"""
        self._log_with_context(LogLevel.AUDIT.value, message, *args, **kwargs)
    
    def performance(
        self,
        operation: str,
        duration: float,
        **metrics
    ):
        """Log performance metrics"""
        extra = {
            'performance_metric': True,
            'operation': operation,
            'duration_ms': duration * 1000,
            **metrics
        }
        
        self._log_with_context(
            LogLevel.TRACE.value,
            f"Performance: {operation} took {duration:.3f}s",
            extra=extra
        )
    
    def exception(
        self,
        message: str,
        exc_info: bool = True,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: LogSeverity = LogSeverity.HIGH,
        **kwargs
    ):
        """Log exception with full traceback"""
        self._log_with_context(
            logging.ERROR, message,
            exc_info=exc_info, category=category, severity=severity, **kwargs
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current logging metrics"""
        with self._metrics_lock:
            return asdict(self.metrics)
    
    def reset_metrics(self):
        """Reset logging metrics"""
        with self._metrics_lock:
            self.metrics = LogMetrics()


# Global logger instances
_loggers: Dict[str, EnhancedLogger] = {}
_default_logger: Optional[EnhancedLogger] = None


def get_logger(
    name: str = "trading_bot",
    **kwargs
) -> EnhancedLogger:
    """
    Get or create an enhanced logger instance
    
    Args:
        name: Logger name
        **kwargs: Additional arguments for logger configuration
    
    Returns:
        EnhancedLogger instance
        
    Raises:
        ValueError: If log level cannot be read from config.yml
    """
    global _loggers, _default_logger
    
    if name not in _loggers:
        # Get log level from config if not provided
        if 'log_level' not in kwargs:
            try:
                from utils.load_config import load_config
                config = load_config()
                logging_config = config.get('logging', {})
                log_level = logging_config.get('level')
                if log_level is None:
                    raise ValueError("logging.level not found in config.yml")
                kwargs['log_level'] = log_level
            except Exception as e:
                raise ValueError(f"Cannot read log level from config.yml: {e}")
        
        _loggers[name] = EnhancedLogger(name, **kwargs)
        
        if _default_logger is None:
            _default_logger = _loggers[name]
    
    return _loggers[name]


def get_default_logger() -> EnhancedLogger:
    """Get the default logger instance"""
    global _default_logger
    
    if _default_logger is None:
        _default_logger = get_logger()
    
    return _default_logger


# Decorators for automatic logging
def log_performance(logger: Optional[EnhancedLogger] = None):
    """Decorator to automatically log function performance"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            log = logger or get_default_logger()
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                log.performance(f"{func.__name__}", duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                log.performance(f"{func.__name__}_failed", duration, error=str(e))
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            log = logger or get_default_logger()
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log.performance(f"{func.__name__}", duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                log.performance(f"{func.__name__}_failed", duration, error=str(e))
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def log_exceptions(
    logger: Optional[EnhancedLogger] = None,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: LogSeverity = LogSeverity.MEDIUM,
    reraise: bool = True
):
    """Decorator to automatically log exceptions"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            log = logger or get_default_logger()
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                log.exception(
                    f"Exception in {func.__name__}: {e}",
                    category=category,
                    severity=severity
                )
                if reraise:
                    raise
                return None
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            log = logger or get_default_logger()
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log.exception(
                    f"Exception in {func.__name__}: {e}",
                    category=category,
                    severity=severity
                )
                if reraise:
                    raise
                return None
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Backward compatibility functions
def error_logger_func() -> EnhancedLogger:
    """Backward compatibility function for existing code"""
    return get_default_logger()


def logger_func() -> EnhancedLogger:
    """Backward compatibility function for existing code"""
    return get_default_logger() 