#!/usr/bin/env python3
"""
Update Binance API keys in secure configuration
"""

import sys
import getpass
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from auth.secure_config import get_secure_config_manager

def main():
    print("🔑 Update Binance API Keys")
    print("=" * 30)
    print()
    
    try:
        secure_config = get_secure_config_manager()
        
        # Load current configuration
        print("Loading current secure configuration...")
        master_password = getpass.getpass("Enter master password: ")
        config_data = secure_config.load_secure_config(master_password)
        
        if not config_data:
            print("❌ Failed to load configuration. Check your master password.")
            return
        
        print("✅ Configuration loaded successfully!")
        print()
        
        # Show current API key (masked)
        current_key = config_data.api_key
        if current_key:
            masked_key = current_key[:8] + "..." + current_key[-8:] if len(current_key) > 16 else "***"
            print(f"Current API Key: {masked_key}")
        else:
            print("Current API Key: (empty)")
        
        print()
        print("Enter new Binance API credentials:")
        print("(Leave blank to keep current values)")
        print()
        
        # Get new API key
        new_api_key = input("New Binance API Key: ").strip()
        if new_api_key:
            config_data.api_key = new_api_key
            print("✅ API Key updated")
        else:
            print("⏭️  API Key unchanged")
        
        # Get new API secret
        new_api_secret = getpass.getpass("New Binance API Secret: ").strip()
        if new_api_secret:
            config_data.api_secret = new_api_secret
            print("✅ API Secret updated")
        else:
            print("⏭️  API Secret unchanged")
        
        # Save updated configuration
        if new_api_key or new_api_secret:
            print("\nSaving updated configuration...")
            success = secure_config.save_secure_config(config_data, master_password)
            
            if success:
                print("🎉 API credentials updated successfully!")
                print("\nYou can now restart the trading bot:")
                print("  python start_secure.py")
            else:
                print("❌ Failed to save configuration")
        else:
            print("\n⏭️  No changes made")
            
    except KeyboardInterrupt:
        print("\n\nUpdate cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 