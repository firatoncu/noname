# API Documentation - n0name Trading Bot

## Overview

This document provides comprehensive API documentation for the n0name trading bot, including all public interfaces, classes, methods, and their usage examples.

## Table of Contents

1. [Core APIs](#core-apis)
2. [Trading Engine API](#trading-engine-api)
3. [Strategy API](#strategy-api)
4. [Position Management API](#position-management-api)
5. [Order Management API](#order-management-api)
6. [Configuration API](#configuration-api)
7. [Logging API](#logging-api)
8. [Exception Handling API](#exception-handling-api)
9. [Type System](#type-system)
10. [REST API Endpoints](#rest-api-endpoints)
11. [WebSocket API](#websocket-api)
12. [Examples](#examples)

## Core APIs

### Main Application Entry Point

#### `main() -> None`

Main entry point for the n0name trading bot application.

**Description:**
Orchestrates the complete lifecycle of the trading bot including configuration loading, API client initialization, service startup, and main trading loop execution.

**Returns:**
- `None`

**Raises:**
- `SystemExit`: On critical errors that prevent bot operation

**Example:**
```python
import asyncio
from n0name import main

# Start the trading bot
asyncio.run(main())
```

#### `initialize_binance_client(api_key: str, api_secret: str, logger: PerformanceLogger, testnet: bool = False) -> AsyncClient`

Initialize Binance client with enhanced error handling and validation.

**Parameters:**
- `api_key` (str): Binance API key for authentication
- `api_secret` (str): Binance API secret for authentication
- `logger` (PerformanceLogger): Enhanced logger instance
- `testnet` (bool, optional): Whether to use Binance testnet. Defaults to False.

**Returns:**
- `AsyncClient`: Initialized and validated Binance client

**Raises:**
- `NetworkException`: If network connectivity issues occur
- `APIException`: If API authentication or permission issues occur
- `ConfigurationException`: If API credentials are invalid

**Example:**
```python
client = await initialize_binance_client(
    api_key="your_api_key",
    api_secret="your_api_secret",
    logger=logger,
    testnet=False
)
```

## Trading Engine API

### TradingEngine Class

The central orchestrator that coordinates all trading activities.

#### `__init__(strategy: BaseStrategy, trading_config: TradingConfig = None, position_config: PositionConfig = None, order_config: OrderConfig = None)`

Initialize the trading engine.

**Parameters:**
- `strategy` (BaseStrategy): Trading strategy to use
- `trading_config` (TradingConfig, optional): Trading engine configuration
- `position_config` (PositionConfig, optional): Position management configuration
- `order_config` (OrderConfig, optional): Order management configuration

**Example:**
```python
from src.core.trading_engine import TradingEngine, TradingConfig
from src.strategies.bollinger_rsi import BollingerRSIStrategy

strategy = BollingerRSIStrategy()
config = TradingConfig(
    max_open_positions=5,
    leverage=10,
    position_value_percentage=0.2
)
engine = TradingEngine(strategy, config)
```

#### `async initialize(symbols: List[str], client: AsyncClient, logger: PerformanceLogger) -> None`

Initialize the trading engine with symbols and market data.

**Parameters:**
- `symbols` (List[str]): List of trading symbols
- `client` (AsyncClient): Binance client
- `logger` (PerformanceLogger): Logger instance

**Example:**
```python
await engine.initialize(
    symbols=["BTCUSDT", "ETHUSDT"],
    client=binance_client,
    logger=logger
)
```

#### `async start_trading(client: AsyncClient, logger: PerformanceLogger) -> None`

Start the main trading loop.

**Parameters:**
- `client` (AsyncClient): Binance client
- `logger` (PerformanceLogger): Logger instance

#### `switch_strategy(new_strategy: BaseStrategy, logger: PerformanceLogger) -> None`

Switch to a new trading strategy.

**Parameters:**
- `new_strategy` (BaseStrategy): New strategy to use
- `logger` (PerformanceLogger): Logger instance

#### `get_trading_status() -> Dict[str, Any]`

Get current trading status and metrics.

**Returns:**
- `Dict[str, Any]`: Trading status information

### TradingConfig Class

Configuration for the trading engine.

**Attributes:**
- `max_open_positions` (int): Maximum number of concurrent positions. Default: 5
- `leverage` (int): Trading leverage. Default: 10
- `lookback_period` (int): Historical data lookback period. Default: 500
- `position_value_percentage` (float): Percentage of capital per position. Default: 0.2
- `enable_database_logging` (bool): Enable database logging. Default: True
- `enable_notifications` (bool): Enable notifications. Default: True

## Strategy API

### BaseStrategy Class

Abstract base class for all trading strategies.

#### `async generate_signals(market_data: MarketData) -> Dict[str, Any]`

Generate trading signals based on market data.

**Parameters:**
- `market_data` (MarketData): Market data for analysis

**Returns:**
- `Dict[str, Any]`: Trading signals with confidence levels

**Example:**
```python
class CustomStrategy(BaseStrategy):
    async def generate_signals(self, market_data: MarketData) -> Dict[str, Any]:
        # Implement your strategy logic here
        return {
            "buy_signal": True,
            "sell_signal": False,
            "confidence": 0.8,
            "stop_loss": 0.02,
            "take_profit": 0.05
        }
```

#### `validate_market_data(market_data: MarketData) -> bool`

Validate if market data is sufficient for analysis.

**Parameters:**
- `market_data` (MarketData): Market data to validate

**Returns:**
- `bool`: True if data is valid, False otherwise

### MarketData Class

Container for market data used in strategy analysis.

**Attributes:**
- `df` (pandas.DataFrame): OHLCV data
- `close_price` (float): Current close price
- `symbol` (str): Trading symbol
- `timestamp` (int): Data timestamp

### SignalType Enum

Enumeration of signal types.

**Values:**
- `BUY`: Buy signal
- `SELL`: Sell signal
- `HOLD`: Hold signal
- `CLOSE`: Close position signal

## Position Management API

### PositionManager Class

Manages the lifecycle of trading positions.

#### `open_position(symbol: str, side: PositionSide, quantity: float, price: float, strategy_info: Dict[str, Any]) -> Position`

Open a new trading position.

**Parameters:**
- `symbol` (str): Trading symbol
- `side` (PositionSide): Position side (LONG/SHORT)
- `quantity` (float): Position quantity
- `price` (float): Entry price
- `strategy_info` (Dict[str, Any]): Strategy-specific information

**Returns:**
- `Position`: Created position object

#### `close_position(position_id: str, price: float, reason: str = "Manual") -> Position`

Close an existing position.

**Parameters:**
- `position_id` (str): Position identifier
- `price` (float): Exit price
- `reason` (str, optional): Reason for closing

**Returns:**
- `Position`: Updated position object

#### `get_position(symbol: str) -> Optional[Position]`

Get position for a specific symbol.

**Parameters:**
- `symbol` (str): Trading symbol

**Returns:**
- `Optional[Position]`: Position object or None if not found

#### `get_all_positions() -> Dict[str, Position]`

Get all open positions.

**Returns:**
- `Dict[str, Position]`: Dictionary of all positions

### Position Class

Represents a trading position.

**Attributes:**
- `id` (str): Unique position identifier
- `symbol` (str): Trading symbol
- `side` (PositionSide): Position side
- `quantity` (float): Position quantity
- `entry_price` (float): Entry price
- `current_price` (float): Current market price
- `pnl` (float): Unrealized profit/loss
- `state` (PositionState): Position state
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

**Methods:**

#### `calculate_pnl(current_price: float) -> float`

Calculate current profit/loss.

#### `update_price(new_price: float) -> None`

Update current market price.

## Order Management API

### OrderManager Class

Handles order execution and management.

#### `async create_market_order(symbol: str, side: OrderSide, quantity: float, client: AsyncClient) -> Order`

Create and execute a market order.

**Parameters:**
- `symbol` (str): Trading symbol
- `side` (OrderSide): Order side (BUY/SELL)
- `quantity` (float): Order quantity
- `client` (AsyncClient): Binance client

**Returns:**
- `Order`: Created order object

#### `async create_limit_order(symbol: str, side: OrderSide, quantity: float, price: float, client: AsyncClient) -> Order`

Create a limit order.

**Parameters:**
- `symbol` (str): Trading symbol
- `side` (OrderSide): Order side (BUY/SELL)
- `quantity` (float): Order quantity
- `price` (float): Limit price
- `client` (AsyncClient): Binance client

**Returns:**
- `Order`: Created order object

#### `async cancel_order(order_id: str, symbol: str, client: AsyncClient) -> bool`

Cancel an existing order.

**Parameters:**
- `order_id` (str): Order identifier
- `symbol` (str): Trading symbol
- `client` (AsyncClient): Binance client

**Returns:**
- `bool`: True if successfully cancelled

### Order Class

Represents a trading order.

**Attributes:**
- `id` (str): Unique order identifier
- `symbol` (str): Trading symbol
- `side` (OrderSide): Order side
- `type` (OrderType): Order type
- `quantity` (float): Order quantity
- `price` (float): Order price
- `status` (OrderStatus): Order status
- `created_at` (datetime): Creation timestamp
- `filled_quantity` (float): Filled quantity
- `average_price` (float): Average fill price

## Configuration API

### Configuration Loading

#### `load_config(config_path: str = "config.yml") -> Dict[str, Any]`

Load configuration from file.

**Parameters:**
- `config_path` (str, optional): Path to configuration file

**Returns:**
- `Dict[str, Any]`: Configuration dictionary

#### `validate_config(config: Dict[str, Any]) -> bool`

Validate configuration structure and values.

**Parameters:**
- `config` (Dict[str, Any]): Configuration to validate

**Returns:**
- `bool`: True if valid

### Configuration Structure

```yaml
# Example configuration
symbols:
  - "BTCUSDT"
  - "ETHUSDT"
  - "ADAUSDT"

capital_tbu: 1000.0
strategy_name: "Bollinger Bands & RSI"
max_open_positions: 5
leverage: 10

api_keys:
  api_key: "encrypted_api_key"
  api_secret: "encrypted_api_secret"

database:
  enabled: true
  host: "localhost"
  port: 8086
  database: "trading_data"

logging:
  level: "INFO"
  structured: true
  file_logging: true

risk_management:
  max_drawdown: 0.1
  position_size_percentage: 0.02
  stop_loss_percentage: 0.02
  take_profit_percentage: 0.05
```

## Logging API

### Enhanced Logging

#### `get_logger(name: str, context: Dict[str, Any] = None) -> PerformanceLogger`

Get an enhanced logger instance.

**Parameters:**
- `name` (str): Logger name
- `context` (Dict[str, Any], optional): Additional context

**Returns:**
- `PerformanceLogger`: Enhanced logger instance

#### `@log_performance()`

Decorator for logging function performance.

**Example:**
```python
@log_performance()
async def expensive_operation():
    # Your code here
    pass
```

### PerformanceLogger Class

Enhanced logger with structured logging capabilities.

#### `info(message: str, extra: Dict[str, Any] = None) -> None`

Log info message.

#### `error(message: str, category: ErrorCategory = None, severity: LogSeverity = None, extra: Dict[str, Any] = None) -> None`

Log error message with categorization.

#### `audit(message: str, extra: Dict[str, Any] = None) -> None`

Log audit message.

## Exception Handling API

### Exception Hierarchy

```
TradingBotException (Base)
├── ConfigurationException
├── NetworkException  
├── APIException
├── TradingException
├── StrategyException
├── DatabaseException
├── SecurityException
├── ValidationException
├── RateLimitException
└── SystemException
```

### TradingBotException Class

Base exception for all trading bot errors.

**Attributes:**
- `message` (str): Error message
- `category` (ErrorCategory): Error category
- `severity` (ErrorSeverity): Error severity
- `context` (ErrorContext): Error context
- `recoverable` (bool): Whether error is recoverable
- `retry_after` (int): Seconds to wait before retry

#### `to_dict() -> Dict[str, Any]`

Convert exception to dictionary for logging/serialization.

### Error Handling Decorators

#### `@handle_exceptions(fallback_value=None, reraise=True)`

Decorator for handling exceptions in functions.

**Example:**
```python
@handle_exceptions(fallback_value=None)
async def risky_operation():
    # Code that might raise exceptions
    pass
```

## Type System

### Custom Types

The bot uses a comprehensive type system for better type safety:

```python
from src.n0name.types import (
    Symbol, Price, Quantity, Volume,
    OrderId, PositionId, TradeId,
    SignalStrength, Confidence, RiskScore,
    Balance, PnL, Leverage
)

# Usage examples
symbol: Symbol = Symbol("BTCUSDT")
price: Price = Price(Decimal("45000.00"))
quantity: Quantity = Quantity(Decimal("0.001"))
```

### Type Validators

#### `is_valid_symbol(value: str) -> bool`

Check if a string is a valid trading symbol.

#### `is_valid_price(value: Union[str, int, float, Decimal]) -> bool`

Check if a value can be converted to a valid price.

#### `is_valid_quantity(value: Union[str, int, float, Decimal]) -> bool`

Check if a value can be converted to a valid quantity.

## REST API Endpoints

The web interface provides REST API endpoints for external integration:

### Trading Control

#### `GET /api/status`

Get current trading status.

**Response:**
```json
{
  "status": "running",
  "uptime": 3600,
  "positions_count": 3,
  "total_pnl": 150.25,
  "strategy": "Bollinger Bands & RSI"
}
```

#### `POST /api/trading/start`

Start trading operations.

**Request:**
```json
{
  "strategy": "Bollinger Bands & RSI",
  "symbols": ["BTCUSDT", "ETHUSDT"]
}
```

#### `POST /api/trading/stop`

Stop trading operations.

**Response:**
```json
{
  "message": "Trading stopped successfully",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Position Management

#### `GET /api/positions`

Get all open positions.

**Response:**
```json
{
  "positions": [
    {
      "id": "pos_123",
      "symbol": "BTCUSDT",
      "side": "LONG",
      "quantity": 0.001,
      "entry_price": 45000.0,
      "current_price": 45500.0,
      "pnl": 0.5,
      "created_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

#### `POST /api/positions/{position_id}/close`

Close a specific position.

**Parameters:**
- `position_id` (str): Position identifier

**Response:**
```json
{
  "message": "Position closed successfully",
  "position_id": "pos_123",
  "exit_price": 45500.0,
  "pnl": 0.5
}
```

### Strategy Management

#### `GET /api/strategies`

Get available strategies.

**Response:**
```json
{
  "strategies": [
    {
      "name": "Bollinger Bands & RSI",
      "description": "Combined Bollinger Bands and RSI strategy",
      "parameters": {
        "bb_period": 20,
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30
      }
    }
  ]
}
```

#### `POST /api/strategy/switch`

Switch trading strategy.

**Request:**
```json
{
  "strategy_name": "MACD & Fibonacci",
  "parameters": {
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9
  }
}
```

## WebSocket API

Real-time data streaming via WebSocket connections.

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Message Types

#### Price Updates

```json
{
  "type": "price_update",
  "symbol": "BTCUSDT",
  "price": 45000.0,
  "timestamp": 1640995200000
}
```

#### Position Updates

```json
{
  "type": "position_update",
  "position_id": "pos_123",
  "symbol": "BTCUSDT",
  "pnl": 0.5,
  "timestamp": 1640995200000
}
```

#### Signal Notifications

```json
{
  "type": "signal",
  "symbol": "BTCUSDT",
  "signal_type": "BUY",
  "confidence": 0.8,
  "timestamp": 1640995200000
}
```

## Examples

### Complete Trading Bot Setup

```python
import asyncio
from src.core.trading_engine import TradingEngine, TradingConfig
from src.strategies.bollinger_rsi import BollingerRSIStrategy
from utils.enhanced_logging import get_logger

async def setup_trading_bot():
    # Initialize logger
    logger = get_logger(__name__)
    
    # Create strategy
    strategy = BollingerRSIStrategy(
        bb_period=20,
        rsi_period=14,
        rsi_overbought=70,
        rsi_oversold=30
    )
    
    # Configure trading engine
    config = TradingConfig(
        max_open_positions=5,
        leverage=10,
        position_value_percentage=0.2
    )
    
    # Initialize trading engine
    engine = TradingEngine(strategy, config)
    
    # Initialize with symbols
    symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
    await engine.initialize(symbols, client, logger)
    
    # Start trading
    await engine.start_trading(client, logger)

# Run the bot
asyncio.run(setup_trading_bot())
```

### Custom Strategy Implementation

```python
from src.core.base_strategy import BaseStrategy, MarketData
from typing import Dict, Any
import pandas as pd

class CustomMACDStrategy(BaseStrategy):
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.name = "Custom MACD Strategy"
    
    async def generate_signals(self, market_data: MarketData) -> Dict[str, Any]:
        df = market_data.df
        
        # Calculate MACD
        exp1 = df['close'].ewm(span=self.fast_period).mean()
        exp2 = df['close'].ewm(span=self.slow_period).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=self.signal_period).mean()
        histogram = macd - signal
        
        # Generate signals
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        prev_macd = macd.iloc[-2]
        prev_signal = signal.iloc[-2]
        
        buy_signal = (prev_macd <= prev_signal) and (current_macd > current_signal)
        sell_signal = (prev_macd >= prev_signal) and (current_macd < current_signal)
        
        return {
            "buy_signal": buy_signal,
            "sell_signal": sell_signal,
            "confidence": abs(current_macd - current_signal) / market_data.close_price,
            "stop_loss": 0.02,
            "take_profit": 0.05,
            "indicators": {
                "macd": current_macd,
                "signal": current_signal,
                "histogram": histogram.iloc[-1]
            }
        }
    
    def validate_market_data(self, market_data: MarketData) -> bool:
        return len(market_data.df) >= max(self.fast_period, self.slow_period) + self.signal_period
```

### Error Handling Example

```python
from src.n0name.exceptions import TradingException, ErrorCategory, ErrorSeverity
from utils.enhanced_logging import get_logger

async def safe_trading_operation():
    logger = get_logger(__name__)
    
    try:
        # Risky trading operation
        result = await execute_trade()
        return result
        
    except TradingException as e:
        if e.recoverable:
            logger.warning(
                f"Recoverable trading error: {e.message}",
                category=e.category,
                severity=e.severity
            )
            # Implement retry logic
            await asyncio.sleep(e.retry_after or 30)
            return await safe_trading_operation()
        else:
            logger.error(
                f"Non-recoverable trading error: {e.message}",
                category=e.category,
                severity=e.severity
            )
            raise
            
    except Exception as e:
        logger.error(
            f"Unexpected error: {str(e)}",
            category=ErrorCategory.SYSTEM,
            severity=LogSeverity.HIGH
        )
        raise TradingException(
            "Unexpected error during trading operation",
            original_exception=e,
            recoverable=True,
            retry_after=60
        )
```

---

This API documentation provides comprehensive coverage of all public interfaces in the n0name trading bot. For implementation details and internal APIs, refer to the source code and inline documentation. 