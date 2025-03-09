import yaml # type: ignore

# Function to load the config file
def load_config(file_path='config.yml'):
    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print(f"Error: Config file '{file_path}' not found")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return None