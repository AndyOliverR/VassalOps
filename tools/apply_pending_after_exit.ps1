# Apply a staged VassalOps zip after the GUI process exits (files are no longer locked).
param(
    [Parameter(Mandatory = $true)][string]$Root,
    [int]$WaitPid = 0,
    [string]$Python = "python"
)

$ErrorActionPreference = "Continue"
Start-Sleep -Seconds 2
if ($WaitPid -gt 0) {
    try {
        Wait-Process -Id $WaitPid -ErrorAction SilentlyContinue
    } catch {}
}

Set-Location $Root
$env:PYTHONPATH = $Root
$script = Join-Path $Root "tools\handshake.py"
if (Test-Path $script) {
    & $Python $script --apply-pending
}
