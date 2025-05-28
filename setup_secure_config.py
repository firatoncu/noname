#!/usr/bin/env python3
"""
Setup script for secure configuration
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from auth.secure_config import get_secure_config_manager

def main():
    print("🔐 n0name Trading Bot - Secure Configuration Setup")
    print("=" * 50)
    print()
    print("This will create a new encrypted configuration file.")
    print("You'll need to provide:")
    print("  - Master password (12+ characters)")
    print("  - Binance API credentials")
    print("  - Web UI admin password")
    print("  - Optional: Telegram bot settings")
    print()
    
    response = input("Continue? (y/N): ").strip().lower()
    if response != 'y':
        print("Setup cancelled.")
        return
    
    try:
        secure_config = get_secure_config_manager()
        success = secure_config.initialize_secure_config(force_recreate=True)
        
        if success:
            print("\n🎉 Secure configuration created successfully!")
            print("You can now run: python start_secure.py")
        else:
            print("\n❌ Failed to create secure configuration.")
            
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")

if __name__ == "__main__":
    main() 