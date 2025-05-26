"""
Test suite for the new state management system.

This module tests both the StateManager class directly and the compatibility
layer to ensure everything works as expected.
"""

import unittest
import tempfile
import os
import json
import sys
from pathlib import Path
import threading
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.state_manager import StateManager, get_state_manager, initialize_state_manager
import utils.globals as globals_compat


class TestStateManager(unittest.TestCase):
    """Test the StateManager class directly."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.state_manager = StateManager(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_trading_state_operations(self):
        """Test trading state operations."""
        symbol = "BTCUSDT"
        
        # Test clean signals
        self.state_manager.set_clean_buy_signal(symbol, 1)
        self.assertEqual(self.state_manager.get_clean_buy_signal(symbol), 1)
        
        self.state_manager.set_clean_sell_signal(symbol, 2)
        self.assertEqual(self.state_manager.get_clean_sell_signal(symbol), 2)
        
        # Test prices and timestamps
        self.state_manager.set_sl_price(symbol, 45000.0)
        self.assertEqual(self.state_manager.get_sl_price(symbol), 45000.0)
        
        self.state_manager.set_last_timestamp(symbol, 1234567890)
        self.assertEqual(self.state_manager.get_last_timestamp(symbol), 1234567890)
        
        # Test buy conditions
        self.state_manager.set_buyconda(symbol, True)
        self.assertTrue(self.state_manager.get_buyconda(symbol))
        
        self.state_manager.set_buycondb(symbol, False)
        self.assertFalse(self.state_manager.get_buycondb(symbol))
        
        self.state_manager.set_buycondc(symbol, True)
        self.assertTrue(self.state_manager.get_buycondc(symbol))
        
        # Test sell conditions
        self.state_manager.set_sellconda(symbol, False)
        self.assertFalse(self.state_manager.get_sellconda(symbol))
        
        self.state_manager.set_sellcondb(symbol, True)
        self.assertTrue(self.state_manager.get_sellcondb(symbol))
        
        self.state_manager.set_sellcondc(symbol, False)
        self.assertFalse(self.state_manager.get_sellcondc(symbol))
        
        # Test flags and signals
        self.state_manager.set_funding_flag(symbol, True)
        self.assertTrue(self.state_manager.get_funding_flag(symbol))
        
        self.state_manager.set_trend_signal(symbol, False)
        self.assertFalse(self.state_manager.get_trend_signal(symbol))
        
        # Test orders
        self.state_manager.set_order_status(symbol, "FILLED")
        self.assertEqual(self.state_manager.get_order_status(symbol), "FILLED")
        
        order_data = {"price": 45000, "quantity": 0.1}
        self.state_manager.set_limit_order(symbol, order_data)
        self.assertEqual(self.state_manager.get_limit_order(symbol), order_data)
        
        # Test capital
        self.state_manager.set_capital_tbu(10000.0)
        self.assertEqual(self.state_manager.get_capital_tbu(), 10000.0)
    
    def test_system_state_operations(self):
        """Test system state operations."""
        # Test error counter
        self.state_manager.set_error_counter(5)
        self.assertEqual(self.state_manager.get_error_counter(), 5)
        
        # Test increment
        new_count = self.state_manager.increment_error_counter()
        self.assertEqual(new_count, 6)
        self.assertEqual(self.state_manager.get_error_counter(), 6)
        
        # Test database status
        self.state_manager.set_db_status(True)
        self.assertTrue(self.state_manager.get_db_status())
        
        # Test notification status
        self.state_manager.set_notif_status(False)
        self.assertFalse(self.state_manager.get_notif_status())
    
    def test_ui_state_operations(self):
        """Test UI state operations."""
        # Test timezone
        self.state_manager.set_user_time_zone("EST")
        self.assertEqual(self.state_manager.get_user_time_zone(), "EST")
        
        # Test strategy name
        self.state_manager.set_strategy_name("Test Strategy")
        self.assertEqual(self.state_manager.get_strategy_name(), "Test Strategy")
    
    def test_bulk_operations(self):
        """Test bulk state operations."""
        symbol = "ETHUSDT"
        
        # Set some state
        self.state_manager.set_clean_buy_signal(symbol, 1)
        self.state_manager.set_buyconda(symbol, True)
        self.state_manager.set_sl_price(symbol, 3000.0)
        
        # Get all trading state
        trading_state = self.state_manager.get_all_trading_state()
        self.assertIn(symbol, trading_state['clean_buy_signals'])
        self.assertEqual(trading_state['clean_buy_signals'][symbol], 1)
        
        # Reset symbol state
        self.state_manager.reset_symbol_state(symbol)
        
        # Verify state is cleared
        self.assertEqual(self.state_manager.get_clean_buy_signal(symbol), 0)
        self.assertFalse(self.state_manager.get_buyconda(symbol))
        self.assertEqual(self.state_manager.get_sl_price(symbol), 0.0)
    
    def test_persistence(self):
        """Test state persistence."""
        symbol = "ADAUSDT"
        
        # Set some state
        self.state_manager.set_clean_buy_signal(symbol, 3)
        self.state_manager.set_strategy_name("Persistence Test")
        self.state_manager.set_error_counter(10)
        
        # Save state
        self.state_manager.save_state()
        
        # Create new state manager with same file
        new_state_manager = StateManager(self.temp_file.name)
        
        # Verify state was loaded
        self.assertEqual(new_state_manager.get_clean_buy_signal(symbol), 3)
        self.assertEqual(new_state_manager.get_strategy_name(), "Persistence Test")
        self.assertEqual(new_state_manager.get_error_counter(), 10)
    
    def test_thread_safety(self):
        """Test thread safety of state operations."""
        symbol = "DOTUSDT"
        num_threads = 10
        operations_per_thread = 100
        
        def worker():
            for i in range(operations_per_thread):
                self.state_manager.set_clean_buy_signal(symbol, i)
                value = self.state_manager.get_clean_buy_signal(symbol)
                self.assertIsInstance(value, int)
        
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify final state is consistent
        final_value = self.state_manager.get_clean_buy_signal(symbol)
        self.assertIsInstance(final_value, int)
        self.assertGreaterEqual(final_value, 0)
        self.assertLess(final_value, operations_per_thread)


class TestCompatibilityLayer(unittest.TestCase):
    """Test the compatibility layer (globals.py)."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Initialize a fresh state manager for testing
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_file.close()
        self.temp_file_name = temp_file.name
        initialize_state_manager(self.temp_file_name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file_name):
            os.unlink(self.temp_file_name)
    
    def test_compatibility_functions(self):
        """Test that all compatibility functions work as expected."""
        symbol = "BTCUSDT"
        
        # Test clean signals
        globals_compat.set_clean_buy_signal(1, symbol)
        self.assertEqual(globals_compat.get_clean_buy_signal(symbol), 1)
        
        globals_compat.set_clean_sell_signal(2, symbol)
        self.assertEqual(globals_compat.get_clean_sell_signal(symbol), 2)
        
        # Test prices and timestamps
        globals_compat.set_sl_price(45000.0, symbol)
        self.assertEqual(globals_compat.get_sl_price(symbol), 45000.0)
        
        globals_compat.set_last_timestamp(1234567890, symbol)
        self.assertEqual(globals_compat.get_last_timestamp(symbol), 1234567890)
        
        # Test buy conditions
        globals_compat.set_buyconda(True, symbol)
        self.assertTrue(globals_compat.get_buyconda(symbol))
        
        globals_compat.set_buycondb(False, symbol)
        self.assertFalse(globals_compat.get_buycondb(symbol))
        
        globals_compat.set_buycondc(True, symbol)
        self.assertTrue(globals_compat.get_buycondc(symbol))
        
        # Test sell conditions
        globals_compat.set_sellconda(False, symbol)
        self.assertFalse(globals_compat.get_sellconda(symbol))
        
        globals_compat.set_sellcondb(True, symbol)
        self.assertTrue(globals_compat.get_sellcondb(symbol))
        
        globals_compat.set_sellcondc(False, symbol)
        self.assertFalse(globals_compat.get_sellcondc(symbol))
        
        # Test flags and signals
        globals_compat.set_funding_flag(True, symbol)
        self.assertTrue(globals_compat.get_funding_flag(symbol))
        
        globals_compat.set_trend_signal(False, symbol)
        self.assertFalse(globals_compat.get_trend_signal(symbol))
        
        # Test orders
        globals_compat.set_order_status("FILLED", symbol)
        self.assertEqual(globals_compat.get_order_status(symbol), "FILLED")
        
        order_data = {"price": 45000, "quantity": 0.1}
        globals_compat.set_limit_order(order_data, symbol)
        self.assertEqual(globals_compat.get_limit_order(symbol), order_data)
        
        # Test capital
        globals_compat.set_capital_tbu(10000.0)
        self.assertEqual(globals_compat.get_capital_tbu(), 10000.0)
        
        # Test system state
        globals_compat.set_error_counter(5)
        self.assertEqual(globals_compat.get_error_counter(), 5)
        
        globals_compat.set_db_status(True)
        self.assertTrue(globals_compat.get_db_status())
        
        globals_compat.set_notif_status(False)
        self.assertFalse(globals_compat.get_notif_status())
        
        # Test UI state
        globals_compat.set_user_time_zone("EST")
        self.assertEqual(globals_compat.get_user_time_zone(), "EST")
        
        globals_compat.set_strategy_name("Test Strategy")
        self.assertEqual(globals_compat.get_strategy_name(), "Test Strategy")
    
    def test_legacy_variables_exist(self):
        """Test that legacy global variables exist for compatibility."""
        # These should exist but not be actively used
        self.assertIsInstance(globals_compat.clean_sell_signal, dict)
        self.assertIsInstance(globals_compat.clean_buy_signal, dict)
        self.assertIsInstance(globals_compat.sl_price, dict)
        self.assertIsInstance(globals_compat.last_timestamp, dict)
        self.assertIsInstance(globals_compat.buyconda, dict)
        self.assertIsInstance(globals_compat.buycondb, dict)
        self.assertIsInstance(globals_compat.buycondc, dict)
        self.assertIsInstance(globals_compat.sellconda, dict)
        self.assertIsInstance(globals_compat.sellcondb, dict)
        self.assertIsInstance(globals_compat.sellcondc, dict)
        self.assertIsInstance(globals_compat.funding_flag, dict)
        self.assertIsInstance(globals_compat.trend_signal, dict)
        self.assertIsInstance(globals_compat.order_status, dict)
        self.assertIsInstance(globals_compat.limit_order, dict)
        
        self.assertIsInstance(globals_compat.error_counter, int)
        self.assertIsInstance(globals_compat.db_status, bool)
        self.assertIsInstance(globals_compat.notif_status, bool)
        self.assertIsInstance(globals_compat.user_time_zone, str)
        self.assertIsInstance(globals_compat.strategy_name, str)


def run_tests():
    """Run all tests."""
    # Create test suite using modern approach
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(loader.loadTestsFromTestCase(TestStateManager))
    suite.addTest(loader.loadTestsFromTestCase(TestCompatibilityLayer))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n✅ All tests passed! The new state management system is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the output above.") 