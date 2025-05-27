"""
Dependency Injection framework for the n0name trading bot.

This module provides a comprehensive dependency injection system using the
dependency-injector library, enabling loose coupling and better testability.
"""

from .container import Container
from .providers import (
    ConfigProvider,
    DatabaseProvider,
    ExchangeProvider,
    StrategyProvider,
    ServiceProvider,
    MonitoringProvider,
)

__all__ = [
    "Container",
    "ConfigProvider",
    "DatabaseProvider", 
    "ExchangeProvider",
    "StrategyProvider",
    "ServiceProvider",
    "MonitoringProvider",
] 