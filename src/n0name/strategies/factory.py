"""
Strategy Factory for creating and managing trading strategies.

This module implements the Factory Pattern for creating trading strategies,
providing a centralized way to instantiate and configure strategies.
"""

from typing import Dict, Type, Any, Optional, List
from abc import ABC, abstractmethod
import importlib
import inspect

from ..interfaces.trading_protocols import TradingStrategyProtocol
from ..config.models import StrategyConfig, StrategyType
from ..types import StrategyName, StrategyParameters
from ..exceptions import ConfigurationException, StrategyException
from .registry import StrategyRegistry


class StrategyFactoryProtocol(ABC):
    """Protocol for strategy factories."""
    
    @abstractmethod
    def create_strategy(
        self, 
        strategy_config: StrategyConfig,
        **kwargs: Any
    ) -> TradingStrategyProtocol:
        """Create a strategy instance."""
        ...
    
    @abstractmethod
    def register_strategy(
        self, 
        strategy_type: StrategyType, 
        strategy_class: Type[TradingStrategyProtocol]
    ) -> None:
        """Register a strategy class."""
        ...
    
    @abstractmethod
    def get_available_strategies(self) -> List[StrategyType]:
        """Get list of available strategy types."""
        ...


class StrategyFactory(StrategyFactoryProtocol):
    """
    Factory for creating trading strategies.
    
    This factory provides a centralized way to create and configure trading strategies,
    supporting both built-in and custom strategies through a registration system.
    """
    
    def __init__(self, logger=None):
        """
        Initialize the strategy factory.
        
        Args:
            logger: Logger instance for logging factory operations
        """
        self.logger = logger
        self._registry = StrategyRegistry()
        self._initialized = False
        
        # Initialize built-in strategies
        self._initialize_builtin_strategies()
    
    def _initialize_builtin_strategies(self) -> None:
        """Initialize and register built-in strategies."""
        try:
            # Import and register built-in strategies
            from .bollinger_rsi import BollingerRSIStrategy
            from .macd_fibonacci import MACDFibonacciStrategy
            
            self._registry.register(StrategyType.BOLLINGER_RSI, BollingerRSIStrategy)
            self._registry.register(StrategyType.MACD_FIBONACCI, MACDFibonacciStrategy)
            
            self._initialized = True
            
            if self.logger:
                self.logger.info(
                    f"Initialized strategy factory with {len(self._registry.get_registered_strategies())} strategies"
                )
                
        except ImportError as e:
            error_msg = f"Failed to import built-in strategies: {e}"
            if self.logger:
                self.logger.error(error_msg)
            raise ConfigurationException(error_msg)
    
    def create_strategy(
        self, 
        strategy_config: StrategyConfig,
        **kwargs: Any
    ) -> TradingStrategyProtocol:
        """
        Create a strategy instance based on configuration.
        
        Args:
            strategy_config: Strategy configuration
            **kwargs: Additional arguments to pass to strategy constructor
            
        Returns:
            Configured strategy instance
            
        Raises:
            StrategyException: If strategy creation fails
            ConfigurationException: If configuration is invalid
        """
        if not self._initialized:
            raise StrategyException("Strategy factory not initialized")
        
        try:
            # Validate configuration
            self._validate_strategy_config(strategy_config)
            
            # Get strategy class from registry
            strategy_class = self._registry.get_strategy_class(strategy_config.type)
            
            if not strategy_class:
                raise StrategyException(f"Strategy type '{strategy_config.type}' not found")
            
            # Prepare strategy parameters
            strategy_params = self._prepare_strategy_parameters(strategy_config, **kwargs)
            
            # Create strategy instance
            strategy_instance = strategy_class(**strategy_params)
            
            # Validate created instance
            self._validate_strategy_instance(strategy_instance)
            
            if self.logger:
                self.logger.info(
                    f"Created strategy instance: {strategy_config.name} ({strategy_config.type})"
                )
            
            return strategy_instance
            
        except Exception as e:
            error_msg = f"Failed to create strategy '{strategy_config.name}': {e}"
            if self.logger:
                self.logger.error(error_msg)
            
            if isinstance(e, (StrategyException, ConfigurationException)):
                raise
            else:
                raise StrategyException(error_msg) from e
    
    def register_strategy(
        self, 
        strategy_type: StrategyType, 
        strategy_class: Type[TradingStrategyProtocol]
    ) -> None:
        """
        Register a custom strategy class.
        
        Args:
            strategy_type: Strategy type identifier
            strategy_class: Strategy class to register
            
        Raises:
            StrategyException: If registration fails
        """
        try:
            # Validate strategy class
            self._validate_strategy_class(strategy_class)
            
            # Register with registry
            self._registry.register(strategy_type, strategy_class)
            
            if self.logger:
                self.logger.info(f"Registered custom strategy: {strategy_type}")
                
        except Exception as e:
            error_msg = f"Failed to register strategy '{strategy_type}': {e}"
            if self.logger:
                self.logger.error(error_msg)
            raise StrategyException(error_msg) from e
    
    def unregister_strategy(self, strategy_type: StrategyType) -> None:
        """
        Unregister a strategy type.
        
        Args:
            strategy_type: Strategy type to unregister
        """
        self._registry.unregister(strategy_type)
        
        if self.logger:
            self.logger.info(f"Unregistered strategy: {strategy_type}")
    
    def get_available_strategies(self) -> List[StrategyType]:
        """
        Get list of available strategy types.
        
        Returns:
            List of registered strategy types
        """
        return self._registry.get_registered_strategies()
    
    def get_strategy_info(self, strategy_type: StrategyType) -> Dict[str, Any]:
        """
        Get information about a strategy type.
        
        Args:
            strategy_type: Strategy type to get info for
            
        Returns:
            Dictionary with strategy information
        """
        strategy_class = self._registry.get_strategy_class(strategy_type)
        
        if not strategy_class:
            raise StrategyException(f"Strategy type '{strategy_type}' not found")
        
        return {
            "type": strategy_type,
            "class_name": strategy_class.__name__,
            "module": strategy_class.__module__,
            "docstring": strategy_class.__doc__,
            "parameters": self._get_strategy_parameters_info(strategy_class),
        }
    
    def create_strategy_from_name(
        self, 
        strategy_name: str, 
        strategy_type: StrategyType,
        parameters: Optional[StrategyParameters] = None,
        **kwargs: Any
    ) -> TradingStrategyProtocol:
        """
        Create a strategy instance from name and type.
        
        Args:
            strategy_name: Name for the strategy instance
            strategy_type: Type of strategy to create
            parameters: Strategy parameters
            **kwargs: Additional arguments
            
        Returns:
            Configured strategy instance
        """
        # Create strategy configuration
        strategy_config = StrategyConfig(
            name=strategy_name,
            type=strategy_type,
            parameters=parameters or {},
            **kwargs
        )
        
        return self.create_strategy(strategy_config)
    
    def load_custom_strategies(self, module_path: str) -> None:
        """
        Load custom strategies from a module.
        
        Args:
            module_path: Python module path containing custom strategies
            
        Raises:
            StrategyException: If loading fails
        """
        try:
            # Import the module
            module = importlib.import_module(module_path)
            
            # Find strategy classes in the module
            strategy_classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (hasattr(obj, '__bases__') and 
                    any(hasattr(base, 'analyze_market') for base in obj.__bases__)):
                    strategy_classes.append(obj)
            
            # Register found strategies
            for strategy_class in strategy_classes:
                # Try to determine strategy type from class name or attributes
                strategy_type = self._infer_strategy_type(strategy_class)
                if strategy_type:
                    self.register_strategy(strategy_type, strategy_class)
            
            if self.logger:
                self.logger.info(
                    f"Loaded {len(strategy_classes)} custom strategies from {module_path}"
                )
                
        except Exception as e:
            error_msg = f"Failed to load custom strategies from '{module_path}': {e}"
            if self.logger:
                self.logger.error(error_msg)
            raise StrategyException(error_msg) from e
    
    def _validate_strategy_config(self, config: StrategyConfig) -> None:
        """Validate strategy configuration."""
        if not config.name:
            raise ConfigurationException("Strategy name is required")
        
        if not config.type:
            raise ConfigurationException("Strategy type is required")
        
        if config.type not in self.get_available_strategies():
            raise ConfigurationException(f"Unknown strategy type: {config.type}")
    
    def _validate_strategy_class(self, strategy_class: Type) -> None:
        """Validate that a class implements the strategy protocol."""
        required_methods = ['analyze_market', 'validate_signal', 'get_risk_parameters']
        
        for method_name in required_methods:
            if not hasattr(strategy_class, method_name):
                raise StrategyException(
                    f"Strategy class must implement '{method_name}' method"
                )
        
        # Check if it's callable
        if not callable(strategy_class):
            raise StrategyException("Strategy class must be callable")
    
    def _validate_strategy_instance(self, instance: TradingStrategyProtocol) -> None:
        """Validate a strategy instance."""
        if not hasattr(instance, 'name'):
            raise StrategyException("Strategy instance must have a 'name' attribute")
        
        if not hasattr(instance, 'parameters'):
            raise StrategyException("Strategy instance must have a 'parameters' attribute")
    
    def _prepare_strategy_parameters(
        self, 
        config: StrategyConfig, 
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Prepare parameters for strategy instantiation."""
        params = {
            'name': config.name,
            'parameters': config.parameters.copy(),
            **kwargs
        }
        
        # Add configuration-specific parameters
        if hasattr(config, 'symbols'):
            params['symbols'] = config.symbols
        
        if hasattr(config, 'timeframe'):
            params['timeframe'] = config.timeframe
        
        if hasattr(config, 'lookback_period'):
            params['lookback_period'] = config.lookback_period
        
        return params
    
    def _get_strategy_parameters_info(self, strategy_class: Type) -> Dict[str, Any]:
        """Get information about strategy parameters."""
        try:
            # Get constructor signature
            sig = inspect.signature(strategy_class.__init__)
            parameters = {}
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                param_info = {
                    'name': param_name,
                    'required': param.default == inspect.Parameter.empty,
                    'default': param.default if param.default != inspect.Parameter.empty else None,
                    'annotation': str(param.annotation) if param.annotation != inspect.Parameter.empty else None,
                }
                
                parameters[param_name] = param_info
            
            return parameters
            
        except Exception:
            return {}
    
    def _infer_strategy_type(self, strategy_class: Type) -> Optional[StrategyType]:
        """Infer strategy type from class name or attributes."""
        class_name = strategy_class.__name__.lower()
        
        # Try to match with known patterns
        if 'bollinger' in class_name and 'rsi' in class_name:
            return StrategyType.BOLLINGER_RSI
        elif 'macd' in class_name and 'fibonacci' in class_name:
            return StrategyType.MACD_FIBONACCI
        
        # Check for strategy_type attribute
        if hasattr(strategy_class, 'strategy_type'):
            return strategy_class.strategy_type
        
        # Default to custom
        return StrategyType.CUSTOM
    
    def __repr__(self) -> str:
        """String representation of the factory."""
        strategies = self.get_available_strategies()
        return f"StrategyFactory(strategies={len(strategies)}, types={strategies})" 