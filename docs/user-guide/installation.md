# Installation Guide

This guide will help you install and set up the n0name Trading Bot on your system.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.8 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: At least 2GB free space
- **Network**: Stable internet connection for market data

### Required Software
- Python 3.8+ with pip
- Git (for cloning the repository)
- Docker (optional, for containerized deployment)

## 🚀 Quick Installation

### Option 1: Using pip (Recommended)
```bash
# Install from PyPI (when available)
pip install n0name-trading-bot

# Or install from source
pip install git+https://github.com/your-username/n0name-trading-bot.git
```

### Option 2: Manual Installation
```bash
# Clone the repository
git clone https://github.com/your-username/n0name-trading-bot.git
cd n0name-trading-bot

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Option 3: Docker Installation
```bash
# Pull the Docker image
docker pull n0name/trading-bot:latest

# Or build from source
git clone https://github.com/your-username/n0name-trading-bot.git
cd n0name-trading-bot
docker build -t n0name/trading-bot .
```

## 🔧 Development Installation

For developers who want to contribute or modify the code:

```bash
# Clone the repository
git clone https://github.com/your-username/n0name-trading-bot.git
cd n0name-trading-bot

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests to verify installation
python -m pytest tests/
```

## ⚙️ Configuration

### 1. Environment Variables
Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit the `.env` file with your settings:
```env
# Trading Configuration
TRADING_MODE=paper  # or 'live' for real trading
EXCHANGE=binance
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here

# Database Configuration
DATABASE_URL=sqlite:///n0name.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/n0name.log
```

### 2. Configuration File
Create or modify the configuration file:

```bash
cp config/default.yml config/local.yml
```

Edit `config/local.yml` with your specific settings.

### 3. API Keys Setup
1. Create accounts on your chosen exchanges
2. Generate API keys with appropriate permissions
3. Add keys to your `.env` file or configuration

**⚠️ Security Note**: Never commit API keys to version control!

## 🏃‍♂️ Running the Bot

### Basic Usage
```bash
# Run with default configuration
python n0name.py

# Run with specific configuration
python n0name.py --config config/local.yml

# Run in paper trading mode
python n0name.py --mode paper

# Run with specific strategy
python n0name.py --strategy macd_fibonacci
```

### Docker Usage
```bash
# Run with Docker
docker run -d \
  --name n0name-bot \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  n0name/trading-bot:latest

# View logs
docker logs -f n0name-bot
```

### Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔍 Verification

### 1. Check Installation
```bash
# Verify Python package
python -c "import n0name; print(n0name.__version__)"

# Check command line tool
n0name --version
```

### 2. Run Health Check
```bash
# Basic health check
python -m n0name.health_check

# Comprehensive system check
python scripts/utilities/validate-setup.py
```

### 3. Test Configuration
```bash
# Test configuration file
python -c "from n0name.config import load_config; print('Config OK')"

# Test exchange connection
python -c "from n0name.exchanges import get_exchange; print('Exchange OK')"
```

## 🛠️ Troubleshooting

### Common Issues

#### Python Version Issues
```bash
# Check Python version
python --version

# If using wrong version, try:
python3.8 -m pip install -r requirements.txt
```

#### Permission Errors
```bash
# On Linux/macOS, use sudo if needed:
sudo pip install -r requirements.txt

# Or use user installation:
pip install --user -r requirements.txt
```

#### Dependency Conflicts
```bash
# Create clean virtual environment
python -m venv fresh_env
source fresh_env/bin/activate  # or fresh_env\Scripts\activate on Windows
pip install -r requirements.txt
```

#### Docker Issues
```bash
# Check Docker is running
docker --version

# Pull latest images
docker-compose pull

# Rebuild containers
docker-compose build --no-cache
```

### Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review the logs in `logs/n0name.log`
3. Search existing [GitHub Issues](https://github.com/your-username/n0name-trading-bot/issues)
4. Create a new issue with:
   - Your operating system
   - Python version
   - Error messages
   - Steps to reproduce

## 📚 Next Steps

After successful installation:

1. **Configuration**: Read the [Configuration Guide](configuration.md)
2. **Trading Strategies**: Learn about [Trading Strategies](trading-strategies.md)
3. **API Usage**: Explore the [API Documentation](../api/endpoints.md)
4. **Development**: Check the [Developer Guide](../developer-guide/architecture.md)

## 🔄 Updates

### Updating the Bot
```bash
# Update from PyPI
pip install --upgrade n0name-trading-bot

# Update from source
git pull origin main
pip install -r requirements.txt

# Update Docker image
docker pull n0name/trading-bot:latest
docker-compose up -d
```

### Version Management
```bash
# Check current version
n0name --version

# List available versions
pip index versions n0name-trading-bot

# Install specific version
pip install n0name-trading-bot==1.2.3
```

---

**Need Help?** Join our community or check the [documentation](../README.md) for more resources. 