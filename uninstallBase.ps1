# Script version
# Below variables are handled by external script that edits them.
$scriptVersion = "v1.0"
$APP_OWNER = ""
$APP_BINARY = ""
$APP_DISPLAYNAME = ""
$APP_FOLDER = ""
Write-Host "$APP_DISPLAYNAME uninstaller | IronShell uninstaller $scriptVersion" -ForegroundColor Cyan

# Define installation path (user only)
$installPath = Join-Path $env:APPDATA "$APP_OWNER\$APP_FOLDER"

# Check if already installed in user path
$binaryPath = Join-Path $installPath "$APP_BINARY"
Write-Host "Expected $APP_BINARY path: $binaryPath" -ForegroundColor Magenta
if (!(Test-Path $binaryPath)) {
    Write-Host "$APP_DISPLAYNAME is not installed at: $binaryPath" -ForegroundColor Yellow
    Write-Host "Nothing to uninstall." -ForegroundColor Green
    Write-Host "Press any key to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    return
}

# Try to remove the binary
try {
    Remove-Item $binaryPath -Force
    Write-Host "Removed $APP_BINARY from $installPath" -ForegroundColor Green
} catch {
    Write-Host ("Failed to remove " + $APP_BINARY + ": " + $_) -ForegroundColor Red
}

# Try to remove the install directory if empty
try {
    if ((Get-ChildItem -Path $installPath | Measure-Object).Count -eq 0) {
        Remove-Item $installPath -Force
        Write-Host "Removed empty install directory: $installPath" -ForegroundColor Green
    } else {
        Write-Host "Install directory not empty, not removed: $installPath" -ForegroundColor Yellow
    }
} catch {
    Write-Host ("Failed to remove install directory: " + $_) -ForegroundColor Red
}

# Remove from user PATH if present
$userEnvPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($userEnvPath -like "*${installPath}*") {
    $newPath = ((($userEnvPath -split ";") | Where-Object { $_ -ne $installPath }) -join ";")
    [System.Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Removed $installPath from user PATH" -ForegroundColor Green
} else {
    Write-Host "$installPath not found in user PATH" -ForegroundColor Yellow
}

# Refresh PATH in current session
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User")

# Final message
Write-Host "Uninstallation complete! $APP_DISPLAYNAME has been removed." -ForegroundColor Green
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")