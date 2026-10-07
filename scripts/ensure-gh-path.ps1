$ghDirectory = 'C:\Program Files\GitHub CLI'

if (-not (Test-Path $ghDirectory)) {
    throw "GitHub CLI was not found at $ghDirectory. Install GitHub CLI first and retry."
}

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$userEntries = @()
if ($userPath) {
    $userEntries = $userPath -split ';' | Where-Object { $_ -and $_.Trim() }
}

if (-not ($userEntries -contains $ghDirectory)) {
    $updatedUserPath = ($userEntries + $ghDirectory) -join ';'
    [Environment]::SetEnvironmentVariable('Path', $updatedUserPath, 'User')
    Write-Host "Added GitHub CLI to your user PATH: $ghDirectory"
}

$currentEntries = $env:PATH -split ';' | Where-Object { $_ -and $_.Trim() }
if (-not ($currentEntries -contains $ghDirectory)) {
    $env:PATH = "$ghDirectory;$env:PATH"
    Write-Host "Updated the current session PATH."
}

Write-Host "GitHub CLI is ready to use from the command line."
Write-Host "Run: gh auth status"
