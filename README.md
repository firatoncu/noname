
# n0name by f0ncu

This repository contains **project n0name** designed for automated futures trading on Binance. The bot leverages the Binance API to execute trades based on configurable parameters. Built with Python..

## Installation

### Prerequisites
- Python 3.8 or higher
- Binance API Key and Secret (obtainable from your Binance account)
- A Binance account with futures trading enabled

### Steps
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/firatoncu/noname.git
   cd noname
   ```

2. **Install Dependencies**: Ensure you have pip installed, then run:
   ```bash
   pip install -r requirements.txt
   ```


3. **Configurations**: 
-   Create noname/config.yml file in a text editor.  
-   Replace the placeholder values with your own Binance credentials:
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

4. **Run**:
* Navigate to the web directory: 
   ```bash
   cd noname
   python app.py
