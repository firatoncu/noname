# Configuration Setup Guide

This guide explains how to set up your n0name trading bot configuration when no configuration file exists or when the existing configuration is invalid.

## Automatic Setup Detection

The trading bot now automatically detects when configuration is missing or invalid and guides you through a setup process:

### When Setup is Triggered

The setup process is automatically triggered when:

1. **No configuration file exists** (`config.yml` not found)
2. **Configuration file is invalid** (corrupted YAML, missing required fields)
3. **Configuration file is incomplete** (missing required keys like `api_keys`, `symbols`, etc.)

### Setup Process

When configuration issues are detected, the bot will:

1. **Start in Setup Mode**: The web interface starts automatically
2. **Display Setup Page**: Navigate to `https://localhost:5173/setup`
3. **Guide Through Configuration**: Step-by-step setup wizard
4. **Validate Settings**: Real-time validation of your inputs
5. **Create Configuration**: Generate a complete `config.yml` file
6. **Restart Automatically**: Bot restarts with the new configuration

## Setup Steps

### Step 1: API Credentials
- Enter your Binance API key and secret
- Choose between testnet (recommended for first-time users) or live trading
- API credentials are encrypted and stored securely

### Step 2: Trading Configuration
- Set your trading capital (USDT amount or -999 for full balance)
- Configure leverage (1-125x)
- Set maximum open positions (1-10)
- Choose your trading strategy
- Select trading symbols from popular cryptocurrencies

### Step 3: Risk Management
- Configure stop loss percentage (0.1-10%)
- Set take profit ratio (0.1-10x)
- Define maximum daily loss percentage (0.1-50%)

### Step 4: Review & Confirm
- Review all your settings
- Confirm and save configuration
- Automatic redirect to dashboard

## Manual Setup Access

You can also manually access the setup page by visiting:
```
https://localhost:5173/setup
```

Add query parameters to indicate the reason:
- `?reason=missing` - Configuration file not found
- `?reason=invalid` - Configuration file is corrupted
- `?reason=error` - General configuration error

## Configuration File Structure

The setup process creates a complete `config.yml` file with both legacy and new format sections for compatibility:

```yaml
# Legacy format (for backward compatibility)
symbols:
  symbols: ["BTCUSDT", "ETHUSDT"]
  max_open_positions: 3
  leverage: 10
capital_tbu: 100
strategy_name: "Bollinger Bands & RSI"
api_keys:
  api_key: "your_api_key"
  api_secret: "your_api_secret"
db_status: "enabled"

# New structured format
trading:
  capital: 100
  leverage: 10
  symbols: ["BTCUSDT", "ETHUSDT"]
  strategy:
    name: "Bollinger Bands & RSI"
    type: "technical_analysis"
  risk:
    max_open_positions: 3
    stop_loss_percentage: 2.0
    take_profit_ratio: 2.0

exchange:
  type: "binance"
  testnet: true
  rate_limit: 1200

logging:
  level: "INFO"
  console_output: true

notifications:
  enabled: false
```

## API Endpoints

The setup process uses these API endpoints:

- `GET /api/config/status` - Check configuration status
- `POST /api/config/setup` - Create new configuration
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update existing configuration

## Testing Setup Process

To test the setup process:

1. **Backup your existing config** (if any):
   ```bash
   cp config.yml config.yml.backup
   ```

2. **Remove or rename the config file**:
   ```bash
   mv config.yml config.yml.temp
   ```

3. **Start the bot**:
   ```bash
   python n0name.py
   ```

4. **Follow the setup process** at `https://localhost:5173/setup`

5. **Restore original config** (if needed):
   ```bash
   mv config.yml.temp config.yml
   ```

## Troubleshooting

### Setup Page Not Loading
- Ensure the bot is running (`python n0name.py`)
- Check that port 5173 is not blocked by firewall
- Try accessing `http://localhost:5173/setup` instead of HTTPS

### API Errors During Setup
- Verify your Binance API credentials
- Ensure API key has futures trading permissions
- Check network connectivity
- Try using testnet first

### Configuration Not Saving
- Check file permissions in the project directory
- Ensure sufficient disk space
- Verify no other process is using the config file

### Bot Not Restarting After Setup
- Manually restart the bot: `python n0name.py`
- Check the logs for any error messages
- Verify the created config file is valid YAML

## Security Notes

- API credentials are stored in the configuration file
- Consider using environment variables for sensitive data
- Use testnet for initial testing
- Never share your API credentials
- Regularly rotate your API keys

## Support

If you encounter issues with the setup process:

1. Check the bot logs for error messages
2. Verify your API credentials are correct
3. Ensure you have proper permissions for futures trading
4. Try the setup process with testnet first
5. Consult the main README.md for additional troubleshooting

## Next Steps

After completing the setup:

1. **Verify Configuration**: Check that all settings are correct
2. **Test with Small Amounts**: Start with minimal capital
3. **Monitor Performance**: Use the web dashboard to track trades
4. **Adjust Settings**: Fine-tune parameters based on performance
5. **Enable Notifications**: Set up alerts for important events 