# n0name Trading Bot - PowerShell Build Script
# This script automates the PyInstaller build process using PowerShell

param(
    [switch]$Debug,
    [switch]$OneFile,
    [switch]$Clean,
    [switch]$Help
)

# Display help if requested
if ($Help) {
    Write-Host @"
n0name Trading Bot - PowerShell Build Script

Usage: .\build.ps1 [options]

Options:
  -Debug     Build with debug information and console window
  -OneFile   Create a single executable file (slower startup)
  -Clean     Clean build directories before building
  -Help      Show this help message

Examples:
  .\build.ps1                    # Standard release build
  .\build.ps1 -Debug             # Debug build with console
  .\build.ps1 -OneFile           # Single file executable
  .\build.ps1 -Clean -Debug      # Clean build with debug info
"@
    exit 0
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " n0name Trading Bot - PowerShell Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "✓ Python version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "n0name.py")) {
    Write-Host "❌ ERROR: n0name.py not found in current directory" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ Current directory: $(Get-Location)" -ForegroundColor Green
Write-Host ""

# Install build dependencies
Write-Host "📦 Installing build dependencies..." -ForegroundColor Blue
Write-Host ""

try {
    # Upgrade pip
    python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip" }
    
    # Install requirements
    python -m pip install -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) { throw "Failed to install requirements" }
    
    Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Failed to install dependencies" -ForegroundColor Red
    Write-Host "Please check your internet connection and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Prepare build arguments
$buildArgs = @()

if ($Clean) {
    $buildArgs += "--clean"
    Write-Host "🧹 Clean build requested" -ForegroundColor Yellow
}

if ($Debug) {
    $buildArgs += "--debug"
    Write-Host "🐛 Debug build requested" -ForegroundColor Yellow
} elseif ($OneFile) {
    $buildArgs += "--onefile"
    Write-Host "📦 Single file build requested" -ForegroundColor Yellow
} else {
    Write-Host "🚀 Release build (default)" -ForegroundColor Green
}

# If no specific build type was requested, ask the user
if (-not $Debug -and -not $OneFile) {
    Write-Host ""
    Write-Host "Choose build type:" -ForegroundColor Cyan
    Write-Host "1. Release build (recommended for distribution)" -ForegroundColor White
    Write-Host "2. Debug build (for testing and troubleshooting)" -ForegroundColor White
    Write-Host "3. Single file build (slower startup, easier to share)" -ForegroundColor White
    Write-Host ""
    
    do {
        $choice = Read-Host "Enter your choice (1-3, or Enter for default)"
        if ([string]::IsNullOrEmpty($choice)) { $choice = "1" }
    } while ($choice -notin @("1", "2", "3"))
    
    switch ($choice) {
        "2" { 
            $buildArgs += "--debug"
            Write-Host "Building debug version..." -ForegroundColor Yellow
        }
        "3" { 
            $buildArgs += "--onefile"
            Write-Host "Building single file version..." -ForegroundColor Yellow
        }
        default { 
            Write-Host "Building release version..." -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "⚙️  Starting build process..." -ForegroundColor Blue
Write-Host "This may take several minutes..." -ForegroundColor Yellow
Write-Host ""

# Run the build script
try {
    $buildCommand = "python build_exe.py " + ($buildArgs -join " ")
    Write-Host "Executing: $buildCommand" -ForegroundColor Gray
    
    Invoke-Expression $buildCommand
    
    if ($LASTEXITCODE -ne 0) {
        throw "Build process failed"
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " BUILD COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "❌ ERROR: Build failed!" -ForegroundColor Red
    Write-Host "Check the error messages above for details" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Show build results
$distPath = "dist\n0name_trading_bot_distribution"
if (Test-Path $distPath) {
    Write-Host "📁 Distribution package created in:" -ForegroundColor Green
    Write-Host "   $(Resolve-Path $distPath)" -ForegroundColor White
    Write-Host ""
    
    Write-Host "📋 Contents:" -ForegroundColor Cyan
    Get-ChildItem $distPath | ForEach-Object {
        $icon = if ($_.PSIsContainer) { "📁" } else { "📄" }
        Write-Host "   $icon $($_.Name)" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "✅ You can now share the entire 'n0name_trading_bot_distribution' folder" -ForegroundColor Green
    Write-Host "   with your friends. They will need to configure their API keys in config.yml" -ForegroundColor Yellow
    Write-Host ""
    
    # Ask if user wants to open the distribution folder
    $openFolder = Read-Host "Open distribution folder? (y/n)"
    if ($openFolder -eq "y" -or $openFolder -eq "Y") {
        Start-Process explorer.exe -ArgumentList $distPath
    }
} else {
    Write-Host "⚠️  WARNING: Distribution package not found" -ForegroundColor Yellow
    Write-Host "Check the dist directory manually" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "⚠️  IMPORTANT REMINDERS:" -ForegroundColor Red
Write-Host "• Test the executable before sharing" -ForegroundColor Yellow
Write-Host "• Recipients need to configure their own API keys" -ForegroundColor Yellow
Write-Host "• Include the DISTRIBUTION_README.txt file when sharing" -ForegroundColor Yellow
Write-Host "• Never share your personal API keys or config.yml with credentials" -ForegroundColor Red
Write-Host ""

Read-Host "Press Enter to exit" 