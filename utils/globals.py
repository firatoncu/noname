"""
Compatibility layer for the old globals.py interface.

This module provides the same function signatures as the original globals.py
but uses the new StateManager underneath. This allows existing code to work
without modification while benefiting from the improved state management.
"""

from utils.state_manager import get_state_manager

# Get the state manager instance
_state = get_state_manager()

# Compatibility functions that match the original globals.py interface

def set_clean_sell_signal(value: int, symbol: str):
    """Set clean sell signal for a symbol."""
    _state.set_clean_sell_signal(symbol, value)

def set_clean_buy_signal(value: int, symbol: str):
    """Set clean buy signal for a symbol."""
    _state.set_clean_buy_signal(symbol, value)

def get_clean_sell_signal(symbol: str):
    """Get clean sell signal for a symbol."""
    return _state.get_clean_sell_signal(symbol)

def get_clean_buy_signal(symbol: str):
    """Get clean buy signal for a symbol."""
    return _state.get_clean_buy_signal(symbol)

def set_sl_price(value: float, symbol: str):
    """Set stop loss price for a symbol."""
    _state.set_sl_price(symbol, value)

def get_sl_price(symbol: str):
    """Get stop loss price for a symbol."""
    return _state.get_sl_price(symbol)

def set_last_timestamp(value: int, symbol: str):
    """Set last timestamp for a symbol."""
    _state.set_last_timestamp(symbol, value)

def get_last_timestamp(symbol: str):
    """Get last timestamp for a symbol."""
    return _state.get_last_timestamp(symbol)

def set_buyconda(value: bool, symbol: str):
    """Set buy condition A for a symbol."""
    _state.set_buyconda(symbol, value)

def get_buyconda(symbol: str):
    """Get buy condition A for a symbol."""
    return _state.get_buyconda(symbol)

def set_buycondb(value: bool, symbol: str):
    """Set buy condition B for a symbol."""
    _state.set_buycondb(symbol, value)

def get_buycondb(symbol: str):
    """Get buy condition B for a symbol."""
    return _state.get_buycondb(symbol)

def set_buycondc(value: bool, symbol: str):
    """Set buy condition C for a symbol."""
    _state.set_buycondc(symbol, value)

def get_buycondc(symbol: str):
    """Get buy condition C for a symbol."""
    return _state.get_buycondc(symbol)

def set_sellconda(value: bool, symbol: str):
    """Set sell condition A for a symbol."""
    _state.set_sellconda(symbol, value)

def get_sellconda(symbol: str):
    """Get sell condition A for a symbol."""
    return _state.get_sellconda(symbol)

def set_sellcondb(value: bool, symbol: str):
    """Set sell condition B for a symbol."""
    _state.set_sellcondb(symbol, value)

def get_sellcondb(symbol: str):
    """Get sell condition B for a symbol."""
    return _state.get_sellcondb(symbol)

def set_sellcondc(value: bool, symbol: str):
    """Set sell condition C for a symbol."""
    _state.set_sellcondc(symbol, value)

def get_sellcondc(symbol: str):
    """Get sell condition C for a symbol."""
    return _state.get_sellcondc(symbol)

def set_funding_flag(value: bool, symbol: str):
    """Set funding flag for a symbol."""
    _state.set_funding_flag(symbol, value)

def get_funding_flag(symbol: str):
    """Get funding flag for a symbol."""
    return _state.get_funding_flag(symbol)

def set_trend_signal(value: bool, symbol: str):
    """Set trend signal for a symbol."""
    _state.set_trend_signal(symbol, value)

def get_trend_signal(symbol: str):
    """Get trend signal for a symbol."""
    return _state.get_trend_signal(symbol)

def set_order_status(value: str, symbol: str):
    """Set order status for a symbol."""
    _state.set_order_status(symbol, value)

def get_order_status(symbol: str):
    """Get order status for a symbol."""
    return _state.get_order_status(symbol)

def set_limit_order(value: dict, symbol: str):
    """Set limit order for a symbol."""
    _state.set_limit_order(symbol, value)

def get_limit_order(symbol: str):
    """Get limit order for a symbol."""
    return _state.get_limit_order(symbol)

def set_capital_tbu(value: float):
    """Set capital to be used."""
    _state.set_capital_tbu(value)

def get_capital_tbu():
    """Get capital to be used."""
    return _state.get_capital_tbu()

def set_error_counter(value: int):
    """Set error counter."""
    _state.set_error_counter(value)

def get_error_counter():
    """Get error counter."""
    return _state.get_error_counter()

def set_db_status(value: bool):
    """Set database status."""
    _state.set_db_status(value)

def get_db_status():
    """Get database status."""
    return _state.get_db_status()

def set_notif_status(value: bool):
    """Set notification status."""
    _state.set_notif_status(value)

def get_notif_status():
    """Get notification status."""
    return _state.get_notif_status()

def set_user_time_zone(value: str):
    """Set user timezone."""
    _state.set_user_time_zone(value)

def get_user_time_zone():
    """Get user timezone."""
    return _state.get_user_time_zone()

def set_strategy_name(name: str):
    """Set strategy name."""
    _state.set_strategy_name(name)

def get_strategy_name():
    """Get strategy name."""
    return _state.get_strategy_name()

# Legacy global variables for backward compatibility
# These are deprecated and should not be used in new code

# Initialize empty dictionaries to maintain compatibility
clean_sell_signal = {}
clean_buy_signal = {}
sl_price = {}
last_timestamp = {}
buyconda = {}
buycondb = {}
buycondc = {}
sellconda = {}
sellcondb = {}
sellcondc = {}
funding_flag = {}
trend_signal = {}
order_status = {}
limit_order = {}

# Initialize scalar values
error_counter = 0
db_status = False
notif_status = True
user_time_zone = "UTC"
strategy_name = "Default Strategy"

# Note: These global variables are kept for compatibility but are not
# actively used. All state operations should go through the functions above
# which use the StateManager underneath.