# Environment Variables Management

This guide explains how to view and manage environment variables in your n0name trading bot project across different environments.

## 🔍 Viewing Environment Variables

### Python Script (Cross-platform)

```bash
# View all environment variables (masked sensitive values)
python scripts/show_env_vars.py

# View with actual sensitive values (use with caution)
python scripts/show_env_vars.py --show-sensitive

# Check for missing required variables
python scripts/show_env_vars.py --check-missing

# Output in JSON format
python scripts/show_env_vars.py --format json
```

### PowerShell Script (Windows)

```powershell
# View all environment variables (masked sensitive values)
PowerShell -ExecutionPolicy Bypass -File scripts/show_env_vars.ps1

# View with actual sensitive values (use with caution)
PowerShell -ExecutionPolicy Bypass -File scripts/show_env_vars.ps1 -ShowSensitive

# Check for missing required variables
PowerShell -ExecutionPolicy Bypass -File scripts/show_env_vars.ps1 -CheckMissing

# Output in JSON format
PowerShell -ExecutionPolicy Bypass -File scripts/show_env_vars.ps1 -Format JSON
```

## 📋 Environment Variable Sources

The scripts check environment variables from multiple sources in this order:

1. **System Environment Variables** - Set at the OS level
2. **`.env` file** - Local environment file (not in git)
3. **`env.example`** - Template file with example values

## 🔧 Setting Environment Variables

### Development Environment

#### Option 1: Create a `.env` file
```bash
# Copy the example file
cp env.example .env

# Edit the .env file with your actual values
# Note: .env file is in .gitignore and won't be committed
```

#### Option 2: Set system environment variables

**Windows (PowerShell):**
```powershell
# Set for current session
$env:BINANCE_API_KEY = "your_actual_api_key"
$env:BINANCE_API_SECRET = "your_actual_api_secret"

# Set permanently for user
[Environment]::SetEnvironmentVariable("BINANCE_API_KEY", "your_actual_api_key", "User")
[Environment]::SetEnvironmentVariable("BINANCE_API_SECRET", "your_actual_api_secret", "User")
```

**Windows (Command Prompt):**
```cmd
# Set for current session
set BINANCE_API_KEY=your_actual_api_key
set BINANCE_API_SECRET=your_actual_api_secret

# Set permanently
setx BINANCE_API_KEY "your_actual_api_key"
setx BINANCE_API_SECRET "your_actual_api_secret"
```

**Linux/macOS:**
```bash
# Set for current session
export BINANCE_API_KEY="your_actual_api_key"
export BINANCE_API_SECRET="your_actual_api_secret"

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export BINANCE_API_KEY="your_actual_api_key"' >> ~/.bashrc
echo 'export BINANCE_API_SECRET="your_actual_api_secret"' >> ~/.bashrc
```

### Production Environment

#### Docker Environment
```yaml
# docker-compose.yml
version: '3.8'
services:
  trading-bot:
    environment:
      - ENVIRONMENT=production
      - BINANCE_API_KEY=${BINANCE_API_KEY}
      - BINANCE_API_SECRET=${BINANCE_API_SECRET}
      - TRADING_CAPITAL=${TRADING_CAPITAL}
    env_file:
      - .env.production
```

#### Kubernetes
```yaml
# k8s-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: trading-bot-secrets
type: Opaque
stringData:
  BINANCE_API_KEY: "your_actual_api_key"
  BINANCE_API_SECRET: "your_actual_api_secret"
```

#### Cloud Platforms

**AWS ECS/Fargate:**
- Use AWS Systems Manager Parameter Store
- Set environment variables in task definition

**Google Cloud Run:**
- Set environment variables in the service configuration
- Use Google Secret Manager for sensitive values

**Azure Container Instances:**
- Set environment variables in container configuration
- Use Azure Key Vault for sensitive values

## 📊 Required vs Optional Variables

### Required Variables
These must be set for the trading bot to function:

- `BINANCE_API_KEY` - Your Binance API key
- `BINANCE_API_SECRET` - Your Binance API secret
- `TRADING_CAPITAL` - Amount of capital to use for trading

### Optional Variables
These enhance functionality but aren't required:

- `TELEGRAM_BOT_TOKEN` - For Telegram notifications
- `TELEGRAM_CHAT_ID` - Telegram chat ID for notifications
- `DATABASE_URL` - PostgreSQL database connection
- `REDIS_URL` - Redis cache connection
- `INFLUXDB_URL` - InfluxDB for metrics storage

## 🔒 Security Best Practices

### 1. Never Commit Secrets
- Add `.env` to `.gitignore`
- Use `env.example` for templates only
- Never put real API keys in code

### 2. Use Different Keys for Different Environments
```bash
# Development
BINANCE_API_KEY=dev_api_key_here

# Production  
BINANCE_API_KEY=prod_api_key_here
```

### 3. Rotate Keys Regularly
- Change API keys periodically
- Use the `update_api_keys.py` script for secure updates

### 4. Limit API Key Permissions
- Enable only required permissions on Binance
- Whitelist IP addresses
- Enable futures trading only if needed

## 🚀 Quick Setup Commands

### For Development
```bash
# 1. Copy example environment file
cp env.example .env

# 2. Edit with your values
nano .env  # or use your preferred editor

# 3. Check configuration
python scripts/show_env_vars.py --check-missing

# 4. Test API connection
python test_api_connection.py
```

### For Production
```bash
# 1. Set environment variables securely
export ENVIRONMENT=production
export BINANCE_API_KEY="your_production_api_key"
export BINANCE_API_SECRET="your_production_api_secret"

# 2. Verify configuration
python scripts/show_env_vars.py --check-missing

# 3. Run the bot
python n0name.py
```

## 🐛 Troubleshooting

### Common Issues

1. **"API key not found" error**
   ```bash
   # Check if variables are set
   python scripts/show_env_vars.py --check-missing
   ```

2. **"Invalid API key" error**
   ```bash
   # Test API connection
   python test_api_connection.py
   ```

3. **Variables not loading from .env file**
   - Ensure `.env` file is in project root
   - Check file format (KEY=VALUE, no spaces around =)
   - Verify file encoding (UTF-8)

### Debug Commands
```bash
# Show all environment sources
python scripts/show_env_vars.py

# Show actual values (be careful!)
python scripts/show_env_vars.py --show-sensitive

# Test specific API endpoints
python test_api_endpoints.py
```

## 📝 Environment File Template

Create a `.env` file with this template:

```bash
# Trading Bot Configuration
ENVIRONMENT=development
DEBUG=true

# Binance API (Required)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# Trading Settings
TRADING_CAPITAL=1000.0
TRADING_LEVERAGE=1

# Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

Remember to replace the placeholder values with your actual configuration! 