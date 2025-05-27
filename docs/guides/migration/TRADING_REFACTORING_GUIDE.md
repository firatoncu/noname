# Trading Logic Refactoring Guide

## Overview

This document describes the comprehensive refactoring of the trading logic in the `src/` directory. The refactoring eliminates code duplication, implements design patterns, and creates a more maintainable and extensible trading system.

## Problems Addressed

### Before Refactoring
- **Code Duplication**: Similar logic repeated across multiple files for buy/sell conditions, position management, and order execution
- **Tight Coupling**: Strategy logic hardcoded in condition checking functions
- **No Abstraction**: No base classes or interfaces for common trading operations
- **Mixed Responsibilities**: Files handling multiple concerns (data fetching, condition checking, order execution)
- **Difficult Testing**: Tightly coupled code made unit testing challenging
- **Hard to Extend**: Adding new strategies required modifying existing code

### After Refactoring
- **Clean Architecture**: Separation of concerns with dedicated managers
- **Strategy Pattern**: Easy switching between different trading strategies
- **Reusable Components**: Common operations abstracted into utility functions
- **Type Safety**: Strong typing with dataclasses and enums
- **Testable Code**: Loosely coupled components enable easy testing
- **Extensible Design**: New strategies can be added without modifying existing code

## New Architecture

### Core Components

#### 1. Base Strategy (`src/core/base_strategy.py`)
```python
class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    @abstractmethod
    def check_buy_conditions(self, market_data: MarketData, symbol: str, logger) -> TradingSignal:
        pass
    
    @abstractmethod
    def check_sell_conditions(self, market_data: MarketData, symbol: str, logger) -> TradingSignal:
        pass
```

**Key Features:**
- Abstract base class defining strategy interface
- Standardized signal format with `TradingSignal` dataclass
- Built-in parameter management and state tracking
- Market data validation

#### 2. Position Manager (`src/core/position_manager.py`)
```python
class PositionManager:
    """Centralized position management"""
    
    async def open_position(self, symbol: str, side: PositionSide, quantity: float, client, logger) -> bool
    async def close_position(self, symbol: str, client, logger, reason: str = "Manual") -> bool
    async def monitor_position(self, symbol: str, market_data: MarketData, client, logger, price_precisions: Dict[str, int]) -> bool
```

**Key Features:**
- Centralized position tracking and management
- Configurable TP/SL parameters
- Automatic risk management with histogram confirmation
- Position monitoring with real-time PnL calculation

#### 3. Order Manager (`src/core/order_manager.py`)
```python
class OrderManager:
    """Centralized order management"""
    
    async def create_market_order(self, symbol: str, side: PositionSide, quantity: float, client, logger, signal: Optional[TradingSignal] = None) -> OrderResult
    async def create_limit_order(self, symbol: str, side: PositionSide, quantity: float, price: float, client, logger, signal: Optional[TradingSignal] = None) -> OrderResult
```

**Key Features:**
- Order validation and execution with retry logic
- Order history tracking and statistics
- Configurable retry parameters and validation rules
- Success rate monitoring

#### 4. Trading Engine (`src/core/trading_engine.py`)
```python
class TradingEngine:
    """Main trading orchestrator"""
    
    async def start_trading(self, client, logger)
    def switch_strategy(self, new_strategy: BaseStrategy, logger)
    async def close_all_positions(self, client, logger, reason: str = "Manual")
```

**Key Features:**
- Orchestrates all trading operations
- Implements strategy pattern for easy strategy switching
- Concurrent signal processing and position monitoring
- Comprehensive status reporting

### Strategy Implementations

#### 1. MACD Fibonacci Strategy (`src/strategies/macd_fibonacci_strategy.py`)
- Combines MACD crossover signals with Fibonacci retracement levels
- Multi-step signal confirmation process
- Configurable parameters for all indicators

#### 2. RSI Bollinger Strategy (`src/strategies/rsi_bollinger_strategy.py`)
- RSI momentum with Bollinger Band squeeze detection
- Price breakout confirmation
- Adaptive thresholds based on market conditions

### Utility Functions (`src/utils/condition_utils.py`)

Common operations extracted into reusable functions:
- `calculate_fibonacci_levels()`: Fibonacci retracement calculation
- `check_macd_crossover()`: MACD crossover detection
- `check_rsi_condition()`: RSI condition checking
- `check_bollinger_squeeze()`: Bollinger Band squeeze detection
- `check_trend_strength()`: ADX-based trend analysis
- `calculate_signal_strength()`: Weighted signal strength calculation

## Usage Examples

### Basic Usage
```python
from src.refactored_trading_main import RefactoredTradingSystem

# Create trading system
trading_system = RefactoredTradingSystem()

# Start trading with MACD Fibonacci strategy
symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
await trading_system.start_trading(symbols, client, "MACD_Fibonacci")
```

### Strategy Switching
```python
# Switch to RSI Bollinger strategy
trading_system.switch_strategy("RSI_Bollinger")

# Get current status
status = trading_system.get_trading_status()
print(f"Current strategy: {status['strategy']}")
```

### Custom Strategy Implementation
```python
from src.core.base_strategy import BaseStrategy, TradingSignal, SignalType

class MyCustomStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("My Custom Strategy", {"param1": 10})
    
    def check_buy_conditions(self, market_data, symbol, logger):
        # Your custom buy logic here
        conditions = {"custom_condition": True}
        return TradingSignal(
            signal_type=SignalType.BUY if all(conditions.values()) else SignalType.HOLD,
            strength=1.0 if all(conditions.values()) else 0.0,
            conditions=conditions
        )
    
    def check_sell_conditions(self, market_data, symbol, logger):
        # Your custom sell logic here
        pass
    
    def get_strategy_info(self):
        return {"name": self.name, "description": "My custom strategy"}

# Add to system
trading_system.add_custom_strategy("MyCustom", MyCustomStrategy)
```

## Configuration

### Trading Configuration
```python
trading_config = TradingConfig(
    max_open_positions=3,
    leverage=10,
    lookback_period=500,
    position_value_percentage=0.25,
    enable_database_logging=True,
    enable_notifications=True
)
```

### Position Configuration
```python
position_config = PositionConfig(
    tp_percentage_long=0.005,   # 0.5% TP
    sl_percentage_long=0.015,   # 1.5% SL
    hard_sl_percentage_long=0.025,  # 2.5% hard SL
    # ... similar for short positions
)
```

### Order Configuration
```python
order_config = OrderConfig(
    max_retries=3,
    retry_delay=1.0,
    validate_funding_fee=True,
    min_order_value=10.0
)
```

## Benefits of Refactoring

### 1. Code Reusability
- Common operations extracted into utility functions
- Base classes provide reusable functionality
- Strategies can share common components

### 2. Maintainability
- Clear separation of concerns
- Single responsibility principle
- Easy to locate and fix bugs

### 3. Extensibility
- New strategies can be added without modifying existing code
- Plugin-like architecture for strategies
- Configurable parameters for all components

### 4. Testability
- Loosely coupled components
- Dependency injection for easy mocking
- Clear interfaces for unit testing

### 5. Type Safety
- Strong typing with dataclasses and enums
- Clear method signatures
- IDE support for autocompletion and error detection

### 6. Performance
- Concurrent processing of signals and position monitoring
- Efficient data structures
- Optimized indicator calculations

## Migration Guide

### From Old Architecture
1. **Replace direct function calls** with strategy pattern:
   ```python
   # Old
   buyAll = await check_buy_conditions(500, symbol, client, logger)
   
   # New
   buy_signal = strategy.check_buy_conditions(market_data, symbol, logger)
   ```

2. **Use centralized managers** instead of scattered logic:
   ```python
   # Old
   await client.futures_create_order(...)
   
   # New
   order_result = await order_manager.create_market_order(...)
   ```

3. **Leverage configuration objects** instead of hardcoded values:
   ```python
   # Old
   tp_price = entry_price * 1.003
   
   # New
   tp_price = entry_price * (1 + position_config.tp_percentage_long)
   ```

### Backward Compatibility
- Original files remain unchanged for gradual migration
- Global state functions still work for compatibility
- Existing indicator functions can be used in new strategies

## Testing

### Unit Tests
```python
import pytest
from src.core.base_strategy import MarketData
from src.strategies.macd_fibonacci_strategy import MACDFibonacciStrategy

def test_macd_fibonacci_buy_conditions():
    strategy = MACDFibonacciStrategy()
    market_data = create_test_market_data()
    
    signal = strategy.check_buy_conditions(market_data, "BTCUSDT", mock_logger)
    
    assert signal.signal_type in [SignalType.BUY, SignalType.HOLD]
    assert 0.0 <= signal.strength <= 1.0
```

### Integration Tests
```python
async def test_trading_engine_integration():
    strategy = MACDFibonacciStrategy()
    engine = TradingEngine(strategy)
    
    await engine.initialize(["BTCUSDT"], mock_client, mock_logger)
    # Test trading operations
```

## Performance Considerations

### Memory Usage
- Efficient pandas operations
- Limited data retention in indicators
- Garbage collection of old signals

### CPU Usage
- Concurrent processing where possible
- Optimized indicator calculations
- Minimal redundant computations

### Network Usage
- Batched API calls where possible
- Efficient data fetching
- Connection pooling

## Future Enhancements

### Planned Features
1. **Machine Learning Integration**: ML-based signal generation
2. **Advanced Risk Management**: Portfolio-level risk controls
3. **Backtesting Framework**: Integrated backtesting with the new architecture
4. **Web Interface**: Real-time monitoring and control
5. **Database Integration**: Enhanced data persistence and analytics

### Extension Points
- Custom indicator framework
- Plugin system for external strategies
- Event-driven architecture for real-time processing
- Multi-exchange support

## Conclusion

The refactored trading system provides a solid foundation for scalable, maintainable trading operations. The clean architecture, design patterns, and comprehensive utilities make it easy to develop, test, and deploy new trading strategies while maintaining high code quality and performance.

For questions or contributions, please refer to the individual module documentation and examples provided in the codebase. 