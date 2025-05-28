#!/usr/bin/env python3
"""
Clear Browser Cache and Open Frontend
This script helps clear browser cache and open the frontend with fresh settings.
"""

import webbrowser
import time
import subprocess
import sys
import os

def print_instructions():
    """Print manual cache clearing instructions"""
    print("🧹 Browser Cache Clearing Instructions")
    print("=" * 50)
    print()
    print("To clear your browser cache manually:")
    print()
    print("🔹 Chrome/Edge:")
    print("   1. Press Ctrl+Shift+Delete")
    print("   2. Select 'All time' as time range")
    print("   3. Check 'Cached images and files'")
    print("   4. Click 'Clear data'")
    print()
    print("🔹 Firefox:")
    print("   1. Press Ctrl+Shift+Delete")
    print("   2. Select 'Everything' as time range")
    print("   3. Check 'Cache'")
    print("   4. Click 'Clear Now'")
    print()
    print("🔹 Alternative - Hard Refresh:")
    print("   1. Go to http://localhost:5173")
    print("   2. Press Ctrl+F5 (or Ctrl+Shift+R)")
    print("   3. This forces a hard refresh")
    print()

def open_frontend():
    """Open the frontend in the default browser"""
    frontend_url = "http://localhost:5173"
    print(f"🌐 Opening frontend: {frontend_url}")
    
    try:
        webbrowser.open(frontend_url)
        print("✅ Frontend opened in browser")
        return True
    except Exception as e:
        print(f"❌ Error opening browser: {e}")
        return False

def check_services():
    """Check if backend and frontend services are running"""
    print("🔍 Checking services...")
    
    # Check backend
    try:
        import requests
        response = requests.get("http://localhost:8000/api/wallet", timeout=5)
        if response.status_code == 200:
            print("✅ Backend (port 8000): Running")
            backend_ok = True
        else:
            print(f"⚠️ Backend (port 8000): HTTP {response.status_code}")
            backend_ok = False
    except Exception as e:
        print(f"❌ Backend (port 8000): Not responding - {e}")
        backend_ok = False
    
    # Check frontend
    try:
        import requests
        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend (port 5173): Running")
            frontend_ok = True
        else:
            print(f"⚠️ Frontend (port 5173): HTTP {response.status_code}")
            frontend_ok = False
    except Exception as e:
        print(f"❌ Frontend (port 5173): Not responding - {e}")
        frontend_ok = False
    
    return backend_ok, frontend_ok

def main():
    """Main function"""
    print("🚀 n0name Trading Bot - Browser Cache Cleaner")
    print("=" * 50)
    print()
    
    # Check if services are running
    backend_ok, frontend_ok = check_services()
    
    if not backend_ok:
        print("❌ Backend is not running. Please start the trading bot first:")
        print("   python n0name.py")
        return
    
    if not frontend_ok:
        print("❌ Frontend is not running. Please start the trading bot first:")
        print("   python n0name.py")
        return
    
    print()
    print("✅ Both services are running!")
    print()
    
    # Print cache clearing instructions
    print_instructions()
    
    # Ask user if they want to open the frontend
    try:
        choice = input("🤔 Do you want to open the frontend now? (y/n): ").lower().strip()
        if choice in ['y', 'yes']:
            open_frontend()
            print()
            print("📝 Next steps:")
            print("1. If the page loads but shows loading spinners:")
            print("   - Press F12 to open Developer Tools")
            print("   - Go to Console tab")
            print("   - Look for any error messages")
            print("   - Check if API calls are going to http://localhost:8000")
            print()
            print("2. If you see HTTPS errors:")
            print("   - Clear your browser cache (instructions above)")
            print("   - Try a hard refresh (Ctrl+F5)")
            print()
            print("3. If problems persist:")
            print("   - Try opening in an incognito/private window")
            print("   - Or try a different browser")
        else:
            print("👍 You can manually open: http://localhost:5173")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main() 