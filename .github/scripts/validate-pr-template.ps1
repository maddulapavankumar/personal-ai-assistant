param(
    [string]$PrBodyPath = "",
    [string]$EventPath = ""
)

$ErrorActionPreference = "Stop"

function Get-PrBody {
    param([string]$BodyPath, [string]$EvtPath)
    if ($BodyPath -and (Test-Path $BodyPath)) {
        return Get-Content -Raw -Path $BodyPath
    }

    $resolvedEventPath = $EvtPath
    if (-not $resolvedEventPath) {
        $resolvedEventPath = $env:GITHUB_EVENT_PATH
    }
    if (-not $resolvedEventPath -or -not (Test-Path $resolvedEventPath)) {
        throw "PR body input not found. Provide -PrBodyPath or valid GITHUB_EVENT_PATH."
    }

    $eventJson = Get-Content -Raw -Path $resolvedEventPath | ConvertFrom-Json
    return [string]$eventJson.pull_request.body
}

$body = Get-PrBody -BodyPath $PrBodyPath -EvtPath $EventPath
$errors = @()

if (-not $body.Trim()) {
    $errors += "PR body is empty."
}

$requiredHeadings = @(
    "## Milestone Contract",
    "### Goal",
    "### Non-goals",
    "### Files to create/modify",
    "### Validation commands",
    "### Stop conditions considered",
    "## Planner -> Builder -> Reviewer checks",
    "## Evidence"
)

foreach ($heading in $requiredHeadings) {
    if ($body -notmatch [regex]::Escape($heading)) {
        $errors += "Missing heading: $heading"
    }
}

$requiredCheckedItems = @(
    "No new dependencies were added without approval",
    "No API/schema scope was expanded without approval",
    "Ambiguous requirements were stopped and clarified",
    "Planner scope was approved before implementation",
    "Builder stayed in approved scope",
    "Reviewer checked correctness and drift risks"
)

foreach ($item in $requiredCheckedItems) {
    $pattern = "- \[x\] " + [regex]::Escape($item)
    if ($body -notmatch $pattern) {
        $errors += "Unchecked required checkbox: $item"
    }
}

if ($body -match "<!--") {
    $errors += "Template placeholder comments are still present. Remove template comments before merge."
}

if ($body -match "- Test results:\s*$") {
    $errors += "Evidence section is missing test result details."
}

if ($errors.Count -gt 0) {
    Write-Host "PR template compliance failed:" -ForegroundColor Red
    foreach ($issue in $errors) {
        Write-Host " - $issue" -ForegroundColor Red
    }
    exit 1
}

Write-Host "PR template compliance passed." -ForegroundColor Green
exit 0
