
# n0name v0.4 by f0ncu

This repository contains **project n0name** designed for automated futures trading on Binance. The bot leverages the Binance API to execute trades based on configurable parameters. Built with Python..

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
    version : 0.4
  
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