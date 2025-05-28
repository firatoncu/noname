"""
Main dependency injection container for the n0name trading bot.

This module defines the central IoC container that manages all dependencies
and their lifecycles throughout the application.
"""

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
from typing import Dict, Any, Optional

from ..config.manager import ConfigManager
from ..config.models import TradingConfig, DatabaseConfig, SecurityConfig
from ..services.binance_service import BinanceService
from ..services.notification_service import NotificationService
from ..services.monitoring_service import MonitoringService
from ..services.database_service import DatabaseService
from ..services.cache_service import CacheService
from ..services.logging_service import LoggingService
from ..core.trading_engine import TradingEngine
from ..core.position_manager import PositionManager
from ..core.order_manager import OrderManager
from ..core.risk_manager import RiskManager
from ..strategies.factory import StrategyFactory
from ..data.market_data_provider import MarketDataProvider
from ..monitoring.metrics_collector import MetricsCollector
from ..monitoring.alert_manager import AlertManager


class Container(containers.DeclarativeContainer):
    """
    Main dependency injection container.
    
    This container manages all application dependencies and their lifecycles,
    providing a centralized way to configure and inject dependencies.
    """
    
    # Configuration
    config = providers.Configuration()
    
    # Configuration Manager
    config_manager = providers.Singleton(
        ConfigManager,
        config_path=config.config_path,
        environment=config.environment,
    )
    
    # Core Configuration Models
    trading_config = providers.Factory(
        TradingConfig,
        **config.trading
    )
    
    database_config = providers.Factory(
        DatabaseConfig,
        **config.database
    )
    
    security_config = providers.Factory(
        SecurityConfig,
        **config.security
    )
    
    # Logging Service
    logging_service = providers.Singleton(
        LoggingService,
        config=config.logging,
        environment=config.environment,
    )
    
    # Cache Service
    cache_service = providers.Singleton(
        CacheService,
        config=config.cache,
        logger=logging_service,
    )
    
    # Database Service
    database_service = providers.Singleton(
        DatabaseService,
        config=database_config,
        logger=logging_service,
    )
    
    # Exchange Services
    binance_service = providers.Singleton(
        BinanceService,
        api_key=config.binance.api_key,
        api_secret=config.binance.api_secret,
        testnet=config.binance.testnet,
        logger=logging_service,
        cache_service=cache_service,
    )
    
    # Market Data Provider
    market_data_provider = providers.Singleton(
        MarketDataProvider,
        exchange_service=binance_service,
        cache_service=cache_service,
        logger=logging_service,
    )
    
    # Risk Manager
    risk_manager = providers.Singleton(
        RiskManager,
        config=trading_config,
        logger=logging_service,
    )
    
    # Order Manager
    order_manager = providers.Singleton(
        OrderManager,
        exchange_service=binance_service,
        database_service=database_service,
        logger=logging_service,
        risk_manager=risk_manager,
    )
    
    # Position Manager
    position_manager = providers.Singleton(
        PositionManager,
        exchange_service=binance_service,
        database_service=database_service,
        order_manager=order_manager,
        logger=logging_service,
    )
    
    # Strategy Factory
    strategy_factory = providers.Singleton(
        StrategyFactory,
        config=trading_config,
        logger=logging_service,
    )
    
    # Trading Engine
    trading_engine = providers.Singleton(
        TradingEngine,
        position_manager=position_manager,
        order_manager=order_manager,
        market_data_provider=market_data_provider,
        risk_manager=risk_manager,
        strategy_factory=strategy_factory,
        config=trading_config,
        logger=logging_service,
    )
    
    # Monitoring Services
    metrics_collector = providers.Singleton(
        MetricsCollector,
        config=config.monitoring,
        logger=logging_service,
    )
    
    alert_manager = providers.Singleton(
        AlertManager,
        config=config.alerts,
        notification_service=providers.Factory(
            NotificationService,
            config=config.notifications,
            logger=logging_service,
        ),
        logger=logging_service,
    )
    
    monitoring_service = providers.Singleton(
        MonitoringService,
        metrics_collector=metrics_collector,
        alert_manager=alert_manager,
        database_service=database_service,
        logger=logging_service,
    )
    
    # Notification Service
    notification_service = providers.Singleton(
        NotificationService,
        config=config.notifications,
        logger=logging_service,
    )
    
    @classmethod
    def create_container(
        cls, 
        config_dict: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
        environment: str = "development"
    ) -> "Container":
        """
        Create and configure a new container instance.
        
        Args:
            config_dict: Configuration dictionary
            config_path: Path to configuration file
            environment: Environment name (development, production, testing)
            
        Returns:
            Configured container instance
        """
        container = cls()
        
        # Configure the container
        if config_dict:
            container.config.from_dict(config_dict)
        elif config_path:
            container.config.from_yaml(config_path)
        else:
            # Load default configuration
            container.config.from_yaml("config/default.yml")
        
        # Set environment-specific overrides
        container.config.environment.from_value(environment)
        container.config.config_path.from_value(config_path or "config/default.yml")
        
        # Wire the container
        container.wire(modules=[
            "n0name.main",
            "n0name.cli",
            "n0name.core",
            "n0name.services",
            "n0name.strategies",
            "n0name.monitoring",
        ])
        
        return container
    
    def get_trading_engine(self) -> TradingEngine:
        """Get the trading engine instance."""
        return self.trading_engine()
    
    def get_config_manager(self) -> ConfigManager:
        """Get the configuration manager instance."""
        return self.config_manager()
    
    def get_logger(self) -> LoggingService:
        """Get the logging service instance."""
        return self.logging_service()
    
    def get_monitoring_service(self) -> MonitoringService:
        """Get the monitoring service instance."""
        return self.monitoring_service()
    
    def shutdown(self) -> None:
        """
        Shutdown the container and clean up resources.
        
        This method should be called when the application is shutting down
        to ensure proper cleanup of all resources.
        """
        # Close database connections
        if hasattr(self, '_database_service'):
            self.database_service().close()
        
        # Close exchange connections
        if hasattr(self, '_binance_service'):
            self.binance_service().close()
        
        # Stop monitoring services
        if hasattr(self, '_monitoring_service'):
            self.monitoring_service().stop()
        
        # Clear cache
        if hasattr(self, '_cache_service'):
            self.cache_service().clear()


# Global container instance
container: Optional[Container] = None


def get_container() -> Container:
    """
    Get the global container instance.
    
    Returns:
        Global container instance
        
    Raises:
        RuntimeError: If container is not initialized
    """
    global container
    if container is None:
        raise RuntimeError("Container not initialized. Call initialize_container() first.")
    return container


def initialize_container(
    config_dict: Optional[Dict[str, Any]] = None,
    config_path: Optional[str] = None,
    environment: str = "development"
) -> Container:
    """
    Initialize the global container instance.
    
    Args:
        config_dict: Configuration dictionary
        config_path: Path to configuration file
        environment: Environment name
        
    Returns:
        Initialized container instance
    """
    global container
    container = Container.create_container(
        config_dict=config_dict,
        config_path=config_path,
        environment=environment
    )
    return container


def shutdown_container() -> None:
    """Shutdown the global container instance."""
    global container
    if container is not None:
        container.shutdown()
        container = None


# Dependency injection decorators for common services
def inject_trading_engine(func):
    """Decorator to inject trading engine dependency."""
    return inject(func, trading_engine=Provide[Container.trading_engine])


def inject_logger(func):
    """Decorator to inject logger dependency."""
    return inject(func, logger=Provide[Container.logging_service])


def inject_config(func):
    """Decorator to inject configuration dependency."""
    return inject(func, config=Provide[Container.config_manager])


def inject_monitoring(func):
    """Decorator to inject monitoring service dependency."""
    return inject(func, monitoring=Provide[Container.monitoring_service]) 