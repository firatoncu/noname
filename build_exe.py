#!/usr/bin/env python3
"""
PyInstaller Build Script for n0name Trading Bot

This script automates the process of building a standalone executable
from the n0name trading bot using PyInstaller with optimized settings.

Usage:
    python build_exe.py [--debug] [--onefile] [--clean]

Options:
    --debug     Build with debug information and console window
    --onefile   Create a single executable file (slower startup)
    --clean     Clean build directories before building
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
import platform

# Build configuration
APP_NAME = "n0name_trading_bot"
MAIN_SCRIPT = "n0name.py"
ICON_PATH = "assets/icon.ico"  # Will create if doesn't exist
VERSION = "2.0.0"

# Directories
BUILD_DIR = Path("build")
DIST_DIR = Path("dist")
SPEC_DIR = Path(".")

def clean_build_dirs():
    """Clean previous build artifacts."""
    print("🧹 Cleaning build directories...")
    
    dirs_to_clean = [BUILD_DIR, DIST_DIR, Path("__pycache__")]
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"   Removed: {dir_path}")
    
    # Remove .spec files
    for spec_file in SPEC_DIR.glob("*.spec"):
        spec_file.unlink()
        print(f"   Removed: {spec_file}")

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    # Map package names to their import names
    package_imports = {
        "pyinstaller": "PyInstaller",
        "pyyaml": "yaml", 
        "python-binance": "binance",
        "pandas": "pandas"
    }
    
    missing_packages = []
    
    for package, import_name in package_imports.items():
        try:
            __import__(import_name)
            print(f"   ✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ✗ {package}")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def create_icon():
    """Create a default icon if one doesn't exist."""
    icon_path = Path(ICON_PATH)
    if not icon_path.exists():
        print("📁 Creating assets directory and default icon...")
        icon_path.parent.mkdir(exist_ok=True)
        
        # Create a simple ICO file (this is a minimal placeholder)
        # In a real scenario, you'd want to provide a proper icon
        try:
            # Try to create a simple icon using PIL if available
            from PIL import Image, ImageDraw
            
            # Create a simple 32x32 icon
            img = Image.new('RGBA', (32, 32), (0, 100, 200, 255))
            draw = ImageDraw.Draw(img)
            draw.text((8, 8), "n0", fill=(255, 255, 255, 255))
            img.save(icon_path, format='ICO')
            print(f"   Created default icon: {icon_path}")
            
        except ImportError:
            print(f"   PIL not available, skipping icon creation")
            return None
    
    return str(icon_path) if icon_path.exists() else None

def get_hidden_imports():
    """Get list of hidden imports needed for the application."""
    return [
        # Core dependencies
        'binance',
        'binance.client',
        'binance.exceptions',
        'pandas',
        'numpy',
        'ta',
        'yaml',
        'pyyaml',
        'asyncio',
        'aiohttp',
        'aiofiles',
        'uvloop',
        'aiodns',
        'chardet',
        'brotlipy',
        
        # FastAPI and web components
        'fastapi',
        'uvicorn',
        'websockets',
        'psutil',
        'email_validator',
        
        # Crypto and security
        'cryptography',
        'cryptography.fernet',
        
        # Utility modules
        'colorama',
        'pydantic',
        'python_dotenv',
        'watchdog',
        
        # Windows specific
        'win32api',
        'win32con',
        'win32gui',
        'winsound',
        
        # Internal modules
        'utils',
        'utils.load_config',
        'utils.initial_adjustments',
        'utils.enhanced_logging',
        'utils.exceptions',
        'utils.app_logging',
        'utils.current_status',
        'utils.globals',
        'utils.web_ui',
        'src',
        'src.open_position',
        'src.check_trending',
        'auth',
        'auth.key_encryption',
    ]

def get_data_files():
    """Get list of data files to include in the build."""
    data_files = []
    
    # Configuration files
    config_files = ['config.yml', 'config2.yml', 'env.example']
    for config_file in config_files:
        if Path(config_file).exists():
            data_files.append((config_file, '.'))
    
    # Include entire directories that contain resources
    directories_to_include = [
        ('utils', 'utils'),
        ('src', 'src'),
        ('auth', 'auth'),
        ('config', 'config'),
        ('assets', 'assets'),
    ]
    
    for src_dir, dst_dir in directories_to_include:
        if Path(src_dir).exists():
            data_files.append((f'{src_dir}/*', dst_dir))
    
    return data_files

def build_executable(debug=False, onefile=False, console=False):
    """Build the executable using PyInstaller."""
    print("🔨 Building executable...")
    
    # Base PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--clean",
        "--noconfirm",
    ]
    
    # Add console/windowed mode
    if debug or console:
        cmd.append("--console")
        if debug:
            cmd.append("--debug=all")
            print("   Debug mode: Console window enabled")
        else:
            print("   Console mode: Console window enabled for debugging")
    else:
        cmd.append("--windowed")
        print("   Release mode: No console window")
    
    # Add file mode
    if onefile:
        cmd.append("--onefile")
        print("   Single file mode: Slower startup, easier distribution")
    else:
        cmd.append("--onedir")
        print("   Directory mode: Faster startup, multiple files")
    
    # Add icon if available
    icon_path = create_icon()
    if icon_path:
        cmd.extend(["--icon", icon_path])
        print(f"   Icon: {icon_path}")
    
    # Add hidden imports
    hidden_imports = get_hidden_imports()
    for import_name in hidden_imports:
        cmd.extend(["--hidden-import", import_name])
    
    # Add data files
    data_files = get_data_files()
    for src, dst in data_files:
        cmd.extend(["--add-data", f"{src};{dst}"])
    
    # Add additional options for better compatibility
    cmd.extend([
        "--collect-all", "binance",
        "--collect-all", "pandas",
        "--collect-all", "numpy",
        "--collect-all", "yaml",
        "--collect-all", "pyyaml",
        "--collect-submodules", "utils",
        "--collect-submodules", "src",
        "--collect-submodules", "auth",
    ])
    
    # Platform-specific options
    if platform.system() == "Windows":
        cmd.extend([
            "--collect-all", "win32api",
            "--collect-all", "win32con",
            "--collect-all", "win32gui",
        ])
    
    # Add the main script
    cmd.append(MAIN_SCRIPT)
    
    print(f"   Command: {' '.join(cmd[:10])}... (truncated)")
    
    # Run PyInstaller
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with error code {e.returncode}")
        print(f"Error output: {e.stderr}")
        return False

def create_distribution_package():
    """Create a distribution package with all necessary files."""
    print("📦 Creating distribution package...")
    
    # Determine the executable path
    if (DIST_DIR / APP_NAME).exists():
        exe_dir = DIST_DIR / APP_NAME
        exe_file = exe_dir / f"{APP_NAME}.exe"
    else:
        exe_dir = DIST_DIR
        exe_file = exe_dir / f"{APP_NAME}.exe"
    
    if not exe_file.exists():
        print(f"❌ Executable not found at {exe_file}")
        return False
    
    # Create distribution directory
    dist_package_dir = DIST_DIR / f"{APP_NAME}_distribution"
    if dist_package_dir.exists():
        shutil.rmtree(dist_package_dir)
    dist_package_dir.mkdir()
    
    # Copy executable and dependencies
    if exe_dir.is_dir() and exe_dir.name == APP_NAME:
        # Directory mode - copy entire directory
        shutil.copytree(exe_dir, dist_package_dir / APP_NAME)
    else:
        # Single file mode - copy just the executable
        shutil.copy2(exe_file, dist_package_dir)
    
    # Copy frontend files if they exist
    frontend_dist_path = Path("utils/web_ui/project/dist")
    if frontend_dist_path.exists():
        frontend_target = dist_package_dir / "web_ui"
        shutil.copytree(frontend_dist_path, frontend_target)
        print(f"   Copied frontend files to: web_ui/")
        print(f"   Frontend will be available at: http://localhost:5173")
    else:
        print("   ⚠️  Frontend dist files not found - web UI will not be available")
        print("   💡 Run 'npm run build' in utils/web_ui/project/ to build frontend")
    
    # Copy important files
    important_files = [
        "README.md",
        "LICENSE",
        "config.yml",
        "env.example",
        "CONFIGURATION_SETUP.md",
    ]
    
    for file_name in important_files:
        file_path = Path(file_name)
        if file_path.exists():
            shutil.copy2(file_path, dist_package_dir)
            print(f"   Copied: {file_name}")
    
    # Create a startup script that works for both onefile and onedir modes
    startup_script = dist_package_dir / "start_trading_bot.bat"
    
    # Determine the correct executable path
    if (dist_package_dir / APP_NAME).exists():
        # Directory mode - executable is in subdirectory
        exe_path = f"{APP_NAME}\\{APP_NAME}.exe"
    else:
        # Single file mode - executable is in root
        exe_path = f"{APP_NAME}.exe"
    
    with open(startup_script, 'w', encoding='utf-8') as f:
        f.write(f"""@echo off
echo ========================================
echo  n0name Trading Bot - Startup Script
echo ========================================
echo.

REM Check if executable exists
if exist "{exe_path}" (
    echo Found executable: {exe_path}
) else (
    echo ERROR: {exe_path} not found!
    echo.
    echo Please make sure you are running this script from the distribution folder.
    echo The folder should contain either:
    echo - {APP_NAME}.exe (single file mode)
    echo - {APP_NAME}/ directory with {APP_NAME}.exe inside (directory mode)
echo.
pause
    exit /b 1
)

echo.
echo IMPORTANT REMINDERS:
echo - Make sure you have configured your API keys in config.yml
echo - Use testnet for initial testing
echo - Never share your API keys with anyone
echo - Press Ctrl+C to stop the bot
echo - Web interface will be available at http://localhost:8000 (API) and http://localhost:5173 (Frontend)
echo.
echo Starting trading bot...
echo.

REM Pause to let user read the instructions
timeout /t 3 /nobreak >nul
echo Starting in 3 seconds... (Press any key to start immediately)
pause >nul

REM Start the executable
"{exe_path}"

echo.
echo Trading bot has stopped.
pause
""")
    print(f"   Created: {startup_script.name}")
    print(f"   Executable path in script: {exe_path}")
    
    # Create a verification script to help users troubleshoot
    verify_script = dist_package_dir / "verify_installation.bat"
    with open(verify_script, 'w', encoding='utf-8') as f:
        f.write(f"""@echo off
echo ========================================
echo  n0name Trading Bot - Installation Verification
echo ========================================
echo.

echo Checking distribution package...
echo.

REM Check for executable
if exist "{exe_path}" (
    echo [OK] Executable found: {exe_path}
) else (
    echo [ERROR] Executable NOT found: {exe_path}
    set HAS_ERRORS=1
)

REM Check for config file
if exist "config.yml" (
    echo [OK] Configuration file found: config.yml
) else (
    echo [WARNING] Configuration file NOT found: config.yml
    echo    You will need to create this before running the bot
)

REM Check for frontend files
if exist "web_ui\\index.html" (
    echo [OK] Frontend files found: web_ui/
    echo    Web interface will be available
) else (
    echo [WARNING] Frontend files NOT found: web_ui/
    echo    Web interface will not be available
)

REM Check for other important files
if exist "README.md" (
    echo [OK] Documentation found: README.md
) else (
    echo [WARNING] Documentation NOT found: README.md
)

if exist "CONFIGURATION_SETUP.md" (
    echo [OK] Setup guide found: CONFIGURATION_SETUP.md
) else (
    echo [WARNING] Setup guide NOT found: CONFIGURATION_SETUP.md
)

echo.
if defined HAS_ERRORS (
    echo [ERROR] ERRORS DETECTED:
    echo    The distribution package appears to be incomplete.
    echo    Please re-download or rebuild the package.
) else (
    echo [SUCCESS] VERIFICATION PASSED:
    echo    The distribution package appears to be complete.
    echo.
    echo Next steps:
    echo    1. Edit config.yml with your API keys
    echo    2. Run start_trading_bot.bat to start the bot
    echo    3. Visit http://localhost:8000 for the API interface
    echo    4. Visit http://localhost:5173 for the web frontend (if available)
)

echo.
pause
""")
    print(f"   Created: {verify_script.name}")
    
    # Create README for distribution
    dist_readme = dist_package_dir / "DISTRIBUTION_README.txt"
    with open(dist_readme, 'w', encoding='utf-8') as f:
        f.write(f"""n0name Trading Bot - Distribution Package
========================================

Version: {VERSION}
Built on: {platform.system()} {platform.release()}

QUICK START GUIDE:
1. Run verify_installation.bat to check if everything is properly set up
2. Edit config.yml with your Binance API keys
3. Run start_trading_bot.bat to start the application
4. Visit http://localhost:8000 for the API interface
5. Visit http://localhost:5173 for the web frontend (if included)

FILES INCLUDED:
- {exe_path} - Main trading bot executable
- config.yml - Configuration file (EDIT THIS FIRST!)
- start_trading_bot.bat - Startup script
- verify_installation.bat - Installation verification script
- env.example - Environment variables example
- web_ui/ - Frontend web interface files (if available)
- README.md - Full documentation (if included)
- CONFIGURATION_SETUP.md - Setup instructions (if included)

WEB INTERFACES:
- API Documentation: http://localhost:8000/docs
- API Status: http://localhost:8000
- Web Frontend: http://localhost:5173 (if web_ui/ folder is present)

CONFIGURATION REQUIREMENTS:
Before running the bot, you MUST edit config.yml and add:
- Your Binance API key and secret
- Select trading symbols
- Configure trading strategy
- Set capital amount and leverage

SECURITY REMINDERS:
- Never share your API keys with anyone
- Keep your config.yml file secure and private  
- Test with small amounts and testnet first
- Use API keys with futures trading permissions only

TROUBLESHOOTING:
If start_trading_bot.bat shows "not recognized" error:
1. Run verify_installation.bat to check the setup
2. Make sure you're in the distribution folder
3. Check that the executable file exists
4. Try running the executable directly: {exe_path}

If the bot fails to start:
1. Check your config.yml file format
2. Verify your API keys are correct
3. Ensure you have internet connectivity
4. Check Windows Defender/antivirus isn't blocking it

SUPPORT:
- Check README.md for detailed documentation
- Ensure all configuration is correct before running
- Test in testnet mode before using real funds
- The bot requires valid Binance API credentials with futures permissions

TIPS:
- Start with testnet: set "testnet: true" in config.yml
- Use small capital amounts for initial testing
- Monitor the bot's performance regularly
- Keep your API keys secure and rotate them periodically

Happy trading!
""")
    print(f"   Created: {dist_readme.name}")
    
    print(f"✅ Distribution package created: {dist_package_dir}")
    return True

def main():
    """Main build function."""
    parser = argparse.ArgumentParser(description="Build n0name Trading Bot executable")
    parser.add_argument("--debug", action="store_true", help="Build with debug information")
    parser.add_argument("--onefile", action="store_true", help="Create single executable file")
    parser.add_argument("--console", action="store_true", help="Show console window for debugging")
    parser.add_argument("--clean", action="store_true", help="Clean build directories first")
    
    args = parser.parse_args()
    
    print("🚀 n0name Trading Bot - PyInstaller Build Script")
    print("=" * 50)
    
    # Clean if requested
    if args.clean:
        clean_build_dirs()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Verify main script exists
    if not Path(MAIN_SCRIPT).exists():
        print(f"❌ Main script not found: {MAIN_SCRIPT}")
        sys.exit(1)
    
    # Build executable
    if not build_executable(debug=args.debug, onefile=args.onefile, console=args.console):
        sys.exit(1)
    
    # Create distribution package
    if not create_distribution_package():
        sys.exit(1)
    
    print("\n🎉 Build process completed successfully!")
    print(f"📁 Distribution package: dist/{APP_NAME}_distribution/")
    print("\n📋 Next steps:")
    print("1. Test the executable in the dist directory")
    print("2. Configure API keys in config.yml")
    print("3. Share the distribution package with your friends")
    if args.console:
        print("\n⚠️  Console mode: You'll see debug output when running the executable")
    print("\n⚠️  Remember: Recipients need to configure their own API keys!")

if __name__ == "__main__":
    main() 