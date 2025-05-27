# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the n0name Trading Bot.

## 🚨 Quick Diagnostics

### Health Check
Run the built-in health check to identify common issues:

```bash
# Basic health check
python -m n0name.health_check

# Comprehensive system check
python scripts/utilities/validate-setup.py

# Check specific components
python -c "from n0name.config import load_config; print('Config: OK')"
python -c "from n0name.exchanges import get_exchange; print('Exchange: OK')"
```

### Log Analysis
Check the logs for error messages:

```bash
# View recent logs
tail -f logs/n0name.log

# Search for errors
grep -i error logs/n0name.log

# View specific component logs
tail -f logs/trading.log
tail -f logs/strategy.log
tail -f logs/api.log
```

## 🔧 Common Issues

### Installation Problems

#### Python Version Issues
**Problem**: `ModuleNotFoundError` or compatibility errors
```
ERROR: Python 3.7 is not supported
```

**Solution**:
```bash
# Check Python version
python --version

# Install with correct Python version
python3.8 -m pip install -r requirements.txt

# Use pyenv to manage Python versions
pyenv install 3.9.0
pyenv local 3.9.0
```

#### Dependency Conflicts
**Problem**: Package version conflicts
```
ERROR: pip's dependency resolver does not currently consider all the packages that are installed
```

**Solution**:
```bash
# Create fresh virtual environment
python -m venv fresh_env
source fresh_env/bin/activate  # Linux/macOS
# or
fresh_env\Scripts\activate  # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Permission Errors
**Problem**: Permission denied during installation
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Solution**:
```bash
# Use user installation
pip install --user -r requirements.txt

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration Issues

#### Invalid Configuration File
**Problem**: YAML parsing errors
```
ERROR: yaml.scanner.ScannerError: while scanning for the next token
```

**Solution**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/default.yml'))"

# Use online YAML validator
# Check indentation (use spaces, not tabs)
# Ensure proper quoting of strings
```

#### Missing Environment Variables
**Problem**: KeyError for required environment variables
```
ERROR: KeyError: 'API_KEY'
```

**Solution**:
```bash
# Check if .env file exists
ls -la .env

# Copy from example
cp .env.example .env

# Edit with your values
nano .env

# Verify environment variables are loaded
python -c "import os; print(os.getenv('API_KEY', 'NOT_SET'))"
```

#### Invalid API Credentials
**Problem**: Authentication errors
```
ERROR: 401 Unauthorized - Invalid API key
```

**Solution**:
1. Verify API key and secret in exchange dashboard
2. Check API key permissions (trading, reading)
3. Ensure IP whitelist includes your server
4. Test credentials:
```python
from n0name.exchanges import get_exchange
exchange = get_exchange('binance')
print(exchange.fetch_balance())
```

### Trading Issues

#### No Trading Signals
**Problem**: Strategy not generating signals
```
INFO: No trading signals generated for the last 2 hours
```

**Diagnosis**:
```bash
# Check market data
python -c "
from n0name.data import get_market_data
data = get_market_data('BTC/USDT', '1h', limit=100)
print(f'Data points: {len(data)}')
print(f'Latest price: {data[-1][\"close\"]}')
"

# Check strategy parameters
python -c "
from n0name.strategies import load_strategy
strategy = load_strategy('macd_fibonacci')
print(f'Strategy loaded: {strategy.name}')
"
```

**Solutions**:
- Verify market data is updating
- Check strategy parameters are reasonable
- Ensure trading pairs are active
- Review market conditions (low volatility periods)

#### Orders Not Executing
**Problem**: Orders placed but not filled
```
WARNING: Order 12345 not filled after 5 minutes
```

**Diagnosis**:
```bash
# Check order status
python -c "
from n0name.exchanges import get_exchange
exchange = get_exchange()
order = exchange.fetch_order('12345')
print(f'Order status: {order[\"status\"]}')
print(f'Filled: {order[\"filled\"]}/{order[\"amount\"]}')
"
```

**Solutions**:
- Check if price moved away from order
- Verify sufficient balance
- Use market orders for immediate execution
- Adjust order timeout settings

#### Insufficient Balance
**Problem**: Not enough funds for trading
```
ERROR: Insufficient balance for order: Required 100 USDT, Available 50 USDT
```

**Solutions**:
```bash
# Check account balance
python -c "
from n0name.exchanges import get_exchange
exchange = get_exchange()
balance = exchange.fetch_balance()
print(f'USDT: {balance[\"USDT\"][\"free\"]}')
"

# Reduce position sizes in configuration
# Add funds to exchange account
# Check for locked/reserved funds
```

### Performance Issues

#### High Memory Usage
**Problem**: Bot consuming too much memory
```
WARNING: Memory usage: 2.5GB (threshold: 2GB)
```

**Solutions**:
```bash
# Monitor memory usage
python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"

# Reduce data retention
# Optimize strategy calculations
# Restart bot periodically
```

#### Slow Response Times
**Problem**: API calls taking too long
```
WARNING: API call took 15.2 seconds (threshold: 5s)
```

**Solutions**:
- Check internet connection
- Use different exchange endpoints
- Implement request caching
- Reduce API call frequency

### Data Issues

#### Missing Market Data
**Problem**: No price data available
```
ERROR: No data available for BTC/USDT on 1h timeframe
```

**Solutions**:
```bash
# Check exchange connectivity
python -c "
from n0name.exchanges import get_exchange
exchange = get_exchange()
markets = exchange.load_markets()
print('BTC/USDT' in markets)
"

# Verify trading pair is active
# Check timeframe is supported
# Try alternative data sources
```

#### Stale Data
**Problem**: Data not updating
```
WARNING: Last data update was 30 minutes ago
```

**Solutions**:
- Check exchange API status
- Verify WebSocket connections
- Restart data feed
- Check rate limits

### Docker Issues

#### Container Won't Start
**Problem**: Docker container exits immediately
```
ERROR: Container exited with code 1
```

**Diagnosis**:
```bash
# Check container logs
docker logs n0name-bot

# Run interactively for debugging
docker run -it --entrypoint /bin/bash n0name/trading-bot

# Check environment variables
docker exec n0name-bot env | grep API
```

#### Volume Mount Issues
**Problem**: Configuration files not accessible
```
ERROR: FileNotFoundError: config/default.yml
```

**Solutions**:
```bash
# Check volume mounts
docker inspect n0name-bot | grep -A 10 Mounts

# Fix volume paths in docker-compose.yml
volumes:
  - ./config:/app/config:ro
  - ./logs:/app/logs:rw
```

#### Network Connectivity
**Problem**: Cannot reach external APIs
```
ERROR: Connection timeout to api.binance.com
```

**Solutions**:
```bash
# Test network from container
docker exec n0name-bot ping api.binance.com

# Check Docker network settings
docker network ls
docker network inspect bridge

# Use host networking if needed
docker run --network host n0name/trading-bot
```

## 🔍 Advanced Debugging

### Enable Debug Logging
```yaml
# config/debug.yml
logging:
  level: DEBUG
  handlers:
    file:
      level: DEBUG
      filename: logs/debug.log
    console:
      level: DEBUG
```

### Performance Profiling
```python
# Add to your strategy
import cProfile
import pstats

def profile_strategy():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your strategy code here
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
```

### Memory Profiling
```python
# Install memory profiler
pip install memory-profiler

# Add decorator to functions
from memory_profiler import profile

@profile
def your_function():
    # Function code here
    pass
```

### Database Debugging
```bash
# Check database connections
python -c "
from n0name.database import get_db_connection
conn = get_db_connection()
print(f'Database connected: {conn is not None}')
"

# Check table structure
sqlite3 data/n0name.db ".schema"

# View recent trades
sqlite3 data/n0name.db "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;"
```

## 📊 Monitoring and Alerts

### System Monitoring
```yaml
# config/monitoring.yml
monitoring:
  system:
    cpu_threshold: 80      # Alert if CPU > 80%
    memory_threshold: 2048 # Alert if memory > 2GB
    disk_threshold: 90     # Alert if disk > 90%
    
  trading:
    max_drawdown: 0.10     # Alert if drawdown > 10%
    min_balance: 1000      # Alert if balance < $1000
    error_rate: 0.05       # Alert if error rate > 5%
```

### Health Check Endpoints
```bash
# Check bot health via API
curl http://localhost:8080/health

# Check specific components
curl http://localhost:8080/health/database
curl http://localhost:8080/health/exchange
curl http://localhost:8080/health/strategy
```

## 🆘 Getting Help

### Before Asking for Help

1. **Check this troubleshooting guide**
2. **Review the logs** for error messages
3. **Run the health check** to identify issues
4. **Search existing issues** on GitHub
5. **Try the suggested solutions** above

### When Reporting Issues

Include the following information:

```bash
# System information
python --version
pip list | grep n0name
uname -a  # Linux/macOS
systeminfo  # Windows

# Configuration (remove sensitive data)
cat config/default.yml

# Recent logs (last 50 lines)
tail -50 logs/n0name.log

# Error reproduction steps
# 1. Step one
# 2. Step two
# 3. Error occurs
```

### Support Channels

1. **GitHub Issues**: [Create an issue](https://github.com/your-username/n0name-trading-bot/issues)
2. **Documentation**: Check the [docs](../README.md)
3. **Community**: Join our Discord/Telegram
4. **Email**: support@n0name-bot.com

### Emergency Procedures

#### Stop All Trading Immediately
```bash
# Emergency stop
python n0name.py --emergency-stop

# Cancel all open orders
python -c "
from n0name.exchanges import get_exchange
exchange = get_exchange()
orders = exchange.fetch_open_orders()
for order in orders:
    exchange.cancel_order(order['id'])
print(f'Cancelled {len(orders)} orders')
"
```

#### Backup Critical Data
```bash
# Backup database
cp data/n0name.db backups/n0name_$(date +%Y%m%d_%H%M%S).db

# Backup configuration
tar -czf backups/config_$(date +%Y%m%d_%H%M%S).tar.gz config/

# Backup logs
tar -czf backups/logs_$(date +%Y%m%d_%H%M%S).tar.gz logs/
```

## 📚 Additional Resources

- [Installation Guide](installation.md)
- [Configuration Guide](configuration.md)
- [Trading Strategies](trading-strategies.md)
- [Developer Guide](../developer-guide/architecture.md)
- [API Documentation](../api/endpoints.md)

---

**Remember**: When in doubt, stop trading and seek help. It's better to miss opportunities than to lose money due to unresolved issues. 