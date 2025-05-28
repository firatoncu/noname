#!/usr/bin/env python3
"""
Simple test script for the simplified configuration management system.
This verifies that config.yml can be loaded without any defaults.
"""
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import utils
sys.path.append(str(Path(__file__).parent.parent))

def test_basic_functionality():
    """Test basic configuration loading and validation."""
    print("🧪 Testing basic functionality...")
    
    try:
        from utils.load_config import load_config
        
        # Test configuration loading from config.yml
        config = load_config()
        
        print("✅ Configuration loaded successfully")
        print(f"   Username: {config['username']}")
        print(f"   Symbols: {config['symbols']['symbols']}")
        print(f"   Logging level: {config['logging']['level']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False


def test_missing_config():
    """Test that missing config file raises appropriate error."""
    print("\n🧪 Testing missing config file...")
    
    try:
        from utils.load_config import load_config
        
        # Temporarily rename config file
        config_path = Path(__file__).parent.parent / "config.yml"
        backup_path = config_path.with_suffix('.yml.backup')
        
        if config_path.exists():
            config_path.rename(backup_path)
        
        try:
            config = load_config()
            print("❌ Should have failed with missing config file")
            return False
        except FileNotFoundError:
            print("✅ Correctly raised FileNotFoundError for missing config")
            return True
        finally:
            # Restore config file
            if backup_path.exists():
                backup_path.rename(config_path)
        
    except Exception as e:
        print(f"❌ Missing config test failed: {e}")
        return False


def test_enhanced_logging():
    """Test enhanced logging reads from config."""
    print("\n🧪 Testing enhanced logging...")
    
    try:
        from utils.enhanced_logging import get_logger
        
        logger = get_logger("test_logger")
        print("✅ Enhanced logger created successfully")
        
        # Test logging
        logger.info("Test log message")
        print("✅ Logging works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced logging test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 SIMPLIFIED CONFIGURATION SYSTEM TESTS")
    print("=" * 60)
    
    tests = [
        test_basic_functionality,
        test_missing_config,
        test_enhanced_logging,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 