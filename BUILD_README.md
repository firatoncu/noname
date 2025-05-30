# n0name Trading Bot - Build Instructions

This document explains how to create a standalone executable of the n0name Trading Bot that you can share with your friends.

## 🚀 Quick Start

### Option 1: Windows Batch File (Easiest)
```bash
# Double-click or run in Command Prompt
build.bat
```

### Option 2: PowerShell Script
```powershell
# Run in PowerShell
.\build.ps1
```

### Option 3: Python Script (Cross-platform)
```bash
# Install dependencies first
pip install -r requirements-build.txt

# Run the build script
python build_exe.py
```

## 📋 Prerequisites

1. **Python 3.8+** installed and accessible via `python` command
2. **Internet connection** for downloading dependencies
3. **Sufficient disk space** (~500MB for build process)
4. **Windows 10+** (for Windows builds)

## 🛠️ Build Options

### Build Types

| Type | Command | Description | Best For |
|------|---------|-------------|----------|
| **Release** | `build.bat` (option 1) | Optimized, no console | Distribution to friends |
| **Debug** | `build.bat` (option 2) | Shows console, debug info | Testing and troubleshooting |
| **Single File** | `build.bat` (option 3) | One .exe file | Easy sharing (slower startup) |

### Advanced Options

```bash
# Python script with options
python build_exe.py --help
python build_exe.py --debug          # Debug build
python build_exe.py --onefile        # Single file
python build_exe.py --clean          # Clean previous builds
python build_exe.py --debug --clean  # Debug + clean
```

```powershell
# PowerShell script with options
.\build.ps1 -Help                     # Show help
.\build.ps1 -Debug                    # Debug build
.\build.ps1 -OneFile                  # Single file
.\build.ps1 -Clean                    # Clean previous builds
.\build.ps1 -Debug -Clean             # Debug + clean
```

## 📁 Output Structure

After a successful build, you'll find:

```
dist/
└── n0name_trading_bot_distribution/
    ├── n0name_trading_bot.exe          # Main executable
    ├── n0name_trading_bot/              # Dependencies (if not single file)
    │   ├── _internal/                   # PyInstaller internals
    │   └── ...
    ├── config.yml                      # Configuration file
    ├── start_trading_bot.bat           # Easy startup script
    ├── DISTRIBUTION_README.txt         # Instructions for recipients
    ├── README.md                       # Full documentation
    ├── LICENSE                         # License file
    └── CONFIGURATION_SETUP.md          # Setup instructions
```

## 🎯 Distribution

### What to Share

Share the entire `n0name_trading_bot_distribution` folder with your friends. This includes:

- ✅ The executable file
- ✅ All necessary dependencies
- ✅ Configuration templates
- ✅ Documentation
- ✅ Easy startup script

### What NOT to Share

- ❌ Your personal `config.yml` with API keys
- ❌ Any files with your credentials
- ❌ The `build/` directory
- ❌ Your development environment

## ⚙️ Configuration for Recipients

Your friends will need to:

1. **Configure API Keys**: Edit `config.yml` with their Binance API credentials
2. **Review Settings**: Adjust trading parameters as needed
3. **Run the Bot**: Use `start_trading_bot.bat` or run the .exe directly

## 🔧 Troubleshooting

### Common Build Issues

#### "Python not found"
```bash
# Check Python installation
python --version

# If not found, install Python 3.8+ from python.org
# Make sure to check "Add Python to PATH" during installation
```

#### "Module not found" errors
```bash
# Install missing dependencies
pip install -r requirements-build.txt

# Or install specific packages
pip install pyinstaller python-binance pandas
```

#### "Permission denied" errors
```bash
# Run as administrator (Windows)
# Or check antivirus software blocking the build
```

#### Build succeeds but executable doesn't work
```bash
# Try debug build to see error messages
python build_exe.py --debug

# Check if all dependencies are included
# Verify configuration files are present
```

### Runtime Issues

#### "API key invalid" errors
- Recipients need to configure their own API keys in `config.yml`
- Ensure API keys have proper permissions on Binance

#### "Module not found" at runtime
- Some dependencies might be missing from the build
- Try adding them to the `get_hidden_imports()` function in `build_exe.py`

#### Slow startup
- This is normal for PyInstaller executables
- Single file builds are slower than directory builds
- Consider using directory build for better performance

## 🔍 Build Process Details

### What PyInstaller Does

1. **Analyzes** your Python script and finds all dependencies
2. **Collects** all required Python modules and libraries
3. **Bundles** everything into a standalone executable
4. **Creates** a distribution package with all necessary files

### Included Dependencies

The build automatically includes:
- Python runtime
- All packages from `requirements.txt`
- Additional PyInstaller-specific dependencies
- Windows-specific modules (on Windows)
- Your application code and resources

### Build Time

Typical build times:
- **First build**: 5-15 minutes (downloading dependencies)
- **Subsequent builds**: 2-5 minutes (using cache)
- **Clean builds**: 3-8 minutes (rebuilding everything)

## 📊 File Sizes

Approximate sizes:
- **Directory build**: 150-300 MB
- **Single file build**: 80-150 MB
- **Compressed distribution**: 50-100 MB

## 🔒 Security Considerations

### For You (Builder)
- Never include your personal API keys in the build
- Review the distribution package before sharing
- Use testnet for testing builds

### For Recipients
- Only download from trusted sources
- Configure their own API keys
- Start with testnet/paper trading
- Review all configuration before live trading

## 🆘 Getting Help

If you encounter issues:

1. **Check this README** for common solutions
2. **Try debug build** to see detailed error messages
3. **Verify dependencies** are properly installed
4. **Check Python version** (3.8+ required)
5. **Review PyInstaller logs** in the build output

### Debug Commands

```bash
# Verbose build output
python build_exe.py --debug

# Check Python environment
python -c "import sys; print(sys.path)"
python -c "import binance; print('Binance OK')"

# Test imports
python -c "from n0name import *"
```

## 📝 Customization

### Adding Dependencies

Edit `build_exe.py` and add to `get_hidden_imports()`:
```python
def get_hidden_imports():
    return [
        # ... existing imports ...
        'your_new_module',
        'another_module',
    ]
```

### Including Additional Files

Edit `build_exe.py` and modify `get_data_files()`:
```python
def get_data_files():
    data_files = [
        # ... existing files ...
        ('your_file.txt', '.'),
        ('your_directory/*', 'your_directory'),
    ]
    return data_files
```

### Changing Build Settings

Modify the PyInstaller command in `build_executable()` function in `build_exe.py`.

## 🎉 Success!

Once you've successfully built and tested your executable:

1. ✅ Test it thoroughly on your machine
2. ✅ Create a test configuration for recipients
3. ✅ Share the distribution folder
4. ✅ Provide setup instructions
5. ✅ Enjoy automated trading with friends!

---

**Happy Building! 🚀** 