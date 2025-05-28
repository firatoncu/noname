# n0name Trading Bot v2.4.5

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-green.svg)](https://github.com/features/actions)

A professional-grade automated cryptocurrency trading bot designed for Binance Futures trading. Built with Python, featuring modular architecture, comprehensive risk management, and extensive monitoring capabilities.

## ⚠️ Disclaimer

**The information provided by this bot is not intended to be and should not be construed as financial advice. Always conduct your own research and consult with a qualified financial advisor before making any trading decisions. Trading in cryptocurrencies and futures involves a high level of risk and may not be suitable for all investors. You should carefully consider your financial situation and risk tolerance before engaging in such activities. There are no guarantees of profit or avoidance of losses when using this bot. Past performance is not indicative of future results. You are solely responsible for any trades executed using this bot. The developers and contributors of this project are not liable for any financial losses or damages that may occur as a result of using this bot. Ensure that your use of this bot complies with all applicable laws and regulations in your jurisdiction.**

## 🚀 Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/your-username/n0name-trading-bot.git
cd n0name-trading-bot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# Run the bot
python n0name.py

# Access the web interface
# Open http://localhost:5173 in your browser
```

### Docker Quick Start
```bash
# Using Docker Compose (Recommended)
docker-compose up -d

# View logs
docker-compose logs -f n0name-bot
```

## 📚 Documentation

Our comprehensive documentation is organized to help both users and developers:

### 🎯 For Users
- **[Installation Guide](docs/user-guide/installation.md)** - Complete setup instructions
- **[Configuration Guide](docs/user-guide/configuration.md)** - Configuration reference
- **[Trading Strategies](docs/user-guide/trading-strategies.md)** - Available strategies and usage
- **[Troubleshooting](docs/user-guide/troubleshooting.md)** - Common issues and solutions

### 🔧 For Developers
- **[Architecture Overview](docs/developer-guide/architecture.md)** - System design and components
- **[Contributing Guidelines](docs/developer-guide/contributing.md)** - How to contribute
- **[Testing Guide](docs/developer-guide/testing.md)** - Testing framework and practices
- **[Performance Guide](docs/developer-guide/performance.md)** - Optimization techniques
- **[Security Guidelines](docs/developer-guide/security.md)** - Security best practices

### 🚀 For DevOps
- **[Docker Deployment](docs/deployment/docker.md)** - Container deployment guide
- **[Monitoring Setup](docs/deployment/monitoring.md)** - Monitoring and alerting
- **[Backup & Recovery](docs/deployment/backup-recovery.md)** - Data protection

### 🔌 API Reference
- **[API Endpoints](docs/api/endpoints.md)** - REST API documentation
- **[API Manager](docs/api/manager.md)** - API client libraries
- **[Authentication](docs/api/authentication.md)** - API security

### 📖 Migration & Guides
- **[Migration Guides](docs/guides/migration/)** - Upgrade and migration instructions
- **[Optimization Guides](docs/guides/optimization/)** - Performance optimization
- **[Modernization Guides](docs/guides/modernization/)** - Code modernization

## ✨ Key Features

### 🌐 Modern Web Interface
- **Enhanced Dashboard**: Real-time trading overview with improved visual design and live position updates
- **Refined Trading Conditions**: Monitor market conditions and strategy signals with better UX and visual clarity
- **Advanced Position Analysis**: Comprehensive performance analytics with enhanced interactive charts and improved metrics display
- **Streamlined Settings**: Intuitive configuration management through redesigned web interface
- **Interactive Symbol Charts**: Click any symbol to view enhanced TradingView-style charts with improved performance
- **Responsive Design**: Optimized experience across desktop, tablet, and mobile devices with better touch interactions
- **Performance Optimized**: Faster loading times, smoother animations, and improved overall responsiveness
- **Accessibility Enhanced**: Better keyboard navigation, screen reader support, and inclusive design principles
- **Visual Polish**: Updated color schemes, typography, icons, and spacing for a more professional appearance
- **Improved Error Handling**: User-friendly error messages and better recovery workflows

### 🎯 Trading Capabilities
- **Multiple Strategies**: MACD-Fibonacci, Bollinger-RSI, and custom strategies
- **Risk Management**: Advanced position sizing, stop-loss, and take-profit
- **Paper Trading**: Test strategies without real money
- **Multi-Timeframe**: Support for various timeframes (1m to 1d)
- **Multi-Asset**: Trade multiple cryptocurrency pairs simultaneously

### 🛡️ Security & Safety
- **Encrypted Configuration**: Secure API key storage with simplified config system
- **Risk Limits**: Configurable drawdown and position limits
- **Emergency Stop**: Immediate trading halt functionality
- **Audit Logging**: Comprehensive trade and system logging with ERROR level by default
- **Production Mode**: Secure production configuration with real API keys
- **Full Balance Trading**: Support for using 100% of futures balance with leverage

### 📊 Monitoring & Analytics
- **Real-time Dashboard**: Modern web-based monitoring interface with React
- **Position Analysis**: Comprehensive trading performance analytics with interactive charts
- **Performance Metrics**: Detailed trading statistics with hover tooltips and explanations
- **Symbol Chart Integration**: Click any symbol to view interactive charts in popup modals
- **Alerting System**: Email, Slack, and Telegram notifications
- **Database Integration**: InfluxDB for time-series data

### 🔧 Technical Excellence
- **Modular Architecture**: Clean, maintainable codebase with simplified configuration system
- **Modern Web UI**: React-based frontend with TypeScript and Tailwind CSS
- **Async Processing**: High-performance async operations
- **Docker Support**: Containerized deployment
- **CI/CD Pipeline**: Automated testing and deployment
- **Comprehensive Testing**: Unit, integration, and performance tests
- **Production Ready**: Full balance trading with 5x leverage support

## 🏗️ Project Structure

```
n0name-trading-bot/
├── 📁 utils/                 # Core utilities and components
│   ├── web_ui/              # Modern React web interface
│   │   └── project/         # React TypeScript frontend
│   │       ├── src/         # React source code
│   │       │   ├── components/  # Reusable UI components
│   │       │   ├── pages/       # Main application pages
│   │       │   └── api/         # FastAPI backend
│   │       └── public/      # Static assets
│   ├── config_manager.py    # Configuration management
│   ├── enhanced_logging.py  # Advanced logging system
│   ├── load_config.py       # Simplified config loader
│   └── config_models.py     # Pydantic configuration models
├── 📁 tests/                # Test suite
├── 📁 docs/                 # Documentation
├── 📁 scripts/              # Automation scripts
├── 📁 tools/                # Development tools
├── 📁 examples/             # Example configurations
├── 📁 archive/              # Archived/legacy files
├── 📁 logs/                 # Application logs
├── 📁 auth/                 # Authentication files
├── config.yml               # Main configuration file
├── n0name.py               # Main trading bot application
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker deployment
└── README.md               # This file
```

## 🎯 Available Strategies

### 1. MACD Fibonacci Strategy
- **Type**: Trend-following
- **Best for**: Trending markets, medium to long-term trades
- **Indicators**: MACD crossovers + Fibonacci retracements
- **Risk Management**: Configurable stop-loss and take-profit

### 2. Bollinger Bands RSI Strategy
- **Type**: Mean reversion
- **Best for**: Range-bound markets, high volatility
- **Indicators**: Bollinger Bands + RSI confirmation
- **Risk Management**: Dynamic position sizing

### 3. Custom Strategy Framework
- **Extensible**: Create your own strategies
- **Template**: Base strategy class with common functionality
- **Backtesting**: Built-in backtesting support

## ⚙️ Configuration

### Environment Variables
```env
# Trading Configuration
TRADING_MODE=paper          # paper or live
EXCHANGE=binance
API_KEY=your_api_key
API_SECRET=your_api_secret

# Database
DATABASE_URL=sqlite:///n0name.db

# Monitoring
INFLUXDB_URL=http://localhost:8086
GRAFANA_URL=http://localhost:3000
```

### Strategy Configuration
```yaml
# config.yml - Simplified single configuration file
trading:
  capital: -999  # Use full balance
  leverage: 5
  symbols: ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "ADAUSDT", "DOGEUSDT"]
  paper_trading: false
  auto_start: true
  strategy:
    name: "bollinger_rsi"
    type: "mean_reversion"
    enabled: true
    timeframe: "1h"
    lookback_period: 20
  risk:
    max_position_size: 1.0  # 100% of balance
    max_open_positions: 1   # One position at a time
    risk_per_trade: 1.0
    stop_loss_percentage: 2.0
    take_profit_ratio: 2.0

exchange:
  type: "binance"
  testnet: false  # Production mode
  rate_limit: 1200
  timeout: 30
  retry_attempts: 3

logging:
  level: "ERROR"  # Minimal logging for production
  console_output: true
  structured_logging: false

notifications:
  enabled: true
```

## 🚀 Deployment Options

### Local Development
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Start development server
python n0name.py --mode paper
```

### Docker Production
```bash
# Production deployment
docker-compose -f docker-compose.yml up -d

# With monitoring stack
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

### Cloud Deployment
- **AWS**: ECS/EKS deployment guides
- **Google Cloud**: GKE deployment
- **Azure**: AKS deployment
- **DigitalOcean**: Droplet deployment

## 📊 Monitoring & Metrics

### Key Metrics
- **Performance**: Win rate, profit factor, Sharpe ratio
- **Risk**: Maximum drawdown, position exposure
- **System**: CPU, memory, API latency
- **Trading**: Order fill rates, slippage

### Dashboards
- **Grafana**: Real-time trading dashboard with enhanced visualizations
- **Enhanced Web UI**: Built-in monitoring interface with improved React frontend and modern design
- **Advanced Position Analysis**: Interactive performance analytics with enhanced UI featuring:
  - Redesigned performance metrics with improved tooltips and visual hierarchy
  - Enhanced symbol performance breakdown with better data visualization
  - Improved trade history with streamlined filtering and better UX
  - Upgraded interactive charts (P&L over time, symbol distribution, win rates) with better performance
  - Refined clickable symbols with smoother chart popup animations and improved responsiveness
- **Mobile Optimized**: Enhanced responsive design with better touch interactions and mobile-first approach

### Alerts
- **Email**: Trade notifications and system alerts
- **Slack**: Team notifications
- **Telegram**: Personal alerts
- **Webhook**: Custom integrations

## 🛠️ Development

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- Git

### Development Setup
```bash
# Clone and setup
git clone https://github.com/your-username/n0name-trading-bot.git
cd n0name-trading-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
make test

# Start development server
make dev
```

### Available Commands
```bash
# Development
make dev              # Start development server
make test             # Run test suite
make lint             # Run linting
make format           # Format code

# Building
make build            # Build Python package
make docker-build     # Build Docker image
make docs             # Generate documentation

# Deployment
make deploy-staging   # Deploy to staging
make deploy-prod      # Deploy to production
make backup           # Backup data
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](docs/developer-guide/contributing.md) for details.

### Quick Contribution Guide
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`make test`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Documentation**: Check our [comprehensive docs](docs/README.md)
- **Issues**: [GitHub Issues](https://github.com/your-username/n0name-trading-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/n0name-trading-bot/discussions)
- **Community**: Join our Discord server

### Reporting Issues
When reporting issues, please include:
- Operating system and Python version
- Error messages and stack traces
- Steps to reproduce the issue
- Configuration (remove sensitive data)

## 🔄 Changelog

### Version 2.4.5 - Latest Release 🎉

#### 🎨 UI Updates & Improvements
- **Enhanced User Interface**: Refined visual design with improved color schemes and typography
- **Improved Responsiveness**: Better mobile and tablet experience with optimized layouts
- **Performance Optimizations**: Faster page load times and smoother animations
- **Accessibility Enhancements**: Better keyboard navigation and screen reader support
- **Visual Polish**: Updated icons, improved spacing, and enhanced visual hierarchy
- **User Experience**: Streamlined workflows and more intuitive navigation patterns
- **Chart Improvements**: Enhanced chart rendering performance and visual clarity
- **Loading States**: Better loading indicators and skeleton screens for improved perceived performance
- **Error Handling**: More user-friendly error messages and recovery options
- **Theme Consistency**: Unified design language across all components and pages

#### 🔧 Technical Improvements
- **Frontend Optimization**: Reduced bundle size and improved rendering performance
- **Component Refactoring**: Cleaner, more maintainable React components
- **CSS Optimization**: Streamlined stylesheets and improved CSS performance
- **API Response Handling**: Enhanced error handling and data validation
- **Memory Management**: Better cleanup and resource management in the frontend

### Version 2.4.0 - Previous Release

#### 🌟 Major Features
- **Position Analysis Dashboard**: Comprehensive trading performance analytics
  - Interactive performance metrics with explanatory tooltips
  - Symbol performance breakdown and comparison
  - Trade history with advanced filtering (timeframe, symbol)
  - Multiple view modes: Overview, Detailed table, Interactive charts
  - Real-time data integration with API endpoints

#### 📊 Enhanced Web Interface
- **Symbol Chart Integration**: Click any symbol to view interactive charts
  - Modal popup with embedded TradingView-style charts
  - External link option to open charts in new tabs
  - Smooth animations and professional UI/UX
- **Improved Navigation**: Streamlined navigation with Dashboard, Trading Conditions, Position Analysis, and Settings
- **Responsive Design**: Optimized for all device sizes

#### ⚙️ Configuration System Overhaul
- **Simplified Configuration**: Single `config.yml` file replaces complex multi-file system
- **No Default Values**: All configuration must be explicitly defined
- **Production Ready**: Full balance trading with leverage support
- **Web-based Settings**: Configure bot through web interface
- **Real-time Updates**: Configuration changes reflect immediately

#### 🔧 Technical Improvements
- **Enhanced Logging**: Configurable log levels with ERROR default for production
- **API Optimization**: Improved endpoint performance and error handling
- **State Management**: Better handling of trading conditions and position updates
- **Error Suppression**: Intelligent handling of harmless connection reset errors

#### 🛡️ Security & Stability
- **Production Mode**: Secure configuration for live trading
- **API Key Management**: Improved security for sensitive credentials
- **Recovery System**: Enhanced error recovery and exception handling
- **Connection Management**: Better handling of network interruptions

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## 🙏 Acknowledgments

- **ccxt**: Cryptocurrency exchange library
- **TA-Lib**: Technical analysis library
- **FastAPI**: Modern web framework
- **Docker**: Containerization platform
- **Grafana**: Monitoring and visualization

## Windows-Specific Considerations

### Connection Reset Errors

On Windows, you may see harmless connection reset errors in the console:
```
ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host
```

These errors are **normal** and **harmless**. They occur when:
- The Binance API server closes idle connections
- Network timeouts occur during normal operation
- Rate limiting is enforced by the exchange

The application automatically suppresses these errors and continues operating normally. The error suppression system:
- Catches and logs these errors at debug level only
- Maintains statistics on suppressed errors
- Ensures the application continues running without interruption

### Event Loop Configuration

The application automatically configures the optimal asyncio event loop for Windows:
- Uses `WindowsProactorEventLoopPolicy` for better compatibility
- Suppresses resource warnings that don't affect functionality
- Handles connection cleanup gracefully

### Monitoring Suppressed Errors

You can monitor suppressed connection errors in the debug logs. The application will log a summary of suppressed errors on shutdown, helping you understand the frequency of these normal network events.

---

**⚡ Ready to start trading?** Check out our [Installation Guide](docs/user-guide/installation.md) to get started!

**🔧 Want to contribute?** Read our [Developer Guide](docs/developer-guide/architecture.md) to understand the architecture.