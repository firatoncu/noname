import yaml # type: ignore

# Function to load the config file
def load_config(file_path='config.yml'):
    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    
    except FileNotFoundError:
        print(f"Config file '{file_path}' not found. Let's create a new one.")
        
        # Get user inputs
        config = {
            'symbols': {},
            'api_keys': {}
        }
        
        # Symbols configuration
        symbols_input = input("Enter symbols (comma-separated, e.g., ETHUSDT,SOLUSDT,XRPUSDT): ").strip()
        symbols_list = [s.strip() for s in symbols_input.split(',')]
        config['symbols']['symbols'] = symbols_list
        
        leverage = int(input("Enter leverage (e.g., 3): ").strip())
        config['symbols']['leverage'] = leverage
        
        max_positions = int(input("Enter max open positions (e.g., 2): ").strip())
        config['symbols']['max_open_positions'] = max_positions
        
        # API keys configuration
        api_key = input("Enter API key: ").strip()
        config['api_keys']['api_key'] = api_key
        
        secret = input("Enter secret key: ").strip()
        config['api_keys']['secret'] = secret
        
        # Save the new config file
        try:
            with open(file_path, 'w') as file:
                yaml.safe_dump(config, file, default_flow_style=False)
            print(f"New config file created at '{file_path}'")
            return config
        except Exception as e:
            print(f"Error saving new config file: {e}")
            return None
            
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return None

# Example usage
if __name__ == "__main__":
    config = load_config()
    if config:
        print("Config loaded successfully:", config)