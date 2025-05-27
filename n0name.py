"""
n0name Trading Bot - Main Entry Point

This module serves as the main entry point for the n0name automated trading bot.
It orchestrates the initialization and execution of all trading components including
strategy management, position monitoring, and risk management.

The bot implements a philosophical approach that combines human creativity and intuition
with computational power to identify patterns in market data and execute trades
based on configurable strategies.

Author: n0name Development Team
Version: 2.0.0
License: MIT

Example:
    Run the trading bot with default configuration:
        $ python n0name.py
    
    Run with specific configuration file:
        $ python n0name.py --config custom_config.yml
    
    Run in debug mode:
        $ python n0name.py --debug

Attributes:
    SUPPORTED_STRATEGIES (List[str]): List of supported trading strategies
    DEFAULT_CONFIG_PATH (str): Default configuration file path
    MAX_RETRY_ATTEMPTS (int): Maximum retry attempts for failed operations
"""

# Standard library imports
import warnings
import asyncio
import sys
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path

# Third-party imports
from binance import AsyncClient
from binance.exceptions import BinanceAPIException, BinanceRequestException

# Local imports - Configuration and utilities
from utils.load_config import load_config
from utils.initial_adjustments import initial_adjustments

# Enhanced logging and exception handling
from utils.enhanced_logging import (
    get_logger, 
    ErrorCategory, 
    LogSeverity, 
    log_performance,
    PerformanceLogger
)
from utils.exceptions import (
    TradingBotException,
    NetworkException,
    APIException,
    ConfigurationException,
    SystemException,
    RecoveryManager,
    handle_exceptions,
    create_error_context,
    map_standard_exception
)

# Backward compatibility - keep old imports working
from utils.app_logging import error_logger_func  # For backward compatibility

# Core trading components
from utils.current_status import current_status
from src.open_position import open_position
from auth.key_encryption import decrypt_api_keys
from utils.globals import get_error_counter, set_strategy_name
from utils.web_ui.project.api.main import start_server_and_updater
from utils.web_ui.npm_run_dev import start_frontend
from src.check_trending import check_trend
from utils.influxdb.db_status_check import db_status_check

# Suppress future warnings for cleaner output
warnings.filterwarnings("ignore", category=FutureWarning)

# Constants
SUPPORTED_STRATEGIES = ["Bollinger Bands & RSI", "MACD & Fibonacci"]
DEFAULT_CONFIG_PATH = "config.yml"
MAX_RETRY_ATTEMPTS = 3
HEALTH_CHECK_INTERVAL = 30  # seconds
POSITION_CHECK_INTERVAL = 5  # seconds


@log_performance()
async def initialize_binance_client(
    api_key: str, 
    api_secret: str, 
    logger: PerformanceLogger,
    testnet: bool = False
) -> AsyncClient:
    """
    Initialize Binance client with enhanced error handling and validation.
    
    This function creates and validates a connection to the Binance API,
    handling various connection scenarios and providing detailed error context.
    
    Args:
        api_key: Binance API key for authentication
        api_secret: Binance API secret for authentication  
        logger: Enhanced logger instance for structured logging
        testnet: Whether to use Binance testnet (default: False)
        
    Returns:
        AsyncClient: Initialized and validated Binance client
        
    Raises:
        NetworkException: If network connectivity issues occur
        APIException: If API authentication or permission issues occur
        ConfigurationException: If API credentials are invalid
        
    Example:
        >>> client = await initialize_binance_client(
        ...     api_key="your_api_key",
        ...     api_secret="your_api_secret", 
        ...     logger=logger
        ... )
        >>> account_info = await client.get_account()
    """
    try:
        logger.info(
            "Initializing Binance client",
            extra={
                "testnet": testnet,
                "api_key_length": len(api_key) if api_key else 0
            }
        )
        
        # Validate API credentials format
        if not api_key or not api_secret:
            raise ConfigurationException(
                "API credentials are missing or empty",
                config_key="api_credentials",
                context=create_error_context(
                    component="binance_client",
                    operation="validate_credentials"
                )
            )
        
        # Create client with appropriate endpoint
        client = await AsyncClient.create(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet
        )
        
        # Validate connection by fetching account info
        try:
            account_info = await client.get_account()
            logger.info(
                "Binance client initialized successfully",
                extra={
                    "account_type": account_info.get("accountType", "unknown"),
                    "can_trade": account_info.get("canTrade", False),
                    "permissions": account_info.get("permissions", [])
                }
            )
        except BinanceAPIException as e:
            if e.code == -2014:  # API key format invalid
                raise ConfigurationException(
                    "Invalid API key format",
                    config_key="api_key",
                    original_exception=e
                )
            elif e.code == -1022:  # Signature verification failed
                raise ConfigurationException(
                    "Invalid API secret or signature verification failed",
                    config_key="api_secret", 
                    original_exception=e
                )
            else:
                raise APIException(
                    f"Binance API error: {e.message}",
                    api_name="binance",
                    api_response={"code": e.code, "message": e.message},
                    original_exception=e
                )
        
        return client
        
    except Exception as e:
        # Map standard exceptions to custom ones for better handling
        custom_exception = map_standard_exception(e)
        
        if isinstance(custom_exception, NetworkException):
            logger.error(
                "Failed to connect to Binance API due to network issues",
                category=ErrorCategory.NETWORK,
                severity=LogSeverity.HIGH,
                extra={"api_endpoint": "api.binance.com"}
            )
        elif isinstance(custom_exception, (ConfigurationException, APIException)):
            # Already handled above, just re-raise
            pass
        else:
            logger.error(
                "Unexpected error during Binance client initialization",
                category=ErrorCategory.API,
                severity=LogSeverity.CRITICAL,
                extra={"error_type": type(e).__name__}
            )
        
        raise custom_exception


@handle_exceptions(fallback_value=None)
async def load_and_validate_config(logger: PerformanceLogger) -> Dict[str, Any]:
    """
    Load and validate configuration with comprehensive error handling.
    
    This function loads the trading bot configuration from file and validates
    all required parameters, providing detailed error messages for missing
    or invalid configuration values.
    
    Args:
        logger: Enhanced logger instance for structured logging
        
    Returns:
        Dict[str, Any]: Validated configuration dictionary
        
    Raises:
        ConfigurationException: If configuration is missing, invalid, or incomplete
        
    Example:
        >>> config = await load_and_validate_config(logger)
        >>> symbols = config['symbols']
        >>> strategy = config['strategy_name']
    """
    try:
        logger.info("Loading trading bot configuration")
        config = load_config()
        
        # Validate required configuration keys
        required_keys = [
            'symbols', 'capital_tbu', 'api_keys', 'strategy_name',
            'max_open_positions', 'leverage'
        ]
        
        missing_keys = []
        for key in required_keys:
            if key not in config:
                missing_keys.append(key)
        
        if missing_keys:
            raise ConfigurationException(
                f"Missing required configuration keys: {', '.join(missing_keys)}",
                config_key=missing_keys[0],  # First missing key for context
                context=create_error_context(
                    component="config_loader",
                    operation="validate_required_keys",
                    additional_data={"missing_keys": missing_keys}
                )
            )
        
        # Validate configuration values
        validation_errors = []
        
        # Validate symbols
        if not isinstance(config['symbols'], list) or len(config['symbols']) == 0:
            validation_errors.append("symbols must be a non-empty list")
        
        # Validate capital
        try:
            capital = float(config['capital_tbu'])
            if capital <= 0:
                validation_errors.append("capital_tbu must be positive")
        except (ValueError, TypeError):
            validation_errors.append("capital_tbu must be a valid number")
        
        # Validate strategy
        if config['strategy_name'] not in SUPPORTED_STRATEGIES:
            validation_errors.append(
                f"strategy_name must be one of: {', '.join(SUPPORTED_STRATEGIES)}"
            )
        
        # Validate max_open_positions
        try:
            max_positions = int(config['max_open_positions'])
            if max_positions <= 0:
                validation_errors.append("max_open_positions must be positive")
        except (ValueError, TypeError):
            validation_errors.append("max_open_positions must be a valid integer")
        
        # Validate leverage
        try:
            leverage = int(config['leverage'])
            if leverage < 1 or leverage > 125:  # Binance futures leverage limits
                validation_errors.append("leverage must be between 1 and 125")
        except (ValueError, TypeError):
            validation_errors.append("leverage must be a valid integer")
        
        if validation_errors:
            raise ConfigurationException(
                f"Configuration validation failed: {'; '.join(validation_errors)}",
                context=create_error_context(
                    component="config_loader",
                    operation="validate_config_values",
                    additional_data={"validation_errors": validation_errors}
                )
            )
        
        logger.info(
            "Configuration loaded and validated successfully",
            extra={
                "symbols_count": len(config['symbols']),
                "strategy": config['strategy_name'],
                "max_positions": config['max_open_positions'],
                "leverage": config['leverage']
            }
        )
        return config
        
    except Exception as e:
        if not isinstance(e, ConfigurationException):
            raise ConfigurationException(
                "Failed to load or validate configuration",
                original_exception=e,
                context=create_error_context(
                    component="config_loader",
                    operation="load_config"
                )
            )
        raise


@handle_exceptions()
async def setup_strategy(strategy_name: str, logger: PerformanceLogger) -> None:
    """
    Setup and validate trading strategy configuration.
    
    This function initializes the specified trading strategy and validates
    that all required components are available and properly configured.
    
    Args:
        strategy_name: Name of the trading strategy to setup
        logger: Enhanced logger instance for structured logging
        
    Raises:
        ConfigurationException: If strategy setup fails or strategy is invalid
        
    Example:
        >>> await setup_strategy("Bollinger Bands & RSI", logger)
    """
    try:
        logger.info(f"Setting up trading strategy: {strategy_name}")
        
        # Validate strategy name
        if strategy_name not in SUPPORTED_STRATEGIES:
            raise ConfigurationException(
                f"Unsupported strategy: {strategy_name}. "
                f"Supported strategies: {', '.join(SUPPORTED_STRATEGIES)}",
                context=create_error_context(
                    component="strategy_manager",
                    operation="validate_strategy",
                    additional_data={"requested_strategy": strategy_name}
                )
            )
        
        # Set global strategy name for other components
        if strategy_name == "Bollinger Bands & RSI":
            set_strategy_name("Bollinger Bands & RSI")
        else:
            set_strategy_name("MACD & Fibonacci")
        
        logger.audit(
            f"Trading strategy configured successfully: {strategy_name}",
            extra={"strategy": strategy_name}
        )
        
    except Exception as e:
        raise ConfigurationException(
            f"Failed to setup trading strategy: {strategy_name}",
            original_exception=e,
            context=create_error_context(
                component="strategy_manager",
                operation="setup_strategy",
                additional_data={"strategy": strategy_name}
            )
        )


@handle_exceptions()
async def initialize_services(
    symbols: List[str], 
    client: AsyncClient, 
    logger: PerformanceLogger
) -> Tuple[Any, Any, Any, Any]:
    """
    Initialize all required services for the trading bot.
    
    This function starts the frontend interface, backend API server,
    data updater service, and trend checking service in the correct order
    with proper error handling.
    
    Args:
        symbols: List of trading symbols to monitor
        client: Initialized Binance client
        logger: Enhanced logger instance for structured logging
        
    Returns:
        Tuple containing:
            - npm_process: Frontend process handle
            - server_task: Backend server task
            - updater_task: Data updater task  
            - check_trend_task: Trend checking task
            
    Raises:
        SystemException: If any service fails to initialize
        
    Example:
        >>> services = await initialize_services(
        ...     symbols=["BTCUSDT", "ETHUSDT"],
        ...     client=binance_client,
        ...     logger=logger
        ... )
        >>> npm_process, server_task, updater_task, trend_task = services
    """
    try:
        logger.info(
            "Initializing trading bot services",
            extra={"symbols_count": len(symbols)}
        )
        
        # Start frontend service
        logger.info("Starting frontend service...")
        npm_process = await start_frontend()
        if npm_process:
            logger.info("Frontend service started successfully")
        else:
            logger.warning("Frontend service failed to start")
        
        # Start backend server and data updater
        logger.info("Starting backend services...")
        server_task, updater_task = await start_server_and_updater(symbols, client)
        logger.info("Backend server and data updater started successfully")
        
        # Start trend checking service
        logger.info("Starting trend analysis service...")
        check_trend_task = asyncio.create_task(
            check_trend(symbols, logger, client)
        )
        logger.info("Trend analysis service started successfully")
        
        logger.info(
            "All services initialized successfully",
            extra={
                "frontend_running": npm_process is not None,
                "backend_running": server_task is not None,
                "updater_running": updater_task is not None,
                "trend_analysis_running": check_trend_task is not None
            }
        )
        
        return npm_process, server_task, updater_task, check_trend_task
        
    except Exception as e:
        raise SystemException(
            "Failed to initialize one or more services",
            original_exception=e,
            context=create_error_context(
                component="service_manager",
                operation="initialize_services",
                additional_data={"symbols": symbols}
            )
        )


async def trading_iteration(
    max_open_positions: int,
    symbols: List[str],
    client: AsyncClient,
    leverage: int,
    logger: PerformanceLogger
) -> None:
    """
    Execute a single trading iteration with comprehensive error handling.
    
    This function represents one cycle of the trading loop, where the bot
    analyzes market conditions and potentially opens new positions based
    on the configured strategy.
    
    Args:
        max_open_positions: Maximum number of concurrent open positions
        symbols: List of trading symbols to analyze
        client: Binance client for API operations
        leverage: Trading leverage to use
        logger: Enhanced logger instance for structured logging
        
    Raises:
        NetworkException: If network connectivity issues occur
        APIException: If API errors occur during trading
        TradingException: If trading-specific errors occur
        
    Example:
        >>> await trading_iteration(
        ...     max_open_positions=5,
        ...     symbols=["BTCUSDT", "ETHUSDT"],
        ...     client=binance_client,
        ...     leverage=10,
        ...     logger=logger
        ... )
    """
    try:
        # Execute the main trading logic
        await open_position(max_open_positions, symbols, logger, client, leverage)
        
    except Exception as e:
        # Convert to custom exception for better handling
        custom_exception = map_standard_exception(e)
        
        if isinstance(custom_exception, NetworkException):
            logger.error(
                "Network error during trading iteration",
                category=ErrorCategory.NETWORK,
                severity=LogSeverity.HIGH,
                extra={
                    "symbols": symbols,
                    "max_positions": max_open_positions
                }
            )
        elif isinstance(custom_exception, APIException):
            logger.error(
                "API error during trading iteration", 
                category=ErrorCategory.API,
                severity=LogSeverity.HIGH,
                extra={
                    "symbols": symbols,
                    "leverage": leverage
                }
            )
        else:
            logger.error(
                "Trading error during iteration",
                category=ErrorCategory.TRADING,
                severity=LogSeverity.MEDIUM,
                extra={
                    "symbols": symbols,
                    "error_type": type(e).__name__
                }
            )
        
        raise custom_exception


async def health_check_loop(
    client: AsyncClient,
    logger: PerformanceLogger,
    check_interval: int = HEALTH_CHECK_INTERVAL
) -> None:
    """
    Continuous health check loop for monitoring system status.
    
    This function runs in the background to monitor the health of various
    system components including API connectivity, database status, and
    system resources.
    
    Args:
        client: Binance client for API health checks
        logger: Enhanced logger instance for structured logging
        check_interval: Interval between health checks in seconds
        
    Note:
        This function runs indefinitely until the main process is terminated.
        
    Example:
        >>> health_task = asyncio.create_task(
        ...     health_check_loop(client, logger, 30)
        ... )
    """
    while True:
        try:
            # Check API connectivity
            try:
                await client.ping()
                api_status = "healthy"
            except Exception:
                api_status = "unhealthy"
            
            # Check database status
            db_status = await db_status_check()
            
            # Log health status
            logger.info(
                "System health check completed",
                extra={
                    "api_status": api_status,
                    "database_status": db_status,
                    "timestamp": time.time()
                }
            )
            
            # Wait for next check
            await asyncio.sleep(check_interval)
            
        except Exception as e:
            logger.error(
                "Error during health check",
                category=ErrorCategory.SYSTEM,
                severity=LogSeverity.MEDIUM,
                extra={"error": str(e)}
            )
            await asyncio.sleep(check_interval)


async def main() -> None:
    """
    Main entry point for the n0name trading bot application.
    
    This function orchestrates the complete lifecycle of the trading bot including:
    - Configuration loading and validation
    - API client initialization
    - Service startup (frontend, backend, monitoring)
    - Main trading loop execution
    - Graceful shutdown handling
    
    The function implements comprehensive error handling and recovery mechanisms
    to ensure robust operation in production environments.
    
    Raises:
        SystemExit: On critical errors that prevent bot operation
        
    Example:
        >>> await main()  # Start the trading bot
        
    Note:
        This function runs indefinitely until interrupted by user or system.
        Use Ctrl+C to gracefully shutdown the bot.
    """
    # Initialize enhanced logger with context
    logger = get_logger(
        __name__,
        context={
            "component": "main",
            "version": "2.0.0",
            "startup_time": time.time()
        }
    )
    
    # Initialize recovery manager for handling critical errors
    recovery_manager = RecoveryManager(logger=logger)
    
    # Track startup metrics
    startup_start_time = time.time()
    
    try:
        logger.info(
            "Starting n0name Trading Bot",
            extra={
                "version": "2.0.0",
                "python_version": sys.version,
                "platform": sys.platform
            }
        )
        
        # Step 1: Load and validate configuration
        logger.info("Step 1: Loading configuration...")
        config = await load_and_validate_config(logger)
        if not config:
            logger.critical("Failed to load configuration - exiting")
            sys.exit(1)
        
        # Extract configuration values with type safety
        symbols: List[str] = config['symbols']
        capital_tbu: float = float(config['capital_tbu'])
        strategy_name: str = config['strategy_name']
        max_open_positions: int = int(config['max_open_positions'])
        leverage: int = int(config['leverage'])
        
        logger.info(
            "Configuration loaded successfully",
            extra={
                "symbols": symbols,
                "capital": capital_tbu,
                "strategy": strategy_name,
                "max_positions": max_open_positions,
                "leverage": leverage
            }
        )
        
        # Step 2: Setup trading strategy
        logger.info("Step 2: Setting up trading strategy...")
        await setup_strategy(strategy_name, logger)
        
        # Step 3: Initialize API credentials
        logger.info("Step 3: Initializing API credentials...")
        try:
            api_key, api_secret = decrypt_api_keys(config['api_keys'])
            if not api_key or not api_secret:
                raise ConfigurationException(
                    "Failed to decrypt API credentials",
                    config_key="api_keys"
                )
        except Exception as e:
            logger.error(
                "Failed to decrypt API credentials",
                category=ErrorCategory.SECURITY,
                severity=LogSeverity.CRITICAL,
                extra={"error": str(e)}
            )
            raise ConfigurationException(
                "API credential decryption failed",
                original_exception=e
            )
        
        # Step 4: Initialize Binance client
        logger.info("Step 4: Initializing Binance client...")
        client = await initialize_binance_client(
            api_key=api_key,
            api_secret=api_secret,
            logger=logger,
            testnet=config.get('testnet', False)
        )
        
        # Step 5: Perform initial adjustments and validations
        logger.info("Step 5: Performing initial system adjustments...")
        try:
            await initial_adjustments(client, symbols, logger)
        except Exception as e:
            logger.warning(
                "Initial adjustments failed - continuing with caution",
                extra={"error": str(e)}
            )
        
        # Step 6: Initialize all services
        logger.info("Step 6: Initializing services...")
        npm_process, server_task, updater_task, check_trend_task = await initialize_services(
            symbols=symbols,
            client=client,
            logger=logger
        )
        
        # Step 7: Start health monitoring
        logger.info("Step 7: Starting health monitoring...")
        health_task = asyncio.create_task(
            health_check_loop(client, logger, HEALTH_CHECK_INTERVAL)
        )
        
        # Calculate and log startup time
        startup_time = time.time() - startup_start_time
        logger.info(
            "n0name Trading Bot started successfully",
            extra={
                "startup_time_seconds": round(startup_time, 2),
                "services_running": {
                    "frontend": npm_process is not None,
                    "backend": server_task is not None,
                    "updater": updater_task is not None,
                    "trend_analysis": check_trend_task is not None,
                    "health_monitor": health_task is not None
                }
            }
        )
        
        # Step 8: Main trading loop
        logger.info("Step 8: Starting main trading loop...")
        iteration_count = 0
        last_status_log = time.time()
        status_log_interval = 300  # Log status every 5 minutes
        
        while True:
            try:
                iteration_start_time = time.time()
                iteration_count += 1
                
                # Log periodic status
                current_time = time.time()
                if current_time - last_status_log >= status_log_interval:
                    logger.info(
                        "Trading bot status update",
                        extra={
                            "iteration_count": iteration_count,
                            "uptime_seconds": round(current_time - startup_start_time, 2),
                            "error_count": get_error_counter()
                        }
                    )
                    last_status_log = current_time
                
                # Execute trading iteration
                await trading_iteration(
                    max_open_positions=max_open_positions,
                    symbols=symbols,
                    client=client,
                    leverage=leverage,
                    logger=logger
                )
                
                # Log iteration performance
                iteration_time = time.time() - iteration_start_time
                if iteration_time > 10:  # Log slow iterations
                    logger.warning(
                        "Slow trading iteration detected",
                        extra={
                            "iteration_time_seconds": round(iteration_time, 2),
                            "iteration_number": iteration_count
                        }
                    )
                
                # Brief pause between iterations to prevent excessive API calls
                await asyncio.sleep(POSITION_CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Received shutdown signal - initiating graceful shutdown")
                break
                
            except (NetworkException, APIException) as e:
                # Handle recoverable errors with exponential backoff
                retry_delay = min(60, 2 ** min(5, e.retry_count if hasattr(e, 'retry_count') else 0))
                logger.warning(
                    f"Recoverable error in trading loop - retrying in {retry_delay}s",
                    category=e.category,
                    severity=LogSeverity.MEDIUM,
                    extra={
                        "error_type": type(e).__name__,
                        "retry_delay": retry_delay,
                        "iteration": iteration_count
                    }
                )
                await asyncio.sleep(retry_delay)
                
            except TradingBotException as e:
                # Handle custom exceptions with recovery
                if e.recoverable:
                    retry_delay = e.retry_after or 30
                    logger.error(
                        f"Recoverable trading error - retrying in {retry_delay}s",
                        category=e.category,
                        severity=e.severity,
                        extra={
                            "error_code": e.error_code,
                            "retry_delay": retry_delay,
                            "iteration": iteration_count
                        }
                    )
                    await asyncio.sleep(retry_delay)
                else:
                    logger.critical(
                        "Non-recoverable error in trading loop - shutting down",
                        category=e.category,
                        severity=LogSeverity.CRITICAL,
                        extra={
                            "error_code": e.error_code,
                            "iteration": iteration_count
                        }
                    )
                    break
                    
            except Exception as e:
                # Handle unexpected errors
                logger.error(
                    "Unexpected error in trading loop",
                    category=ErrorCategory.SYSTEM,
                    severity=LogSeverity.HIGH,
                    extra={
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "iteration": iteration_count
                    }
                )
                
                # Use recovery manager for critical errors
                if not await recovery_manager.handle_error(e):
                    logger.critical("Recovery failed - shutting down")
                    break
                
                await asyncio.sleep(30)  # Wait before retry
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt - initiating shutdown")
        
    except SystemExit:
        logger.info("System exit requested")
        
    except Exception as e:
        logger.critical(
            "Critical error during startup",
            category=ErrorCategory.SYSTEM,
            severity=LogSeverity.CRITICAL,
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
        sys.exit(1)
        
    finally:
        # Graceful shutdown sequence
        logger.info("Initiating graceful shutdown...")
        
        try:
            # Cancel all running tasks
            tasks_to_cancel = []
            
            # Collect all tasks that need cancellation
            if 'health_task' in locals() and not health_task.done():
                tasks_to_cancel.append(health_task)
            if 'check_trend_task' in locals() and not check_trend_task.done():
                tasks_to_cancel.append(check_trend_task)
            if 'server_task' in locals() and not server_task.done():
                tasks_to_cancel.append(server_task)
            if 'updater_task' in locals() and not updater_task.done():
                tasks_to_cancel.append(updater_task)
            
            # Cancel tasks gracefully
            if tasks_to_cancel:
                logger.info(f"Cancelling {len(tasks_to_cancel)} background tasks...")
                for task in tasks_to_cancel:
                    task.cancel()
                
                # Wait for tasks to complete cancellation
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*tasks_to_cancel, return_exceptions=True),
                        timeout=10.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("Some tasks did not cancel within timeout")
            
            # Close Binance client
            if 'client' in locals():
                logger.info("Closing Binance client connection...")
                await client.close_connection()
            
            # Terminate frontend process
            if 'npm_process' in locals() and npm_process:
                logger.info("Terminating frontend process...")
                try:
                    npm_process.terminate()
                    await asyncio.sleep(2)  # Give it time to terminate gracefully
                    if npm_process.poll() is None:
                        npm_process.kill()
                except Exception as e:
                    logger.warning(f"Error terminating frontend process: {e}")
            
            # Final status log
            total_runtime = time.time() - startup_start_time
            logger.info(
                "n0name Trading Bot shutdown completed",
                extra={
                    "total_runtime_seconds": round(total_runtime, 2),
                    "total_iterations": iteration_count if 'iteration_count' in locals() else 0,
                    "final_error_count": get_error_counter()
                }
            )
            
        except Exception as e:
            logger.error(
                "Error during shutdown sequence",
                extra={"error": str(e)}
            )


if __name__ == "__main__":
    """
    Entry point when script is run directly.
    
    This block handles command-line execution and sets up the async event loop
    for the main application function.
    """
    try:
        # Set up event loop policy for Windows compatibility
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Run the main application
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)