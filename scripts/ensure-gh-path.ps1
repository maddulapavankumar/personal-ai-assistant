$ghDirectory = 'C:\Program Files\GitHub CLI'
$ghDirectoryNormalized = $ghDirectory.TrimEnd('\')

if (-not (Test-Path $ghDirectory)) {
    throw "GitHub CLI was not found at $ghDirectory. Install GitHub CLI first and retry."
}

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$userEntries = @()
if ($userPath) {
    $userEntries = $userPath -split ';' | ForEach-Object { $_.Trim() } | Where-Object { $_ }
}

$normalizedUserEntries = @($userEntries | ForEach-Object { $_.TrimEnd('\') })
if (-not ($normalizedUserEntries -contains $ghDirectoryNormalized)) {
    $updatedUserPath = @($userEntries + $ghDirectory) -join ';'
    [Environment]::SetEnvironmentVariable('Path', $updatedUserPath, 'User')
    Write-Host "Added GitHub CLI to your user PATH: $ghDirectory"
}

$currentEntries = @($env:PATH -split ';' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$normalizedCurrentEntries = @($currentEntries | ForEach-Object { $_.TrimEnd('\') })
if (-not ($normalizedCurrentEntries -contains $ghDirectoryNormalized)) {
    $env:PATH = "$ghDirectory;$env:PATH"
    Write-Host "Updated the current session PATH."
}

Write-Host "GitHub CLI is ready to use from the command line."
Write-Host "Run: gh auth status"
