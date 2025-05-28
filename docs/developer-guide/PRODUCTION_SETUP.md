# 🚀 Production Setup Guide

This guide will help you set up the n0name Trading Bot for production use with real trading.

## ⚠️ Important Warnings

**REAL MONEY TRADING**: This bot will trade with real money. You can lose your entire investment.

- Start with small amounts to test the strategy
- Monitor the bot closely, especially initially  
- Understand the risks of automated trading
- Never invest more than you can afford to lose

## 🔧 Setup Steps

### 1. Get Binance API Keys

1. Go to [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Create a new API key with these permissions:
   - ✅ Enable Reading
   - ✅ Enable Futures Trading
   - ❌ Disable Withdrawals (for security)
3. Save your API Key and Secret Key securely

### 2. Run Production Setup

```bash
python setup_production.py
```

This interactive script will:
- Configure your API keys
- Set trading parameters (capital, leverage, symbols)
- Enable production mode (disable paper trading and testnet)
- Create a backup of your current config

### 3. Verify Configuration

Check your `config.yml` file to ensure:
- `api_keys` contains your real Binance credentials
- `exchange.testnet` is set to `false`
- `trading.paper_trading` is set to `false`
- Trading parameters match your risk tolerance

### 4. Start the Bot

```bash
python n0name.py
```

## 📋 Configuration Options

### Capital Management
- **Fixed Amount**: Set a specific USD amount (e.g., 1000.0)
- **Full Balance**: Use -999.0 to use your entire futures balance

### Risk Settings
- **Leverage**: 1-125x (start with low leverage like 3-5x)
- **Max Positions**: Maximum concurrent open positions
- **Symbols**: Trading pairs (must end with USDT)

### Strategy Settings
- **Strategy**: Currently supports "Bollinger Bands & RSI"
- **Timeframe**: 5-minute candles
- **Risk per Trade**: 2% of capital per position

## 🛡️ Security Best Practices

1. **API Key Security**:
   - Never share your API keys
   - Use IP restrictions on Binance
   - Disable withdrawal permissions
   - Regularly rotate your keys

2. **Trading Security**:
   - Start with small amounts
   - Use stop-losses
   - Monitor positions regularly
   - Have an exit strategy

3. **System Security**:
   - Keep your system updated
   - Use secure networks
   - Regular backups of config

## 📊 Monitoring

The bot provides:
- Real-time logging with ERROR level (clean output)
- Web UI at http://localhost:3000 for monitoring
- Position tracking and performance metrics

## 🆘 Emergency Stop

To stop the bot immediately:
1. Press `Ctrl+C` in the terminal
2. The bot will gracefully close all connections
3. Existing positions will remain open (close manually if needed)

## 🔄 Switching Back to Test Mode

To switch back to test/development mode:

1. Edit `config.yml`:
   ```yaml
   exchange:
     testnet: true
   trading:
     paper_trading: true
   ```

2. Or run the setup script again and choose test mode

## 📞 Support

- Check logs in the terminal for error messages
- Review the main README.md for general troubleshooting
- Ensure your Binance account has sufficient futures balance
- Verify API key permissions and IP restrictions

---

**Remember**: Automated trading involves significant risk. Only trade with money you can afford to lose and always monitor your positions. 