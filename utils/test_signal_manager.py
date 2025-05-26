"""
Test and demonstration script for the SignalManager system.

This script demonstrates the key features of the new SignalManager including:
- Signal creation and management
- History tracking
- Validation and lifecycle management
- Backward compatibility with existing code
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from utils.signal_manager import (
    SignalManager, SignalType, SignalStatus, Signal, SignalHistory,
    initialize_signal_manager, get_signal_manager
)
from utils.signal_globals import (
    set_clean_buy_signal, get_clean_buy_signal,
    set_clean_sell_signal, get_clean_sell_signal,
    set_buyconda, get_buyconda,
    set_buycondb, get_buycondb,
    set_buycondc, get_buycondc,
    set_sellconda, get_sellconda,
    set_sellcondb, get_sellcondb,
    set_sellcondc, get_sellcondc,
    set_trend_signal, get_trend_signal,
    create_enhanced_buy_signal, create_enhanced_sell_signal,
    create_wave_signal, get_signal_statistics,
    validate_trading_signals, reset_symbol_signals,
    get_signal_history_summary
)


class TestSignalManager(unittest.TestCase):
    """Test the SignalManager functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary file for persistence testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        
        # Initialize signal manager with test file
        self.signal_manager = SignalManager(persistence_file=self.temp_file.name, auto_cleanup=False)
        
        # Test symbol
        self.test_symbol = "BTCUSDT"
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary file
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_signal_creation_and_retrieval(self):
        """Test basic signal creation and retrieval."""
        # Create a buy signal
        signal = self.signal_manager.create_signal(
            symbol=self.test_symbol,
            signal_type=SignalType.BUY,
            value=True,
            confidence=0.8,
            strength=0.9,
            strategy_name="Test Strategy",
            source_indicator="test_indicator",
            conditions_met=["condition1", "condition2"]
        )
        
        # Verify signal properties
        self.assertEqual(signal.symbol, self.test_symbol)
        self.assertEqual(signal.signal_type, SignalType.BUY)
        self.assertEqual(signal.value, True)
        self.assertEqual(signal.confidence, 0.8)
        self.assertEqual(signal.strength, 0.9)
        self.assertEqual(signal.strategy_name, "Test Strategy")
        self.assertEqual(signal.source_indicator, "test_indicator")
        self.assertEqual(signal.conditions_met, ["condition1", "condition2"])
        self.assertEqual(signal.status, SignalStatus.ACTIVE)
        
        # Retrieve signal
        retrieved_signal = self.signal_manager.get_active_signal(self.test_symbol, SignalType.BUY)
        self.assertIsNotNone(retrieved_signal)
        self.assertEqual(retrieved_signal.signal_id, signal.signal_id)
        
        # Get signal value
        value = self.signal_manager.get_signal_value(self.test_symbol, SignalType.BUY)
        self.assertEqual(value, True)
    
    def test_signal_update(self):
        """Test signal updating."""
        # Create initial signal
        self.signal_manager.create_signal(
            symbol=self.test_symbol,
            signal_type=SignalType.SELL,
            value=1,
            confidence=0.5
        )
        
        # Update signal
        updated_signal = self.signal_manager.update_signal(
            symbol=self.test_symbol,
            signal_type=SignalType.SELL,
            value=2,
            confidence=0.9,
            strength=0.8
        )
        
        # Verify update
        self.assertEqual(updated_signal.value, 2)
        self.assertEqual(updated_signal.confidence, 0.9)
        self.assertEqual(updated_signal.strength, 0.8)
        
        # Check lifecycle events
        self.assertTrue(len(updated_signal.lifecycle_events) > 0)
        self.assertEqual(updated_signal.lifecycle_events[-1]["event"], "value_updated")
    
    def test_signal_validation(self):
        """Test signal validation rules."""
        # Create signal with validation rules
        signal = self.signal_manager.create_signal(
            symbol=self.test_symbol,
            signal_type=SignalType.TREND,
            value=True,
            confidence=0.3,
            validation_rules={"min_confidence": 0.5, "max_age_minutes": 1}
        )
        
        # Signal should be invalid due to low confidence
        self.assertFalse(signal.is_valid())
        
        # Update confidence
        signal.update_value(True, confidence=0.7)
        self.assertTrue(signal.is_valid())
        
        # Test age validation (simulate old signal)
        signal.created_at = datetime.now() - timedelta(minutes=2)
        self.assertFalse(signal.is_valid())
    
    def test_signal_expiration(self):
        """Test signal expiration."""
        # Create signal with expiration
        signal = self.signal_manager.create_signal(
            symbol=self.test_symbol,
            signal_type=SignalType.WAVE,
            value=1,
            expires_in_minutes=1
        )
        
        # Signal should not be expired initially
        self.assertFalse(signal.is_expired())
        
        # Simulate expiration
        signal.expires_at = datetime.now() - timedelta(minutes=1)
        self.assertTrue(signal.is_expired())
        self.assertFalse(signal.is_valid())
    
    def test_signal_history(self):
        """Test signal history management."""
        # Create multiple signals
        for i in range(5):
            self.signal_manager.create_signal(
                symbol=self.test_symbol,
                signal_type=SignalType.BUY,
                value=i,
                confidence=0.5 + i * 0.1
            )
        
        # Get history
        history = self.signal_manager.get_signal_history(self.test_symbol)
        self.assertIsNotNone(history)
        self.assertEqual(len(history.signals), 5)
        
        # Get latest signal
        latest = history.get_latest_signal(SignalType.BUY)
        self.assertIsNotNone(latest)
        self.assertEqual(latest.value, 4)
    
    def test_signal_statistics(self):
        """Test signal statistics."""
        # Create signals with different statuses
        signal1 = self.signal_manager.create_signal(
            symbol=self.test_symbol,
            signal_type=SignalType.BUY,
            value=True,
            confidence=0.8
        )
        
        signal2 = self.signal_manager.create_signal(
            symbol=self.test_symbol,
            signal_type=SignalType.SELL,
            value=True,
            confidence=0.6
        )
        
        # Confirm one signal
        self.signal_manager.confirm_signal(self.test_symbol, SignalType.BUY, "Test confirmation")
        
        # Cancel another signal
        self.signal_manager.cancel_signal(self.test_symbol, SignalType.SELL, "Test cancellation")
        
        # Get statistics
        stats = self.signal_manager.get_signal_statistics(self.test_symbol)
        self.assertEqual(stats["total_signals"], 2)
        self.assertEqual(stats["confirmed_signals"], 1)
        self.assertEqual(stats["cancelled_signals"], 1)
        self.assertEqual(stats["average_confidence"], 0.7)
    
    def test_persistence(self):
        """Test signal persistence."""
        # Create signals
        self.signal_manager.create_signal(
            symbol=self.test_symbol,
            signal_type=SignalType.BUY,
            value=True,
            confidence=0.8
        )
        
        # Save signals
        self.signal_manager.save_signals()
        
        # Create new signal manager and load
        new_manager = SignalManager(persistence_file=self.temp_file.name, auto_cleanup=False)
        
        # Verify signals were loaded
        signal = new_manager.get_active_signal(self.test_symbol, SignalType.BUY)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.value, True)
        self.assertEqual(signal.confidence, 0.8)
    
    def test_backward_compatibility(self):
        """Test backward compatibility with existing global functions."""
        # Initialize global signal manager
        initialize_signal_manager(persistence_file=self.temp_file.name)
        
        # Test clean signals
        set_clean_buy_signal(2, self.test_symbol)
        self.assertEqual(get_clean_buy_signal(self.test_symbol), 2)
        
        set_clean_sell_signal(1, self.test_symbol)
        self.assertEqual(get_clean_sell_signal(self.test_symbol), 1)
        
        # Test buy conditions
        set_buyconda(True, self.test_symbol)
        self.assertTrue(get_buyconda(self.test_symbol))
        
        set_buycondb(False, self.test_symbol)
        self.assertFalse(get_buycondb(self.test_symbol))
        
        set_buycondc(True, self.test_symbol)
        self.assertTrue(get_buycondc(self.test_symbol))
        
        # Test sell conditions
        set_sellconda(True, self.test_symbol)
        self.assertTrue(get_sellconda(self.test_symbol))
        
        set_sellcondb(False, self.test_symbol)
        self.assertFalse(get_sellcondb(self.test_symbol))
        
        set_sellcondc(True, self.test_symbol)
        self.assertTrue(get_sellcondc(self.test_symbol))
        
        # Test trend signal
        set_trend_signal(True, self.test_symbol)
        self.assertTrue(get_trend_signal(self.test_symbol))
    
    def test_enhanced_signals(self):
        """Test enhanced signal creation functions."""
        # Initialize global signal manager
        initialize_signal_manager(persistence_file=self.temp_file.name)
        
        # Create enhanced buy signal
        buy_signal = create_enhanced_buy_signal(
            symbol=self.test_symbol,
            value=True,
            confidence=0.9,
            strength=0.8,
            strategy_name="Enhanced Strategy",
            source_indicator="enhanced_indicator",
            conditions_met=["enhanced_condition"],
            expires_in_minutes=30
        )
        
        self.assertIsNotNone(buy_signal)
        self.assertEqual(buy_signal.strategy_name, "Enhanced Strategy")
        self.assertEqual(buy_signal.source_indicator, "enhanced_indicator")
        self.assertEqual(buy_signal.conditions_met, ["enhanced_condition"])
        
        # Create wave signal
        wave_signal = create_wave_signal(
            symbol=self.test_symbol,
            value=2,
            confidence=0.7,
            wave_stage=2,
            strategy_name="Wave Strategy"
        )
        
        self.assertIsNotNone(wave_signal)
        self.assertEqual(wave_signal.metadata["wave_stage"], 2)
        self.assertIn("wave_stage_2", wave_signal.conditions_met)
    
    def test_signal_validation_combination(self):
        """Test signal combination validation."""
        # Initialize global signal manager
        initialize_signal_manager(persistence_file=self.temp_file.name)
        
        # Set up buy conditions
        set_buyconda(True, self.test_symbol)
        set_buycondb(True, self.test_symbol)
        set_buycondc(False, self.test_symbol)  # Missing condition
        
        # Validate signals
        validation = validate_trading_signals(self.test_symbol)
        self.assertFalse(validation["buy_conditions_valid"])
        self.assertFalse(validation["all_valid"])
        
        # Complete buy conditions
        set_buycondc(True, self.test_symbol)
        validation = validate_trading_signals(self.test_symbol)
        self.assertTrue(validation["buy_conditions_valid"])
    
    def test_signal_history_summary(self):
        """Test signal history summary function."""
        # Initialize global signal manager
        initialize_signal_manager(persistence_file=self.temp_file.name)
        
        # Create some signals
        create_enhanced_buy_signal(
            symbol=self.test_symbol,
            value=True,
            confidence=0.8,
            strategy_name="Test Strategy"
        )
        
        create_enhanced_sell_signal(
            symbol=self.test_symbol,
            value=True,
            confidence=0.6,
            strategy_name="Test Strategy"
        )
        
        # Get history summary
        summary = get_signal_history_summary(self.test_symbol)
        self.assertEqual(summary["total_signals"], 2)
        self.assertEqual(len(summary["recent_signals"]), 2)
        self.assertIn("statistics", summary)


def demonstrate_signal_manager():
    """Demonstrate SignalManager features."""
    print("=== SignalManager Demonstration ===\n")
    
    # Initialize signal manager
    signal_manager = SignalManager(auto_cleanup=False)
    symbol = "BTCUSDT"
    
    print("1. Creating signals with different types and metadata:")
    
    # Create buy signal
    buy_signal = signal_manager.create_signal(
        symbol=symbol,
        signal_type=SignalType.BUY,
        value=True,
        confidence=0.85,
        strength=0.9,
        strategy_name="MACD Crossover & Fibonacci",
        source_indicator="macd_crossover",
        conditions_met=["macd_crossover", "fibonacci_support"],
        expires_in_minutes=60
    )
    print(f"Created buy signal: {buy_signal.signal_id}")
    print(f"  - Value: {buy_signal.value}")
    print(f"  - Confidence: {buy_signal.confidence}")
    print(f"  - Strategy: {buy_signal.strategy_name}")
    print(f"  - Conditions: {buy_signal.conditions_met}")
    
    # Create wave signal
    wave_signal = signal_manager.create_signal(
        symbol=symbol,
        signal_type=SignalType.WAVE,
        value=2,
        confidence=0.7,
        strategy_name="Elliott Wave",
        source_indicator="wave_analysis",
        metadata={"wave_stage": 2, "wave_type": "impulse"}
    )
    print(f"\nCreated wave signal: {wave_signal.signal_id}")
    print(f"  - Wave stage: {wave_signal.metadata['wave_stage']}")
    print(f"  - Wave type: {wave_signal.metadata['wave_type']}")
    
    print("\n2. Updating signals:")
    
    # Update buy signal
    updated_signal = signal_manager.update_signal(
        symbol=symbol,
        signal_type=SignalType.BUY,
        value=True,
        confidence=0.95,
        strength=0.95,
        conditions_met=["macd_crossover", "fibonacci_support", "volume_confirmation"]
    )
    print(f"Updated buy signal confidence: {updated_signal.confidence}")
    print(f"New conditions: {updated_signal.conditions_met}")
    
    print("\n3. Signal lifecycle events:")
    for event in updated_signal.lifecycle_events:
        print(f"  - {event['timestamp']}: {event['event']}")
    
    print("\n4. Getting all active signals:")
    active_signals = signal_manager.get_all_active_signals(symbol)
    for signal_type, signal in active_signals.items():
        print(f"  - {signal_type.value}: {signal.value} (confidence: {signal.confidence})")
    
    print("\n5. Signal statistics:")
    stats = signal_manager.get_signal_statistics(symbol)
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    print("\n6. Confirming and cancelling signals:")
    signal_manager.confirm_signal(symbol, SignalType.BUY, "Trade executed successfully")
    signal_manager.cancel_signal(symbol, SignalType.WAVE, "Wave pattern invalidated")
    
    print("\n7. Updated statistics after status changes:")
    stats = signal_manager.get_signal_statistics(symbol)
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    print("\n8. Backward compatibility demonstration:")
    
    # Initialize global signal manager for compatibility functions
    initialize_signal_manager()
    
    # Use old-style functions
    set_clean_buy_signal(2, symbol)
    set_buyconda(True, symbol)
    set_buycondb(True, symbol)
    set_buycondc(True, symbol)
    set_trend_signal(True, symbol)
    
    print(f"Clean buy signal: {get_clean_buy_signal(symbol)}")
    print(f"Buy condition A: {get_buyconda(symbol)}")
    print(f"Buy condition B: {get_buycondb(symbol)}")
    print(f"Buy condition C: {get_buycondc(symbol)}")
    print(f"Trend signal: {get_trend_signal(symbol)}")
    
    # Validate trading signals
    validation = validate_trading_signals(symbol)
    print(f"\nSignal validation: {validation}")
    
    print("\n9. Enhanced signal creation:")
    enhanced_signal = create_enhanced_buy_signal(
        symbol=symbol,
        value=True,
        confidence=0.9,
        strength=0.85,
        strategy_name="Enhanced MACD Strategy",
        source_indicator="enhanced_macd",
        conditions_met=["macd_divergence", "rsi_oversold", "support_level"],
        expires_in_minutes=45
    )
    print(f"Enhanced signal created: {enhanced_signal.signal_id}")
    print(f"  - Strategy: {enhanced_signal.strategy_name}")
    print(f"  - Expires at: {enhanced_signal.expires_at}")
    
    print("\n=== Demonstration Complete ===")


if __name__ == "__main__":
    # Run demonstration
    demonstrate_signal_manager()
    
    print("\n" + "="*50)
    print("Running unit tests...")
    print("="*50)
    
    # Run tests
    unittest.main(verbosity=2) 