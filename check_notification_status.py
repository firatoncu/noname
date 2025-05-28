#!/usr/bin/env python3
"""
Check and manage notification status.

This script helps diagnose and fix notification status issues.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.globals import get_notif_status, set_notif_status
from utils.load_config import load_config


def check_notification_status():
    """Check current notification status and configuration."""
    print("🔍 Checking notification status...")
    print("=" * 40)
    
    try:
        # Check global notification status
        notif_status = get_notif_status()
        print(f"📊 Global notification status: {'✅ ENABLED' if notif_status else '❌ DISABLED'}")
        
        # Check config file
        try:
            config = load_config()
            config_notif = config.get('notifications', {}).get('enabled', True)
            print(f"📋 Config notification setting: {'✅ ENABLED' if config_notif else '❌ DISABLED'}")
            
            # Check Telegram configuration
            telegram_config = config.get('telegram', {})
            has_token = bool(telegram_config.get('token'))
            has_chat_id = bool(telegram_config.get('chat_id'))
            
            print(f"🤖 Telegram bot token: {'✅ CONFIGURED' if has_token else '❌ MISSING'}")
            print(f"💬 Telegram chat ID: {'✅ CONFIGURED' if has_chat_id else '❌ MISSING'}")
            
            if has_token and has_chat_id:
                print("🎯 Telegram configuration appears complete")
            else:
                print("⚠️  Telegram configuration is incomplete")
                
        except Exception as e:
            print(f"❌ Error reading config: {e}")
            
    except Exception as e:
        print(f"❌ Error checking notification status: {e}")


def enable_notifications():
    """Enable notifications."""
    try:
        set_notif_status(True)
        print("✅ Notifications have been ENABLED")
        
        # Verify the change
        if get_notif_status():
            print("✅ Verification: Notifications are now enabled")
        else:
            print("❌ Verification failed: Notifications are still disabled")
            
    except Exception as e:
        print(f"❌ Error enabling notifications: {e}")


def disable_notifications():
    """Disable notifications."""
    try:
        set_notif_status(False)
        print("⚠️  Notifications have been DISABLED")
        
        # Verify the change
        if not get_notif_status():
            print("✅ Verification: Notifications are now disabled")
        else:
            print("❌ Verification failed: Notifications are still enabled")
            
    except Exception as e:
        print(f"❌ Error disabling notifications: {e}")


def main():
    """Main function."""
    print("🔔 Notification Status Manager")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Check notification status")
        print("2. Enable notifications")
        print("3. Disable notifications")
        print("4. Exit")
        
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                check_notification_status()
            elif choice == "2":
                enable_notifications()
            elif choice == "3":
                disable_notifications()
            elif choice == "4":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main() 