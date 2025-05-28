"""
Refactored Trading Main - Example Usage

This module demonstrates how to use the refactored trading architecture
with the strategy pattern and centralized managers.
"""

import asyncio
import logging
from typing import List

from .core.trading_engine import TradingEngine, TradingConfig
from .core.position_manager import PositionConfig
from .core.order_manager import OrderConfig
from .strategies.macd_fibonacci_strategy import MACDFibonacciStrategy
from .strategies.rsi_bollinger_strategy import RSIBollingerStrategy
from utils.app_logging import setup_logger


class RefactoredTradingSystem:
    """
    Refactored trading system using the new architecture.
    
    This class demonstrates how to use the strategy pattern and
    centralized managers for clean, maintainable trading logic.
    """
    
    def __init__(self):
        """Initialize the refactored trading system"""
        self.logger = setup_logger("RefactoredTrading")
        self.trading_engine = None
        self.available_strategies = {
            "MACD_Fibonacci": MACDFibonacciStrategy,
            "RSI_Bollinger": RSIBollingerStrategy
        }
    
    def create_trading_engine(self, strategy_name: str = "MACD_Fibonacci") -> TradingEngine:
        """
        Create a trading engine with the specified strategy.
        
        Args:
            strategy_name: Name of the strategy to use
            
        Returns:
            Configured TradingEngine instance
        """
        # Create strategy instance
        if strategy_name not in self.available_strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        strategy_class = self.available_strategies[strategy_name]
        strategy = strategy_class()
        
        # Configure trading parameters
        trading_config = TradingConfig(
            max_open_positions=3,
            leverage=10,
            lookback_period=500,
            position_value_percentage=0.25,  # 25% of capital per position
            enable_database_logging=True,
            enable_notifications=True
        )
        
        # Configure position management
        position_config = PositionConfig(
            tp_percentage_long=0.005,   # 0.5% TP for long
            sl_percentage_long=0.015,   # 1.5% SL for long
            hard_sl_percentage_long=0.025,  # 2.5% hard SL for long
            tp_percentage_short=0.005,  # 0.5% TP for short
            sl_percentage_short=0.015,  # 1.5% SL for short
            hard_sl_percentage_short=0.025  # 2.5% hard SL for short
        )
        
        # Configure order management
        order_config = OrderConfig(
            max_retries=3,
            retry_delay=1.0,
            validate_funding_fee=True,
            min_order_value=10.0
        )
        
        # Create trading engine
        self.trading_engine = TradingEngine(
            strategy=strategy,
            trading_config=trading_config,
            position_config=position_config,
            order_config=order_config
        )
        
        self.logger.info(f"Created trading engine with {strategy_name} strategy")
        return self.trading_engine
    
    async def start_trading(
        self, 
        symbols: List[str], 
        client, 
        strategy_name: str = "MACD_Fibonacci"
    ):
        """
        Start the trading system.
        
        Args:
            symbols: List of trading symbols
            client: Binance client
            strategy_name: Strategy to use
        """
        try:
            # Create trading engine if not exists
            if self.trading_engine is None:
                self.create_trading_engine(strategy_name)
            
            # Initialize the engine
            await self.trading_engine.initialize(symbols, client, self.logger)
            
            # Start trading
            self.logger.info("Starting refactored trading system...")
            await self.trading_engine.start_trading(client, self.logger)
            
        except Exception as e:
            self.logger.error(f"Error in trading system: {e}")
            raise
    
    async def stop_trading(self):
        """Stop the trading system"""
        if self.trading_engine:
            await self.trading_engine.stop_trading()
            self.logger.info("Trading system stopped")
    
    def switch_strategy(self, strategy_name: str):
        """
        Switch to a different trading strategy.
        
        Args:
            strategy_name: Name of the new strategy
        """
        if strategy_name not in self.available_strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        if self.trading_engine is None:
            raise RuntimeError("Trading engine not initialized")
        
        strategy_class = self.available_strategies[strategy_name]
        new_strategy = strategy_class()
        
        self.trading_engine.switch_strategy(new_strategy, self.logger)
        self.logger.info(f"Switched to {strategy_name} strategy")
    
    def get_trading_status(self) -> dict:
        """Get current trading status"""
        if self.trading_engine is None:
            return {"status": "Not initialized"}
        
        return self.trading_engine.get_trading_status()
    
    async def close_all_positions(self, client, reason: str = "Manual"):
        """Close all open positions"""
        if self.trading_engine:
            await self.trading_engine.close_all_positions(client, self.logger, reason)
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available strategies"""
        return list(self.available_strategies.keys())
    
    def add_custom_strategy(self, name: str, strategy_class):
        """
        Add a custom strategy to the system.
        
        Args:
            name: Strategy name
            strategy_class: Strategy class (must inherit from BaseStrategy)
        """
        self.available_strategies[name] = strategy_class
        self.logger.info(f"Added custom strategy: {name}")


# Example usage functions
async def example_basic_usage():
    """Example of basic usage of the refactored system"""
    # Create trading system
    trading_system = RefactoredTradingSystem()
    
    # Define symbols to trade
    symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
    
    # Note: In real usage, you would pass an actual Binance client
    # client = await AsyncClient.create(api_key, api_secret)
    client = None  # Placeholder
    
    try:
        # Start trading with MACD Fibonacci strategy
        await trading_system.start_trading(symbols, client, "MACD_Fibonacci")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await trading_system.stop_trading()


async def example_strategy_switching():
    """Example of switching between strategies"""
    trading_system = RefactoredTradingSystem()
    
    # Create engine with initial strategy
    trading_system.create_trading_engine("MACD_Fibonacci")
    
    # Get initial status
    status = trading_system.get_trading_status()
    print(f"Initial strategy: {status['strategy']}")
    
    # Switch to RSI Bollinger strategy
    trading_system.switch_strategy("RSI_Bollinger")
    
    # Get updated status
    status = trading_system.get_trading_status()
    print(f"New strategy: {status['strategy']}")


def example_custom_strategy():
    """Example of adding a custom strategy"""
    from .core.base_strategy import BaseStrategy, TradingSignal, SignalType, MarketData
    
    class CustomStrategy(BaseStrategy):
        def __init__(self):
            super().__init__("Custom Strategy", {"param1": 10})
        
        def check_buy_conditions(self, market_data: MarketData, symbol: str, logger) -> TradingSignal:
            # Custom buy logic here
            return TradingSignal(
                signal_type=SignalType.HOLD,
                strength=0.0,
                conditions={"custom": False}
            )
        
        def check_sell_conditions(self, market_data: MarketData, symbol: str, logger) -> TradingSignal:
            # Custom sell logic here
            return TradingSignal(
                signal_type=SignalType.HOLD,
                strength=0.0,
                conditions={"custom": False}
            )
        
        def get_strategy_info(self) -> dict:
            return {
                "name": self.name,
                "description": "Custom trading strategy example",
                "parameters": self.parameters
            }
    
    # Add custom strategy to system
    trading_system = RefactoredTradingSystem()
    trading_system.add_custom_strategy("Custom", CustomStrategy)
    
    print(f"Available strategies: {trading_system.get_available_strategies()}")


if __name__ == "__main__":
    # Run examples
    print("Running refactored trading system examples...")
    
    # Example 1: Basic usage
    print("\n1. Basic Usage Example:")
    # asyncio.run(example_basic_usage())  # Uncomment when you have a real client
    
    # Example 2: Strategy switching
    print("\n2. Strategy Switching Example:")
    asyncio.run(example_strategy_switching())
    
    # Example 3: Custom strategy
    print("\n3. Custom Strategy Example:")
    example_custom_strategy() 