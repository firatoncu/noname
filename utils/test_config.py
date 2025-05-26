#!/usr/bin/env python3
"""
Simple test script for the new configuration management system.
This verifies basic functionality and compatibility.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path so we can import utils
sys.path.append(str(Path(__file__).parent.parent))

def test_basic_functionality():
    """Test basic configuration loading and validation."""
    print("🧪 Testing basic functionality...")
    
    try:
        from utils.config_models import AppConfig, ConfigDefaults
        from utils.config_manager import ConfigManager, ConfigurationError
        
        # Test default configuration
        default_config = ConfigDefaults.get_default_config()
        config = AppConfig(**default_config)
        
        print("✅ Default configuration validation passed")
        print(f"   Username: {config.username}")
        print(f"   Symbols: {config.symbols.symbols}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False


def test_validation():
    """Test configuration validation."""
    print("\n🧪 Testing validation...")
    
    try:
        from utils.config_models import AppConfig
        from pydantic import ValidationError
        
        # Test invalid leverage
        try:
            AppConfig(
                username="Test",
                api_keys={"api_key": "test", "api_secret": "test"},
                telegram={"token": "test", "chat_id": "123"},
                symbols={"leverage": 200}  # Invalid: too high
            )
            print("❌ Validation should have failed for invalid leverage")
            return False
        except ValidationError:
            print("✅ Validation correctly caught invalid leverage")
        
        # Test invalid symbols
        try:
            AppConfig(
                username="Test",
                api_keys={"api_key": "test", "api_secret": "test"},
                telegram={"token": "test", "chat_id": "123"},
                symbols={"symbols": ["INVALID"]}  # Invalid: doesn't end with USDT
            )
            print("❌ Validation should have failed for invalid symbols")
            return False
        except ValidationError:
            print("✅ Validation correctly caught invalid symbols")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False


def test_environment_variables():
    """Test environment variable configuration."""
    print("\n🧪 Testing environment variables...")
    
    try:
        from utils.config_manager import ConfigManager
        
        # Set test environment variables
        test_env = {
            "NONAME_USERNAME": "EnvTestUser",
            "NONAME_LEVERAGE": "7",
            "NONAME_SYMBOLS": "BTCUSDT,ETHUSDT"
        }
        
        # Save original values
        original_env = {}
        for key in test_env:
            original_env[key] = os.environ.get(key)
            os.environ[key] = test_env[key]
        
        try:
            # Create a temporary config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                f.write("""
username: "FileUser"
api_keys:
  api_key: "test_key"
  api_secret: "test_secret"
telegram:
  token: "test_token"
  chat_id: 123456
symbols:
  leverage: 3
  symbols:
    - BTCUSDT
""")
                temp_config_file = f.name
            
            # Test that environment variables override file values
            config_manager = ConfigManager(
                config_file=temp_config_file,
                env_prefix="NONAME_",
                auto_create=False
            )
            
            config = config_manager.get_config()
            
            # Check that env vars overrode file values
            if config.username == "EnvTestUser" and config.symbols.leverage == 7:
                print("✅ Environment variables correctly override file values")
                result = True
            else:
                print(f"❌ Environment override failed: username={config.username}, leverage={config.symbols.leverage}")
                result = False
            
        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            
            # Clean up temp file
            try:
                os.unlink(temp_config_file)
            except:
                pass
        
        return result
        
    except Exception as e:
        print(f"❌ Environment variable test failed: {e}")
        return False


def test_backward_compatibility():
    """Test backward compatibility with old load_config function."""
    print("\n🧪 Testing backward compatibility...")
    
    try:
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("""
username: "BackwardCompatTest"
api_keys:
  api_key: "test_key"
  api_secret: "test_secret"
telegram:
  token: "test_token"
  chat_id: 123456
symbols:
  leverage: 3
  symbols:
    - BTCUSDT
    - ETHUSDT
""")
            temp_config_file = f.name
        
        try:
            # Change to temp directory to avoid conflicts
            original_dir = os.getcwd()
            temp_dir = os.path.dirname(temp_config_file)
            config_filename = os.path.basename(temp_config_file)
            
            os.chdir(temp_dir)
            
            # Test old load_config function
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                
                from utils.load_config import load_config
                config_dict = load_config(config_filename)
            
            if config_dict and config_dict.get('username') == 'BackwardCompatTest':
                print("✅ Backward compatibility with load_config() works")
                result = True
            else:
                print("❌ Backward compatibility test failed")
                result = False
                
        finally:
            os.chdir(original_dir)
            try:
                os.unlink(temp_config_file)
            except:
                pass
        
        return result
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🎯 CONFIGURATION SYSTEM TESTS")
    print("=" * 50)
    
    tests = [
        test_basic_functionality,
        test_validation,
        test_environment_variables,
        test_backward_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The configuration system is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 