"""
Modern configuration loading system with backward compatibility.
This module provides a bridge between the old load_config function and the new ConfigManager.
"""
import warnings
from typing import Dict, Any, Optional
from .config_manager import get_config_manager, ConfigManager, ConfigurationError
from .config_models import AppConfig


def load_config(file_path: str = 'config.yml') -> Optional[Dict[str, Any]]:
    """
    Legacy function for backward compatibility.
    
    Args:
        file_path: Path to the configuration file
        
    Returns:
        Configuration dictionary or None if failed
        
    Note:
        This function is deprecated. Use ConfigManager directly for new code.
    """
    warnings.warn(
        "load_config() is deprecated. Use ConfigManager or get_config() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        # Use the new configuration manager
        config_manager = get_config_manager(
            config_file=file_path,
            auto_create=True,
            enable_hot_reload=False
        )
        
        config = config_manager.get_config()
        
        # Convert Pydantic model to dictionary for backward compatibility
        config_dict = config.dict()
        
        # Handle SecretStr for backward compatibility
        if 'api_keys' in config_dict and 'api_secret' in config_dict['api_keys']:
            config_dict['api_keys']['api_secret'] = config.api_keys.api_secret.get_secret_value()
        
        return config_dict
        
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error loading configuration: {e}")
        return None


# New recommended functions for modern usage
def get_config() -> AppConfig:
    """
    Get the current configuration using the modern ConfigManager.
    
    Returns:
        AppConfig: Validated configuration object
        
    Raises:
        ConfigurationError: If configuration cannot be loaded or is invalid
    """
    return get_config_manager().get_config()


def create_config_manager(
    config_file: str = "config.yml",
    env_file: str = ".env",
    env_prefix: str = "NONAME_",
    enable_hot_reload: bool = False,
    auto_create: bool = True
) -> ConfigManager:
    """
    Create a new configuration manager with custom settings.
    
    Args:
        config_file: Path to the configuration file
        env_file: Path to the environment file
        env_prefix: Prefix for environment variables
        enable_hot_reload: Enable hot-reloading of configuration
        auto_create: Automatically create config file if it doesn't exist
        
    Returns:
        ConfigManager: Configured manager instance
    """
    return ConfigManager(
        config_file=config_file,
        env_file=env_file,
        env_prefix=env_prefix,
        enable_hot_reload=enable_hot_reload,
        auto_create=auto_create
    )


def update_config(**kwargs) -> None:
    """
    Update configuration with new values.
    
    Args:
        **kwargs: Configuration values to update
        
    Example:
        update_config(username="NewUser", leverage=5)
        update_config(**{"symbols.leverage": 10})  # Nested updates
        
    Raises:
        ConfigurationError: If update fails or validation errors occur
    """
    get_config_manager().update_config(**kwargs)


def reload_config() -> None:
    """
    Reload configuration from all sources.
    
    Raises:
        ConfigurationError: If reload fails
    """
    get_config_manager().reload_config()


def save_config(config: Optional[AppConfig] = None) -> None:
    """
    Save configuration to file.
    
    Args:
        config: Configuration to save (uses current if None)
        
    Raises:
        ConfigurationError: If save fails
    """
    get_config_manager().save_config(config)


# Backward compatibility aliases
def get_api_keys() -> Dict[str, str]:
    """Get API keys from configuration."""
    config = get_config()
    return {
        'api_key': config.api_keys.api_key,
        'api_secret': config.api_keys.api_secret.get_secret_value()
    }


def get_telegram_config() -> Dict[str, Any]:
    """Get Telegram configuration."""
    config = get_config()
    return {
        'token': config.telegram.token,
        'chat_id': config.telegram.chat_id
    }


def get_symbols_config() -> Dict[str, Any]:
    """Get symbols configuration."""
    config = get_config()
    return {
        'symbols': config.symbols.symbols,
        'leverage': config.symbols.leverage,
        'max_open_positions': config.symbols.max_open_positions
    }


def get_capital() -> float:
    """Get capital to be used."""
    return get_config().capital_tbu


def get_username() -> str:
    """Get username."""
    return get_config().username


def get_strategy_name() -> str:
    """Get strategy name."""
    return get_config().strategy_name


def get_db_status() -> str:
    """Get database status."""
    return get_config().db_status