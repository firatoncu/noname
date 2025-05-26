# SignalManager Migration Guide

This guide explains how to migrate from the old dictionary-based signal storage system to the new structured SignalManager system.

## Overview

The new SignalManager provides:
- **Structured signal management** with proper data types and validation
- **Signal history tracking** with timestamps and lifecycle events
- **Confidence levels and signal strength** for better decision making
- **Signal expiration and validation rules** for automatic cleanup
- **Backward compatibility** with existing code
- **Thread-safe operations** for concurrent access
- **Persistence support** for signal state across restarts

## Key Components

### 1. SignalManager Class
The main class that manages all signals with features like:
- Signal creation, updating, and retrieval
- History management and statistics
- Validation and lifecycle management
- Persistence and cleanup

### 2. Signal Class
Individual signal data structure with:
- Unique ID and timestamps
- Signal type, value, confidence, and strength
- Strategy name and source indicator
- Conditions met and metadata
- Lifecycle events tracking

### 3. SignalType Enum
Defines all available signal types:
- `BUY` / `SELL` - Main trading signals
- `TREND` - Trend direction signals
- `WAVE` - Wave analysis signals
- `BUY_CONDITION_A/B/C` - Buy condition signals
- `SELL_CONDITION_A/B/C` - Sell condition signals

## Migration Steps

### Step 1: Update Imports

**Old way:**
```python
from utils.globals import (
    set_clean_buy_signal, get_clean_buy_signal,
    set_buyconda, get_buyconda,
    # ... other imports
)
```

**New way (backward compatible):**
```python
from utils.signal_globals import (
    set_clean_buy_signal, get_clean_buy_signal,
    set_buyconda, get_buyconda,
    # ... other imports
)
```

**Or use the new SignalManager directly:**
```python
from utils.signal_manager import SignalManager, SignalType, initialize_signal_manager
```

### Step 2: Initialize SignalManager

Add this to your main application startup:

```python
from utils.signal_manager import initialize_signal_manager

# Initialize with persistence
initialize_signal_manager(persistence_file="signals.json")
```

### Step 3: Gradual Migration

You can migrate gradually by using both systems side by side:

#### Option A: Keep existing code unchanged
Your existing code will continue to work without changes:

```python
# This still works exactly as before
set_clean_buy_signal(2, "BTCUSDT")
value = get_clean_buy_signal("BTCUSDT")
```

#### Option B: Use enhanced features
Start using enhanced signal creation for new code:

```python
from utils.signal_globals import create_enhanced_buy_signal

signal = create_enhanced_buy_signal(
    symbol="BTCUSDT",
    value=True,
    confidence=0.85,
    strength=0.9,
    strategy_name="MACD Crossover",
    source_indicator="macd",
    conditions_met=["crossover", "volume_confirm"],
    expires_in_minutes=60
)
```

#### Option C: Use SignalManager directly
For maximum control and features:

```python
from utils.signal_manager import get_signal_manager, SignalType

signal_manager = get_signal_manager()

signal = signal_manager.create_signal(
    symbol="BTCUSDT",
    signal_type=SignalType.BUY,
    value=True,
    confidence=0.85,
    strategy_name="MACD Crossover",
    source_indicator="macd"
)
```

## Code Examples

### Basic Signal Operations

**Creating signals:**
```python
from utils.signal_manager import get_signal_manager, SignalType

sm = get_signal_manager()

# Create a buy signal
buy_signal = sm.create_signal(
    symbol="BTCUSDT",
    signal_type=SignalType.BUY,
    value=True,
    confidence=0.8,
    strength=0.9
)

# Create a wave signal with metadata
wave_signal = sm.create_signal(
    symbol="BTCUSDT",
    signal_type=SignalType.WAVE,
    value=2,
    confidence=0.7,
    metadata={"wave_stage": 2, "wave_type": "impulse"}
)
```

**Updating signals:**
```python
# Update existing signal
updated_signal = sm.update_signal(
    symbol="BTCUSDT",
    signal_type=SignalType.BUY,
    value=True,
    confidence=0.95,
    conditions_met=["macd_crossover", "volume_confirm"]
)
```

**Retrieving signals:**
```python
# Get active signal
signal = sm.get_active_signal("BTCUSDT", SignalType.BUY)

# Get signal value with default
value = sm.get_signal_value("BTCUSDT", SignalType.BUY, default_value=False)

# Get all active signals for a symbol
all_signals = sm.get_all_active_signals("BTCUSDT")
```

### Signal Validation and Lifecycle

**Signal validation:**
```python
# Check if signal is valid
if signal.is_valid():
    print("Signal is valid")

# Check if signal is expired
if signal.is_expired():
    print("Signal has expired")
```

**Signal lifecycle management:**
```python
# Confirm a signal
sm.confirm_signal("BTCUSDT", SignalType.BUY, "Trade executed")

# Cancel a signal
sm.cancel_signal("BTCUSDT", SignalType.SELL, "Conditions changed")
```

### History and Statistics

**Getting signal history:**
```python
history = sm.get_signal_history("BTCUSDT")
if history:
    print(f"Total signals: {len(history.signals)}")
    
    # Get latest signal of specific type
    latest_buy = history.get_latest_signal(SignalType.BUY)
```

**Signal statistics:**
```python
stats = sm.get_signal_statistics("BTCUSDT")
print(f"Total signals: {stats['total_signals']}")
print(f"Confirmation rate: {stats['confirmation_rate']:.2%}")
print(f"Average confidence: {stats['average_confidence']:.2f}")
```

### Backward Compatibility Functions

**Using enhanced compatibility functions:**
```python
from utils.signal_globals import (
    create_enhanced_buy_signal,
    validate_trading_signals,
    get_signal_statistics,
    get_signal_history_summary
)

# Create enhanced signal
signal = create_enhanced_buy_signal(
    symbol="BTCUSDT",
    value=True,
    confidence=0.9,
    strategy_name="Enhanced MACD",
    expires_in_minutes=30
)

# Validate all trading conditions
validation = validate_trading_signals("BTCUSDT")
if validation["all_valid"]:
    print("All trading conditions are met")

# Get comprehensive statistics
stats = get_signal_statistics("BTCUSDT")
```

## Updating Existing Indicator Code

### Before (Old System):
```python
def first_wave_signal(close_prices, high_prices, low_prices, side, symbol, logger):
    # ... calculation logic ...
    
    if side == 'buy' and condition_met:
        set_clean_buy_signal(1, symbol)
        set_buycondc(False, symbol)
    
    if side == 'buy' and second_condition_met:
        set_clean_buy_signal(2, symbol)
        set_buycondc(True, symbol)
```

### After (Enhanced System):
```python
def first_wave_signal(close_prices, high_prices, low_prices, side, symbol, logger):
    # ... calculation logic ...
    
    if side == 'buy' and condition_met:
        create_wave_signal(
            symbol=symbol,
            value=1,
            confidence=0.7,
            strategy_name="Fibonacci Wave",
            source_indicator="fibonacci_wave",
            wave_stage=1
        )
        set_buycondc(False, symbol)
    
    if side == 'buy' and second_condition_met:
        create_wave_signal(
            symbol=symbol,
            value=2,
            confidence=0.9,
            strategy_name="Fibonacci Wave",
            source_indicator="fibonacci_wave",
            wave_stage=2,
            conditions_met=["fibonacci_retracement", "volume_confirmation"]
        )
        set_buycondc(True, symbol)
```

## Configuration and Persistence

### Enable Persistence
```python
# Initialize with persistence file
initialize_signal_manager(persistence_file="trading_signals.json")

# Signals will be automatically saved and loaded
```

### Custom Validation Rules
```python
# Create signal with custom validation
signal = sm.create_signal(
    symbol="BTCUSDT",
    signal_type=SignalType.BUY,
    value=True,
    confidence=0.8,
    validation_rules={
        "min_confidence": 0.7,
        "max_age_minutes": 30
    }
)
```

### Signal Expiration
```python
# Create signal that expires in 1 hour
signal = sm.create_signal(
    symbol="BTCUSDT",
    signal_type=SignalType.TREND,
    value=True,
    expires_in_minutes=60
)
```

## Best Practices

### 1. Use Appropriate Confidence Levels
```python
# High confidence for strong signals
strong_signal = sm.create_signal(
    symbol="BTCUSDT",
    signal_type=SignalType.BUY,
    value=True,
    confidence=0.9  # 90% confidence
)

# Lower confidence for weak signals
weak_signal = sm.create_signal(
    symbol="BTCUSDT",
    signal_type=SignalType.TREND,
    value=True,
    confidence=0.6  # 60% confidence
)
```

### 2. Include Strategy Context
```python
signal = sm.create_signal(
    symbol="BTCUSDT",
    signal_type=SignalType.BUY,
    value=True,
    strategy_name="MACD Crossover & Fibonacci",
    source_indicator="macd_fibonacci",
    conditions_met=["macd_crossover", "fibonacci_support", "volume_spike"]
)
```

### 3. Use Signal Validation
```python
# Validate signal combinations before trading
validation = validate_trading_signals("BTCUSDT")
if validation["buy_conditions_valid"] and validation["sell_conditions_valid"]:
    # Proceed with trading logic
    pass
```

### 4. Monitor Signal Statistics
```python
# Regular monitoring
stats = get_signal_statistics("BTCUSDT")
if stats["confirmation_rate"] < 0.5:
    logger.warning(f"Low confirmation rate for {symbol}: {stats['confirmation_rate']:.2%}")
```

## Testing

Run the test suite to verify everything works:

```bash
python utils/test_signal_manager.py
```

This will run comprehensive tests and demonstrate all features.

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure to update import statements
2. **Signal Manager Not Initialized**: Call `initialize_signal_manager()` at startup
3. **Persistence Issues**: Check file permissions for the persistence file
4. **Memory Usage**: The system automatically cleans up old signals, but you can adjust history limits

### Debug Information

```python
# Get debug information
from utils.signal_manager import get_signal_manager

sm = get_signal_manager()
all_signals = sm.get_all_active_signals("BTCUSDT")
for signal_type, signal in all_signals.items():
    print(f"{signal_type.value}: {signal.value} (confidence: {signal.confidence})")
    print(f"  Created: {signal.created_at}")
    print(f"  Updated: {signal.updated_at}")
    print(f"  Events: {len(signal.lifecycle_events)}")
```

## Benefits of Migration

1. **Better Signal Quality**: Confidence levels and validation rules
2. **Historical Analysis**: Complete signal history with statistics
3. **Debugging**: Lifecycle events and detailed metadata
4. **Reliability**: Thread-safe operations and automatic cleanup
5. **Flexibility**: Easy to extend with new signal types and features
6. **Monitoring**: Built-in statistics and validation functions

The migration can be done gradually, and existing code will continue to work without changes while you adopt the new features incrementally. 