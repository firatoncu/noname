# Environment Variables Viewer for Windows PowerShell
# This script helps you view environment variables safely

param(
    [switch]$ShowSensitive = $false,
    [ValidateSet("Table", "JSON")]
    [string]$Format = "Table",
    [switch]$CheckMissing = $false
)

function Mask-SensitiveValue {
    param(
        [string]$Key,
        [string]$Value
    )
    
    $sensitiveKeywords = @('password', 'secret', 'key', 'token', 'api', 'jwt', 'auth', 'credential', 'private', 'secure')
    
    $isSensitive = $false
    foreach ($keyword in $sensitiveKeywords) {
        if ($Key.ToLower().Contains($keyword)) {
            $isSensitive = $true
            break
        }
    }
    
    if ($isSensitive) {
        if ($Value.Length -le 8) {
            return '*' * $Value.Length
        } else {
            return $Value.Substring(0, 4) + ('*' * ($Value.Length - 8)) + $Value.Substring($Value.Length - 4)
        }
    }
    
    return $Value
}

function Get-EnvironmentType {
    $env = $env:ENVIRONMENT
    if (-not $env) { $env = "development" }
    
    switch ($env.ToLower()) {
        { $_ -in @("prod", "production") } { return "production" }
        { $_ -in @("dev", "development") } { return "development" }
        { $_ -in @("test", "testing") } { return "testing" }
        default { return "unknown" }
    }
}

function Read-EnvFile {
    param([string]$FilePath)
    
    $envVars = @{}
    
    if (-not (Test-Path $FilePath)) {
        return $envVars
    }
    
    try {
        $content = Get-Content $FilePath -ErrorAction Stop
        foreach ($line in $content) {
            $line = $line.Trim()
            
            # Skip empty lines and comments
            if ([string]::IsNullOrEmpty($line) -or $line.StartsWith('#')) {
                continue
            }
            
            # Parse KEY=VALUE format
            if ($line.Contains('=')) {
                $parts = $line.Split('=', 2)
                $key = $parts[0].Trim()
                $value = $parts[1].Trim()
                
                # Remove quotes if present
                if (($value.StartsWith('"') -and $value.EndsWith('"')) -or 
                    ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                    $value = $value.Substring(1, $value.Length - 2)
                }
                
                $envVars[$key] = $value
            }
        }
    }
    catch {
        Write-Host "Error reading ${FilePath}: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    return $envVars
}

function Show-EnvironmentVariables {
    param(
        [bool]$ShowSensitive = $false,
        [string]$Format = "Table"
    )
    
    Write-Host "🔍 Environment Variables Viewer" -ForegroundColor Cyan
    Write-Host ("=" * 50) -ForegroundColor Gray
    
    # Determine environment
    $envType = Get-EnvironmentType
    Write-Host "📍 Environment: $($envType.ToUpper())" -ForegroundColor Yellow
    Write-Host ""
    
    # Trading bot specific variables
    $tradingVars = @(
        'ENVIRONMENT', 'DEBUG', 'VERSION',
        'BINANCE_API_KEY', 'BINANCE_API_SECRET',
        'TRADING_CAPITAL', 'TRADING_LEVERAGE',
        'DATABASE_URL', 'REDIS_URL', 'INFLUXDB_URL',
        'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID',
        'EMAIL_USERNAME', 'EMAIL_PASSWORD',
        'JWT_SECRET', 'API_SECRET_KEY',
        'LOG_LEVEL', 'LOG_FORMAT'
    )
    
    # Collect environment variables from different sources
    $sources = @{
        'System Environment' = @{}
        '.env file' = Read-EnvFile ".env"
        'env.example' = Read-EnvFile "env.example"
    }
    
    # Get system environment variables
    foreach ($var in $tradingVars) {
        $value = [Environment]::GetEnvironmentVariable($var)
        if ($value) {
            $sources['System Environment'][$var] = $value
        }
    }
    
    if ($Format -eq "JSON") {
        # JSON output
        $output = @{}
        foreach ($sourceName in $sources.Keys) {
            $output[$sourceName] = @{}
            foreach ($var in $tradingVars) {
                if ($sources[$sourceName].ContainsKey($var)) {
                    $value = $sources[$sourceName][$var]
                    if (-not $ShowSensitive) {
                        $value = Mask-SensitiveValue -Key $var -Value $value
                    }
                    $output[$sourceName][$var] = $value
                }
            }
        }
        
        $output | ConvertTo-Json -Depth 3
    }
    else {
        # Table output
        foreach ($sourceName in $sources.Keys) {
            Write-Host "📋 $sourceName" -ForegroundColor Green
            Write-Host ("-" * 30) -ForegroundColor Gray
            
            $foundVars = @()
            foreach ($var in $tradingVars) {
                if ($sources[$sourceName].ContainsKey($var)) {
                    $value = $sources[$sourceName][$var]
                    if (-not $ShowSensitive) {
                        $value = Mask-SensitiveValue -Key $var -Value $value
                    }
                    $foundVars += @{ Key = $var; Value = $value }
                }
            }
            
            if ($foundVars.Count -gt 0) {
                foreach ($item in $foundVars) {
                    Write-Host "  $($item.Key.PadRight(20)) = $($item.Value)"
                }
            }
            else {
                Write-Host "  No relevant variables found" -ForegroundColor Gray
            }
            
            Write-Host ""
        }
    }
}

function Show-MissingVariables {
    Write-Host "🔍 Missing Environment Variables Check" -ForegroundColor Cyan
    Write-Host ("=" * 40) -ForegroundColor Gray
    
    $requiredVars = @('BINANCE_API_KEY', 'BINANCE_API_SECRET', 'TRADING_CAPITAL')
    $optionalVars = @('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'DATABASE_URL', 'REDIS_URL')
    
    Write-Host "📋 Required Variables:" -ForegroundColor Yellow
    $missingRequired = @()
    foreach ($var in $requiredVars) {
        $value = [Environment]::GetEnvironmentVariable($var)
        if ($value) {
            $maskedValue = Mask-SensitiveValue -Key $var -Value $value
            Write-Host "  ✅ $($var.PadRight(20)) = $maskedValue" -ForegroundColor Green
        }
        else {
            Write-Host "  ❌ $($var.PadRight(20)) = NOT SET" -ForegroundColor Red
            $missingRequired += $var
        }
    }
    
    Write-Host "`n📋 Optional Variables:" -ForegroundColor Yellow
    $missingOptional = @()
    foreach ($var in $optionalVars) {
        $value = [Environment]::GetEnvironmentVariable($var)
        if ($value) {
            $maskedValue = Mask-SensitiveValue -Key $var -Value $value
            Write-Host "  ✅ $($var.PadRight(20)) = $maskedValue" -ForegroundColor Green
        }
        else {
            Write-Host "  ⚠️  $($var.PadRight(20)) = NOT SET" -ForegroundColor Yellow
            $missingOptional += $var
        }
    }
    
    if ($missingRequired.Count -gt 0) {
        Write-Host "`n❌ Missing $($missingRequired.Count) required variables:" -ForegroundColor Red
        foreach ($var in $missingRequired) {
            Write-Host "   - $var" -ForegroundColor Red
        }
        Write-Host "`n💡 Set these variables before running the trading bot!" -ForegroundColor Cyan
    }
    
    if ($missingOptional.Count -gt 0) {
        Write-Host "`n⚠️  Missing $($missingOptional.Count) optional variables:" -ForegroundColor Yellow
        foreach ($var in $missingOptional) {
            Write-Host "   - $var" -ForegroundColor Yellow
        }
        Write-Host "`n💡 These are optional but recommended for full functionality." -ForegroundColor Cyan
    }
}

# Main execution
if ($CheckMissing) {
    Show-MissingVariables
}
else {
    Show-EnvironmentVariables -ShowSensitive $ShowSensitive -Format $Format
}

if ($ShowSensitive) {
    Write-Host "`n⚠️  WARNING: Sensitive values were displayed. Clear your terminal history!" -ForegroundColor Red
} 