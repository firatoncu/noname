#!/usr/bin/env python3
"""
Production Setup Script for n0name Trading Bot

This script helps you set up the trading bot for production use with real API keys.
"""

import sys
import yaml
import getpass
from pathlib import Path

def main():
    print("🚀 n0name Trading Bot - Production Setup")
    print("=" * 50)
    print()
    print("⚠️  IMPORTANT: This will configure the bot for REAL TRADING")
    print("   Make sure you understand the risks before proceeding.")
    print()
    
    # Confirm production setup
    confirm = input("Do you want to set up the bot for production trading? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("Setup cancelled.")
        return
    
    print("\n📋 Production Configuration")
    print("-" * 30)
    
    # Get API credentials
    print("\n🔑 Binance API Credentials")
    print("You can get these from: https://www.binance.com/en/my/settings/api-management")
    print()
    
    api_key = input("Enter your Binance API Key: ").strip()
    if not api_key:
        print("❌ API Key is required")
        return
    
    api_secret = getpass.getpass("Enter your Binance API Secret: ").strip()
    if not api_secret:
        print("❌ API Secret is required")
        return
    
    # Trading configuration
    print("\n⚙️  Trading Configuration")
    print("-" * 25)
    
    # Capital amount
    while True:
        try:
            capital_input = input("Enter capital amount (or -999 for full balance): ").strip()
            capital = float(capital_input)
            if capital != -999.0 and capital <= 0:
                print("❌ Capital must be positive or -999 for full balance")
                continue
            break
        except ValueError:
            print("❌ Please enter a valid number")
    
    # Leverage
    while True:
        try:
            leverage = int(input("Enter leverage (1-125): ").strip())
            if leverage < 1 or leverage > 125:
                print("❌ Leverage must be between 1 and 125")
                continue
            break
        except ValueError:
            print("❌ Please enter a valid number")
    
    # Max positions
    while True:
        try:
            max_positions = int(input("Enter max open positions (1-10): ").strip())
            if max_positions < 1 or max_positions > 10:
                print("❌ Max positions must be between 1 and 10")
                continue
            break
        except ValueError:
            print("❌ Please enter a valid number")
    
    # Trading symbols
    print("\nDefault symbols: BTCUSDT, ETHUSDT, XRPUSDT, SOLUSDT, ADAUSDT, DOGEUSDT")
    use_default_symbols = input("Use default symbols? (y/n): ").strip().lower()
    
    if use_default_symbols in ['y', 'yes']:
        symbols = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "ADAUSDT", "DOGEUSDT"]
    else:
        symbols_input = input("Enter symbols (comma-separated, e.g., BTCUSDT,ETHUSDT): ").strip()
        symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
        if not symbols:
            print("❌ At least one symbol is required")
            return
    
    # Load current config
    config_path = Path("config.yml")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Update configuration
    config['environment'] = 'production'
    config['debug'] = False
    config['api_keys']['api_key'] = api_key
    config['api_keys']['api_secret'] = api_secret
    config['capital_tbu'] = capital
    config['symbols']['leverage'] = leverage
    config['symbols']['max_open_positions'] = max_positions
    config['symbols']['symbols'] = symbols
    config['trading']['capital'] = capital
    config['trading']['leverage'] = leverage
    config['trading']['symbols'] = symbols
    config['trading']['risk']['max_open_positions'] = max_positions
    config['trading']['paper_trading'] = False
    config['exchange']['testnet'] = False
    
    # Save configuration
    try:
        # Create backup
        backup_path = config_path.with_suffix('.yml.backup')
        if config_path.exists():
            config_path.rename(backup_path)
            print(f"✅ Backup created: {backup_path}")
        
        # Save new config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        print(f"✅ Configuration saved to {config_path}")
        
    except Exception as e:
        print(f"❌ Error saving config: {e}")
        return
    
    print("\n🎉 Production setup completed successfully!")
    print()
    print("📋 Configuration Summary:")
    print(f"   • API Key: {api_key[:8]}...{api_key[-8:]}")
    print(f"   • Capital: {capital}")
    print(f"   • Leverage: {leverage}x")
    print(f"   • Max Positions: {max_positions}")
    print(f"   • Symbols: {', '.join(symbols)}")
    print(f"   • Paper Trading: Disabled")
    print(f"   • Testnet: Disabled")
    print()
    print("⚠️  IMPORTANT REMINDERS:")
    print("   • Start with small amounts to test the strategy")
    print("   • Monitor the bot closely, especially initially")
    print("   • Make sure you understand the risks of automated trading")
    print("   • Keep your API keys secure and never share them")
    print()
    print("🚀 You can now start the bot with: python n0name.py")

if __name__ == "__main__":
    main() 