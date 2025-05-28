"""
Type definitions for the n0name trading bot.

This module provides type aliases and custom types used throughout the application
for better type safety and code clarity.
"""

from typing import NewType, Union, Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime
from uuid import UUID

# Basic trading types
Symbol = NewType("Symbol", str)  # e.g., "BTCUSDT"
Price = NewType("Price", Decimal)
Quantity = NewType("Quantity", Decimal)
Volume = NewType("Volume", Decimal)
Percentage = NewType("Percentage", float)  # 0.0 to 1.0

# Identifiers
OrderId = NewType("OrderId", str)
PositionId = NewType("PositionId", str)
TradeId = NewType("TradeId", str)
StrategyId = NewType("StrategyId", str)
UserId = NewType("UserId", str)
SessionId = NewType("SessionId", str)

# Time-related types
Timestamp = NewType("Timestamp", int)  # Unix timestamp in milliseconds
TimeInterval = NewType("TimeInterval", str)  # e.g., "1m", "5m", "1h", "1d"

# Signal and analysis types
SignalStrength = NewType("SignalStrength", float)  # 0.0 to 1.0
Confidence = NewType("Confidence", float)  # 0.0 to 1.0
RiskScore = NewType("RiskScore", float)  # 0.0 to 1.0

# Configuration types
ConfigValue = Union[str, int, float, bool, List[Any], Dict[str, Any]]
ConfigDict = Dict[str, ConfigValue]

# Market data types
OHLCV = Dict[str, Union[Price, Volume, Timestamp]]
TickerData = Dict[str, Union[Price, Volume, Percentage, Timestamp]]
OrderBookLevel = Dict[str, Union[Price, Quantity]]
OrderBookData = Dict[str, List[OrderBookLevel]]

# Financial types
Balance = NewType("Balance", Decimal)
PnL = NewType("PnL", Decimal)  # Profit and Loss
Leverage = NewType("Leverage", int)
MarginRatio = NewType("MarginRatio", float)

# Network and API types
APIKey = NewType("APIKey", str)
APISecret = NewType("APISecret", str)
WebSocketURL = NewType("WebSocketURL", str)
RestAPIURL = NewType("RestAPIURL", str)

# Error and logging types
ErrorCode = NewType("ErrorCode", str)
LogLevel = NewType("LogLevel", str)
TraceId = NewType("TraceId", str)

# Event types
EventType = NewType("EventType", str)
EventData = Dict[str, Any]

# Performance types
Latency = NewType("Latency", float)  # in milliseconds
Throughput = NewType("Throughput", float)  # operations per second
MemoryUsage = NewType("MemoryUsage", int)  # in bytes
CPUUsage = NewType("CPUUsage", float)  # 0.0 to 1.0

# Database types
DatabaseURL = NewType("DatabaseURL", str)
TableName = NewType("TableName", str)
QueryResult = List[Dict[str, Any]]

# Security types
EncryptedData = NewType("EncryptedData", bytes)
HashValue = NewType("HashValue", str)
Salt = NewType("Salt", bytes)

# Notification types
NotificationChannel = NewType("NotificationChannel", str)
NotificationMessage = NewType("NotificationMessage", str)

# Strategy types
StrategyName = NewType("StrategyName", str)
StrategyParameters = Dict[str, ConfigValue]
IndicatorValue = NewType("IndicatorValue", float)

# Risk management types
RiskLimit = NewType("RiskLimit", Decimal)
DrawdownLimit = NewType("DrawdownLimit", Percentage)
MaxPositions = NewType("MaxPositions", int)

# Backtesting types
BacktestId = NewType("BacktestId", str)
BacktestPeriod = NewType("BacktestPeriod", str)
BacktestResult = Dict[str, Union[float, int, str, List[Any]]]

# WebSocket types
WebSocketMessage = Dict[str, Any]
SubscriptionId = NewType("SubscriptionId", str)

# File system types
FilePath = NewType("FilePath", str)
DirectoryPath = NewType("DirectoryPath", str)
FileName = NewType("FileName", str)

# Monitoring types
MetricName = NewType("MetricName", str)
MetricValue = Union[int, float, str]
AlertThreshold = NewType("AlertThreshold", float)

# Cache types
CacheKey = NewType("CacheKey", str)
CacheValue = Any
TTL = NewType("TTL", int)  # Time to live in seconds

# Utility type aliases
JSONData = Dict[str, Any]
Headers = Dict[str, str]
QueryParams = Dict[str, Union[str, int, float]]
URLPath = NewType("URLPath", str)

# Optional types for common nullable values
OptionalPrice = Optional[Price]
OptionalQuantity = Optional[Quantity]
OptionalTimestamp = Optional[Timestamp]
OptionalSymbol = Optional[Symbol]

# Union types for flexibility
NumericValue = Union[int, float, Decimal]
StringOrBytes = Union[str, bytes]
PriceOrFloat = Union[Price, float]
QuantityOrFloat = Union[Quantity, float]

# Type guards and validators
def is_valid_symbol(value: str) -> bool:
    """Check if a string is a valid trading symbol."""
    return len(value) >= 3 and value.isupper() and value.isalpha()

def is_valid_price(value: Union[str, int, float, Decimal]) -> bool:
    """Check if a value can be converted to a valid price."""
    try:
        price = Decimal(str(value))
        return price > 0
    except (ValueError, TypeError):
        return False

def is_valid_quantity(value: Union[str, int, float, Decimal]) -> bool:
    """Check if a value can be converted to a valid quantity."""
    try:
        quantity = Decimal(str(value))
        return quantity > 0
    except (ValueError, TypeError):
        return False

def is_valid_percentage(value: Union[int, float]) -> bool:
    """Check if a value is a valid percentage (0.0 to 1.0)."""
    return isinstance(value, (int, float)) and 0.0 <= value <= 1.0

def is_valid_timestamp(value: Union[int, str]) -> bool:
    """Check if a value is a valid timestamp."""
    try:
        timestamp = int(value)
        # Check if timestamp is reasonable (between 2020 and 2050)
        return 1577836800000 <= timestamp <= 2524608000000  # milliseconds
    except (ValueError, TypeError):
        return False 