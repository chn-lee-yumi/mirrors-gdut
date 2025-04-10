# ******************************************************************************
# Description: This script must be run with administrative privileges to perform certificate installation, modify hosts, and Docker configuration.
# ******************************************************************************

# Function to check if the script is running with admin rights
function Test-IsElevated {
    $user = [Security.Principal.WindowsIdentity]::GetCurrent()
    (New-Object Security.Principal.WindowsPrincipal($user)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check if the script is running with admin rights
if (-not (Test-IsElevated)) {
    Write-Host "This script requires administrator privileges. Restarting as administrator..." -ForegroundColor Yellow

    # Get the current script path
    $scriptPath = $MyInvocation.MyCommand.Path

    # Start a new process with elevated privileges
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" -Verb RunAs

    exit 0
}

# 1. Download and install the CA certificate
Write-Host "[1/4] Download and install the CA certificate..." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri "https://mirrors.gdut.edu.cn/certs/mirrors-ca.crt" -OutFile "$env:TEMP\mirrors-ca.crt"
} catch {
    Write-Host "Download failed, please check your network connection." -ForegroundColor Red
    exit 1
}

Write-Host "Installing CA certificate to the system root certificate authority..." -ForegroundColor Cyan
$certUtilResult = certutil -addstore "Root" "$env:TEMP\mirrors-ca.crt"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Certificate installation failed, please run this script with administrative privileges." -ForegroundColor Red
    exit 1
}

# 2. Modify the hosts file, add resolution information
Write-Host "[2/4] Modifying the hosts file..." -ForegroundColor Cyan
Add-Content -Path "$env:SystemRoot\System32\drivers\etc\hosts" -Value @"
# GDUT Mirrors Registry
202.116.132.68 docker.registry.gdut.edu.cn
202.116.132.68 ghcr.registry.gdut.edu.cn
202.116.132.68 quay.registry.gdut.edu.cn
202.116.132.68 k8s.registry.gdut.edu.cn
202.116.132.68 mcr.registry.gdut.edu.cn
202.116.132.68 gcr.registry.gdut.edu.cn
202.116.132.68 nvcr.registry.gdut.edu.cn
202.116.132.68 elastic.registry.gdut.edu.cn
# GDUT Mirrors Registry END
"@ -ErrorAction Stop

# 3. Modify the Docker daemon configuration to use docker.registry.gdut.edu.cn by default.
Write-Host "[3/4] Detecting Docker Desktop deployment type..." -ForegroundColor Cyan
$isWSLBased = $false
try {
    $wslConfig = wsl --list --verbose | Select-String -Pattern "d" | Select-String -Pattern "o" | Select-String -Pattern "c" | Select-String -Pattern "k" | Select-String -Pattern "e" | Select-String -Pattern "r"
    if ($wslConfig) {
        $isWSLBased = $true
    }
} catch {
    Write-Host "Failed to detect Docker Desktop deployment type. Assuming non-WSL deployment." -ForegroundColor Yellow
}

if ($isWSLBased) {
    Write-Host "WARNING: Detected that you are using Docker Desktop based on WSL, you may need to write the following configuration to the Docker daemon configuration file manually:" -ForegroundColor Yellow
    Write-Host @"
{
    `"insecure-registries`":  [
        `"docker.registry.gdut.edu.cn`"
    ],
    `"registry-mirrors`":  [
        `"https://docker.registry.gdut.edu.cn`"
    ]
}
"@ -ForegroundColor Yellow
}

# Modify the Docker daemon configuration to use docker.registry.gdut.edu.cn by default.
Write-Host "[4/4] Configuring Docker daemon..." -ForegroundColor Cyan

#$userDockerConfigDir = "C:\ProgramData\Docker\config"
#$userDockerConfigFile = "C:\ProgramData\Docker\config\daemon.json"
$userDockerConfigDir = Join-Path -Path $env:USERPROFILE -ChildPath ".docker"
$userDockerConfigFile = Join-Path -Path $userDockerConfigDir -ChildPath "daemon.json"

# If there is no ".docker" directory, create it.
if (-Not (Test-Path $userDockerConfigDir)) {
    New-Item -ItemType Directory -Path $userDockerConfigDir
}

# Load existing configuration (if it exists)
$newConfig = @{
    "insecure-registries" = @("docker.registry.gdut.edu.cn")
    "registry-mirrors"    = @("https://docker.registry.gdut.edu.cn")
}

if (Test-Path $userDockerConfigFile) {
    try {
        $existingConfig = Get-Content -Path $userDockerConfigFile | ConvertFrom-Json
        # Merge new config into existing config
        foreach ($key in $newConfig.Keys) {
            if ($existingConfig.PSObject.Properties.Name -contains $key) {
                $existingConfig.$key += $newConfig.$key | Where-Object { $_ -notin $existingConfig.$key }
            } else {
                Add-Member -InputObject $existingConfig -MemberType NoteProperty -Name $key -Value $newConfig.$key
            }
        }
        $finalConfig = $existingConfig
    } catch {
        Write-Host "Failed to parse existing daemon.json file. Creating a new one..." -ForegroundColor Yellow
        $finalConfig = $newConfig
    }
} else {
    $finalConfig = $newConfig
}

# Write the final configuration to daemon.json
$finalConfigJson = $finalConfig | ConvertTo-Json -Depth 100
Set-Content -Path $userDockerConfigFile -Value $finalConfigJson

Write-Host "Done! The script execution has ended, please " -ForegroundColor Green -NoNewline
Write-Host "RESTART DOCKER" -ForegroundColor Red -BackgroundColor Black -NoNewline
Write-Host " to make the new configuration available." -ForegroundColor Green
exit 0