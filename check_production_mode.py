#!/usr/bin/env python3
"""
Check if the bot is properly configured for production mode
"""

import yaml
from pathlib import Path

def check_production_config():
    """Check if configuration is set for production"""
    print("🔍 Checking Production Configuration")
    print("=" * 40)
    
    config_path = Path("config.yml")
    if not config_path.exists():
        print("❌ config.yml not found")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False
    
    issues = []
    warnings = []
    
    # Check environment
    environment = config.get('environment', 'unknown')
    if environment != 'production':
        issues.append(f"Environment is '{environment}', should be 'production'")
    else:
        print("✅ Environment: production")
    
    # Check debug mode
    debug = config.get('debug', True)
    if debug:
        issues.append("Debug mode is enabled, should be false for production")
    else:
        print("✅ Debug: disabled")
    
    # Check testnet
    testnet = config.get('exchange', {}).get('testnet', True)
    if testnet:
        issues.append("Testnet is enabled, should be false for production")
    else:
        print("✅ Testnet: disabled (using real Binance)")
    
    # Check paper trading
    paper_trading = config.get('trading', {}).get('paper_trading', True)
    if paper_trading:
        issues.append("Paper trading is enabled, should be false for production")
    else:
        print("✅ Paper trading: disabled (real trading)")
    
    # Check API keys
    api_key = config.get('api_keys', {}).get('api_key', '')
    api_secret = config.get('api_keys', {}).get('api_secret', '')
    
    if api_key in ['your_binance_api_key_here', 'test_api_key', '']:
        issues.append("API key is not set to real credentials")
    elif len(api_key) < 20:
        warnings.append("API key seems too short")
    else:
        print(f"✅ API Key: {api_key[:8]}...{api_key[-8:]}")
    
    if api_secret in ['your_binance_api_secret_here', 'test_api_secret', '']:
        issues.append("API secret is not set to real credentials")
    elif len(api_secret) < 20:
        warnings.append("API secret seems too short")
    else:
        print("✅ API Secret: configured")
    
    # Check capital
    capital = config.get('capital_tbu', 0)
    if capital == 0:
        warnings.append("Capital is set to 0")
    elif capital == -999:
        print("✅ Capital: full balance mode")
    else:
        print(f"✅ Capital: {capital} USDT")
    
    # Check leverage
    leverage = config.get('symbols', {}).get('leverage', 1)
    if leverage > 10:
        warnings.append(f"High leverage ({leverage}x) - consider starting lower")
    else:
        print(f"✅ Leverage: {leverage}x")
    
    # Check symbols
    symbols = config.get('symbols', {}).get('symbols', [])
    if not symbols:
        issues.append("No trading symbols configured")
    else:
        print(f"✅ Symbols: {len(symbols)} pairs ({', '.join(symbols)})")
    
    print("\n" + "=" * 40)
    
    if issues:
        print("❌ PRODUCTION ISSUES FOUND:")
        for issue in issues:
            print(f"   • {issue}")
        print("\n🔧 Run 'python setup_production.py' to fix these issues")
        return False
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   • {warning}")
    
    if not issues:
        print("🎉 Configuration is ready for PRODUCTION!")
        print("\n🚀 You can start the bot with: python n0name.py")
        print("\n⚠️  REMEMBER:")
        print("   • This will trade with REAL MONEY")
        print("   • Start with small amounts")
        print("   • Monitor closely")
        return True

if __name__ == "__main__":
    check_production_config() 