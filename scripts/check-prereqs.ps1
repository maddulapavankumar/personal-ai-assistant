param()

$ErrorActionPreference = "Stop"

function Test-Tool {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [string]$VersionArg = "--version"
    )

    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) {
        return [pscustomobject]@{
            Tool = $Name
            Installed = $false
            Version = "NOT INSTALLED"
        }
    }

    try {
        $version = & $Name $VersionArg 2>&1 | Select-Object -First 1
    } catch {
        $version = "Installed, version unknown"
    }

    return [pscustomobject]@{
        Tool = $Name
        Installed = $true
        Version = $version
    }
}

$checks = @(
    (Test-Tool -Name "git"),
    (Test-Tool -Name "python"),
    (Test-Tool -Name "node"),
    (Test-Tool -Name "npm"),
    (Test-Tool -Name "docker")
)

Write-Host "=== Prerequisite Check ===" -ForegroundColor Cyan
$checks | Format-Table -AutoSize

$required = @("git", "python", "node", "npm")
$missingRequired = $checks | Where-Object { $required -contains $_.Tool -and -not $_.Installed }
$docker = $checks | Where-Object { $_.Tool -eq "docker" } | Select-Object -First 1

if ($missingRequired.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing required tools:" -ForegroundColor Red
    $missingRequired | ForEach-Object { Write-Host ("- " + $_.Tool) -ForegroundColor Red }
    exit 1
}

Write-Host ""
Write-Host "Required tools are installed." -ForegroundColor Green

if ($docker -and -not $docker.Installed) {
    Write-Host "Docker is optional right now (recommended later for containerized dev)." -ForegroundColor Yellow
}

exit 0

