# Script version | Based on original weget installer (see: https://github.com/KRWCLASSIC/weget/blob/2407bb9dca90645af8df5dbe99ac1ca621a68d61/install/install_weget.ps1)
# Below variables are handled by external script that scrapes versions and edits these variables.
$scriptVersion = "v2.0"
$APP_NAME = " "
$APP_OWNER = ""
$APP_VERSION = ""
$APP_BINARY = ""
$APP_DISPLAYNAME = ""
$APP_FOLDER = ""
Write-Host "$APP_DISPLAYNAME ($APP_VERSION) | IronShell installer $scriptVersion" -ForegroundColor Cyan

# Define installation path (user only)
$installPath = Join-Path $env:APPDATA "$APP_OWNER\$APP_FOLDER"

# Add a function to calculate the hash of a file
function Get-FileHashValue {
    param ([string]$filePath)
    return (Get-FileHash -Path $filePath -Algorithm SHA256).Hash
}

# Check if already installed in user path
$existingPaths = @($installPath) | Where-Object { Test-Path (Join-Path $_ "$APP_BINARY") }
if ($existingPaths) {
    Write-Host "$APP_DISPLAYNAME is already installed at: $($existingPaths -join ', ')" -ForegroundColor Yellow
    $installPath = $existingPaths
} else {
    # Create directory if it does not exist
    if (!(Test-Path $installPath)) {
        Write-Host "Creating installation directory: $installPath" -ForegroundColor Green
        New-Item -ItemType Directory -Path $installPath -Force | Out-Null
    }
}

# Verify installation
$binaryPath = Join-Path $installPath "$APP_BINARY"
Write-Host "Expected $APP_BINARY path: $binaryPath" -ForegroundColor Magenta
if (Test-Path $binaryPath) {
    Write-Host "Verifying existing installation of $APP_DISPLAYNAME..." -ForegroundColor Cyan
}

# Verify existing installation
$usedCachedDownload = $false
if (Test-Path $binaryPath) {
    try {
        Write-Host "Calculating hash of existing binary..." -ForegroundColor DarkGray
        $existingHash = Get-FileHashValue $binaryPath
        $binaryUrl = "https://github.com/$APP_OWNER/$APP_NAME/releases/download/$APP_VERSION/$APP_BINARY"
        $tempExeDestination = Join-Path $installPath "$APP_BINARY.temp"
        Write-Host "Downloading latest binary for hash comparison..." -ForegroundColor DarkGray
        Invoke-WebRequest -Uri $binaryUrl -OutFile $tempExeDestination -ErrorAction Stop
        Write-Host "Calculating hash of downloaded binary..." -ForegroundColor DarkGray
        $newHash = Get-FileHashValue $tempExeDestination
        if ($existingHash -ne $newHash) {
            Write-Host "New version detected. Updating $APP_DISPLAYNAME..." -ForegroundColor Green
            Move-Item -Path $tempExeDestination -Destination $binaryPath -Force
            $usedCachedDownload = $true
        } else {
            Write-Host "Existing installation is up to date." -ForegroundColor Green
            Remove-Item $tempExeDestination -Force
            return
        }
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 500) {
            Write-Host "GitHub returned 500. GitHub seems to be down." -ForegroundColor Red
        } else {
            Write-Host "Failed to verify existing installation: $_" -ForegroundColor Red
        }
        return
    }
} else {
    Write-Host "$APP_DISPLAYNAME not found. Proceeding with installation..." -ForegroundColor Yellow
}

# Fetch the latest binary URL and install (only if not already downloaded and moved)
if (-not $usedCachedDownload) {
    try {
        $binaryUrl = "https://github.com/$APP_OWNER/$APP_NAME/releases/download/$APP_VERSION/$APP_BINARY"
        $exeDestination = Join-Path $installPath "$APP_BINARY"
        Write-Host "Downloading $APP_DISPLAYNAME ($APP_VERSION) to: $exeDestination" -ForegroundColor Cyan
        Invoke-WebRequest -Uri $binaryUrl -OutFile $exeDestination -ErrorAction Stop
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 500) {
            Write-Host "GitHub returned 500. GitHub seems to be down." -ForegroundColor Red
        } else {
            Write-Host "Failed to download ${APP_DISPLAYNAME}: $_" -ForegroundColor Red
        }
        return
    }
}

# Add to user PATH
$userEnvPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($userEnvPath -notlike "*$installPath*") {
    Write-Host "Adding to user PATH" -ForegroundColor Green
    [System.Environment]::SetEnvironmentVariable("Path", "$userEnvPath;$installPath", "User")
} else {
    Write-Host "Already in user PATH" -ForegroundColor Yellow
}

# Refresh PATH in current session
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User")

# Final message
Write-Host "Installation complete! $APP_DISPLAYNAME ($APP_VERSION) is ready to use." -ForegroundColor Green
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")