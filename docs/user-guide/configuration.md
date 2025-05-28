# Configuration Guide

The n0name trading bot uses a simplified configuration system that reads only from `config.yml`. There are no default values - all required configuration must be present in the config file.

## 📁 Configuration File

The bot requires a `config.yml` file in the project root directory. If this file is missing or contains invalid values, the bot will not start.

### Basic Structure

```yaml
# Application environment
environment: production
debug: false
version: "2.0.0"

# User configuration
username: "User"
strategy_name: "Bollinger Bands & RSI"
capital_tbu: 999.0
db_status: "n"

# API Keys (Required)
api_keys:
  api_key: "your_binance_api_key"
  api_secret: "your_binance_api_secret"

# Telegram (Required)
telegram:
  token: "your_telegram_bot_token"
  chat_id: "your_telegram_chat_id"

# Trading symbols (Required)
symbols:
  leverage: 5
  max_open_positions: 1
  symbols:
    - "BTCUSDT"
    - "ETHUSDT"
    - "XRPUSDT"

# Logging configuration (Required)
logging:
  level: "ERROR"
  console_output: true
  structured_logging: true

# Trading configuration (Required)
trading:
  capital: 999.0
  leverage: 5
  margin:
    mode: "full"
    fixed_amount: 100
    percentage: 50
    ask_user_selection: false
    default_to_full_margin: true
    user_response_timeout: 30
  symbols:
    - "BTCUSDT"
    - "ETHUSDT"
    - "XRPUSDT"
  paper_trading: false
  auto_start: false
  strategy:
    name: "Bollinger Bands & RSI"
    type: "bollinger_rsi"
    enabled: true
    timeframe: "5m"
    lookback_period: 500
  risk:
    max_position_size: 0.1
    max_daily_loss: 0.05
    max_drawdown: 0.2
    risk_per_trade: 0.02
    max_open_positions: 1
    stop_loss_percentage: 0.02
    take_profit_ratio: 2

# Exchange configuration (Required)
exchange:
  type: "binance"
  testnet: false
  rate_limit: 1200
  timeout: 30
  retry_attempts: 3
  recovery_action: "restart"

# Notifications (Required)
notifications:
  enabled: true
```

## ⚠️ Important Notes

1. **No Default Values**: The bot does not provide any default configuration values. All required fields must be present in `config.yml`.

2. **Required Sections**: The following sections are mandatory:
   - `api_keys`
   - `telegram`
   - `symbols`
   - `logging`
   - `trading`
   - `exchange`
   - `notifications`

3. **Error Handling**: If any required field is missing, the bot will display a clear error message and refuse to start.

4. **No Environment Variables**: The simplified system does not support environment variable overrides.

5. **No Command Line Arguments**: Configuration cannot be overridden via command line arguments.

## 🔧 Configuration Management

### Loading Configuration

```python
from utils.load_config import load_config

# Load configuration (raises error if file missing or invalid)
config = load_config()
```

### Validation

The configuration system validates:
- File existence and readability
- YAML syntax
- Required field presence
- Data type correctness
- Value constraints (e.g., leverage limits)

### Error Messages

Common error scenarios:

```
FileNotFoundError: Configuration file not found: /path/to/config.yml
ValueError: Configuration file is empty
ValueError: Missing required configuration keys: api_keys, symbols
ValueError: Invalid YAML in config file: ...
```

## 🚀 Getting Started

1. Copy the example configuration above to `config.yml`
2. Replace placeholder values with your actual credentials
3. Ensure all required sections are present
4. Run the bot - it will validate the configuration on startup

## 🔒 Security

- Store sensitive values (API keys, tokens) securely
- Use appropriate file permissions for `config.yml`
- Never commit real credentials to version control
- Consider using encrypted storage for production deployments 