param(
    [string]$Owner = "",
    [string]$Repo = "",
    [string]$PullRequest = "",
    [switch]$IncludeLow
)

$ErrorActionPreference = "Stop"

function Get-ReviewSeverity {
    param(
        [Parameter(Mandatory = $true)][string]$Text
    )

    $normalized = $Text.Trim()
    if ([string]::IsNullOrWhiteSpace($normalized)) {
        return "unknown"
    }

    $checks = @(
        @{ Severity = 'critical'; Regex = '(?i)\b(critical|severity\s*[:=]\s*critical|sev-?0)\b' },
        @{ Severity = 'high'; Regex = '(?i)\b(high|severity\s*[:=]\s*high|sev-?1)\b' },
        @{ Severity = 'medium'; Regex = '(?i)\b(medium|severity\s*[:=]\s*medium|sev-?2)\b' },
        @{ Severity = 'low'; Regex = '(?i)\b(low|severity\s*[:=]\s*low|sev-?3)\b' }
    )

    foreach ($check in $checks) {
        if ($normalized -match $check.Regex) {
            return $check.Severity
        }
    }

    return "unknown"
}

if (-not $Owner) {
    if ($env:GITHUB_REPOSITORY) {
        $Owner = ($env:GITHUB_REPOSITORY -split '/')[0]
        $Repo = ($env:GITHUB_REPOSITORY -split '/')[1]
    }
}

if (-not $Repo -and $Owner -and $Owner.Contains('/')) {
    $parts = $Owner.Split('/', 2)
    $Owner = $parts[0]
    $Repo = $parts[1]
}

if (-not $Owner) {
    $Owner = "maddulapavankumar"
}

if (-not $Repo) {
    $Repo = "personal-ai-assistant"
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI (gh) is not installed or available in PATH. Run: powershell -ExecutionPolicy Bypass -File .\scripts\ensure-gh-path.ps1"
    exit 2
}

if (-not $PullRequest) {
    if ($env:GITHUB_EVENT_PULL_REQUEST_NUMBER) {
        $PullRequest = $env:GITHUB_EVENT_PULL_REQUEST_NUMBER
    }
}

if (-not $PullRequest) {
    $PullRequest = gh pr view --json number --jq '.number' 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($PullRequest)) {
        Write-Error "Could not determine the pull request number. Pass -PullRequest <number> or run this from a PR checkout."
        exit 2
    }
}

$query = @'
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100) {
        nodes {
          isResolved
          comments(first: 50) {
            nodes {
              body
              author {
                login
              }
            }
          }
        }
      }
    }
  }
}
'@

$payload = gh api graphql -f query="$query" -F owner="$Owner" -F repo="$Repo" -F pr=$PullRequest 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($payload)) {
    Write-Error "Unable to fetch review data for $Owner/$Repo#$PullRequest"
    exit 2
}

$parsed = $payload | ConvertFrom-Json
$threads = @($parsed.data.repository.pullRequest.reviewThreads.nodes)
$blocking = @()
$advisory = @()
$unknown = @()

foreach ($thread in $threads) {
    if (-not $thread) { continue }

    foreach ($comment in @($thread.comments.nodes)) {
        if (-not $comment -or [string]::IsNullOrWhiteSpace($comment.body)) { continue }

        $severity = Get-ReviewSeverity -Text $comment.body
        $record = [pscustomobject]@{
            Severity = $severity
            Author = $comment.author.login
            Resolved = $thread.isResolved
            Body = $comment.body
        }

        if ($severity -in @('medium', 'high', 'critical')) {
            $blocking += $record
        }
        elseif ($severity -eq 'low') {
            $advisory += $record
        }
        else {
            $unknown += $record
        }
    }
}

if ($blocking.Count -gt 0) {
    Write-Host "Blocking review findings detected by the repo policy (medium/high/critical):" -ForegroundColor Red
    $blocking | ForEach-Object {
        Write-Host ("- [{0}] {1} | Resolved={2}" -f $_.Severity.ToUpper(), $_.Author, $_.Resolved)
        Write-Host $_.Body.Trim()
        Write-Host ""
    }
    exit 1
}

if ($IncludeLow) {
    Write-Host "Low-severity review findings are allowed because -IncludeLow was requested." -ForegroundColor Yellow
}

if ($advisory.Count -gt 0) {
    Write-Host "Low-severity review findings are advisory only and do not block merge." -ForegroundColor Yellow
    $advisory | ForEach-Object {
        Write-Host ("- [{0}] {1} | Resolved={2}" -f $_.Severity.ToUpper(), $_.Author, $_.Resolved)
        Write-Host $_.Body.Trim()
        Write-Host ""
    }
}

if ($unknown.Count -gt 0) {
    Write-Host "Unclassified review comments were ignored by the default policy; remove or classify them explicitly." -ForegroundColor Yellow
    $unknown | ForEach-Object {
        Write-Host ("- [UNKNOWN] {0} | Resolved={1}" -f $_.Author, $_.Resolved)
        Write-Host $_.Body.Trim()
        Write-Host ""
    }
}

if ($blocking.Count -eq 0 -and $advisory.Count -eq 0 -and $unknown.Count -eq 0) {
    Write-Host "No review findings detected for $Owner/$Repo#$PullRequest." -ForegroundColor Green
}

exit 0
