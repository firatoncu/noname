
# n0name v0.9.5 by f0ncu
This repository contains *project n0name* designed for automated Futures Trading on Binance. The bot leverages the Binance API to execute trades based on configurable parameters. Built with Python..

# Disclaimer

*The information provided by this bot is not intended to be and should not be construed as financial advice. Always conduct your own research and consult with a qualified financial advisor before making any trading decisions.Trading in cryptocurrencies and futures involves a high level of risk and may not be suitable for all investors. You should carefully consider your financial situation and risk tolerance before engaging in such activities.There are no guarantees of profit or avoidance of losses when using this bot. Past performance is not indicative of future results.You are solely responsible for any trades executed using this bot. The developers and contributors of this project are not liable for any financial losses or damages that may occur as a result of using this bot.Ensure that your use of this bot complies with all applicable laws and regulations in your jurisdiction. It is your responsibility to understand and adhere to any legal requirements related to cryptocurrency trading.*
#

# Description
n0name is an automated, multi-layered technical analysis system developed for traders. Thanks to its ability to monitor 12 different highly volatile cryptocurrencies on minute-based charts, numerous trades can be executed in the market and investment opportunities are continuously evaluated. The system generates both buy and sell signals by combining various technical tools such as the MACD indicator, histogram analysis, and Fibonacci levels.

The system executes trades using 3x leverage and targets a 1% profit on each trade. With a success rate of approximately 88%, and by maintaining an average risk/reward ratio of 1.5:5 in its orders, this structure not only helps control risk but also maximizes potential profit. With all these features combined, the robot is expected to deliver a daily return of between 3-4%.

In its trading strategy, the robot utilizes the trend and momentum data provided by the MACD. Clean signal if price area updates itself and create new highs or lows. Additionally, the analysis of the last 500 data points of the histogram helps to control abrupt price movements and extreme conditions. Fibonacci levels play a critical role in identifying price retracement and reversal points. Thanks to the harmonious operation of these three methods, signals are activated only when all conditions are met, preventing erroneous buy or sell decisions.

# Key Features

- Uses Python’s asyncio for non-blocking operations, enabling efficient handling of multiple symbols and tasks concurrently.
- Loads settings from a config file, including trading symbols, leverage, capital allocation, and maximum open positions. Creates a default config if none exists.
- Employs MACD (histogram breakout and signal line crossover) and Fibonacci retracement to determine trading signals.
- Monitors open positions, calculates quantities, and sets stop-loss and take-profit levels dynamically.
- Logs errors to a file and stops the bot after 3 errors to prevent erratic behavior.
- Optionally stores real-time trading data in InfluxDB for analysis.
- Displays real-time trading conditions and position statuses in the terminal using colored outputs.
- Encrypts Binance API keys using AES-256-GCM with a user-provided password, stored in an encrypted_keys.bin file.

# Strategy

*The trading strategy relies on three conditions for both buying and selling, evaluated over the last 500 1-minute candles:*

## Buy Conditions
### MACD Histogram Breakout :
The latest positive histogram value exceeds the 85th percentile of the last 500 positive histogram values, indicating strong upward momentum.
### Fibonacci Retracement Confirmation:
Price breaks above the 78.6% retracement level (from the lowest to highest price in the last 500 candles) with a significant gap (>1%) to the 61.8% level, confirming a bullish move.
### First Wave Signal:
Price breaks above highest value of current Fibonacci area . After an buy signal, price has to move at least %60 of current Fibonacci Area.

**Action: Opens a long position if all conditions are true and the max open positions limit isn’t reached.**

## Sell Conditions
### MACD Histogram Breakout:
The latest negative histogram value falls below the 85th percentile of the last 500 negative histogram values (absolute), indicating strong downward momentum.
### Fibonacci Retracement Confirmation:
Price drops below the 23.6% retracement level with a significant gap (>1%) to the 38.2% level, confirming a bearish move.
### First Wave Signal:
Price dips below lowest value of current Fibonacci area. After an sell signal, price has to move at least %60 of current Fibonacci Area.

**Action: Opens a short position if all conditions are true and the max open positions limit isn’t reached.**

## Risk Management

### Stop-Loss:
There are 2 types of Stop Loss values in new strategy.
*Soft Stop Loss Point*: %5 (gets activated if there is an cross-side signal)
*Hard Stop Loss Point*: %8.5


### Take-Profit:
Profit goal for every position is **%1.5** (%1 after fees.)


# Release Notes (0.9.5) 
##### *[click for pre-production roadmap](https://github.com/users/firatoncu/projects/3/views/2?filterQuery=-status%3A%22In+review%22)*
- Finalization of MACD Overlap & Fibonacci Retracement Strategy.
- Enhancements on UI.
- TradingView Integration completed. Added charts of open and historical positions.
- Implemented trend checking logic and created a new strategy "Volatile Trading"
- Big Strategy Update ! Wave prediction is way more stronger now.
- Added wallet and historical positions data models
- Enhance TradingConditionsCard with navigation buttons
- Added initial web UI project setup with Tailwind CSS, Vite, and React.
- Added Telegram Notification module.


##
### Older Releases (< 0.8.2)
- InfluxDB integration and notification status management.
- Positional improvements on condition table.
- Implemented Enhanced Stop Loss strategy.
- Streamline buy/sell condition checks while in-position status.
- Time synchronization feature added.
- Added Funding Fee management.
- Added InfluxDB Integration & Setup Pipeline for real-time data logging !
- Better Signal Initialization Logic for MACD conditions and clean Buy/Sell signals.
- Upgraded PPL(*Position Processing Logic*) to utilize Dynamic Stoploss values.
- Improved position value calculations and enhance balance checking.
- Cold Start Condition Check feature went live!
- Enhance backtesting pipeline with logging for input retrieval and strategy execution.
- **Backtesting module** is Online!
- Big Security Update! Implemented API keys encryption and decryption with AES-256-GCM with an encrypted password using PBKDF2 (with over 100.000 iterations.) 
- Enhance backtesting pipeline with user-defined balance, leverage, and fee rate inputs; improve error handling and user prompts.
- Now, Logger Module saves error logs on *error.log* file. 
- Bug fixes and major improvements
- Real-Time Strategy Tracking module & graphical updates on UI.
- Added strategy explanation to terminal UI.
- Enhanced position management to include Dynamic Capital Allocation.
- User-friendly Configuration Setup Page.
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
