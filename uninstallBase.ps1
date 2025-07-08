# Script version
# Below variables are handled by external script that edits them.
$scriptVersion = "v1.1"
$APP_OWNER = ""
$APP_BINARY = ""
$APP_DISPLAYNAME = ""
$APP_FOLDER = ""
$APP_POST_UNINSTALL_MESSAGE = ""

# Define installation path (user only)
$installPath = Join-Path $env:APPDATA "$APP_OWNER\$APP_FOLDER"

# ISver file path
$isverPath = Join-Path $installPath "ISver.txt"
$installedVersion = "unknown"
if (Test-Path $isverPath) {
    $installedVersion = (Get-Content $isverPath -Raw).Trim()
}
Write-Host "$APP_DISPLAYNAME ($installedVersion) uninstaller | IronShell uninstaller $scriptVersion" -ForegroundColor Cyan

# Check if already installed in user path
$binaryPath = Join-Path $installPath "$APP_BINARY"
Write-Host "Expected $APP_BINARY path: $binaryPath" -ForegroundColor Magenta

# Try to remove the binary (if it exists)
try {
    if (Test-Path $binaryPath) {
        Remove-Item $binaryPath -Force
        Write-Host "Removed $APP_BINARY from $installPath" -ForegroundColor Green
    } else {
        Write-Host "$APP_BINARY not found in $installPath" -ForegroundColor Yellow
    }
} catch {
    Write-Host ("Failed to remove " + $APP_BINARY + ": " + $_) -ForegroundColor Red
}

# Try to remove ISver.txt (if it exists)
try {
    if (Test-Path $isverPath) {
        Remove-Item $isverPath -Force
        Write-Host "Removed ISver.txt from $installPath" -ForegroundColor Green
    } else {
        Write-Host "ISver.txt not found in $installPath" -ForegroundColor Yellow
    }
} catch {
    Write-Host ("Failed to remove ISver.txt: " + $_) -ForegroundColor Red
}

# Try to remove the install directory if empty
try {
    if (Test-Path $installPath) {
        if ((Get-ChildItem -Path $installPath | Measure-Object).Count -eq 0) {
            Remove-Item $installPath -Force
            Write-Host "Removed empty install directory: $installPath" -ForegroundColor Green
        } else {
            Write-Host "Install directory not empty, not removed: $installPath" -ForegroundColor Yellow
        }
    } else {
        Write-Host "$installPath does not exist, nothing to remove." -ForegroundColor Yellow
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

if ($APP_POST_UNINSTALL_MESSAGE -ne "") {
    Write-Host $APP_POST_UNINSTALL_MESSAGE -ForegroundColor Magenta
}

Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")