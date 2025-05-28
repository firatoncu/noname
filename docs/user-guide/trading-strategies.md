# Trading Strategies Guide

This guide explains the available trading strategies in the n0name Trading Bot and how to configure and use them effectively.

## 📊 Available Strategies

### 1. MACD Fibonacci Strategy
A combination of MACD (Moving Average Convergence Divergence) and Fibonacci retracement levels for trend-following trades.

**How it works:**
- Uses MACD crossovers to identify trend changes
- Applies Fibonacci retracement levels for entry and exit points
- Includes risk management with stop-loss and take-profit levels

**Best for:**
- Trending markets
- Medium to long-term trades
- Markets with clear directional movement

**Configuration:**
```yaml
strategy:
  name: macd_fibonacci
  parameters:
    macd:
      fast_period: 12
      slow_period: 26
      signal_period: 9
    fibonacci:
      levels: [0.236, 0.382, 0.618, 0.786]
    risk_management:
      stop_loss: 0.02  # 2%
      take_profit: 0.06  # 6%
```

### 2. Bollinger Bands RSI Strategy
Combines Bollinger Bands for volatility analysis with RSI for momentum confirmation.

**How it works:**
- Uses Bollinger Bands to identify overbought/oversold conditions
- RSI confirms momentum and filters false signals
- Trades mean reversion opportunities

**Best for:**
- Range-bound markets
- High volatility periods
- Short to medium-term trades

**Configuration:**
```yaml
strategy:
  name: bollinger_rsi
  parameters:
    bollinger:
      period: 20
      std_dev: 2.0
    rsi:
      period: 14
      overbought: 70
      oversold: 30
    risk_management:
      stop_loss: 0.015  # 1.5%
      take_profit: 0.045  # 4.5%
```

### 3. Custom Strategy Framework
Create your own strategies using the base strategy framework.

**Example Custom Strategy:**
```python
from n0name.strategies.base_strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.name = "my_custom_strategy"
    
    def generate_signals(self, data):
        # Your signal generation logic here
        signals = []
        # ... implementation
        return signals
    
    def calculate_position_size(self, signal, account_balance):
        # Your position sizing logic
        return position_size
```

## ⚙️ Strategy Configuration

### Configuration File Structure
```yaml
# config/strategies/my_strategy.yml
strategy:
  name: "strategy_name"
  enabled: true
  
  # Strategy-specific parameters
  parameters:
    # Technical indicator settings
    indicators:
      sma_short: 10
      sma_long: 50
    
    # Risk management
    risk_management:
      max_position_size: 0.1  # 10% of portfolio
      stop_loss: 0.02         # 2%
      take_profit: 0.06       # 6%
      max_drawdown: 0.15      # 15%
    
    # Entry/Exit conditions
    entry_conditions:
      min_volume: 1000000
      min_price_change: 0.005
    
    exit_conditions:
      profit_target: 0.05
      time_limit: 3600  # 1 hour in seconds

# Trading pairs and timeframes
trading:
  pairs: ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
  timeframe: "1h"
  max_concurrent_trades: 3

# Backtesting settings
backtesting:
  start_date: "2023-01-01"
  end_date: "2023-12-31"
  initial_balance: 10000
```

### Environment-Specific Configurations

#### Development/Paper Trading
```yaml
# config/environments/development.yml
trading:
  mode: paper
  initial_balance: 10000
  
strategy:
  risk_management:
    max_position_size: 0.05  # More conservative
    stop_loss: 0.01
```

#### Production/Live Trading
```yaml
# config/environments/production.yml
trading:
  mode: live
  
strategy:
  risk_management:
    max_position_size: 0.02  # Very conservative
    stop_loss: 0.015
    
monitoring:
  alerts:
    enabled: true
    channels: ["email", "slack"]
```

## 🎯 Strategy Selection

### Choosing the Right Strategy

**Market Conditions:**
- **Trending Markets**: MACD Fibonacci, Trend Following
- **Range-bound Markets**: Bollinger RSI, Mean Reversion
- **High Volatility**: Bollinger RSI with tighter stops
- **Low Volatility**: Breakout strategies

**Risk Tolerance:**
- **Conservative**: Lower position sizes, tighter stops
- **Moderate**: Balanced risk/reward ratios
- **Aggressive**: Higher position sizes, wider stops

**Time Horizon:**
- **Scalping**: 1m-5m timeframes, quick profits
- **Day Trading**: 15m-1h timeframes, intraday moves
- **Swing Trading**: 4h-1d timeframes, multi-day holds

### Strategy Performance Metrics

Monitor these key metrics:
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Average Trade Duration**: Time in market per trade

## 🔧 Implementation

### Running a Strategy

```bash
# Run with specific strategy
python n0name.py --strategy macd_fibonacci

# Run with custom configuration
python n0name.py --config config/strategies/my_strategy.yml

# Run in paper trading mode
python n0name.py --strategy bollinger_rsi --mode paper

# Run with specific pairs
python n0name.py --strategy macd_fibonacci --pairs BTC/USDT,ETH/USDT
```

### Strategy Switching

```bash
# Stop current strategy
python n0name.py --stop

# Start new strategy
python n0name.py --strategy new_strategy_name

# Hot-swap strategies (advanced)
python n0name.py --reload-strategy new_strategy_name
```

### Multiple Strategies

```yaml
# config/multi_strategy.yml
strategies:
  - name: macd_fibonacci
    pairs: ["BTC/USDT", "ETH/USDT"]
    allocation: 0.6  # 60% of capital
    
  - name: bollinger_rsi
    pairs: ["ADA/USDT", "DOT/USDT"]
    allocation: 0.4  # 40% of capital
```

## 📈 Backtesting

### Running Backtests

```bash
# Backtest a strategy
python -m n0name.backtesting --strategy macd_fibonacci --start 2023-01-01 --end 2023-12-31

# Backtest with custom data
python -m n0name.backtesting --strategy bollinger_rsi --data data/historical/BTCUSDT_1h.csv

# Compare multiple strategies
python -m n0name.backtesting --compare macd_fibonacci,bollinger_rsi --period 6m
```

### Backtest Results

```
Strategy: MACD Fibonacci
Period: 2023-01-01 to 2023-12-31
Initial Balance: $10,000

Performance Metrics:
- Total Return: 23.45%
- Win Rate: 67.3%
- Profit Factor: 1.84
- Sharpe Ratio: 1.23
- Max Drawdown: -8.7%
- Total Trades: 156
- Average Trade: 0.15%

Monthly Returns:
Jan: +2.1%  Feb: -1.3%  Mar: +4.2%  Apr: +1.8%
May: +3.1%  Jun: -0.7%  Jul: +2.9%  Aug: +1.4%
Sep: +2.3%  Oct: +3.7%  Nov: +1.9%  Dec: +2.1%
```

## 🛡️ Risk Management

### Position Sizing
```python
# Kelly Criterion
def kelly_position_size(win_rate, avg_win, avg_loss):
    return (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win

# Fixed Percentage
def fixed_percentage_size(balance, risk_percent):
    return balance * risk_percent

# Volatility-based
def volatility_based_size(balance, volatility, target_risk):
    return (balance * target_risk) / volatility
```

### Stop Loss Strategies
- **Fixed Percentage**: Simple percentage-based stops
- **ATR-based**: Based on Average True Range
- **Support/Resistance**: Technical level stops
- **Trailing Stops**: Dynamic stops that follow price

### Risk Limits
```yaml
risk_management:
  # Position limits
  max_position_size: 0.05      # 5% per trade
  max_portfolio_risk: 0.20     # 20% total risk
  max_correlation: 0.7         # Between positions
  
  # Drawdown limits
  max_daily_loss: 0.03         # 3% daily loss limit
  max_drawdown: 0.15           # 15% max drawdown
  
  # Time limits
  max_trade_duration: 86400    # 24 hours
  cooling_off_period: 3600     # 1 hour between trades
```

## 📊 Monitoring and Alerts

### Performance Monitoring
```yaml
monitoring:
  metrics:
    - pnl_realtime
    - win_rate_rolling
    - drawdown_current
    - position_count
    
  alerts:
    drawdown_threshold: 0.10   # Alert at 10% drawdown
    loss_streak: 5             # Alert after 5 consecutive losses
    profit_target: 0.20        # Alert at 20% profit
```

### Alert Channels
```yaml
alerts:
  email:
    enabled: true
    recipients: ["trader@example.com"]
    
  slack:
    enabled: true
    webhook_url: "https://hooks.slack.com/..."
    
  telegram:
    enabled: true
    bot_token: "your_bot_token"
    chat_id: "your_chat_id"
```

## 🔄 Strategy Optimization

### Parameter Optimization
```python
# Grid search example
parameters = {
    'macd_fast': [8, 12, 16],
    'macd_slow': [21, 26, 31],
    'stop_loss': [0.01, 0.02, 0.03]
}

# Run optimization
results = optimize_strategy(
    strategy='macd_fibonacci',
    parameters=parameters,
    data=historical_data,
    metric='sharpe_ratio'
)
```

### Walk-Forward Analysis
```python
# Test strategy robustness
walk_forward_results = walk_forward_analysis(
    strategy='bollinger_rsi',
    data=data,
    train_period=252,  # 1 year
    test_period=63,    # 3 months
    step_size=21       # 1 month
)
```

## 📚 Best Practices

### Strategy Development
1. **Start Simple**: Begin with basic strategies
2. **Backtest Thoroughly**: Test on multiple time periods
3. **Paper Trade First**: Validate in real-time without risk
4. **Monitor Performance**: Track key metrics continuously
5. **Iterate and Improve**: Refine based on results

### Risk Management
1. **Never Risk More Than You Can Afford to Lose**
2. **Diversify Across Strategies and Assets**
3. **Use Proper Position Sizing**
4. **Set Clear Stop Losses**
5. **Monitor Correlation Between Positions**

### Common Pitfalls
- **Overfitting**: Optimizing too much on historical data
- **Curve Fitting**: Creating strategies that only work on past data
- **Ignoring Transaction Costs**: Not accounting for fees and slippage
- **Emotional Trading**: Overriding strategy signals
- **Insufficient Testing**: Not testing in various market conditions

## 🆘 Troubleshooting

### Common Issues

**Strategy Not Executing:**
- Check if strategy is enabled in configuration
- Verify market data connection
- Check for sufficient account balance

**Poor Performance:**
- Review market conditions vs strategy design
- Check for parameter drift
- Verify data quality and completeness

**High Drawdown:**
- Reduce position sizes
- Tighten stop losses
- Check for correlated positions

### Getting Help

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review strategy logs in `logs/strategy.log`
3. Join our community discussions
4. Contact support with specific strategy questions

---

**Next Steps**: Learn about [Configuration](configuration.md) or explore the [API Documentation](../api/endpoints.md). 