param(
    [Parameter(Mandatory = $true)][string]$BaseSha,
    [Parameter(Mandatory = $true)][string]$HeadSha,
    [string]$EventPath = ""
)

$ErrorActionPreference = "Stop"

function Get-ChangedFiles {
    param([string]$Base, [string]$Head)
    $mergeBase = git merge-base $Base $Head
    if (-not $mergeBase) {
        throw "Unable to compute merge-base for $Base and $Head."
    }
    $files = git --no-pager diff --name-only $mergeBase $Head
    if (-not $files) {
        return @()
    }
    return @($files)
}

function Add-UniqueMissingDocs {
    param(
        [System.Collections.Generic.List[string]]$Collector,
        [string[]]$Expected,
        [string[]]$Changed
    )
    foreach ($doc in $Expected) {
        if (($Changed -notcontains $doc) -and ($Collector -notcontains $doc)) {
            [void]$Collector.Add($doc)
        }
    }
}

function Emit-MilestoneMarkerWarnings {
    param([string]$Path)
    $resolvedPath = $Path
    if (-not $resolvedPath) {
        $resolvedPath = $env:GITHUB_EVENT_PATH
    }
    if (-not $resolvedPath -or -not (Test-Path $resolvedPath)) {
        return
    }

    $eventJson = Get-Content -Raw -Path $resolvedPath | ConvertFrom-Json
    $prBody = [string]$eventJson.pull_request.body
    if (-not $prBody.Trim()) {
        Write-Host "::warning title=Definition-of-done marker signal::PR body is empty; include milestone contract and evidence sections."
        return
    }

    $markers = @(
        "## Milestone Contract",
        "## Evidence",
        "- Test results:"
    )
    foreach ($marker in $markers) {
        if ($prBody -notmatch [regex]::Escape($marker)) {
            Write-Host "::warning title=Definition-of-done marker signal::Missing advisory PR marker: $marker"
        }
    }
}

$changedFiles = Get-ChangedFiles -Base $BaseSha -Head $HeadSha
if ($changedFiles.Count -eq 0) {
    Write-Host "No changed files detected."
    exit 0
}

$backendCategoryTouched = $false
$workflowCategoryTouched = $false

$requiredDocsForBackendChanges = @(
    "README.md"
)
$requiredDocsForWorkflowChanges = @(
    "docs/github-review-setup.md",
    "docs/agent-workflow.md",
    ".github/instructions/agent-scope-control.instructions.md"
)

foreach ($file in $changedFiles) {
    if ($file -match '^backend/app/' -or $file -match '^backend/tests/') {
        $backendCategoryTouched = $true
    }
    if ($file -match '^\.github/workflows/' -or $file -match '^\.github/scripts/') {
        $workflowCategoryTouched = $true
    }
}

$missingDocs = [System.Collections.Generic.List[string]]::new()
if ($backendCategoryTouched) {
    Add-UniqueMissingDocs -Collector $missingDocs -Expected $requiredDocsForBackendChanges -Changed $changedFiles
}
if ($workflowCategoryTouched) {
    Add-UniqueMissingDocs -Collector $missingDocs -Expected $requiredDocsForWorkflowChanges -Changed $changedFiles
}

if ($missingDocs.Count -gt 0) {
    $requiredSummary = $missingDocs -join ", "
    Write-Host "::error title=Definition-of-done gate failed::Required docs were not updated for the changed-file categories. Missing: $requiredSummary"
    Write-Host "Changed files:"
    $changedFiles | ForEach-Object { Write-Host " - $_" }
    exit 1
}

Write-Host "Definition-of-done docs mapping check passed."
Emit-MilestoneMarkerWarnings -Path $EventPath
exit 0
