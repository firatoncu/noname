"""
Interface definitions and protocols for the n0name trading bot.

This module defines the contracts that various components must implement,
enabling better type safety, dependency injection, and testing.
"""

from .trading_protocols import (
    TradingStrategyProtocol,
    PositionManagerProtocol,
    OrderManagerProtocol,
    MarketDataProviderProtocol,
    RiskManagerProtocol,
)

from .service_protocols import (
    ExchangeServiceProtocol,
    NotificationServiceProtocol,
    DatabaseServiceProtocol,
    MonitoringServiceProtocol,
    LoggingServiceProtocol,
)

from .data_protocols import (
    ConfigProviderProtocol,
    CacheProviderProtocol,
    EventBusProtocol,
    MetricsCollectorProtocol,
)

__all__ = [
    # Trading protocols
    "TradingStrategyProtocol",
    "PositionManagerProtocol",
    "OrderManagerProtocol",
    "MarketDataProviderProtocol",
    "RiskManagerProtocol",
    # Service protocols
    "ExchangeServiceProtocol",
    "NotificationServiceProtocol",
    "DatabaseServiceProtocol",
    "MonitoringServiceProtocol",
    "LoggingServiceProtocol",
    # Data protocols
    "ConfigProviderProtocol",
    "CacheProviderProtocol",
    "EventBusProtocol",
    "MetricsCollectorProtocol",
] 