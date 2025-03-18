
# n0name v0.7.2 by f0ncu
This repository contains *project n0name* designed for automated Futures Trading on Binance. The bot leverages the Binance API to execute trades based on configurable parameters. Built with Python..

# Disclaimer

*The information provided by this bot is not intended to be and should not be construed as financial advice. Always conduct your own research and consult with a qualified financial advisor before making any trading decisions.Trading in cryptocurrencies and futures involves a high level of risk and may not be suitable for all investors. You should carefully consider your financial situation and risk tolerance before engaging in such activities.There are no guarantees of profit or avoidance of losses when using this bot. Past performance is not indicative of future results.You are solely responsible for any trades executed using this bot. The developers and contributors of this project are not liable for any financial losses or damages that may occur as a result of using this bot.Ensure that your use of this bot complies with all applicable laws and regulations in your jurisdiction. It is your responsibility to understand and adhere to any legal requirements related to cryptocurrency trading.*
#

# Description
This repository contains **n0name**, a sophisticated automated trading bot designed specifically for Futures Trading on the Binance platform. Built with Python, n0name leverages the Binance API to execute trades based on highly configurable parameters and advanced trading strategies. The bot is engineered to optimize trading performance by combining technical analysis, robust risk management, and efficient operational workflows. It caters to traders who seek a reliable, customizable, and responsive tool to navigate the fast-paced and volatile futures market.

The bot integrates cutting-edge methodologies such as **MACD histogram analysis**, **Fibonacci retracement**, and **signal validation** to make informed trading decisions. With its asynchronous architecture, n0name ensures high performance by managing multiple tasks concurrently, while its comprehensive error-handling and logging systems provide transparency and reliability. Whether you're a seasoned trader or an enthusiast looking to automate your strategies, n0name offers a powerful and adaptable solution for trading futures on Binance.

# Installation
### Prerequisites
- Python 3.11 or higher
- Binance API Key and Secret with Futures Trading enabled

### Steps
1. Download [**n0name Trading Bot** (v0.7.2)](https://github.com/firatoncu/noname/releases/download/noname-v072/n0name-v0-7-2.exe)
2. Run **n0name-v072.exe** 
3. Follow the instructions and generate a config file (you can change it later!)  

# Key Features
n0name offers a robust set of capabilities to enhance trading efficiency and precision:
- **Backtesting**: Backtesting with desired symbols and timeframe. ****(easiest backtesting module ever!)****
- **Asynchronous Processing**: Utilizes asynchronous programming to handle multiple tasks concurrently, improving operational efficiency and reducing latency.
- **Customizable Parameters**: Empowers users to tailor trading variables, such as trading pairs (e.g., BTC/USDT), leverage settings, and the maximum number of simultaneous open positions.
- **Advanced Trading Strategies**: Incorporates powerful methodologies, including Fibonacci retracement and MACD histogram analysis, to drive intelligent trading decisions.
- **Global Signal Coordination**: Maintains consistent buy and sell signals across all operations, ensuring coherent and unified trading logic.
- **Robust Error Handling and Logging**: Features comprehensive mechanisms for error detection, detailed logging, and troubleshooting, enabling users to monitor performance effectively.

  
# Release Notes (0.7.2) 
##### *[click for pre-production roadmap](https://github.com/users/firatoncu/projects/3/views/2?filterQuery=-status%3A%22In+review%22)*
- Cold Start Condition Check feature went live!
- Enhance backtesting pipeline with logging for input retrieval and strategy execution.
- Big Security Update! Implemented API keys encryption and decryption with AES-256-GCM with an encrypted password using PBKDF2 (with over 100.000 iterations.) 
- Enhance backtesting pipeline with user-defined balance, leverage, and fee rate inputs; improve error handling and user prompts.
- **Backtesting module** is Online!
- Now, Logger Module saves error logs on *error.log* file. 
- Bug fixes and major improvements
- Real-Time Strategy Tracking module & graphical updates on UI.
- Added strategy explanation to terminal UI.
- Enhanced position management to include Dynamic Capital Allocation.
- User-friendly Configuration Setup Page.

##
### Older Releases (< 0.7.0)
- Adaptive MACD & Signal Line Control.
- Global signal management for Buy/Sell conditions.
- Price values made more weighted than MACD values.
- Added Fibonnaci Retratement Strategy.
- Improvements in the code structure and execution logic.
- Using Market Order instead of Limit Order to avoid being traced.
- Windows Application released.
- **Asynchronous Operation**, enhancing performance and responsiveness.
- Update function definitions and logging for clarity.
- Buy and Sell condition checks to utilize Histogram checker.
- Improvements on Fibonacci logic for higher accuracy.
