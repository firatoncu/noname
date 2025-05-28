"""
Signal Management Compatibility Layer

This module provides backward compatibility with the existing global signal functions
while using the new SignalManager underneath. This allows for gradual migration
from the old dictionary-based system to the new structured signal management.
"""

from typing import Union
from utils.signal_manager import (
    SignalManager, SignalType, get_signal_manager, initialize_signal_manager
)
import logging

logger = logging.getLogger(__name__)

# Initialize the signal manager if not already done
try:
    get_signal_manager()
except RuntimeError:
    initialize_signal_manager(persistence_file="signals.json")


# Clean signal functions (backward compatibility)
def set_clean_buy_signal(value: int, symbol: str):
    """Set clean buy signal for a symbol."""
    try:
        signal_manager = get_signal_manager()
        signal_manager.update_signal(
            symbol=symbol,
            signal_type=SignalType.BUY,
            value=value,
            confidence=0.7 if value > 0 else 0.3,
            source_indicator="clean_signal"
        )
    except Exception as e:
        logger.error(f"Error setting clean buy signal: {e}")


def get_clean_buy_signal(symbol: str) -> int:
    """Get clean buy signal for a symbol."""
    try:
        signal_manager = get_signal_manager()
        return signal_manager.get_signal_value(symbol, SignalType.BUY, 0)
    except Exception as e:
        logger.error(f"Error getting clean buy signal: {e}")
        return 0


def set_clean_sell_signal(value: int, symbol: str):
    """Set clean sell signal for a symbol."""
    try:
        signal_manager = get_signal_manager()
        signal_manager.update_signal(
            symbol=symbol,
            signal_type=SignalType.SELL,
            value=value,
            confidence=0.7 if value > 0 else 0.3,
            source_indicator="clean_signal"
        )
    except Exception as e:
        logger.error(f"Error setting clean sell signal: {e}")


def get_clean_sell_signal(symbol: str) -> int:
    """Get clean sell signal for a symbol."""
    try:
        signal_manager = get_signal_manager()
        return signal_manager.get_signal_value(symbol, SignalType.SELL, 0)
    except Exception as e:
        logger.error(f"Error getting clean sell signal: {e}")
        return 0


# Buy condition functions
def set_buyconda(value: bool, symbol: str):
    """Set buy condition A for a symbol."""
    try:
        signal_manager = get_signal_manager()
        signal_manager.update_signal(
            symbol=symbol,
            signal_type=SignalType.BUY_CONDITION_A,
            value=value,
            confidence=0.8 if value else 0.2,
            source_indicator="buy_condition_a"
        )
    except Exception as e:
        logger.error(f"Error setting buy condition A: {e}")


def get_buyconda(symbol: str) -> bool:
    """Get buy condition A for a symbol."""
    try:
        signal_manager = get_signal_manager()
        return signal_manager.get_signal_value(symbol, SignalType.BUY_CONDITION_A, False)
    except Exception as e:
        logger.error(f"Error getting buy condition A: {e}")
        return False


def set_buycondb(value: bool, symbol: str):
    """Set buy condition B for a symbol."""
    try:
        signal_manager = get_signal_manager()
        signal_manager.update_signal(
            symbol=symbol,
            signal_type=SignalType.BUY_CONDITION_B,
            value=value,
            confidence=0.8 if value else 0.2,
            source_indicator="buy_condition_b"
        )
    except Exception as e:
        logger.error(f"Error setting buy condition B: {e}")


def get_buycondb(symbol: str) -> bool:
    """Get buy condition B for a symbol."""
    try:
        signal_manager = get_signal_manager()
        return signal_manager.get_signal_value(symbol, SignalType.BUY_CONDITION_B, False)
    except Exception as e:
        logger.error(f"Error getting buy condition B: {e}")
        return False


def set_buycondc(value: bool, symbol: str):
    """Set buy condition C for a symbol."""
    try:
        signal_manager = get_signal_manager()
        signal_manager.update_signal(
            symbol=symbol,
            signal_type=SignalType.BUY_CONDITION_C,
            value=value,
            confidence=0.8 if value else 0.2,
            source_indicator="buy_condition_c"
        )
    except Exception as e:
        logger.error(f"Error setting buy condition C: {e}")


def get_buycondc(symbol: str) -> bool:
    """Get buy condition C for a symbol."""
    try:
        signal_manager = get_signal_manager()
        return signal_manager.get_signal_value(symbol, SignalType.BUY_CONDITION_C, False)
    except Exception as e:
        logger.error(f"Error getting buy condition C: {e}")
        return False


# Sell condition functions
def set_sellconda(value: bool, symbol: str):
    """Set sell condition A for a symbol."""
    try:
        signal_manager = get_signal_manager()
        signal_manager.update_signal(
            symbol=symbol,
            signal_type=SignalType.SELL_CONDITION_A,
            value=value,
            confidence=0.8 if value else 0.2,
            source_indicator="sell_condition_a"
        )
    except Exception as e:
        logger.error(f"Error setting sell condition A: {e}")


def get_sellconda(symbol: str) -> bool:
    """Get sell condition A for a symbol."""
    try:
        signal_manager = get_signal_manager()
        return signal_manager.get_signal_value(symbol, SignalType.SELL_CONDITION_A, False)
    except Exception as e:
        logger.error(f"Error getting sell condition A: {e}")
        return False


def set_sellcondb(value: bool, symbol: str):
    """Set sell condition B for a symbol."""
    try:
        signal_manager = get_signal_manager()
        signal_manager.update_signal(
            symbol=symbol,
            signal_type=SignalType.SELL_CONDITION_B,
            value=value,
            confidence=0.8 if value else 0.2,
            source_indicator="sell_condition_b"
        )
    except Exception as e:
        logger.error(f"Error setting sell condition B: {e}")


def get_sellcondb(symbol: str) -> bool:
    """Get sell condition B for a symbol."""
    try:
        signal_manager = get_signal_manager()
        return signal_manager.get_signal_value(symbol, SignalType.SELL_CONDITION_B, False)
    except Exception as e:
        logger.error(f"Error getting sell condition B: {e}")
        return False


def set_sellcondc(value: bool, symbol: str):
    """Set sell condition C for a symbol."""
    try:
        signal_manager = get_signal_manager()
        signal_manager.update_signal(
            symbol=symbol,
            signal_type=SignalType.SELL_CONDITION_C,
            value=value,
            confidence=0.8 if value else 0.2,
            source_indicator="sell_condition_c"
        )
    except Exception as e:
        logger.error(f"Error setting sell condition C: {e}")


def get_sellcondc(symbol: str) -> bool:
    """Get sell condition C for a symbol."""
    try:
        signal_manager = get_signal_manager()
        return signal_manager.get_signal_value(symbol, SignalType.SELL_CONDITION_C, False)
    except Exception as e:
        logger.error(f"Error getting sell condition C: {e}")
        return False


# Trend signal functions
def set_trend_signal(value: bool, symbol: str):
    """Set trend signal for a symbol."""
    try:
        signal_manager = get_signal_manager()
        signal_manager.update_signal(
            symbol=symbol,
            signal_type=SignalType.TREND,
            value=value,
            confidence=0.8 if value else 0.2,
            source_indicator="trend_signal"
        )
    except Exception as e:
        logger.error(f"Error setting trend signal: {e}")


def get_trend_signal(symbol: str) -> bool:
    """Get trend signal for a symbol."""
    try:
        signal_manager = get_signal_manager()
        return signal_manager.get_signal_value(symbol, SignalType.TREND, False)
    except Exception as e:
        logger.error(f"Error getting trend signal: {e}")
        return False


# Enhanced signal functions with additional features
def create_enhanced_buy_signal(
    symbol: str,
    value: Union[bool, int],
    confidence: float = 0.5,
    strength: float = 0.0,
    strategy_name: str = "",
    source_indicator: str = "",
    conditions_met: list = None,
    expires_in_minutes: int = None
):
    """Create an enhanced buy signal with additional metadata."""
    try:
        signal_manager = get_signal_manager()
        return signal_manager.create_signal(
            symbol=symbol,
            signal_type=SignalType.BUY,
            value=value,
            confidence=confidence,
            strength=strength,
            strategy_name=strategy_name,
            source_indicator=source_indicator,
            conditions_met=conditions_met or [],
            expires_in_minutes=expires_in_minutes
        )
    except Exception as e:
        logger.error(f"Error creating enhanced buy signal: {e}")
        return None


def create_enhanced_sell_signal(
    symbol: str,
    value: Union[bool, int],
    confidence: float = 0.5,
    strength: float = 0.0,
    strategy_name: str = "",
    source_indicator: str = "",
    conditions_met: list = None,
    expires_in_minutes: int = None
):
    """Create an enhanced sell signal with additional metadata."""
    try:
        signal_manager = get_signal_manager()
        return signal_manager.create_signal(
            symbol=symbol,
            signal_type=SignalType.SELL,
            value=value,
            confidence=confidence,
            strength=strength,
            strategy_name=strategy_name,
            source_indicator=source_indicator,
            conditions_met=conditions_met or [],
            expires_in_minutes=expires_in_minutes
        )
    except Exception as e:
        logger.error(f"Error creating enhanced sell signal: {e}")
        return None


def create_wave_signal(
    symbol: str,
    value: Union[bool, int],
    confidence: float = 0.5,
    strength: float = 0.0,
    strategy_name: str = "",
    source_indicator: str = "",
    wave_stage: int = 0,
    expires_in_minutes: int = None
):
    """Create a wave signal with wave-specific metadata."""
    try:
        signal_manager = get_signal_manager()
        return signal_manager.create_signal(
            symbol=symbol,
            signal_type=SignalType.WAVE,
            value=value,
            confidence=confidence,
            strength=strength,
            strategy_name=strategy_name,
            source_indicator=source_indicator,
            conditions_met=[f"wave_stage_{wave_stage}"],
            expires_in_minutes=expires_in_minutes,
            metadata={"wave_stage": wave_stage}
        )
    except Exception as e:
        logger.error(f"Error creating wave signal: {e}")
        return None


def get_signal_statistics(symbol: str):
    """Get comprehensive signal statistics for a symbol."""
    try:
        signal_manager = get_signal_manager()
        return signal_manager.get_signal_statistics(symbol)
    except Exception as e:
        logger.error(f"Error getting signal statistics: {e}")
        return {}


def validate_trading_signals(symbol: str, required_buy_conditions: list = None, required_sell_conditions: list = None):
    """Validate that all required trading signals are active."""
    try:
        signal_manager = get_signal_manager()
        
        # Default required conditions
        if required_buy_conditions is None:
            required_buy_conditions = [SignalType.BUY_CONDITION_A, SignalType.BUY_CONDITION_B, SignalType.BUY_CONDITION_C]
        
        if required_sell_conditions is None:
            required_sell_conditions = [SignalType.SELL_CONDITION_A, SignalType.SELL_CONDITION_B, SignalType.SELL_CONDITION_C]
        
        # Check buy conditions
        buy_valid = True
        if required_buy_conditions:
            active_signals = signal_manager.get_all_active_signals(symbol)
            buy_valid = all(signal_type in active_signals for signal_type in required_buy_conditions)
        
        # Check sell conditions
        sell_valid = True
        if required_sell_conditions:
            active_signals = signal_manager.get_all_active_signals(symbol)
            sell_valid = all(signal_type in active_signals for signal_type in required_sell_conditions)
        
        return {
            "buy_conditions_valid": buy_valid,
            "sell_conditions_valid": sell_valid,
            "all_valid": buy_valid and sell_valid
        }
        
    except Exception as e:
        logger.error(f"Error validating trading signals: {e}")
        return {"buy_conditions_valid": False, "sell_conditions_valid": False, "all_valid": False}


def reset_symbol_signals(symbol: str):
    """Reset all signals for a symbol."""
    try:
        signal_manager = get_signal_manager()
        signal_manager.reset_symbol_signals(symbol)
    except Exception as e:
        logger.error(f"Error resetting symbol signals: {e}")


def get_signal_history_summary(symbol: str):
    """Get a summary of signal history for a symbol."""
    try:
        signal_manager = get_signal_manager()
        history = signal_manager.get_signal_history(symbol)
        if not history:
            return {"total_signals": 0, "recent_signals": []}
        
        # Get recent signals (last 10)
        recent_signals = []
        for signal in history.signals[-10:]:
            recent_signals.append({
                "signal_type": signal.signal_type.value,
                "value": signal.value,
                "confidence": signal.confidence,
                "status": signal.status.value,
                "created_at": signal.created_at.isoformat(),
                "source_indicator": signal.source_indicator,
                "strategy_name": signal.strategy_name
            })
        
        return {
            "total_signals": len(history.signals),
            "recent_signals": recent_signals,
            "statistics": signal_manager.get_signal_statistics(symbol)
        }
        
    except Exception as e:
        logger.error(f"Error getting signal history summary: {e}")
        return {"total_signals": 0, "recent_signals": [], "statistics": {}} 