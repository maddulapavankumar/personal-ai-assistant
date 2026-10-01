param(
    [Parameter(Mandatory = $true)][string]$BaseSha,
    [Parameter(Mandatory = $true)][string]$HeadSha
)

$ErrorActionPreference = "Stop"

$changedFiles = git --no-pager diff --name-only $BaseSha $HeadSha

if (-not $changedFiles) {
    Write-Host "No changed files detected."
    exit 0
}

$codeTouched = $false
$docsTouched = $false
$docsFiles = @(
    "README.md",
    "docs/agent-workflow.md",
    ".github/instructions/agent-scope-control.instructions.md"
)

foreach ($file in $changedFiles) {
    if ($file -match '^backend/app/' -or $file -match '^backend/tests/' -or $file -match '^\.github/workflows/') {
        $codeTouched = $true
    }
    if ($docsFiles -contains $file) {
        $docsTouched = $true
    }
}

if ($codeTouched -and -not $docsTouched) {
    Write-Host "::warning title=Docs/instructions drift signal::Code or workflow files changed without updates to README/workflow/instruction docs. Consider updating README.md, docs/agent-workflow.md, or .github/instructions/agent-scope-control.instructions.md."
    Write-Host "Changed files:"
    $changedFiles | ForEach-Object { Write-Host " - $_" }
    exit 0
}

Write-Host "Docs/instructions drift check passed."
exit 0

