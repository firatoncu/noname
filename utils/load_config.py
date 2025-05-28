"""
Simple configuration loading that only reads from config.yml.
No defaults, no fallbacks - if config.yml doesn't exist or is missing values, an error is raised.
"""
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


def load_config(file_path: str = 'config.yml') -> Dict[str, Any]:
    """
    Load configuration from config.yml file.
    
    Args:
        file_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid or missing required values
    """
    # Get the project root (parent of utils directory)
    project_root = Path(__file__).parent.parent
    config_path = project_root / file_path
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file: {e}")
    except Exception as e:
        raise ValueError(f"Error reading config file: {e}")
    
    if config is None:
        raise ValueError("Configuration file is empty")
    
    # Validate required keys exist
    required_keys = ['symbols', 'capital_tbu', 'api_keys', 'strategy_name']
    missing_keys = [key for key in required_keys if key not in config]
    
    if missing_keys:
        raise ValueError(f"Missing required configuration keys: {', '.join(missing_keys)}")
    
    return config


def get_db_status() -> str:
    """Get database status from config."""
    config = load_config()
    db_status = config.get('db_status')
    if db_status is None:
        raise ValueError("db_status not found in configuration")
    return db_status