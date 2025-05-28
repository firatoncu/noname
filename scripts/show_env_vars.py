#!/usr/bin/env python3
"""
Environment Variables Viewer
This script helps you view environment variables safely in development and production
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def mask_sensitive_value(key: str, value: str) -> str:
    """Mask sensitive values for security"""
    sensitive_keywords = [
        'password', 'secret', 'key', 'token', 'api', 'jwt', 
        'auth', 'credential', 'private', 'secure'
    ]
    
    if any(keyword in key.lower() for keyword in sensitive_keywords):
        if len(value) <= 8:
            return '*' * len(value)
        else:
            return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"
    
    return value

def get_environment_type() -> str:
    """Determine the current environment type"""
    env = os.getenv('ENVIRONMENT', 'development').lower()
    if env in ['prod', 'production']:
        return 'production'
    elif env in ['dev', 'development']:
        return 'development'
    elif env in ['test', 'testing']:
        return 'testing'
    else:
        return 'unknown'

def load_env_file(file_path: Path) -> Dict[str, str]:
    """Load environment variables from a .env file"""
    env_vars = {}
    
    if not file_path.exists():
        return env_vars
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE format
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    env_vars[key] = value
                    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return env_vars

def show_environment_variables(show_sensitive: bool = False, format_output: str = 'table'):
    """Display environment variables"""
    
    print("🔍 Environment Variables Viewer")
    print("=" * 50)
    
    # Determine environment
    env_type = get_environment_type()
    print(f"📍 Environment: {env_type.upper()}")
    print()
    
    # Collect environment variables from different sources
    sources = {
        'System Environment': dict(os.environ),
        '.env file': load_env_file(project_root / '.env'),
        'env.example': load_env_file(project_root / 'env.example')
    }
    
    # Trading bot specific variables
    trading_vars = [
        'ENVIRONMENT', 'DEBUG', 'VERSION',
        'BINANCE_API_KEY', 'BINANCE_API_SECRET',
        'TRADING_CAPITAL', 'TRADING_LEVERAGE',
        'DATABASE_URL', 'REDIS_URL', 'INFLUXDB_URL',
        'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID',
        'EMAIL_USERNAME', 'EMAIL_PASSWORD',
        'JWT_SECRET', 'API_SECRET_KEY',
        'LOG_LEVEL', 'LOG_FORMAT'
    ]
    
    if format_output == 'json':
        # JSON output
        output = {}
        for source_name, env_vars in sources.items():
            output[source_name] = {}
            for key in trading_vars:
                if key in env_vars:
                    value = env_vars[key]
                    if not show_sensitive:
                        value = mask_sensitive_value(key, value)
                    output[source_name][key] = value
        
        print(json.dumps(output, indent=2))
        
    else:
        # Table output
        for source_name, env_vars in sources.items():
            print(f"📋 {source_name}")
            print("-" * 30)
            
            found_vars = []
            for key in trading_vars:
                if key in env_vars:
                    value = env_vars[key]
                    if not show_sensitive:
                        value = mask_sensitive_value(key, value)
                    found_vars.append((key, value))
            
            if found_vars:
                for key, value in found_vars:
                    print(f"  {key:<20} = {value}")
            else:
                print("  No relevant variables found")
            
            print()

def show_missing_variables():
    """Show which required variables are missing"""
    print("🔍 Missing Environment Variables Check")
    print("=" * 40)
    
    required_vars = [
        'BINANCE_API_KEY',
        'BINANCE_API_SECRET',
        'TRADING_CAPITAL'
    ]
    
    optional_vars = [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID',
        'DATABASE_URL',
        'REDIS_URL'
    ]
    
    print("📋 Required Variables:")
    missing_required = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            masked_value = mask_sensitive_value(var, value)
            print(f"  ✅ {var:<20} = {masked_value}")
        else:
            print(f"  ❌ {var:<20} = NOT SET")
            missing_required.append(var)
    
    print("\n📋 Optional Variables:")
    missing_optional = []
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            masked_value = mask_sensitive_value(var, value)
            print(f"  ✅ {var:<20} = {masked_value}")
        else:
            print(f"  ⚠️  {var:<20} = NOT SET")
            missing_optional.append(var)
    
    if missing_required:
        print(f"\n❌ Missing {len(missing_required)} required variables:")
        for var in missing_required:
            print(f"   - {var}")
        print("\n💡 Set these variables before running the trading bot!")
    
    if missing_optional:
        print(f"\n⚠️  Missing {len(missing_optional)} optional variables:")
        for var in missing_optional:
            print(f"   - {var}")
        print("\n💡 These are optional but recommended for full functionality.")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='View environment variables')
    parser.add_argument('--show-sensitive', action='store_true', 
                       help='Show actual values of sensitive variables (use with caution)')
    parser.add_argument('--format', choices=['table', 'json'], default='table',
                       help='Output format')
    parser.add_argument('--check-missing', action='store_true',
                       help='Check for missing required variables')
    
    args = parser.parse_args()
    
    if args.check_missing:
        show_missing_variables()
    else:
        show_environment_variables(args.show_sensitive, args.format)
    
    if args.show_sensitive:
        print("\n⚠️  WARNING: Sensitive values were displayed. Clear your terminal history!")

if __name__ == "__main__":
    main() 