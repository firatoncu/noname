"""
Example script demonstrating the new state management system.

This script shows how to use both the StateManager directly and the
compatibility layer for existing code.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.state_manager import get_state_manager, initialize_state_manager
import utils.globals as globals_compat


def demonstrate_state_manager():
    """Demonstrate direct StateManager usage."""
    print("=== Direct StateManager Usage ===")
    
    # Initialize with a custom persistence file
    state = initialize_state_manager("example_state.json")
    
    # Trading operations
    symbol = "BTCUSDT"
    
    print(f"Setting trading state for {symbol}...")
    state.set_clean_buy_signal(symbol, 1)
    state.set_clean_sell_signal(symbol, 0)
    state.set_sl_price(symbol, 45000.0)
    state.set_buyconda(symbol, True)
    state.set_sellconda(symbol, False)
    state.set_trend_signal(symbol, True)
    
    print(f"Buy signal: {state.get_clean_buy_signal(symbol)}")
    print(f"Sell signal: {state.get_clean_sell_signal(symbol)}")
    print(f"Stop loss price: {state.get_sl_price(symbol)}")
    print(f"Buy condition A: {state.get_buyconda(symbol)}")
    print(f"Sell condition A: {state.get_sellconda(symbol)}")
    print(f"Trend signal: {state.get_trend_signal(symbol)}")
    
    # System operations
    print("\nSetting system state...")
    state.set_error_counter(5)
    state.set_db_status(True)
    state.set_notif_status(True)
    
    print(f"Error counter: {state.get_error_counter()}")
    print(f"Database status: {state.get_db_status()}")
    print(f"Notification status: {state.get_notif_status()}")
    
    # UI operations
    print("\nSetting UI state...")
    state.set_strategy_name("Example Strategy")
    state.set_user_time_zone("EST")
    
    print(f"Strategy name: {state.get_strategy_name()}")
    print(f"User timezone: {state.get_user_time_zone()}")
    
    # Bulk operations
    print("\nBulk operations...")
    trading_state = state.get_all_trading_state()
    print(f"All trading signals: {trading_state['clean_buy_signals']}")
    
    # Increment error counter
    new_count = state.increment_error_counter()
    print(f"Incremented error counter: {new_count}")


def demonstrate_compatibility_layer():
    """Demonstrate compatibility layer usage."""
    print("\n=== Compatibility Layer Usage ===")
    
    symbol = "ETHUSDT"
    
    print(f"Setting state for {symbol} using old interface...")
    
    # Use the old interface - same function signatures as before
    globals_compat.set_clean_buy_signal(2, symbol)
    globals_compat.set_clean_sell_signal(1, symbol)
    globals_compat.set_sl_price(3000.0, symbol)
    globals_compat.set_buyconda(False, symbol)
    globals_compat.set_sellconda(True, symbol)
    
    print(f"Buy signal: {globals_compat.get_clean_buy_signal(symbol)}")
    print(f"Sell signal: {globals_compat.get_clean_sell_signal(symbol)}")
    print(f"Stop loss price: {globals_compat.get_sl_price(symbol)}")
    print(f"Buy condition A: {globals_compat.get_buyconda(symbol)}")
    print(f"Sell condition A: {globals_compat.get_sellconda(symbol)}")
    
    # System state
    globals_compat.set_error_counter(10)
    globals_compat.set_db_status(False)
    
    print(f"Error counter: {globals_compat.get_error_counter()}")
    print(f"Database status: {globals_compat.get_db_status()}")
    
    # UI state
    globals_compat.set_strategy_name("Compatibility Test")
    globals_compat.set_user_time_zone("PST")
    
    print(f"Strategy name: {globals_compat.get_strategy_name()}")
    print(f"User timezone: {globals_compat.get_user_time_zone()}")


def demonstrate_persistence():
    """Demonstrate state persistence."""
    print("\n=== State Persistence ===")
    
    state = get_state_manager()
    
    # Show current state
    print("Current state:")
    print(f"  Strategy: {state.get_strategy_name()}")
    print(f"  Error count: {state.get_error_counter()}")
    
    # Save state manually
    state.save_state("manual_backup.json")
    print("State saved to manual_backup.json")
    
    # Modify state
    state.set_strategy_name("Modified Strategy")
    state.set_error_counter(99)
    
    print("\nAfter modification:")
    print(f"  Strategy: {state.get_strategy_name()}")
    print(f"  Error count: {state.get_error_counter()}")
    
    # Load from backup
    success = state.load_state("manual_backup.json")
    if success:
        print("\nAfter loading backup:")
        print(f"  Strategy: {state.get_strategy_name()}")
        print(f"  Error count: {state.get_error_counter()}")
    else:
        print("Failed to load backup")


def demonstrate_thread_safety():
    """Demonstrate thread safety."""
    print("\n=== Thread Safety ===")
    
    import threading
    import time
    
    state = get_state_manager()
    symbol = "ADAUSDT"
    
    def worker(worker_id):
        """Worker function for threading test."""
        for i in range(10):
            state.set_clean_buy_signal(symbol, worker_id * 10 + i)
            value = state.get_clean_buy_signal(symbol)
            print(f"Worker {worker_id}: Set {worker_id * 10 + i}, Got {value}")
            time.sleep(0.01)  # Small delay
    
    # Create and start threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    final_value = state.get_clean_buy_signal(symbol)
    print(f"Final value: {final_value}")


def cleanup():
    """Clean up example files."""
    import os
    files_to_remove = ["example_state.json", "manual_backup.json"]
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"Cleaned up {file}")


if __name__ == "__main__":
    print("State Management System Example")
    print("=" * 40)
    
    try:
        demonstrate_state_manager()
        demonstrate_compatibility_layer()
        demonstrate_persistence()
        demonstrate_thread_safety()
        
        print("\n" + "=" * 40)
        print("✅ All demonstrations completed successfully!")
        print("\nKey benefits of the new system:")
        print("- Thread-safe operations")
        print("- Automatic state persistence")
        print("- Type safety with hints")
        print("- Organized state containers")
        print("- Backward compatibility")
        print("- Comprehensive error handling")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cleanup() 