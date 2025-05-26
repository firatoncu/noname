"""
State Management System for Trading Application

This module provides a thread-safe state management solution using dataclasses
and proper encapsulation. It replaces the global variable system with organized
state containers for different concerns.
"""

import json
import threading
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Union
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TradingState:
    """State container for trading-related data."""
    
    # Signal states per symbol
    clean_sell_signals: Dict[str, int] = field(default_factory=dict)
    clean_buy_signals: Dict[str, int] = field(default_factory=dict)
    
    # Stop loss prices per symbol
    sl_prices: Dict[str, float] = field(default_factory=dict)
    
    # Last timestamps per symbol
    last_timestamps: Dict[str, int] = field(default_factory=dict)
    
    # Buy conditions per symbol
    buy_conditions_a: Dict[str, bool] = field(default_factory=dict)
    buy_conditions_b: Dict[str, bool] = field(default_factory=dict)
    buy_conditions_c: Dict[str, bool] = field(default_factory=dict)
    
    # Sell conditions per symbol
    sell_conditions_a: Dict[str, bool] = field(default_factory=dict)
    sell_conditions_b: Dict[str, bool] = field(default_factory=dict)
    sell_conditions_c: Dict[str, bool] = field(default_factory=dict)
    
    # Funding flags per symbol
    funding_flags: Dict[str, bool] = field(default_factory=dict)
    
    # Trend signals per symbol
    trend_signals: Dict[str, bool] = field(default_factory=dict)
    
    # Order status per symbol
    order_statuses: Dict[str, str] = field(default_factory=dict)
    
    # Limit orders per symbol
    limit_orders: Dict[str, dict] = field(default_factory=dict)
    
    # Capital to be used
    capital_tbu: float = 0.0


@dataclass
class SystemState:
    """State container for system-related data."""
    
    # Error tracking
    error_counter: int = 0
    
    # Database status
    db_status: bool = False
    
    # Notification status
    notif_status: bool = True


@dataclass
class UIState:
    """State container for UI-related data."""
    
    # User timezone
    user_time_zone: str = "UTC"
    
    # Current strategy name
    strategy_name: str = "Default Strategy"


class StateManager:
    """
    Thread-safe state manager for the trading application.
    
    Provides centralized state management with proper encapsulation,
    type hints, and persistence capabilities.
    """
    
    def __init__(self, persistence_file: Optional[str] = None):
        """
        Initialize the state manager.
        
        Args:
            persistence_file: Optional file path for state persistence
        """
        self._lock = threading.RLock()
        self._trading_state = TradingState()
        self._system_state = SystemState()
        self._ui_state = UIState()
        self._persistence_file = persistence_file
        
        # Load persisted state if file exists
        if self._persistence_file and Path(self._persistence_file).exists():
            self.load_state()
    
    # Trading State Methods
    def set_clean_sell_signal(self, symbol: str, value: int) -> None:
        """Set clean sell signal for a symbol."""
        with self._lock:
            self._trading_state.clean_sell_signals[symbol] = value
            self._auto_persist()
    
    def get_clean_sell_signal(self, symbol: str) -> int:
        """Get clean sell signal for a symbol."""
        with self._lock:
            return self._trading_state.clean_sell_signals.get(symbol, 0)
    
    def set_clean_buy_signal(self, symbol: str, value: int) -> None:
        """Set clean buy signal for a symbol."""
        with self._lock:
            self._trading_state.clean_buy_signals[symbol] = value
            self._auto_persist()
    
    def get_clean_buy_signal(self, symbol: str) -> int:
        """Get clean buy signal for a symbol."""
        with self._lock:
            return self._trading_state.clean_buy_signals.get(symbol, 0)
    
    def set_sl_price(self, symbol: str, value: float) -> None:
        """Set stop loss price for a symbol."""
        with self._lock:
            self._trading_state.sl_prices[symbol] = value
            self._auto_persist()
    
    def get_sl_price(self, symbol: str) -> float:
        """Get stop loss price for a symbol."""
        with self._lock:
            return self._trading_state.sl_prices.get(symbol, 0.0)
    
    def set_last_timestamp(self, symbol: str, value: int) -> None:
        """Set last timestamp for a symbol."""
        with self._lock:
            self._trading_state.last_timestamps[symbol] = value
            self._auto_persist()
    
    def get_last_timestamp(self, symbol: str) -> int:
        """Get last timestamp for a symbol."""
        with self._lock:
            return self._trading_state.last_timestamps.get(symbol, 0)
    
    # Buy Conditions Methods
    def set_buyconda(self, symbol: str, value: bool) -> None:
        """Set buy condition A for a symbol."""
        with self._lock:
            self._trading_state.buy_conditions_a[symbol] = value
            self._auto_persist()
    
    def get_buyconda(self, symbol: str) -> bool:
        """Get buy condition A for a symbol."""
        with self._lock:
            return self._trading_state.buy_conditions_a.get(symbol, False)
    
    def set_buycondb(self, symbol: str, value: bool) -> None:
        """Set buy condition B for a symbol."""
        with self._lock:
            self._trading_state.buy_conditions_b[symbol] = value
            self._auto_persist()
    
    def get_buycondb(self, symbol: str) -> bool:
        """Get buy condition B for a symbol."""
        with self._lock:
            return self._trading_state.buy_conditions_b.get(symbol, False)
    
    def set_buycondc(self, symbol: str, value: bool) -> None:
        """Set buy condition C for a symbol."""
        with self._lock:
            self._trading_state.buy_conditions_c[symbol] = value
            self._auto_persist()
    
    def get_buycondc(self, symbol: str) -> bool:
        """Get buy condition C for a symbol."""
        with self._lock:
            return self._trading_state.buy_conditions_c.get(symbol, False)
    
    # Sell Conditions Methods
    def set_sellconda(self, symbol: str, value: bool) -> None:
        """Set sell condition A for a symbol."""
        with self._lock:
            self._trading_state.sell_conditions_a[symbol] = value
            self._auto_persist()
    
    def get_sellconda(self, symbol: str) -> bool:
        """Get sell condition A for a symbol."""
        with self._lock:
            return self._trading_state.sell_conditions_a.get(symbol, False)
    
    def set_sellcondb(self, symbol: str, value: bool) -> None:
        """Set sell condition B for a symbol."""
        with self._lock:
            self._trading_state.sell_conditions_b[symbol] = value
            self._auto_persist()
    
    def get_sellcondb(self, symbol: str) -> bool:
        """Get sell condition B for a symbol."""
        with self._lock:
            return self._trading_state.sell_conditions_b.get(symbol, False)
    
    def set_sellcondc(self, symbol: str, value: bool) -> None:
        """Set sell condition C for a symbol."""
        with self._lock:
            self._trading_state.sell_conditions_c[symbol] = value
            self._auto_persist()
    
    def get_sellcondc(self, symbol: str) -> bool:
        """Get sell condition C for a symbol."""
        with self._lock:
            return self._trading_state.sell_conditions_c.get(symbol, False)
    
    # Funding and Trend Methods
    def set_funding_flag(self, symbol: str, value: bool) -> None:
        """Set funding flag for a symbol."""
        with self._lock:
            self._trading_state.funding_flags[symbol] = value
            self._auto_persist()
    
    def get_funding_flag(self, symbol: str) -> bool:
        """Get funding flag for a symbol."""
        with self._lock:
            return self._trading_state.funding_flags.get(symbol, False)
    
    def set_trend_signal(self, symbol: str, value: bool) -> None:
        """Set trend signal for a symbol."""
        with self._lock:
            self._trading_state.trend_signals[symbol] = value
            self._auto_persist()
    
    def get_trend_signal(self, symbol: str) -> bool:
        """Get trend signal for a symbol."""
        with self._lock:
            return self._trading_state.trend_signals.get(symbol, False)
    
    # Order Methods
    def set_order_status(self, symbol: str, value: str) -> None:
        """Set order status for a symbol."""
        with self._lock:
            self._trading_state.order_statuses[symbol] = value
            self._auto_persist()
    
    def get_order_status(self, symbol: str) -> str:
        """Get order status for a symbol."""
        with self._lock:
            return self._trading_state.order_statuses.get(symbol, "")
    
    def set_limit_order(self, symbol: str, value: dict) -> None:
        """Set limit order for a symbol."""
        with self._lock:
            self._trading_state.limit_orders[symbol] = value
            self._auto_persist()
    
    def get_limit_order(self, symbol: str) -> dict:
        """Get limit order for a symbol."""
        with self._lock:
            return self._trading_state.limit_orders.get(symbol, {})
    
    # Capital Methods
    def set_capital_tbu(self, value: float) -> None:
        """Set capital to be used."""
        with self._lock:
            self._trading_state.capital_tbu = value
            self._auto_persist()
    
    def get_capital_tbu(self) -> float:
        """Get capital to be used."""
        with self._lock:
            return self._trading_state.capital_tbu
    
    # System State Methods
    def set_error_counter(self, value: int) -> None:
        """Set error counter."""
        with self._lock:
            self._system_state.error_counter = value
            self._auto_persist()
    
    def get_error_counter(self) -> int:
        """Get error counter."""
        with self._lock:
            return self._system_state.error_counter
    
    def increment_error_counter(self) -> int:
        """Increment error counter and return new value."""
        with self._lock:
            self._system_state.error_counter += 1
            self._auto_persist()
            return self._system_state.error_counter
    
    def set_db_status(self, value: bool) -> None:
        """Set database status."""
        with self._lock:
            self._system_state.db_status = value
            self._auto_persist()
    
    def get_db_status(self) -> bool:
        """Get database status."""
        with self._lock:
            return self._system_state.db_status
    
    def set_notif_status(self, value: bool) -> None:
        """Set notification status."""
        with self._lock:
            self._system_state.notif_status = value
            self._auto_persist()
    
    def get_notif_status(self) -> bool:
        """Get notification status."""
        with self._lock:
            return self._system_state.notif_status
    
    # UI State Methods
    def set_user_time_zone(self, value: str) -> None:
        """Set user timezone."""
        with self._lock:
            self._ui_state.user_time_zone = value
            self._auto_persist()
    
    def get_user_time_zone(self) -> str:
        """Get user timezone."""
        with self._lock:
            return self._ui_state.user_time_zone
    
    def set_strategy_name(self, name: str) -> None:
        """Set strategy name."""
        with self._lock:
            self._ui_state.strategy_name = name
            self._auto_persist()
    
    def get_strategy_name(self) -> str:
        """Get strategy name."""
        with self._lock:
            return self._ui_state.strategy_name
    
    # Bulk Operations
    def get_all_trading_state(self) -> Dict[str, Any]:
        """Get all trading state as a dictionary."""
        with self._lock:
            return asdict(self._trading_state)
    
    def get_all_system_state(self) -> Dict[str, Any]:
        """Get all system state as a dictionary."""
        with self._lock:
            return asdict(self._system_state)
    
    def get_all_ui_state(self) -> Dict[str, Any]:
        """Get all UI state as a dictionary."""
        with self._lock:
            return asdict(self._ui_state)
    
    def reset_symbol_state(self, symbol: str) -> None:
        """Reset all state for a specific symbol."""
        with self._lock:
            # Remove symbol from all trading state dictionaries
            state_dicts = [
                self._trading_state.clean_sell_signals,
                self._trading_state.clean_buy_signals,
                self._trading_state.sl_prices,
                self._trading_state.last_timestamps,
                self._trading_state.buy_conditions_a,
                self._trading_state.buy_conditions_b,
                self._trading_state.buy_conditions_c,
                self._trading_state.sell_conditions_a,
                self._trading_state.sell_conditions_b,
                self._trading_state.sell_conditions_c,
                self._trading_state.funding_flags,
                self._trading_state.trend_signals,
                self._trading_state.order_statuses,
                self._trading_state.limit_orders,
            ]
            
            for state_dict in state_dicts:
                state_dict.pop(symbol, None)
            
            self._auto_persist()
    
    # Persistence Methods
    def save_state(self, file_path: Optional[str] = None) -> None:
        """
        Save current state to file.
        
        Args:
            file_path: Optional custom file path, uses default if not provided
        """
        target_file = file_path or self._persistence_file
        if not target_file:
            logger.warning("No persistence file specified, cannot save state")
            return
        
        with self._lock:
            state_data = {
                'trading_state': asdict(self._trading_state),
                'system_state': asdict(self._system_state),
                'ui_state': asdict(self._ui_state),
                'timestamp': datetime.now().isoformat(),
            }
            
            try:
                with open(target_file, 'w') as f:
                    json.dump(state_data, f, indent=2)
                logger.info(f"State saved to {target_file}")
            except Exception as e:
                logger.error(f"Failed to save state: {e}")
    
    def load_state(self, file_path: Optional[str] = None) -> bool:
        """
        Load state from file.
        
        Args:
            file_path: Optional custom file path, uses default if not provided
            
        Returns:
            True if state was loaded successfully, False otherwise
        """
        target_file = file_path or self._persistence_file
        if not target_file or not Path(target_file).exists():
            return False
        
        # Check if file is empty
        if Path(target_file).stat().st_size == 0:
            return False
        
        with self._lock:
            try:
                with open(target_file, 'r') as f:
                    state_data = json.load(f)
                
                # Restore trading state
                if 'trading_state' in state_data:
                    trading_data = state_data['trading_state']
                    self._trading_state = TradingState(**trading_data)
                
                # Restore system state
                if 'system_state' in state_data:
                    system_data = state_data['system_state']
                    self._system_state = SystemState(**system_data)
                
                # Restore UI state
                if 'ui_state' in state_data:
                    ui_data = state_data['ui_state']
                    self._ui_state = UIState(**ui_data)
                
                logger.info(f"State loaded from {target_file}")
                return True
                
            except Exception as e:
                # Only log errors that aren't related to empty files
                if "Expecting value" not in str(e):
                    logger.error(f"Failed to load state: {e}")
                return False
    
    def _auto_persist(self) -> None:
        """Automatically persist state if persistence is enabled."""
        if self._persistence_file:
            try:
                self.save_state()
            except Exception as e:
                # Only log errors that aren't related to initial empty files
                if "Expecting value" not in str(e):
                    logger.error(f"Auto-persistence failed: {e}")


# Global state manager instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """
    Get the global state manager instance.
    
    Returns:
        The global StateManager instance
    """
    global _state_manager
    if _state_manager is None:
        # Initialize with default persistence file
        persistence_file = Path(__file__).parent / "state_persistence.json"
        _state_manager = StateManager(str(persistence_file))
    return _state_manager


def initialize_state_manager(persistence_file: Optional[str] = None) -> StateManager:
    """
    Initialize the global state manager with custom settings.
    
    Args:
        persistence_file: Optional custom persistence file path
        
    Returns:
        The initialized StateManager instance
    """
    global _state_manager
    _state_manager = StateManager(persistence_file)
    return _state_manager 