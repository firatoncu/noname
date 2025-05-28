#!/usr/bin/env python3
"""
Clear Cache and Restart Script

This script clears any configuration cache and restarts the bot
to ensure the updated configuration is loaded properly.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def clear_cache():
    """Clear Python cache files"""
    print("🧹 Clearing Python cache files...")
    
    # Clear __pycache__ directories
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                cache_dir = os.path.join(root, dir_name)
                print(f"  Removing: {cache_dir}")
                try:
                    import shutil
                    shutil.rmtree(cache_dir)
                except Exception as e:
                    print(f"  Warning: Could not remove {cache_dir}: {e}")
    
    # Clear .pyc files
    for root, dirs, files in os.walk('.'):
        for file_name in files:
            if file_name.endswith('.pyc'):
                pyc_file = os.path.join(root, file_name)
                print(f"  Removing: {pyc_file}")
                try:
                    os.remove(pyc_file)
                except Exception as e:
                    print(f"  Warning: Could not remove {pyc_file}: {e}")

def kill_existing_processes():
    """Kill any existing bot processes"""
    print("🔄 Checking for existing bot processes...")
    
    try:
        # Check for processes using port 8000
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, shell=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            if ':8000' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) > 4:
                    pid = parts[-1]
                    print(f"  Found process using port 8000: PID {pid}")
                    try:
                        subprocess.run(['taskkill', '/PID', pid, '/F'], shell=True)
                        print(f"  Killed process {pid}")
                    except Exception as e:
                        print(f"  Warning: Could not kill process {pid}: {e}")
    except Exception as e:
        print(f"  Warning: Could not check for existing processes: {e}")

def verify_config():
    """Verify the configuration file"""
    print("📋 Verifying configuration...")
    
    config_file = Path('config.yml')
    if config_file.exists():
        with open(config_file, 'r') as f:
            content = f.read()
            if 'capital_tbu: 50.0' in content:
                print("  ✅ Configuration updated correctly (capital_tbu: 50.0)")
            else:
                print("  ❌ Configuration may not be updated correctly")
                print("  Current config content:")
                print(content[:500] + "..." if len(content) > 500 else content)
    else:
        print("  ❌ Configuration file not found!")

def restart_bot():
    """Restart the trading bot"""
    print("🚀 Starting the trading bot...")
    
    try:
        # Use the full Python path
        python_path = r"C:\Users\ffira\AppData\Local\Programs\Python\Python311\python.exe"
        
        # Start the bot
        process = subprocess.Popen([python_path, 'n0name.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        print(f"  Bot started with PID: {process.pid}")
        print("  Monitoring startup for 10 seconds...")
        
        # Monitor for 10 seconds
        for i in range(10):
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"  ❌ Bot exited early with code: {process.returncode}")
                if stderr:
                    print(f"  Error output: {stderr[:500]}")
                return False
            
            print(f"  Running... ({i+1}/10)")
            time.sleep(1)
        
        print("  ✅ Bot appears to be running successfully!")
        print(f"  You can check the logs or visit https://localhost:8000")
        return True
        
    except Exception as e:
        print(f"  ❌ Error starting bot: {e}")
        return False

def main():
    """Main function"""
    print("🔧 n0name Trading Bot - Clear Cache and Restart")
    print("=" * 50)
    
    # Step 1: Clear cache
    clear_cache()
    print()
    
    # Step 2: Kill existing processes
    kill_existing_processes()
    print()
    
    # Step 3: Verify config
    verify_config()
    print()
    
    # Step 4: Wait a moment
    print("⏳ Waiting 3 seconds before restart...")
    time.sleep(3)
    print()
    
    # Step 5: Restart bot
    success = restart_bot()
    
    if success:
        print("\n🎉 Bot restart completed successfully!")
        print("📊 Check the web interface at: https://localhost:8000")
        print("📱 Frontend available at: http://localhost:5173")
    else:
        print("\n❌ Bot restart failed. Please check the error messages above.")
        print("💡 You may need to run the bot manually: python n0name.py")

if __name__ == "__main__":
    main() 