import yaml  # type: ignore
import os
import sys
import time

def load_config(file_path='config.yml'):
    os.system("cls" if os.name == "nt" else "clear") 
    # Determine the base path (script dir or executable dir)
    if getattr(sys, 'frozen', False):  # Running as PyInstaller executable
        base_path = os.path.dirname(sys.executable)
    else:  # Running as a Python script
        base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, file_path)

    try:
        with open(full_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    
    except FileNotFoundError:
        print(f"\nConfig file '{full_path}' not found. Let's create a new one. \n \n")
        
        # Get user inputs
        config = {
            'symbols': {},
            'api_keys': {},
            'capital_tbu': float  # Default to use full balance 
        }
        
        # Symbols configuration
        symbols_input = input("Enter symbols (comma-separated, e.g., ETHUSDT,SOLUSDT,XRPUSDT): " ).strip() or -999
        time.sleep(1)
        if symbols_input == -999:
            print("No symbols entered, defaulting to BTCUSDT & ETHUSDT")
            symbols_input = "BTCUSDT,ETHUSDT"
        symbols_list = [s.strip() for s in symbols_input.split(',')]
        config['symbols']['symbols'] = symbols_list
        time.sleep(1)

        leverage = int(input("\nEnter leverage (e.g., 3): ").strip() or -999)
        time.sleep(1)
        if leverage == -999:
            leverage = 3
            print("Defaulting to 3x leverage")
        config['symbols']['leverage'] = leverage
        time.sleep(1)

        capital_tbu = float(input("\nCapital to be used (leave blank to use the full balance): ").strip() or -999) 
        time.sleep(1)
        if capital_tbu == -999:
            print("Using full balance")
        config['capital_tbu'] = capital_tbu
        time.sleep(1)

        max_positions = int(input("\nEnter max open positions (e.g., 2): ").strip() or -999)
        time.sleep(1)
        if max_positions == -999:
            max_positions = 2
            print("Defaulting to 2 max open positions")
        config['symbols']['max_open_positions'] = max_positions
        time.sleep(1)

        # API keys configuration
        api_key = input("\nEnter API key: ").strip()
        time.sleep(1)
        if not api_key:
            print("API key is required!")
            exit(1)
        config['api_keys']['api_key'] = api_key
        time.sleep(1)

        secret = input("\nEnter secret key: ").strip()
        time.sleep(1)
        if not secret:
            print("Secret key is required!")
            exit(1)
        config['api_keys']['secret'] = secret
        
        # Save the new config file
        try:
            with open(full_path, 'w') as file:
                yaml.safe_dump(config, file, default_flow_style=False)
            print(f"New config file created at '{full_path}'")
            return config
        except Exception as e:
            print(f"Error saving new config file: {e}")
            return None
            
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file (delete the config file and n0name will create a new one for you): {e}")
        return None