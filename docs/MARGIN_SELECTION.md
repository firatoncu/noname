# Margin Selection Feature

## Overview

The margin selection feature allows you to control how much margin is used for trading positions. You can choose between using a fixed amount, full margin, or a percentage of available margin. The system also supports interactive user selection at startup.

## Features

- **Fixed Amount**: Use a specific USDT amount for trading
- **Full Margin**: Use all available margin for maximum position sizes
- **Percentage**: Use a percentage of available margin
- **Interactive Selection**: Ask user to choose margin mode at startup
- **Timeout Handling**: Automatic fallback if user doesn't respond
- **Safe Defaults**: Configurable fallback behavior

## Configuration

Add the following configuration to your `config.yml` file under the `trading` section:

```yaml
trading:
  # ... other trading settings ...
  
  # Margin configuration
  margin:
    # Margin mode: "fixed" for specific amount, "full" for all available margin, "percentage" for percentage of available
    mode: "fixed"  # Options: "fixed", "full", "percentage"
    
    # Fixed margin amount (used when mode is "fixed")
    fixed_amount: 100.0
    
    # Percentage of available margin to use (used when mode is "percentage")
    percentage: 50.0  # 50% of available margin
    
    # Ask user for margin selection at startup
    ask_user_selection: true
    
    # Default to full margin if user doesn't respond within timeout
    default_to_full_margin: true
    
    # Timeout for user response in seconds
    user_response_timeout: 30
```

## Configuration Options

### `mode`
- **Type**: String
- **Options**: `"fixed"`, `"full"`, `"percentage"`
- **Default**: `"fixed"`
- **Description**: Default margin mode when user selection is disabled

### `fixed_amount`
- **Type**: Float
- **Default**: `100.0`
- **Description**: Fixed margin amount in USDT when using fixed mode

### `percentage`
- **Type**: Float (1-100)
- **Default**: `50.0`
- **Description**: Percentage of available margin to use when using percentage mode

### `ask_user_selection`
- **Type**: Boolean
- **Default**: `false`
- **Description**: Whether to prompt user for margin selection at startup

### `default_to_full_margin`
- **Type**: Boolean
- **Default**: `true`
- **Description**: Whether to default to full margin if user doesn't respond within timeout

### `user_response_timeout`
- **Type**: Integer
- **Default**: `30`
- **Description**: Timeout in seconds for user response

## Usage Examples

### Example 1: Fixed Amount Mode
```yaml
trading:
  margin:
    mode: "fixed"
    fixed_amount: 200.0
    ask_user_selection: false
```
This will always use 200 USDT for trading, regardless of available balance.

### Example 2: Full Margin Mode
```yaml
trading:
  margin:
    mode: "full"
    ask_user_selection: false
```
This will use all available margin for trading positions.

### Example 3: Percentage Mode
```yaml
trading:
  margin:
    mode: "percentage"
    percentage: 75.0
    ask_user_selection: false
```
This will use 75% of available margin for trading.

### Example 4: Interactive Selection
```yaml
trading:
  margin:
    ask_user_selection: true
    default_to_full_margin: true
    user_response_timeout: 30
```
This will prompt the user to select margin mode at startup.

## Interactive Selection

When `ask_user_selection` is enabled, the bot will display a menu like this:

```
============================================================
🔹 MARGIN SELECTION
============================================================
Available Margin: 1000.00 USDT

Please select your margin mode:
1. Fixed Amount - Use a specific margin amount
2. Full Margin - Use all available margin
3. Percentage - Use a percentage of available margin

You have 30 seconds to respond...
Press Enter after making your selection.

Enter your choice (1-3): 
```

### Option 1: Fixed Amount
- Prompts for specific USDT amount
- Validates amount doesn't exceed available margin
- Falls back to configured fixed_amount if invalid input

### Option 2: Full Margin
- Uses all available margin
- No additional input required

### Option 3: Percentage
- Prompts for percentage (1-100)
- Calculates amount based on available margin
- Falls back to 50% if invalid input

## Position Value Calculation

The margin selection affects how position values are calculated:

```
Position Value = (Selected Margin / Max Positions) × Leverage
```

### Example Calculation
- Selected Margin: 1000 USDT
- Max Positions: 5
- Leverage: 3x

```
Margin per Position = 1000 / 5 = 200 USDT
Position Value = 200 × 3 = 600 USDT per position
```

## Error Handling

The system includes comprehensive error handling:

- **API Errors**: Graceful fallback to safe defaults
- **Invalid Input**: Automatic correction with user feedback
- **Timeout**: Configurable default behavior
- **Network Issues**: Retry logic with exponential backoff

## Testing

Run the test script to verify functionality:

```bash
python test_margin_selection.py
```

This will test various scenarios and configurations without requiring real API credentials.

## Integration

The margin selection feature is automatically integrated into the trading bot. No additional code changes are required beyond configuration.

### Code Integration Points

1. **Position Value Calculation**: `src/position_value.py`
2. **Trading Iteration**: `n0name.py`
3. **Configuration Loading**: `utils/load_config.py`

## Best Practices

### Risk Management
- Start with smaller fixed amounts or percentages
- Monitor performance before using full margin
- Consider market volatility when selecting margin

### Configuration
- Use interactive selection for manual trading
- Use fixed configuration for automated trading
- Set appropriate timeouts for your environment

### Testing
- Test with paper trading first
- Verify calculations with small amounts
- Monitor position sizes and margin usage

## Troubleshooting

### Common Issues

**Issue**: User selection not appearing
- **Solution**: Ensure `ask_user_selection: true` in config

**Issue**: Timeout too short
- **Solution**: Increase `user_response_timeout` value

**Issue**: Position sizes too large/small
- **Solution**: Adjust margin amount or check leverage settings

**Issue**: API errors during margin retrieval
- **Solution**: Check API credentials and network connection

### Debug Mode

Enable debug logging to see detailed margin selection process:

```yaml
logging:
  level: "DEBUG"
```

## Security Considerations

- Margin selection affects position sizes and risk exposure
- Always validate margin amounts against account balance
- Use appropriate risk management settings
- Monitor margin usage in live trading

## Future Enhancements

Planned improvements include:
- Dynamic margin adjustment based on market conditions
- Risk-based margin scaling
- Historical performance-based recommendations
- Integration with portfolio management tools 