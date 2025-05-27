"""
Exception hierarchy for the n0name trading bot.

This module defines a comprehensive exception hierarchy that provides
clear error categorization and context for better error handling.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
import traceback


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    CONFIGURATION = "configuration"
    NETWORK = "network"
    API = "api"
    TRADING = "trading"
    STRATEGY = "strategy"
    DATABASE = "database"
    SECURITY = "security"
    SYSTEM = "system"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    DATA = "data"
    CALCULATION = "calculation"


class ErrorContext:
    """Context information for errors."""
    
    def __init__(
        self,
        component: Optional[str] = None,
        operation: Optional[str] = None,
        symbol: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize error context.
        
        Args:
            component: Component where error occurred
            operation: Operation being performed
            symbol: Trading symbol (if applicable)
            user_id: User ID (if applicable)
            session_id: Session ID (if applicable)
            request_id: Request ID for tracing
            additional_data: Additional context data
        """
        self.component = component
        self.operation = operation
        self.symbol = symbol
        self.user_id = user_id
        self.session_id = session_id
        self.request_id = request_id
        self.additional_data = additional_data or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "component": self.component,
            "operation": self.operation,
            "symbol": self.symbol,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "additional_data": self.additional_data,
        }


class TradingBotException(Exception):
    """
    Base exception for all trading bot errors.
    
    This is the root exception class that all other custom exceptions inherit from.
    It provides common functionality for error handling, logging, and context management.
    """
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        original_exception: Optional[Exception] = None,
        error_code: Optional[str] = None,
        recoverable: bool = True,
        retry_after: Optional[int] = None,
    ):
        """
        Initialize trading bot exception.
        
        Args:
            message: Error message
            category: Error category
            severity: Error severity
            context: Error context
            original_exception: Original exception that caused this error
            error_code: Unique error code
            recoverable: Whether the error is recoverable
            retry_after: Seconds to wait before retry (if applicable)
        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or ErrorContext()
        self.original_exception = original_exception
        self.error_code = error_code
        self.recoverable = recoverable
        self.retry_after = retry_after
        self.timestamp = datetime.utcnow()
        self.traceback_str = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "error_code": self.error_code,
            "recoverable": self.recoverable,
            "retry_after": self.retry_after,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context.to_dict(),
            "original_exception": str(self.original_exception) if self.original_exception else None,
            "traceback": self.traceback_str,
        }
    
    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [f"{self.__class__.__name__}: {self.message}"]
        
        if self.error_code:
            parts.append(f"Code: {self.error_code}")
        
        if self.context.component:
            parts.append(f"Component: {self.context.component}")
        
        if self.context.operation:
            parts.append(f"Operation: {self.context.operation}")
        
        return " | ".join(parts)


class ConfigurationException(TradingBotException):
    """Exception for configuration-related errors."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_file: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize configuration exception.
        
        Args:
            message: Error message
            config_key: Configuration key that caused the error
            config_file: Configuration file path
            **kwargs: Additional arguments for base class
        """
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        self.config_key = config_key
        self.config_file = config_file
        
        # Add to context
        if config_key:
            self.context.additional_data["config_key"] = config_key
        if config_file:
            self.context.additional_data["config_file"] = config_file


class NetworkException(TradingBotException):
    """Exception for network-related errors."""
    
    def __init__(
        self,
        message: str,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize network exception.
        
        Args:
            message: Error message
            endpoint: API endpoint that failed
            status_code: HTTP status code
            response_body: Response body content
            **kwargs: Additional arguments for base class
        """
        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        self.endpoint = endpoint
        self.status_code = status_code
        self.response_body = response_body
        
        # Add to context
        if endpoint:
            self.context.additional_data["endpoint"] = endpoint
        if status_code:
            self.context.additional_data["status_code"] = status_code
        if response_body:
            self.context.additional_data["response_body"] = response_body


class APIException(TradingBotException):
    """Exception for API-related errors."""
    
    def __init__(
        self,
        message: str,
        api_name: Optional[str] = None,
        api_method: Optional[str] = None,
        api_response: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize API exception.
        
        Args:
            message: Error message
            api_name: Name of the API (e.g., 'binance')
            api_method: API method that failed
            api_response: API response data
            **kwargs: Additional arguments for base class
        """
        super().__init__(
            message,
            category=ErrorCategory.API,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        self.api_name = api_name
        self.api_method = api_method
        self.api_response = api_response
        
        # Add to context
        if api_name:
            self.context.additional_data["api_name"] = api_name
        if api_method:
            self.context.additional_data["api_method"] = api_method
        if api_response:
            self.context.additional_data["api_response"] = api_response


class TradingException(TradingBotException):
    """Exception for trading-related errors."""
    
    def __init__(
        self,
        message: str,
        symbol: Optional[str] = None,
        order_id: Optional[str] = None,
        position_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize trading exception.
        
        Args:
            message: Error message
            symbol: Trading symbol
            order_id: Order ID (if applicable)
            position_id: Position ID (if applicable)
            **kwargs: Additional arguments for base class
        """
        super().__init__(
            message,
            category=ErrorCategory.TRADING,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        self.symbol = symbol
        self.order_id = order_id
        self.position_id = position_id
        
        # Add to context
        if symbol:
            self.context.symbol = symbol
        if order_id:
            self.context.additional_data["order_id"] = order_id
        if position_id:
            self.context.additional_data["position_id"] = position_id


class StrategyException(TradingBotException):
    """Exception for strategy-related errors."""
    
    def __init__(
        self,
        message: str,
        strategy_name: Optional[str] = None,
        strategy_type: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize strategy exception.
        
        Args:
            message: Error message
            strategy_name: Name of the strategy
            strategy_type: Type of the strategy
            **kwargs: Additional arguments for base class
        """
        super().__init__(
            message,
            category=ErrorCategory.STRATEGY,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        self.strategy_name = strategy_name
        self.strategy_type = strategy_type
        
        # Add to context
        if strategy_name:
            self.context.additional_data["strategy_name"] = strategy_name
        if strategy_type:
            self.context.additional_data["strategy_type"] = strategy_type


class DatabaseException(TradingBotException):
    """Exception for database-related errors."""
    
    def __init__(
        self,
        message: str,
        table_name: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize database exception.
        
        Args:
            message: Error message
            table_name: Database table name
            query: SQL query that failed
            **kwargs: Additional arguments for base class
        """
        super().__init__(
            message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        self.table_name = table_name
        self.query = query
        
        # Add to context
        if table_name:
            self.context.additional_data["table_name"] = table_name
        if query:
            self.context.additional_data["query"] = query


class SecurityException(TradingBotException):
    """Exception for security-related errors."""
    
    def __init__(
        self,
        message: str,
        security_event: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize security exception.
        
        Args:
            message: Error message
            security_event: Type of security event
            **kwargs: Additional arguments for base class
        """
        super().__init__(
            message,
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.CRITICAL,
            recoverable=False,
            **kwargs
        )
        self.security_event = security_event
        
        # Add to context
        if security_event:
            self.context.additional_data["security_event"] = security_event


class ValidationException(TradingBotException):
    """Exception for validation errors."""
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        validation_rule: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize validation exception.
        
        Args:
            message: Error message
            field_name: Name of the field that failed validation
            field_value: Value that failed validation
            validation_rule: Validation rule that was violated
            **kwargs: Additional arguments for base class
        """
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        self.field_name = field_name
        self.field_value = field_value
        self.validation_rule = validation_rule
        
        # Add to context
        if field_name:
            self.context.additional_data["field_name"] = field_name
        if field_value is not None:
            self.context.additional_data["field_value"] = str(field_value)
        if validation_rule:
            self.context.additional_data["validation_rule"] = validation_rule


class RateLimitException(TradingBotException):
    """Exception for rate limiting errors."""
    
    def __init__(
        self,
        message: str,
        limit_type: Optional[str] = None,
        reset_time: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize rate limit exception.
        
        Args:
            message: Error message
            limit_type: Type of rate limit (e.g., 'requests_per_minute')
            reset_time: Unix timestamp when limit resets
            **kwargs: Additional arguments for base class
        """
        super().__init__(
            message,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        self.limit_type = limit_type
        self.reset_time = reset_time
        
        # Add to context
        if limit_type:
            self.context.additional_data["limit_type"] = limit_type
        if reset_time:
            self.context.additional_data["reset_time"] = reset_time


class SystemException(TradingBotException):
    """Exception for system-level errors."""
    
    def __init__(
        self,
        message: str,
        system_component: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize system exception.
        
        Args:
            message: Error message
            system_component: System component that failed
            **kwargs: Additional arguments for base class
        """
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            **kwargs
        )
        self.system_component = system_component
        
        # Add to context
        if system_component:
            self.context.additional_data["system_component"] = system_component


# Utility functions for exception handling

def create_error_context(
    component: Optional[str] = None,
    operation: Optional[str] = None,
    **kwargs
) -> ErrorContext:
    """
    Create an error context with the given parameters.
    
    Args:
        component: Component name
        operation: Operation name
        **kwargs: Additional context data
        
    Returns:
        ErrorContext instance
    """
    return ErrorContext(
        component=component,
        operation=operation,
        **kwargs
    )


def map_standard_exception(
    exception: Exception,
    context: Optional[ErrorContext] = None
) -> TradingBotException:
    """
    Map a standard Python exception to a custom trading bot exception.
    
    Args:
        exception: Standard exception to map
        context: Error context
        
    Returns:
        Mapped trading bot exception
    """
    message = str(exception)
    
    # Map common exception types
    if isinstance(exception, (ConnectionError, TimeoutError)):
        return NetworkException(
            message,
            context=context,
            original_exception=exception
        )
    elif isinstance(exception, ValueError):
        return ValidationException(
            message,
            context=context,
            original_exception=exception
        )
    elif isinstance(exception, KeyError):
        return ConfigurationException(
            message,
            context=context,
            original_exception=exception
        )
    elif isinstance(exception, PermissionError):
        return SecurityException(
            message,
            context=context,
            original_exception=exception
        )
    else:
        return SystemException(
            message,
            context=context,
            original_exception=exception
        )


def handle_exception(
    exception: Exception,
    logger=None,
    context: Optional[ErrorContext] = None,
    reraise: bool = True
) -> Optional[TradingBotException]:
    """
    Handle an exception with proper logging and conversion.
    
    Args:
        exception: Exception to handle
        logger: Logger instance
        context: Error context
        reraise: Whether to reraise the exception
        
    Returns:
        Converted exception (if not reraised)
        
    Raises:
        TradingBotException: If reraise is True
    """
    # Convert to custom exception if needed
    if isinstance(exception, TradingBotException):
        custom_exception = exception
    else:
        custom_exception = map_standard_exception(exception, context)
    
    # Log the exception
    if logger:
        logger.error(
            f"Exception handled: {custom_exception}",
            extra=custom_exception.to_dict()
        )
    
    if reraise:
        raise custom_exception
    
    return custom_exception


# Exception handler decorator
def exception_handler(
    exception_types: Union[Exception, tuple] = Exception,
    logger=None,
    reraise: bool = True,
    default_return=None
):
    """
    Decorator for handling exceptions in functions.
    
    Args:
        exception_types: Exception types to catch
        logger: Logger instance
        reraise: Whether to reraise exceptions
        default_return: Default return value if exception is caught
        
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                context = create_error_context(
                    component=func.__module__,
                    operation=func.__name__
                )
                
                if reraise:
                    handle_exception(e, logger, context, reraise=True)
                else:
                    handle_exception(e, logger, context, reraise=False)
                    return default_return
        
        return wrapper
    return decorator 