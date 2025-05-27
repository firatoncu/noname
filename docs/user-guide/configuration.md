# Modern Configuration Management System

This document describes the new modern configuration management system that replaces the old YAML-based interactive setup with a robust, validated, and feature-rich solution.

## 🚀 Features

- **Pydantic Validation**: Type-safe configuration with automatic validation
- **Multiple Configuration Sources**: File, environment variables, and command line arguments
- **Hot-Reloading**: Automatic configuration reload when files change
- **Better Error Handling**: Clear, detailed validation error messages
- **Backward Compatibility**: Existing code continues to work
- **Environment Variable Support**: Override any configuration via environment variables
- **Command Line Arguments**: Override configuration from command line
- **Secure Secret Handling**: Proper handling of sensitive data like API keys

## 📁 File Structure

```
utils/
├── config_models.py      # Pydantic models for validation
├── config_manager.py     # Main ConfigManager class
├── load_config.py        # Backward compatibility layer
└── config_example.py     # Usage examples
```

## 🔧 Basic Usage

### Simple Configuration Loading

```python
from utils.load_config import get_config

# Load and validate configuration
config = get_config()

# Access configuration values with type safety
print(f"Username: {config.username}")
print(f"Symbols: {config.symbols.symbols}")
print(f"Leverage: {config.symbols.leverage}")
```

### Advanced Configuration Manager

```python
from utils.config_manager import ConfigManager

# Create a configuration manager with custom settings
config_manager = ConfigManager(
    config_file="config.yml",
    env_prefix="NONAME_",
    enable_hot_reload=True,
    auto_create=True
)

# Get configuration
config = config_manager.get_config()

# Update configuration
config_manager.update_config(
    username="NewUser",
    **{"symbols.leverage": 5}
)

# Save configuration
config_manager.save_config()
```

## 🌍 Environment Variables

You can override any configuration value using environment variables with the `NONAME_` prefix:

```bash
# Application settings
export NONAME_USERNAME="YourUsername"
export NONAME_STRATEGY_NAME="Custom Strategy"

# API configuration
export NONAME_API_KEY="your_api_key"
export NONAME_API_SECRET="your_api_secret"

# Telegram configuration
export NONAME_TELEGRAM_TOKEN="your_bot_token"
export NONAME_TELEGRAM_CHAT_ID="your_chat_id"

# Trading configuration
export NONAME_CAPITAL_TBU="1000.0"
export NONAME_LEVERAGE="5"
export NONAME_MAX_POSITIONS="3"
export NONAME_SYMBOLS="BTCUSDT,ETHUSDT,XRPUSDT"

# Database configuration
export NONAME_DB_STATUS="y"
```

### Using .env Files

Create a `.env` file in your project root:

```env
NONAME_USERNAME=YourUsername
NONAME_API_KEY=your_api_key_here
NONAME_API_SECRET=your_api_secret_here
NONAME_TELEGRAM_TOKEN=your_telegram_bot_token
NONAME_TELEGRAM_CHAT_ID=your_chat_id
NONAME_LEVERAGE=5
NONAME_SYMBOLS=BTCUSDT,ETHUSDT,ADAUSDT
```

## 💻 Command Line Arguments

Override configuration from the command line:

```bash
python your_script.py \
  --config-username "CLIUser" \
  --config-leverage 10 \
  --config-symbols "BTCUSDT,ETHUSDT" \
  --config-capital 2000.0
```

Available command line arguments:
- `--config-username`
- `--config-api-key`
- `--config-api-secret`
- `--config-telegram-token`
- `--config-telegram-chat-id`
- `--config-capital`
- `--config-leverage`
- `--config-max-positions`
- `--config-symbols`

## 🔄 Configuration Priority

Configuration values are loaded in the following order (later sources override earlier ones):

1. **Default values** (defined in `ConfigDefaults`)
2. **Configuration file** (`config.yml`)
3. **Environment variables** (with `NONAME_` prefix)
4. **Command line arguments** (with `--config-` prefix)

## ⚡ Hot-Reloading

Enable hot-reloading to automatically reload configuration when the file changes:

```python
from utils.config_manager import ConfigManager

config_manager = ConfigManager(enable_hot_reload=True)

# Add a callback to be notified of changes
def on_config_change(new_config):
    print(f"Configuration updated! New username: {new_config.username}")

config_manager.add_reload_callback(on_config_change)
```

## ✅ Validation

The new system provides comprehensive validation:

### Automatic Type Validation

```python
# These will raise ValidationError with clear messages:
config_manager.update_config(leverage=200)  # Error: leverage must be <= 125
config_manager.update_config(symbols=["INVALID"])  # Error: symbols must end with 'USDT'
config_manager.update_config(capital_tbu=-100)  # Error: capital must be positive
```

### Custom Validation Rules

- **Symbols**: Must end with 'USDT'
- **Leverage**: Must be between 1 and 125
- **Max Positions**: Must be between 1 and 50
- **Capital**: Must be positive or -999 for full balance
- **API Keys**: Must not be empty
- **Chat ID**: Must be a valid integer

## 🔒 Security Features

### Secure Secret Handling

API secrets are handled using Pydantic's `SecretStr` type:

```python
config = get_config()

# This is safe - doesn't expose the secret in logs
print(f"API Key: {config.api_keys.api_key}")

# Get the actual secret value when needed
secret = config.api_keys.api_secret.get_secret_value()
```

### Environment Variable Security

Store sensitive data in environment variables or `.env` files instead of configuration files:

```bash
export NONAME_API_SECRET="your_secret_here"
```

## 🔄 Backward Compatibility

Existing code using the old `load_config()` function continues to work:

```python
from utils.load_config import load_config

# This still works but shows a deprecation warning
config = load_config()
```

### Migration Guide

**Old way:**
```python
from utils.load_config import load_config
config = load_config()
username = config['username']
symbols = config['symbols']['symbols']
```

**New way:**
```python
from utils.load_config import get_config
config = get_config()
username = config.username
symbols = config.symbols.symbols
```

## 🛠️ Configuration Schema

### Complete Configuration Structure

```yaml
username: "User"
strategy_name: "Bollinger Bands & RSI"

api_keys:
  api_key: "your_api_key"
  api_secret: "your_api_secret"

telegram:
  token: "your_bot_token"
  chat_id: 123456789

capital_tbu: -999.0  # -999 for full balance

db_status: "n"  # "y" or "n"

symbols:
  leverage: 3
  max_open_positions: 1
  symbols:
    - BTCUSDT
    - ETHUSDT
    - XRPUSDT
```

### Field Descriptions

| Field | Type | Description | Default | Validation |
|-------|------|-------------|---------|------------|
| `username` | string | User identifier | "User" | Min length: 1 |
| `strategy_name` | string | Trading strategy name | "Bollinger Bands & RSI" | - |
| `api_keys.api_key` | string | Binance API key | - | Required, min length: 1 |
| `api_keys.api_secret` | SecretStr | Binance API secret | - | Required, min length: 1 |
| `telegram.token` | string | Telegram bot token | - | Required, min length: 1 |
| `telegram.chat_id` | int/string | Telegram chat ID | - | Must be valid integer |
| `capital_tbu` | float | Capital to use | -999.0 | Positive or -999 |
| `db_status` | enum | Database status | "n" | "y" or "n" |
| `symbols.leverage` | int | Trading leverage | 3 | 1-125 |
| `symbols.max_open_positions` | int | Max open positions | 1 | 1-50 |
| `symbols.symbols` | list[string] | Trading symbols | ["BTCUSDT", "ETHUSDT"] | Must end with 'USDT' |

## 🧪 Testing and Examples

Run the example script to see all features in action:

```bash
python utils/config_example.py
```

This will demonstrate:
- Basic configuration loading
- Advanced features (hot-reload, callbacks)
- Environment variable overrides
- Validation error handling
- Command line argument support
- Backward compatibility

## 🚨 Error Handling

The new system provides clear, actionable error messages:

```
Configuration validation failed:
  • symbols -> leverage: ensure this value is less than or equal to 125 (got: 200)
  • symbols -> symbols -> 0: Symbol INVALID must end with 'USDT' (got: INVALID)
  • capital_tbu: Capital must be positive or -999 for full balance (got: -100)
```

## 📝 Best Practices

1. **Use Environment Variables for Secrets**: Store API keys and tokens in environment variables
2. **Enable Hot-Reload in Development**: Use `enable_hot_reload=True` during development
3. **Use Type Hints**: Take advantage of the type-safe configuration objects
4. **Handle Validation Errors**: Always catch `ConfigurationError` exceptions
5. **Use Context Managers**: Use `with ConfigManager() as cm:` for automatic cleanup

## 🔧 Troubleshooting

### Common Issues

**Configuration file not found:**
- The system will automatically create a new configuration through interactive prompts
- Set `auto_create=False` to disable this behavior

**Validation errors:**
- Check the error message for specific field issues
- Ensure all required fields are provided
- Verify data types and value ranges

**Environment variables not working:**
- Ensure variables use the correct prefix (`NONAME_` by default)
- Check variable names match the expected format
- Verify `.env` file is in the correct location

**Hot-reload not working:**
- Ensure the configuration file exists
- Check file permissions
- Verify the file path is correct

### Debug Mode

Enable debug logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

config_manager = ConfigManager()
```

## 🎯 Migration Checklist

- [ ] Install new dependencies: `pip install pydantic python-dotenv watchdog`
- [ ] Update imports to use new functions
- [ ] Test existing functionality
- [ ] Consider using environment variables for secrets
- [ ] Enable hot-reload for development environments
- [ ] Update deployment scripts to use new configuration options

## 📚 API Reference

### ConfigManager Class

```python
class ConfigManager:
    def __init__(
        self,
        config_file: str = "config.yml",
        env_file: str = ".env",
        env_prefix: str = "NONAME_",
        enable_hot_reload: bool = False,
        auto_create: bool = True
    )
    
    def get_config(self) -> AppConfig
    def update_config(self, **kwargs) -> None
    def save_config(self, config: Optional[AppConfig] = None) -> None
    def reload_config(self) -> None
    def add_reload_callback(self, callback: Callable[[AppConfig], None]) -> None
    def validate_config(self, config_data: Dict[str, Any]) -> AppConfig
    def close(self) -> None
```

### Convenience Functions

```python
def get_config() -> AppConfig
def update_config(**kwargs) -> None
def reload_config() -> None
def save_config(config: Optional[AppConfig] = None) -> None
def create_config_manager(**kwargs) -> ConfigManager
```

### Legacy Functions (Deprecated)

```python
def load_config(file_path: str = 'config.yml') -> Optional[Dict[str, Any]]
def get_api_keys() -> Dict[str, str]
def get_telegram_config() -> Dict[str, Any]
def get_symbols_config() -> Dict[str, Any]
``` 