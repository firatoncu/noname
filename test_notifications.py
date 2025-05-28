#!/usr/bin/env python3
"""
Test script for Telegram notification system.

This script tests all notification functions to ensure they work properly.
Run this script to verify your Telegram bot configuration and notification formatting.

Usage:
    python test_notifications.py
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.send_notification import (
    send_position_open_alert,
    send_position_close_alert,
    send_tp_limit_filled_alert
)
from utils.load_config import load_config


async def test_telegram_config():
    """Test if Telegram configuration is properly loaded."""
    try:
        config = load_config()
        telegram_config = config.get('telegram', {})
        
        token = telegram_config.get('token')
        chat_id = telegram_config.get('chat_id')
        
        if not token:
            print("❌ Telegram bot token not found in config.yml")
            return False
        
        if not chat_id:
            print("❌ Telegram chat_id not found in config.yml")
            return False
        
        print(f"✅ Telegram configuration found:")
        print(f"   Token: {token[:10]}...{token[-10:] if len(token) > 20 else token}")
        print(f"   Chat ID: {chat_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False


async def test_position_open_notifications():
    """Test position open notifications."""
    print("\n🧪 Testing position open notifications...")
    
    test_cases = [
        ("BTCUSDT", "LONG"),
        ("ETHUSDT", "SHORT"),
        ("SOLUSDT", "LONG"),
    ]
    
    for symbol, side in test_cases:
        try:
            print(f"   📤 Sending {side} position open alert for {symbol}...")
            await send_position_open_alert(symbol, side)
            await asyncio.sleep(2)  # Wait between messages
            print(f"   ✅ {symbol} {side} position open notification sent successfully")
        except Exception as e:
            print(f"   ❌ Failed to send {symbol} {side} position open notification: {e}")


async def test_position_close_notifications():
    """Test position close notifications."""
    print("\n🧪 Testing position close notifications...")
    
    test_cases = [
        # (tp, symbol, side, profit)
        (True, "BTCUSDT", "LONG", 25.50),    # Take profit
        (False, "ETHUSDT", "SHORT", 12.75),  # Stop loss
        (True, "SOLUSDT", "SHORT", 8.90),    # Take profit
        (False, "ADAUSDT", "LONG", 5.25),    # Stop loss
    ]
    
    for tp, symbol, side, profit in test_cases:
        try:
            action = "Take Profit" if tp else "Stop Loss"
            print(f"   📤 Sending {side} {action} alert for {symbol} (${profit})...")
            await send_position_close_alert(tp, symbol, side, profit)
            await asyncio.sleep(2)  # Wait between messages
            print(f"   ✅ {symbol} {side} {action} notification sent successfully")
        except Exception as e:
            print(f"   ❌ Failed to send {symbol} {side} {action} notification: {e}")


async def test_limit_order_notifications():
    """Test limit order filled notifications."""
    print("\n🧪 Testing limit order filled notifications...")
    
    test_cases = [
        ("BTCUSDT", "LONG"),
        ("ETHUSDT", "SHORT"),
    ]
    
    for symbol, side in test_cases:
        try:
            print(f"   📤 Sending {side} limit order filled alert for {symbol}...")
            await send_tp_limit_filled_alert(symbol, side)
            await asyncio.sleep(2)  # Wait between messages
            print(f"   ✅ {symbol} {side} limit order notification sent successfully")
        except Exception as e:
            print(f"   ❌ Failed to send {symbol} {side} limit order notification: {e}")


async def main():
    """Main test function."""
    print("🚀 Starting Telegram Notification System Test")
    print("=" * 50)
    
    # Test configuration
    config_ok = await test_telegram_config()
    if not config_ok:
        print("\n❌ Configuration test failed. Please check your config.yml file.")
        return
    
    print("\n⚠️  This test will send actual messages to your Telegram chat.")
    print("   Make sure you want to receive test notifications before proceeding.")
    
    # Ask for confirmation
    try:
        response = input("\nDo you want to proceed with sending test notifications? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Test cancelled by user.")
            return
    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
        return
    
    print("\n🎯 Starting notification tests...")
    
    try:
        # Test all notification types
        await test_position_open_notifications()
        await test_position_close_notifications()
        await test_limit_order_notifications()
        
        print("\n" + "=" * 50)
        print("✅ All notification tests completed successfully!")
        print("📱 Check your Telegram chat to verify the messages were received.")
        print("🎨 The messages should have beautiful formatting with emojis and proper structure.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}") 