"""
Advanced Signal Management System for Trading Application

This module provides a comprehensive signal management solution with proper state tracking,
history management, signal validation, and lifecycle management. It replaces the current
dictionary-based signal storage with a structured approach that includes timestamps,
confidence levels, and signal validation.
"""

import json
import threading
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Union, Literal, Any
from pathlib import Path
import logging
from datetime import datetime, timedelta
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Enumeration of signal types."""
    BUY = "buy"
    SELL = "sell"
    TREND = "trend"
    WAVE = "wave"
    BUY_CONDITION_A = "buy_condition_a"
    BUY_CONDITION_B = "buy_condition_b"
    BUY_CONDITION_C = "buy_condition_c"
    SELL_CONDITION_A = "sell_condition_a"
    SELL_CONDITION_B = "sell_condition_b"
    SELL_CONDITION_C = "sell_condition_c"


class SignalStatus(Enum):
    """Enumeration of signal statuses."""
    PENDING = "pending"
    ACTIVE = "active"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class Signal:
    """Individual signal data structure."""
    
    # Core signal properties
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str = ""
    signal_type: SignalType = SignalType.BUY
    status: SignalStatus = SignalStatus.PENDING
    
    # Signal values and metadata
    value: Union[bool, int, float] = False
    confidence: float = 0.0  # 0.0 to 1.0
    strength: float = 0.0    # Signal strength indicator
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # Signal context
    strategy_name: str = ""
    source_indicator: str = ""
    conditions_met: List[str] = field(default_factory=list)
    
    # Validation and lifecycle
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    lifecycle_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if isinstance(self.signal_type, str):
            self.signal_type = SignalType(self.signal_type)
        if isinstance(self.status, str):
            self.status = SignalStatus(self.status)
    
    def update_value(self, new_value: Union[bool, int, float], confidence: float = None, strength: float = None):
        """Update signal value and metadata."""
        old_value = self.value
        self.value = new_value
        self.updated_at = datetime.now()
        
        if confidence is not None:
            self.confidence = max(0.0, min(1.0, confidence))
        if strength is not None:
            self.strength = strength
            
        # Log lifecycle event
        self.lifecycle_events.append({
            "timestamp": self.updated_at.isoformat(),
            "event": "value_updated",
            "old_value": old_value,
            "new_value": new_value,
            "confidence": self.confidence,
            "strength": self.strength
        })
    
    def set_status(self, new_status: SignalStatus, reason: str = ""):
        """Update signal status with reason."""
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()
        
        # Log lifecycle event
        self.lifecycle_events.append({
            "timestamp": self.updated_at.isoformat(),
            "event": "status_changed",
            "old_status": old_status.value,
            "new_status": new_status.value,
            "reason": reason
        })
    
    def is_expired(self) -> bool:
        """Check if signal has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if signal is valid based on validation rules."""
        if self.is_expired():
            return False
        
        # Check confidence threshold
        min_confidence = self.validation_rules.get("min_confidence", 0.0)
        if self.confidence < min_confidence:
            return False
        
        # Check age limit
        max_age_minutes = self.validation_rules.get("max_age_minutes")
        if max_age_minutes:
            age = datetime.now() - self.created_at
            if age > timedelta(minutes=max_age_minutes):
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary."""
        data = asdict(self)
        data["signal_type"] = self.signal_type.value
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Signal":
        """Create signal from dictionary."""
        # Convert datetime strings back to datetime objects
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if "expires_at" in data and isinstance(data["expires_at"], str):
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        
        return cls(**data)


@dataclass
class SignalHistory:
    """Signal history container for a symbol."""
    
    symbol: str = ""
    signals: List[Signal] = field(default_factory=list)
    max_history_size: int = 1000
    
    def add_signal(self, signal: Signal):
        """Add signal to history."""
        self.signals.append(signal)
        
        # Maintain history size limit
        if len(self.signals) > self.max_history_size:
            self.signals = self.signals[-self.max_history_size:]
    
    def get_latest_signal(self, signal_type: SignalType) -> Optional[Signal]:
        """Get the latest signal of a specific type."""
        for signal in reversed(self.signals):
            if signal.signal_type == signal_type:
                return signal
        return None
    
    def get_active_signals(self, signal_type: Optional[SignalType] = None) -> List[Signal]:
        """Get all active signals, optionally filtered by type."""
        active_signals = []
        for signal in self.signals:
            if signal.status == SignalStatus.ACTIVE and signal.is_valid():
                if signal_type is None or signal.signal_type == signal_type:
                    active_signals.append(signal)
        return active_signals
    
    def get_signals_by_timeframe(self, start_time: datetime, end_time: datetime) -> List[Signal]:
        """Get signals within a specific timeframe."""
        return [
            signal for signal in self.signals
            if start_time <= signal.created_at <= end_time
        ]
    
    def cleanup_expired_signals(self):
        """Remove expired and old signals."""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(days=7)  # Keep signals for 7 days
        
        self.signals = [
            signal for signal in self.signals
            if signal.created_at > cutoff_time and not signal.is_expired()
        ]


class SignalManager:
    """
    Advanced signal manager for trading applications.
    
    Provides comprehensive signal management with state tracking, history management,
    validation, and lifecycle management.
    """
    
    def __init__(self, persistence_file: Optional[str] = None, auto_cleanup: bool = True):
        """
        Initialize the signal manager.
        
        Args:
            persistence_file: Optional file path for signal persistence
            auto_cleanup: Whether to automatically cleanup expired signals
        """
        self._lock = threading.RLock()
        self._signal_histories: Dict[str, SignalHistory] = {}
        self._active_signals: Dict[str, Dict[SignalType, Signal]] = {}
        self._persistence_file = persistence_file
        self._auto_cleanup = auto_cleanup
        
        # Default validation rules
        self._default_validation_rules = {
            "min_confidence": 0.0,
            "max_age_minutes": 60,  # 1 hour default
        }
        
        # Load persisted signals if file exists
        if self._persistence_file and Path(self._persistence_file).exists():
            self.load_signals()
        
        # Start cleanup thread if auto_cleanup is enabled
        if self._auto_cleanup:
            self._start_cleanup_thread()
    
    def create_signal(
        self,
        symbol: str,
        signal_type: SignalType,
        value: Union[bool, int, float],
        confidence: float = 0.5,
        strength: float = 0.0,
        strategy_name: str = "",
        source_indicator: str = "",
        conditions_met: List[str] = None,
        expires_in_minutes: Optional[int] = None,
        validation_rules: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> Signal:
        """
        Create a new signal.
        
        Args:
            symbol: Trading symbol
            signal_type: Type of signal
            value: Signal value
            confidence: Confidence level (0.0 to 1.0)
            strength: Signal strength
            strategy_name: Name of the strategy generating the signal
            source_indicator: Source indicator name
            conditions_met: List of conditions that were met
            expires_in_minutes: Signal expiration time in minutes
            validation_rules: Custom validation rules
            metadata: Additional metadata
            
        Returns:
            Created signal object
        """
        with self._lock:
            # Create signal
            signal = Signal(
                symbol=symbol,
                signal_type=signal_type,
                value=value,
                confidence=max(0.0, min(1.0, confidence)),
                strength=strength,
                strategy_name=strategy_name,
                source_indicator=source_indicator,
                conditions_met=conditions_met or [],
                validation_rules={**self._default_validation_rules, **(validation_rules or {})},
                metadata=metadata or {}
            )
            
            # Set expiration if specified
            if expires_in_minutes:
                signal.expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)
            
            # Set initial status
            signal.set_status(SignalStatus.ACTIVE, "Signal created")
            
            # Add to history
            if symbol not in self._signal_histories:
                self._signal_histories[symbol] = SignalHistory(symbol=symbol)
            self._signal_histories[symbol].add_signal(signal)
            
            # Update active signals
            if symbol not in self._active_signals:
                self._active_signals[symbol] = {}
            self._active_signals[symbol][signal_type] = signal
            
            # Auto-persist
            self._auto_persist()
            
            logger.debug(f"Created signal: {signal.signal_id} for {symbol} - {signal_type.value}")
            return signal
    
    def update_signal(
        self,
        symbol: str,
        signal_type: SignalType,
        value: Union[bool, int, float],
        confidence: float = None,
        strength: float = None,
        conditions_met: List[str] = None
    ) -> Optional[Signal]:
        """
        Update an existing signal or create a new one.
        
        Args:
            symbol: Trading symbol
            signal_type: Type of signal
            value: New signal value
            confidence: New confidence level
            strength: New signal strength
            conditions_met: Updated conditions met
            
        Returns:
            Updated or created signal
        """
        with self._lock:
            # Get existing signal
            existing_signal = self.get_active_signal(symbol, signal_type)
            
            if existing_signal:
                # Update existing signal
                existing_signal.update_value(value, confidence, strength)
                if conditions_met is not None:
                    existing_signal.conditions_met = conditions_met
                
                # Validate signal
                if not existing_signal.is_valid():
                    existing_signal.set_status(SignalStatus.EXPIRED, "Signal validation failed")
                    self._remove_active_signal(symbol, signal_type)
                
                self._auto_persist()
                return existing_signal
            else:
                # Create new signal if none exists
                return self.create_signal(
                    symbol=symbol,
                    signal_type=signal_type,
                    value=value,
                    confidence=confidence or 0.5,
                    strength=strength or 0.0,
                    conditions_met=conditions_met
                )
    
    def get_active_signal(self, symbol: str, signal_type: SignalType) -> Optional[Signal]:
        """Get active signal for symbol and type."""
        with self._lock:
            if symbol in self._active_signals and signal_type in self._active_signals[symbol]:
                signal = self._active_signals[symbol][signal_type]
                if signal.is_valid():
                    return signal
                else:
                    # Remove invalid signal
                    self._remove_active_signal(symbol, signal_type)
            return None
    
    def get_signal_value(self, symbol: str, signal_type: SignalType, default_value: Union[bool, int, float] = False) -> Union[bool, int, float]:
        """Get signal value with default fallback."""
        signal = self.get_active_signal(symbol, signal_type)
        return signal.value if signal else default_value
    
    def get_all_active_signals(self, symbol: str) -> Dict[SignalType, Signal]:
        """Get all active signals for a symbol."""
        with self._lock:
            if symbol not in self._active_signals:
                return {}
            
            valid_signals = {}
            invalid_types = []
            
            for signal_type, signal in self._active_signals[symbol].items():
                if signal.is_valid():
                    valid_signals[signal_type] = signal
                else:
                    invalid_types.append(signal_type)
            
            # Remove invalid signals
            for signal_type in invalid_types:
                self._remove_active_signal(symbol, signal_type)
            
            return valid_signals
    
    def confirm_signal(self, symbol: str, signal_type: SignalType, reason: str = "") -> bool:
        """Confirm a signal (mark as confirmed)."""
        with self._lock:
            signal = self.get_active_signal(symbol, signal_type)
            if signal:
                signal.set_status(SignalStatus.CONFIRMED, reason)
                self._auto_persist()
                return True
            return False
    
    def cancel_signal(self, symbol: str, signal_type: SignalType, reason: str = "") -> bool:
        """Cancel a signal."""
        with self._lock:
            signal = self.get_active_signal(symbol, signal_type)
            if signal:
                signal.set_status(SignalStatus.CANCELLED, reason)
                self._remove_active_signal(symbol, signal_type)
                self._auto_persist()
                return True
            return False
    
    def get_signal_history(self, symbol: str) -> Optional[SignalHistory]:
        """Get signal history for a symbol."""
        with self._lock:
            return self._signal_histories.get(symbol)
    
    def get_signal_statistics(self, symbol: str, signal_type: Optional[SignalType] = None) -> Dict[str, Any]:
        """Get signal statistics for a symbol."""
        with self._lock:
            history = self.get_signal_history(symbol)
            if not history:
                return {}
            
            signals = history.signals
            if signal_type:
                signals = [s for s in signals if s.signal_type == signal_type]
            
            if not signals:
                return {}
            
            # Calculate statistics
            total_signals = len(signals)
            active_signals = len([s for s in signals if s.status == SignalStatus.ACTIVE])
            confirmed_signals = len([s for s in signals if s.status == SignalStatus.CONFIRMED])
            cancelled_signals = len([s for s in signals if s.status == SignalStatus.CANCELLED])
            expired_signals = len([s for s in signals if s.status == SignalStatus.EXPIRED])
            
            avg_confidence = sum(s.confidence for s in signals) / total_signals
            avg_strength = sum(s.strength for s in signals) / total_signals
            
            return {
                "total_signals": total_signals,
                "active_signals": active_signals,
                "confirmed_signals": confirmed_signals,
                "cancelled_signals": cancelled_signals,
                "expired_signals": expired_signals,
                "average_confidence": avg_confidence,
                "average_strength": avg_strength,
                "confirmation_rate": confirmed_signals / total_signals if total_signals > 0 else 0,
                "cancellation_rate": cancelled_signals / total_signals if total_signals > 0 else 0
            }
    
    def validate_signal_combination(self, symbol: str, required_signals: List[SignalType]) -> bool:
        """Validate that all required signals are active and valid."""
        with self._lock:
            active_signals = self.get_all_active_signals(symbol)
            return all(signal_type in active_signals for signal_type in required_signals)
    
    def reset_symbol_signals(self, symbol: str):
        """Reset all signals for a symbol."""
        with self._lock:
            if symbol in self._active_signals:
                # Cancel all active signals
                for signal_type, signal in self._active_signals[symbol].items():
                    signal.set_status(SignalStatus.CANCELLED, "Symbol reset")
                del self._active_signals[symbol]
            
            # Clear history
            if symbol in self._signal_histories:
                del self._signal_histories[symbol]
            
            self._auto_persist()
    
    def cleanup_expired_signals(self):
        """Clean up expired and old signals."""
        with self._lock:
            # Clean up active signals
            symbols_to_clean = []
            for symbol, signals in self._active_signals.items():
                types_to_remove = []
                for signal_type, signal in signals.items():
                    if not signal.is_valid():
                        signal.set_status(SignalStatus.EXPIRED, "Signal expired during cleanup")
                        types_to_remove.append(signal_type)
                
                for signal_type in types_to_remove:
                    del signals[signal_type]
                
                if not signals:
                    symbols_to_clean.append(symbol)
            
            for symbol in symbols_to_clean:
                del self._active_signals[symbol]
            
            # Clean up histories
            for history in self._signal_histories.values():
                history.cleanup_expired_signals()
            
            self._auto_persist()
    
    def save_signals(self, file_path: Optional[str] = None) -> None:
        """Save signals to file."""
        save_path = file_path or self._persistence_file
        if not save_path:
            return
        
        with self._lock:
            try:
                data = {
                    "signal_histories": {
                        symbol: {
                            "symbol": history.symbol,
                            "signals": [signal.to_dict() for signal in history.signals],
                            "max_history_size": history.max_history_size
                        }
                        for symbol, history in self._signal_histories.items()
                    },
                    "active_signals": {
                        symbol: {
                            signal_type.value: signal.to_dict()
                            for signal_type, signal in signals.items()
                        }
                        for symbol, signals in self._active_signals.items()
                    },
                    "saved_at": datetime.now().isoformat()
                }
                
                with open(save_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                logger.debug(f"Signals saved to {save_path}")
                
            except Exception as e:
                logger.error(f"Failed to save signals: {e}")
    
    def load_signals(self, file_path: Optional[str] = None) -> bool:
        """Load signals from file."""
        load_path = file_path or self._persistence_file
        if not load_path or not Path(load_path).exists():
            return False
        
        with self._lock:
            try:
                with open(load_path, 'r') as f:
                    data = json.load(f)
                
                # Load signal histories
                self._signal_histories = {}
                for symbol, history_data in data.get("signal_histories", {}).items():
                    history = SignalHistory(
                        symbol=history_data["symbol"],
                        max_history_size=history_data.get("max_history_size", 1000)
                    )
                    history.signals = [
                        Signal.from_dict(signal_data)
                        for signal_data in history_data["signals"]
                    ]
                    self._signal_histories[symbol] = history
                
                # Load active signals
                self._active_signals = {}
                for symbol, signals_data in data.get("active_signals", {}).items():
                    self._active_signals[symbol] = {}
                    for signal_type_str, signal_data in signals_data.items():
                        signal_type = SignalType(signal_type_str)
                        signal = Signal.from_dict(signal_data)
                        self._active_signals[symbol][signal_type] = signal
                
                logger.debug(f"Signals loaded from {load_path}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load signals: {e}")
                return False
    
    def _remove_active_signal(self, symbol: str, signal_type: SignalType):
        """Remove active signal."""
        if symbol in self._active_signals and signal_type in self._active_signals[symbol]:
            del self._active_signals[symbol][signal_type]
            if not self._active_signals[symbol]:
                del self._active_signals[symbol]
    
    def _auto_persist(self):
        """Auto-persist signals if persistence is enabled."""
        if self._persistence_file:
            try:
                self.save_signals()
            except Exception as e:
                logger.error(f"Auto-persist failed: {e}")
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread."""
        def cleanup_worker():
            import time
            while True:
                try:
                    time.sleep(300)  # Run every 5 minutes
                    self.cleanup_expired_signals()
                except Exception as e:
                    logger.error(f"Cleanup thread error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()


# Global signal manager instance
_signal_manager: Optional[SignalManager] = None


def get_signal_manager() -> SignalManager:
    """Get the global signal manager instance."""
    global _signal_manager
    if _signal_manager is None:
        raise RuntimeError("Signal manager not initialized. Call initialize_signal_manager() first.")
    return _signal_manager


def initialize_signal_manager(persistence_file: Optional[str] = None, auto_cleanup: bool = True) -> SignalManager:
    """Initialize the global signal manager."""
    global _signal_manager
    _signal_manager = SignalManager(persistence_file=persistence_file, auto_cleanup=auto_cleanup)
    return _signal_manager


# Convenience functions for backward compatibility
def create_buy_signal(symbol: str, value: Union[bool, int], confidence: float = 0.5, **kwargs) -> Signal:
    """Create a buy signal."""
    return get_signal_manager().create_signal(symbol, SignalType.BUY, value, confidence, **kwargs)


def create_sell_signal(symbol: str, value: Union[bool, int], confidence: float = 0.5, **kwargs) -> Signal:
    """Create a sell signal."""
    return get_signal_manager().create_signal(symbol, SignalType.SELL, value, confidence, **kwargs)


def create_trend_signal(symbol: str, value: bool, confidence: float = 0.5, **kwargs) -> Signal:
    """Create a trend signal."""
    return get_signal_manager().create_signal(symbol, SignalType.TREND, value, confidence, **kwargs)


def create_wave_signal(symbol: str, value: Union[bool, int], confidence: float = 0.5, **kwargs) -> Signal:
    """Create a wave signal."""
    return get_signal_manager().create_signal(symbol, SignalType.WAVE, value, confidence, **kwargs)


def get_buy_signal(symbol: str, default_value: Union[bool, int] = False) -> Union[bool, int]:
    """Get buy signal value."""
    return get_signal_manager().get_signal_value(symbol, SignalType.BUY, default_value)


def get_sell_signal(symbol: str, default_value: Union[bool, int] = False) -> Union[bool, int]:
    """Get sell signal value."""
    return get_signal_manager().get_signal_value(symbol, SignalType.SELL, default_value)


def get_trend_signal(symbol: str, default_value: bool = False) -> bool:
    """Get trend signal value."""
    return get_signal_manager().get_signal_value(symbol, SignalType.TREND, default_value)


def get_wave_signal(symbol: str, default_value: Union[bool, int] = False) -> Union[bool, int]:
    """Get wave signal value."""
    return get_signal_manager().get_signal_value(symbol, SignalType.WAVE, default_value) 