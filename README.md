
# n0name v0.5 by f0ncu

This repository contains **project n0name** designed for automated Futures Trading on Binance. The bot leverages the Binance API to execute trades based on configurable parameters. Built with Python..

## Release Notes (0.5)
- Added Fibonnaci Retratement Strategy.
- Price values made more weighted than MACD values.
- Improvements in the code structure and execution logic.

## Installation

### Prerequisites
- Python 3.8 or higher
- Binance API Key and Secret with Futures Trading enabled

### Steps
1. **Configurations**: 
*   Create noname/config.yml file in a text editor, with structure below.  
*   Replace the placeholder values with your own Binance credentials and add desired symbols:
   ```yaml
  # config.yml
  version:
    version : 0.5
  
  symbols:
    symbols : ['ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'SUIUSDT']
    leverage : 3
    max_open_positions : 2
  
  api_keys:
    api_key : 'api_key'
    secret : 'secret'
   ```

2. **Run**:
   ```bash
   python app.py
   ```