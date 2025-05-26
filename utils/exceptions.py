"""
Custom Exception Classes and Recovery Mechanisms

This module provides:
- Hierarchical custom exception classes for different error types
- Recovery mechanisms and retry strategies
- Error context and debugging information
- Exception handling decorators and utilities
- Circuit breaker patterns for fault tolerance
"""

import asyncio
import time
import traceback
import functools
from typing import Dict, Any, Optional, Union, List, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import logging
import random


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryAction(Enum):
    """Recovery actions for different error types"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAK = "circuit_break"
    ESCALATE = "escalate"
    IGNORE = "ignore"
    RESTART = "restart"


@dataclass
class ErrorContext:
    """Context information for errors"""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    symbol: Optional[str] = None
    strategy: Optional[str] = None
    user_data: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    
    def __post_init__(self):
        if self.stack_trace is None:
            self.stack_trace = traceback.format_stack()


@dataclass
class RetryConfig:
    """Configuration for retry mechanisms"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    backoff_strategy: str = "exponential"  # exponential, linear, fixed


# Base Exception Classes
class TradingBotException(Exception):
    """Base exception for all trading bot errors"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        recovery_action: RecoveryAction = RecoveryAction.RETRY,
        context: Optional[ErrorContext] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.severity = severity
        self.recovery_action = recovery_action
        self.context = context or ErrorContext()
        self.original_exception = original_exception
        self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "severity": self.severity.value,
            "recovery_action": self.recovery_action.value,
            "timestamp": self.timestamp.isoformat(),
            "context": {
                "correlation_id": self.context.correlation_id,
                "component": self.context.component,
                "operation": self.context.operation,
                "symbol": self.context.symbol,
                "strategy": self.context.strategy,
                "user_data": self.context.user_data,
            },
            "original_exception": str(self.original_exception) if self.original_exception else None,
        }


# Network and API Exceptions
class NetworkException(TradingBotException):
    """Base class for network-related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            recovery_action=RecoveryAction.RETRY,
            **kwargs
        )


class APIException(TradingBotException):
    """Base class for API-related errors"""
    
    def __init__(
        self,
        message: str,
        api_endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            recovery_action=RecoveryAction.RETRY,
            **kwargs
        )
        self.api_endpoint = api_endpoint
        self.status_code = status_code


class ConnectionTimeoutException(NetworkException):
    """Connection timeout error"""
    
    def __init__(self, message: str = "Connection timeout", **kwargs):
        super().__init__(message, **kwargs)


class RateLimitException(APIException):
    """API rate limit exceeded"""
    
    def __init__(
        self,
        message: str = "API rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message,
            recovery_action=RecoveryAction.RETRY,
            **kwargs
        )
        self.retry_after = retry_after


class AuthenticationException(APIException):
    """Authentication failed"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.CRITICAL,
            recovery_action=RecoveryAction.ESCALATE,
            **kwargs
        )


class InsufficientPermissionsException(APIException):
    """Insufficient API permissions"""
    
    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            recovery_action=RecoveryAction.ESCALATE,
            **kwargs
        )


# Trading-specific Exceptions
class TradingException(TradingBotException):
    """Base class for trading-related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            recovery_action=RecoveryAction.FALLBACK,
            **kwargs
        )


class InsufficientBalanceException(TradingException):
    """Insufficient balance for trading"""
    
    def __init__(
        self,
        message: str = "Insufficient balance",
        required_amount: Optional[float] = None,
        available_amount: Optional[float] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.required_amount = required_amount
        self.available_amount = available_amount


class InvalidOrderException(TradingException):
    """Invalid order parameters"""
    
    def __init__(self, message: str = "Invalid order parameters", **kwargs):
        super().__init__(
            message,
            recovery_action=RecoveryAction.IGNORE,
            **kwargs
        )


class OrderExecutionException(TradingException):
    """Order execution failed"""
    
    def __init__(
        self,
        message: str = "Order execution failed",
        order_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.order_id = order_id


class PositionManagementException(TradingException):
    """Position management error"""
    
    def __init__(self, message: str = "Position management error", **kwargs):
        super().__init__(message, **kwargs)


class RiskManagementException(TradingException):
    """Risk management violation"""
    
    def __init__(
        self,
        message: str = "Risk management violation",
        risk_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            recovery_action=RecoveryAction.CIRCUIT_BREAK,
            **kwargs
        )
        self.risk_type = risk_type


# Data and Validation Exceptions
class DataException(TradingBotException):
    """Base class for data-related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            recovery_action=RecoveryAction.RETRY,
            **kwargs
        )


class DataValidationException(DataException):
    """Data validation failed"""
    
    def __init__(
        self,
        message: str = "Data validation failed",
        field_name: Optional[str] = None,
        expected_type: Optional[str] = None,
        actual_value: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.field_name = field_name
        self.expected_type = expected_type
        self.actual_value = actual_value


class DataCorruptionException(DataException):
    """Data corruption detected"""
    
    def __init__(self, message: str = "Data corruption detected", **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            recovery_action=RecoveryAction.FALLBACK,
            **kwargs
        )


class MissingDataException(DataException):
    """Required data is missing"""
    
    def __init__(
        self,
        message: str = "Required data is missing",
        missing_fields: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.missing_fields = missing_fields or []


# System and Configuration Exceptions
class SystemException(TradingBotException):
    """Base class for system-related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.CRITICAL,
            recovery_action=RecoveryAction.RESTART,
            **kwargs
        )


class ConfigurationException(SystemException):
    """Configuration error"""
    
    def __init__(
        self,
        message: str = "Configuration error",
        config_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            recovery_action=RecoveryAction.ESCALATE,
            **kwargs
        )
        self.config_key = config_key


class DatabaseException(SystemException):
    """Database operation failed"""
    
    def __init__(self, message: str = "Database operation failed", **kwargs):
        super().__init__(message, **kwargs)


class FileSystemException(SystemException):
    """File system operation failed"""
    
    def __init__(self, message: str = "File system operation failed", **kwargs):
        super().__init__(message, **kwargs)


# Strategy and Indicator Exceptions
class StrategyException(TradingBotException):
    """Base class for strategy-related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            recovery_action=RecoveryAction.FALLBACK,
            **kwargs
        )


class IndicatorException(StrategyException):
    """Indicator calculation failed"""
    
    def __init__(
        self,
        message: str = "Indicator calculation failed",
        indicator_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.indicator_name = indicator_name


class SignalGenerationException(StrategyException):
    """Signal generation failed"""
    
    def __init__(self, message: str = "Signal generation failed", **kwargs):
        super().__init__(message, **kwargs)


# Recovery Mechanisms
class RecoveryManager:
    """Manages error recovery strategies"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.recovery_stats = {}
    
    async def handle_exception(
        self,
        exception: TradingBotException,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Handle exception with appropriate recovery strategy
        
        Args:
            exception: The exception to handle
            operation: The operation to retry/recover
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation
        
        Returns:
            Result of the recovery operation
        """
        recovery_action = exception.recovery_action
        
        if self.logger:
            self.logger.error(
                f"Handling exception: {exception.message}",
                extra=exception.to_dict()
            )
        
        if recovery_action == RecoveryAction.RETRY:
            return await self._retry_operation(exception, operation, *args, **kwargs)
        elif recovery_action == RecoveryAction.FALLBACK:
            return await self._fallback_operation(exception, operation, *args, **kwargs)
        elif recovery_action == RecoveryAction.CIRCUIT_BREAK:
            return await self._circuit_break_operation(exception, operation, *args, **kwargs)
        elif recovery_action == RecoveryAction.ESCALATE:
            return await self._escalate_operation(exception, operation, *args, **kwargs)
        elif recovery_action == RecoveryAction.IGNORE:
            return await self._ignore_operation(exception, operation, *args, **kwargs)
        elif recovery_action == RecoveryAction.RESTART:
            return await self._restart_operation(exception, operation, *args, **kwargs)
        else:
            raise exception
    
    async def _retry_operation(
        self,
        exception: TradingBotException,
        operation: Callable,
        *args,
        retry_config: Optional[RetryConfig] = None,
        **kwargs
    ) -> Any:
        """Retry operation with exponential backoff"""
        config = retry_config or RetryConfig()
        
        for attempt in range(config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(operation):
                    return await operation(*args, **kwargs)
                else:
                    return operation(*args, **kwargs)
            except Exception as e:
                if attempt == config.max_attempts - 1:
                    raise e
                
                # Calculate delay
                if config.backoff_strategy == "exponential":
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                elif config.backoff_strategy == "linear":
                    delay = min(config.base_delay * (attempt + 1), config.max_delay)
                else:  # fixed
                    delay = config.base_delay
                
                # Add jitter
                if config.jitter:
                    delay *= (0.5 + random.random() * 0.5)
                
                if self.logger:
                    self.logger.warning(
                        f"Retry attempt {attempt + 1}/{config.max_attempts} "
                        f"after {delay:.2f}s delay"
                    )
                
                await asyncio.sleep(delay)
        
        raise exception
    
    async def _fallback_operation(
        self,
        exception: TradingBotException,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute fallback operation"""
        if self.logger:
            self.logger.warning(f"Executing fallback for: {exception.message}")
        
        # Return safe default value or None
        return None
    
    async def _circuit_break_operation(
        self,
        exception: TradingBotException,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Circuit breaker pattern"""
        if self.logger:
            self.logger.critical(f"Circuit breaker activated: {exception.message}")
        
        # Implement circuit breaker logic
        raise exception
    
    async def _escalate_operation(
        self,
        exception: TradingBotException,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Escalate to higher level handling"""
        if self.logger:
            self.logger.critical(f"Escalating exception: {exception.message}")
        
        # Escalate to system administrator or higher level handler
        raise exception
    
    async def _ignore_operation(
        self,
        exception: TradingBotException,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Ignore the exception and continue"""
        if self.logger:
            self.logger.warning(f"Ignoring exception: {exception.message}")
        
        return None
    
    async def _restart_operation(
        self,
        exception: TradingBotException,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Restart the component or system"""
        if self.logger:
            self.logger.critical(f"Restart required: {exception.message}")
        
        # Implement restart logic
        raise exception


# Exception Handling Decorators
def handle_exceptions(
    recovery_manager: Optional[RecoveryManager] = None,
    retry_config: Optional[RetryConfig] = None,
    fallback_value: Any = None,
    logger=None
):
    """Decorator for automatic exception handling"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            manager = recovery_manager or RecoveryManager(logger)
            
            try:
                return await func(*args, **kwargs)
            except TradingBotException as e:
                try:
                    return await manager.handle_exception(e, func, *args, **kwargs)
                except Exception:
                    return fallback_value
            except Exception as e:
                # Convert to TradingBotException
                trading_exception = TradingBotException(
                    f"Unexpected error in {func.__name__}: {str(e)}",
                    original_exception=e,
                    severity=ErrorSeverity.HIGH
                )
                
                try:
                    return await manager.handle_exception(trading_exception, func, *args, **kwargs)
                except Exception:
                    return fallback_value
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            manager = recovery_manager or RecoveryManager(logger)
            
            try:
                return func(*args, **kwargs)
            except TradingBotException as e:
                try:
                    # For sync functions, we can't use async recovery
                    if logger:
                        logger.error(f"Exception in {func.__name__}: {e.message}")
                    return fallback_value
                except Exception:
                    return fallback_value
            except Exception as e:
                if logger:
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                return fallback_value
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def validate_data(
    validation_rules: Dict[str, Callable],
    raise_on_error: bool = True
):
    """Decorator for data validation"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Validate arguments
            for field_name, validator in validation_rules.items():
                if field_name in kwargs:
                    value = kwargs[field_name]
                    if not validator(value):
                        error = DataValidationException(
                            f"Validation failed for field '{field_name}'",
                            field_name=field_name,
                            actual_value=value
                        )
                        if raise_on_error:
                            raise error
                        return None
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Utility Functions
def create_error_context(
    correlation_id: Optional[str] = None,
    component: Optional[str] = None,
    operation: Optional[str] = None,
    **kwargs
) -> ErrorContext:
    """Create error context with provided information"""
    return ErrorContext(
        correlation_id=correlation_id,
        component=component,
        operation=operation,
        user_data=kwargs
    )


def wrap_exception(
    original_exception: Exception,
    message: Optional[str] = None,
    exception_class: Type[TradingBotException] = TradingBotException,
    **kwargs
) -> TradingBotException:
    """Wrap a standard exception in a TradingBotException"""
    error_message = message or f"Wrapped exception: {str(original_exception)}"
    
    return exception_class(
        error_message,
        original_exception=original_exception,
        **kwargs
    )


# Exception Registry for mapping standard exceptions
EXCEPTION_MAPPING = {
    ConnectionError: NetworkException,
    TimeoutError: ConnectionTimeoutException,
    ValueError: DataValidationException,
    KeyError: MissingDataException,
    FileNotFoundError: FileSystemException,
    PermissionError: InsufficientPermissionsException,
}


def map_standard_exception(exception: Exception) -> TradingBotException:
    """Map standard Python exceptions to custom trading bot exceptions"""
    exception_type = type(exception)
    
    if exception_type in EXCEPTION_MAPPING:
        mapped_class = EXCEPTION_MAPPING[exception_type]
        return mapped_class(
            str(exception),
            original_exception=exception
        )
    
    return TradingBotException(
        f"Unmapped exception: {str(exception)}",
        original_exception=exception
    ) 