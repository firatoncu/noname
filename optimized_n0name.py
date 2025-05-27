"""
Optimized Trading Bot Application with Performance Enhancements

This optimized version includes:
- Advanced caching mechanisms
- Memory usage optimization
- CPU-intensive operation optimization
- Database query optimization
- Performance profiling and monitoring
- Batch processing capabilities
"""

import warnings
import asyncio
import sys
import time
from binance import AsyncClient 
from utils.load_config import load_config
from utils.initial_adjustments import initial_adjustments 

# Enhanced logging and exception handling
from utils.enhanced_logging import get_logger, ErrorCategory, LogSeverity, log_performance
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

# Performance optimization imports
from utils.performance_optimizer import (
    get_cache_system, get_memory_optimizer, get_profiler, get_cpu_optimizer,
    profiled, cached, cleanup_performance_optimizers
)
from utils.optimized_fetch_data import (
    get_data_fetcher, batch_fetch_symbols_data, monitor_data_performance,
    cleanup_data_fetcher
)
from utils.optimized_database import (
    get_optimized_database, get_optimized_influxdb, cleanup_database_optimizers
)

from utils.current_status import current_status  
from src.optimized_open_position import optimized_open_position  # We'll create this
from auth.key_encryption import decrypt_api_keys
from utils.globals import get_error_counter, set_strategy_name
from utils.web_ui.project.api.main import start_server_and_updater
from utils.web_ui.npm_run_dev import start_frontend
from src.check_trending import check_trend  
from utils.influxdb.db_status_check import db_status_check

warnings.filterwarnings("ignore", category=FutureWarning)


@log_performance()
@profiled
async def initialize_binance_client(api_key: str, api_secret: str, logger):
    """Initialize Binance client with enhanced error handling and caching"""
    try:
        logger.info("Initializing Binance client")
        client = await AsyncClient.create(api_key, api_secret)
        logger.info("Binance client initialized successfully")
        return client
    except Exception as e:
        # Map standard exceptions to custom ones
        custom_exception = map_standard_exception(e)
        if isinstance(custom_exception, NetworkException):
            logger.error(
                "Failed to connect to Binance API",
                category=ErrorCategory.NETWORK,
                severity=LogSeverity.HIGH,
                extra={"api_endpoint": "binance.com"}
            )
        else:
            logger.error(
                "Failed to initialize Binance client",
                category=ErrorCategory.API,
                severity=LogSeverity.CRITICAL,
                extra={"error_type": type(e).__name__}
            )
        raise custom_exception


@handle_exceptions(fallback_value=None)
@profiled
async def load_and_validate_config(logger):
    """Load and validate configuration with enhanced error handling and caching"""
    try:
        logger.info("Loading configuration")
        config = load_config()
        
        # Validate required configuration
        required_keys = ['symbols', 'capital_tbu', 'api_keys', 'strategy_name']
        for key in required_keys:
            if key not in config:
                raise ConfigurationException(
                    f"Missing required configuration key: {key}",
                    config_key=key,
                    context=create_error_context(
                        component="config_loader",
                        operation="validate_config"
                    )
                )
        
        logger.info("Configuration loaded and validated successfully")
        return config
        
    except Exception as e:
        if not isinstance(e, ConfigurationException):
            raise ConfigurationException(
                "Failed to load configuration",
                original_exception=e,
                context=create_error_context(
                    component="config_loader",
                    operation="load_config"
                )
            )
        raise


@handle_exceptions()
@profiled
async def setup_strategy(strategy_name: str, logger):
    """Setup trading strategy with validation"""
    try:
        logger.info(f"Setting up strategy: {strategy_name}")
        
        if strategy_name == "Bollinger Bands & RSI":
            set_strategy_name("Bollinger Bands & RSI")
        else:
            set_strategy_name("MACD & Fibonacci")
        
        logger.audit(f"Strategy set to: {strategy_name}")
        
    except Exception as e:
        raise ConfigurationException(
            f"Failed to setup strategy: {strategy_name}",
            original_exception=e,
            context=create_error_context(
                component="strategy_manager",
                operation="setup_strategy",
                strategy=strategy_name
            )
        )


@handle_exceptions()
@profiled
async def initialize_services(symbols, client, logger):
    """Initialize all services with enhanced error handling"""
    try:
        logger.info("Starting frontend and backend services")
        
        # Start frontend
        npm_process = await start_frontend()
        logger.info("Frontend service started")
        
        # Start server and updater
        server_task, updater_task = await start_server_and_updater(symbols, client)
        logger.info("Server and updater services started")
        
        # Start trend checking
        check_trend_task = asyncio.create_task(check_trend(symbols, logger, client))
        logger.info("Trend checking service started")
        
        return npm_process, server_task, updater_task, check_trend_task
        
    except Exception as e:
        raise SystemException(
            "Failed to initialize services",
            original_exception=e,
            context=create_error_context(
                component="service_manager",
                operation="initialize_services"
            )
        )


@profiled
async def initialize_performance_systems(logger):
    """Initialize performance optimization systems"""
    try:
        logger.info("Initializing performance optimization systems")
        
        # Initialize cache system
        cache_system = get_cache_system()
        logger.info("Cache system initialized")
        
        # Initialize memory optimizer and start monitoring
        memory_optimizer = get_memory_optimizer()
        await memory_optimizer.start_monitoring()
        logger.info("Memory optimizer initialized and monitoring started")
        
        # Initialize profiler
        profiler = get_profiler()
        logger.info("Performance profiler initialized")
        
        # Initialize optimized database
        database = get_optimized_database()
        influxdb = get_optimized_influxdb()
        await influxdb.start_auto_flush()
        logger.info("Optimized database systems initialized")
        
        # Start data performance monitoring
        data_monitor_task = asyncio.create_task(monitor_data_performance())
        logger.info("Data performance monitoring started")
        
        return data_monitor_task
        
    except Exception as e:
        logger.error(f"Failed to initialize performance systems: {e}")
        raise


@profiled
async def optimized_trading_iteration(max_open_positions, symbols, client, leverage, logger):
    """Optimized trading iteration with performance enhancements"""
    try:
        # Use optimized open position function
        await optimized_open_position(max_open_positions, symbols, logger, client, leverage)
        
    except Exception as e:
        # Convert to custom exception for better handling
        custom_exception = map_standard_exception(e)
        
        if isinstance(custom_exception, NetworkException):
            logger.error(
                "Network error during trading iteration",
                category=ErrorCategory.NETWORK,
                severity=LogSeverity.HIGH
            )
        elif isinstance(custom_exception, APIException):
            logger.error(
                "API error during trading iteration",
                category=ErrorCategory.API,
                severity=LogSeverity.HIGH
            )
        else:
            logger.error(
                "Trading error during iteration",
                category=ErrorCategory.TRADING,
                severity=LogSeverity.MEDIUM
            )
        
        raise custom_exception


@profiled
async def performance_monitoring_loop(logger):
    """Background task for performance monitoring and reporting"""
    profiler = get_profiler()
    memory_optimizer = get_memory_optimizer()
    data_fetcher = get_data_fetcher()
    
    while True:
        try:
            # Generate performance report
            performance_report = profiler.get_performance_report()
            memory_stats = memory_optimizer.get_memory_usage()
            data_stats = data_fetcher.get_performance_stats()
            
            # Log performance summary
            logger.info(
                f"Performance Summary - "
                f"Memory: {memory_stats['rss_mb']:.1f}MB, "
                f"Cache Hit Rate: {data_stats['cache_hit_rate']:.2%}, "
                f"Avg Fetch Time: {data_stats['avg_fetch_time']:.3f}s"
            )
            
            # Identify bottlenecks
            bottlenecks = profiler.identify_bottlenecks(threshold_seconds=0.5)
            if bottlenecks:
                logger.warning(f"Performance bottlenecks detected: {', '.join(bottlenecks[:3])}")
            
            # Check memory usage
            if memory_stats['percent'] > 80:
                logger.warning(f"High memory usage: {memory_stats['percent']:.1f}%")
                memory_optimizer.force_garbage_collection()
            
            await asyncio.sleep(300)  # Report every 5 minutes
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in performance monitoring: {e}")
            await asyncio.sleep(60)


async def main():
    # Initialize enhanced logger with context
    logger = get_logger("optimized_main_application")
    recovery_manager = RecoveryManager(logger)
    
    # Create correlation ID for this session
    correlation_id = f"session_{int(time.time())}"
    
    with logger.context(
        component="optimized_main_application",
        correlation_id=correlation_id,
        session_type="optimized_trading_bot"
    ):
        try:
            logger.info("Starting optimized trading bot application")
            logger.audit("Optimized trading bot startup initiated")
            
            # Initialize performance systems first
            data_monitor_task = await initialize_performance_systems(logger)
            
            # Load and validate configuration
            config = await load_and_validate_config(logger)
            if not config:
                raise ConfigurationException("Failed to load configuration")
            
            # Extract configuration details with validation
            try:
                symbol_config = config['symbols']
                leverage = symbol_config['leverage']
                max_open_positions = symbol_config['max_open_positions']
                symbols = symbol_config['symbols']
                capital_tbu = config['capital_tbu']
                api_keys = config['api_keys']
                api_key = api_keys['api_key']
                api_secret = api_keys['api_secret']
                strategy_name = config['strategy_name']
                db_status = config['db_status']
                
                logger.info(
                    "Configuration extracted successfully",
                    extra={
                        "symbols_count": len(symbols),
                        "leverage": leverage,
                        "max_positions": max_open_positions,
                        "strategy": strategy_name
                    }
                )
                
            except KeyError as e:
                raise ConfigurationException(
                    f"Missing configuration key: {e}",
                    config_key=str(e),
                    context=create_error_context(
                        component="config_parser",
                        operation="extract_config"
                    )
                )
            
            # Setup strategy
            await setup_strategy(strategy_name, logger)
            
            # Check database status
            with logger.context(component="database"):
                await db_status_check(db_status)
                logger.info("Database status check completed")
            
            # Initialize Binance client
            with logger.context(component="binance_client"):
                client = await initialize_binance_client(api_key, api_secret, logger)
            
            # Perform initial adjustments
            with logger.context(component="initial_setup"):
                logger.info("Performing initial adjustments")
                await initial_adjustments(leverage, symbols, capital_tbu, client, logger)
                logger.info("Initial adjustments completed")
            
            # Initialize services
            services = await initialize_services(symbols, client, logger)
            npm_process, server_task, updater_task, check_trend_task = services
            
            # Start performance monitoring
            perf_monitor_task = asyncio.create_task(performance_monitoring_loop(logger))
            
            logger.audit("Optimized trading bot fully initialized and ready")
            logger.info("Starting optimized main trading loop")
            
            # Main trading loop with enhanced error handling and optimization
            error_count = 0
            max_errors = 3
            iteration_count = 0
            
            while error_count < max_errors:
                try:
                    iteration_start = time.time()
                    
                    with logger.context(
                        operation="optimized_trading_iteration",
                        iteration_time=iteration_start,
                        iteration_count=iteration_count
                    ):
                        await optimized_trading_iteration(
                            max_open_positions, symbols, client, leverage, logger
                        )
                    
                    iteration_time = time.time() - iteration_start
                    iteration_count += 1
                    
                    # Reset error count on successful iteration
                    if error_count > 0:
                        logger.info(f"Error count reset after successful iteration")
                        error_count = 0
                    
                    # Log performance metrics every 10 iterations
                    if iteration_count % 10 == 0:
                        logger.info(f"Completed {iteration_count} iterations, last took {iteration_time:.3f}s")
                    
                    await asyncio.sleep(1)  # Prevent tight looping
                    
                except TradingBotException as e:
                    error_count += 1
                    logger.error(
                        f"Trading bot exception (attempt {error_count}/{max_errors})",
                        category=ErrorCategory.TRADING,
                        severity=LogSeverity.HIGH,
                        extra=e.to_dict()
                    )
                    
                    # Try recovery
                    try:
                        await recovery_manager.handle_exception(
                            e, optimized_trading_iteration,
                            max_open_positions, symbols, client, leverage, logger
                        )
                        error_count = 0  # Reset on successful recovery
                    except Exception as recovery_error:
                        logger.error(
                            "Recovery failed",
                            category=ErrorCategory.SYSTEM,
                            severity=LogSeverity.CRITICAL,
                            extra={"recovery_error": str(recovery_error)}
                        )
                
                except Exception as e:
                    error_count += 1
                    custom_exception = map_standard_exception(e)
                    
                    logger.exception(
                        f"Unexpected error in main loop (attempt {error_count}/{max_errors})",
                        category=ErrorCategory.SYSTEM,
                        severity=LogSeverity.CRITICAL,
                        extra={
                            "error_type": type(e).__name__,
                            "error_message": str(e)
                        }
                    )
                    
                    # Break on critical errors
                    if error_count >= max_errors:
                        break
                    
                    # Wait before retry
                    await asyncio.sleep(5)
            
            if error_count >= max_errors:
                logger.critical(
                    "Maximum error count reached, shutting down",
                    category=ErrorCategory.SYSTEM,
                    severity=LogSeverity.CRITICAL,
                    extra={"max_errors": max_errors, "final_error_count": error_count}
                )
                logger.audit("Optimized trading bot shutdown due to excessive errors")
        
        except ConfigurationException as e:
            logger.critical(
                "Configuration error - cannot start application",
                category=ErrorCategory.CONFIGURATION,
                severity=LogSeverity.CRITICAL,
                extra=e.to_dict()
            )
            logger.audit("Optimized trading bot startup failed - configuration error")
            sys.exit(1)
            
        except SystemException as e:
            logger.critical(
                "System error during startup",
                category=ErrorCategory.SYSTEM,
                severity=LogSeverity.CRITICAL,
                extra=e.to_dict()
            )
            logger.audit("Optimized trading bot startup failed - system error")
            sys.exit(1)
            
        except Exception as e:
            logger.critical(
                "Fatal unexpected error during startup",
                category=ErrorCategory.SYSTEM,
                severity=LogSeverity.CRITICAL,
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            logger.audit("Optimized trading bot startup failed - unexpected error")
            sys.exit(1)
            
        finally:
            # Cleanup resources
            try:
                logger.info("Cleaning up resources")
                
                # Cancel monitoring tasks
                if 'data_monitor_task' in locals():
                    data_monitor_task.cancel()
                if 'perf_monitor_task' in locals():
                    perf_monitor_task.cancel()
                
                # Close client connection
                if 'client' in locals():
                    await client.close_connection()
                    logger.info("Binance client connection closed")
                
                # Cleanup performance optimizers
                await cleanup_performance_optimizers()
                await cleanup_data_fetcher()
                await cleanup_database_optimizers()
                
                logger.audit("Optimized trading bot shutdown completed")
                
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {cleanup_error}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1) 