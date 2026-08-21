# Check GitHub Releases and optionally apply an update (preserves duties + config).
# Called from bootstrap_and_run.ps1. Skip with: $env:VASSALOPS_SKIP_UPDATE = "1"
param(
    [string]$Root = (Split-Path -Parent $MyInvocation.MyCommand.Path),
    [string]$Repo = "AndyOliverR/VassalOps"
)

$ErrorActionPreference = "Continue"

function Get-LocalVersion {
    $path = Join-Path $Root "VERSION"
    if (-not (Test-Path $path)) { return "0.0.0" }
    return ((Get-Content $path -Raw) -replace '\s', '')
}

function ConvertTo-VersionObject([string]$raw) {
    $clean = ($raw -replace '^v', '' -replace '\s', '')
    $parts = $clean.Split('.')
    $major = 0; $minor = 0; $patch = 0
    if ($parts.Count -ge 1) { [void][int]::TryParse($parts[0], [ref]$major) }
    if ($parts.Count -ge 2) { [void][int]::TryParse($parts[1], [ref]$minor) }
    if ($parts.Count -ge 3) {
        $patchPart = ($parts[2] -split '[-+]')[0]
        [void][int]::TryParse($patchPart, [ref]$patch)
    }
    return [pscustomobject]@{ Major = $major; Minor = $minor; Patch = $patch; Raw = $clean }
}

function Test-IsNewerVersion([string]$Candidate, [string]$Current) {
    $a = ConvertTo-VersionObject $Candidate
    $b = ConvertTo-VersionObject $Current
    if ($a.Major -ne $b.Major) { return $a.Major -gt $b.Major }
    if ($a.Minor -ne $b.Minor) { return $a.Minor -gt $b.Minor }
    return $a.Patch -gt $b.Patch
}

function Write-UpdateLog([string]$Message) {
    $logDir = Join-Path $Root "storage"
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path (Join-Path $logDir "launch.log") -Value $line
    Write-Host $line
}

function Show-UpdatePrompt([string]$LocalVer, [string]$RemoteVer, [string]$Notes) {
    $body = "VassalOps $RemoteVer is available (you have $LocalVer).`n`nUpdate now? Your duties, teach memory, and config.json are kept.`nApprove-gated desktop behavior is unchanged."
    if ($Notes) {
        $trim = $Notes.Trim()
        if ($trim.Length -gt 280) { $trim = $trim.Substring(0, 280) + "..." }
        $body += "`n`n$trim"
    }
    try {
        Add-Type -AssemblyName System.Windows.Forms | Out-Null
        $r = [System.Windows.Forms.MessageBox]::Show(
            $body,
            "VassalOps Update",
            [System.Windows.Forms.MessageBoxButtons]::YesNo,
            [System.Windows.Forms.MessageBoxIcon]::Question
        )
        return ($r -eq [System.Windows.Forms.DialogResult]::Yes)
    } catch {
        Write-Host $body
        Write-Host "Type Y to update, anything else to skip:"
        $ans = Read-Host
        return ($ans -match '^[Yy]')
    }
}

function Get-LatestRelease {
    $uri = "https://api.github.com/repos/$Repo/releases/latest"
    $headers = @{
        "User-Agent" = "VassalOps-Updater"
        "Accept"     = "application/vnd.github+json"
    }
    return Invoke-RestMethod -Uri $uri -Headers $headers -TimeoutSec 12
}

function Find-ReleaseZipUrl($release, [string]$version) {
    $want = @("VassalOps-$version.zip", "VassalOps-v$version.zip")
    if ($release.assets) {
        foreach ($name in $want) {
            $hit = @($release.assets | Where-Object { $_.name -eq $name }) | Select-Object -First 1
            if ($hit -and $hit.browser_download_url) { return [string]$hit.browser_download_url }
        }
        $any = @($release.assets | Where-Object { $_.name -like "VassalOps-*.zip" }) | Select-Object -First 1
        if ($any -and $any.browser_download_url) { return [string]$any.browser_download_url }
    }
    # Fallback: source zipball (nested folder; apply step handles it)
    if ($release.zipball_url) { return [string]$release.zipball_url }
    return $null
}

function Resolve-ExtractedRoot([string]$ExtractDir) {
    $direct = Join-Path $ExtractDir "app.py"
    if (Test-Path $direct) { return $ExtractDir }
    $kids = Get-ChildItem -Path $ExtractDir -Directory -ErrorAction SilentlyContinue
    foreach ($k in $kids) {
        if (Test-Path (Join-Path $k.FullName "app.py")) { return $k.FullName }
    }
    return $ExtractDir
}

function Invoke-VassalOpsUpdate([string]$ZipUrl, [string]$NewVersion) {
    $work = Join-Path $env:TEMP ("vassalops-update-" + [guid]::NewGuid().ToString("N"))
    $zipPath = Join-Path $work "release.zip"
    $extract = Join-Path $work "extract"
    $preserve = Join-Path $work "preserve"
    New-Item -ItemType Directory -Path $extract, $preserve | Out-Null

    Write-UpdateLog "Downloading update from $ZipUrl"
    Invoke-WebRequest -Uri $ZipUrl -OutFile $zipPath -UseBasicParsing -TimeoutSec 120
    Expand-Archive -Path $zipPath -DestinationPath $extract -Force
    $src = Resolve-ExtractedRoot $extract
    Write-UpdateLog "Extracted update root: $src"

    # Preserve user state
    $configPath = Join-Path $Root "config.json"
    if (Test-Path $configPath) {
        Copy-Item $configPath (Join-Path $preserve "config.json") -Force
    }
    $storageSrc = Join-Path $Root "storage"
    if (Test-Path $storageSrc) {
        Copy-Item $storageSrc (Join-Path $preserve "storage") -Recurse -Force
    }

    # Overlay product files (do not touch .git)
    Get-ChildItem -Path $src -Force | ForEach-Object {
        if ($_.Name -eq ".git") { return }
        $dest = Join-Path $Root $_.Name
        if ($_.PSIsContainer) {
            if ($_.Name -eq "storage") { return } # restore + merge below
            Copy-Item $_.FullName $dest -Recurse -Force
        } else {
            if ($_.Name -eq "config.json") { return }
            Copy-Item $_.FullName $dest -Force
        }
    }

    # Restore storage, then refresh product surfaces from the release
    $restoredStorage = Join-Path $Root "storage"
    if (Test-Path (Join-Path $preserve "storage")) {
        if (Test-Path $restoredStorage) { Remove-Item $restoredStorage -Recurse -Force }
        Copy-Item (Join-Path $preserve "storage") $restoredStorage -Recurse -Force
    } elseif (-not (Test-Path $restoredStorage)) {
        New-Item -ItemType Directory -Path $restoredStorage | Out-Null
    }

    $newStorage = Join-Path $src "storage"
    foreach ($rel in @("dashboard", "duties\packs")) {
        $from = Join-Path $newStorage $rel
        $to = Join-Path $restoredStorage $rel
        if (Test-Path $from) {
            if (-not (Test-Path $to)) { New-Item -ItemType Directory -Path $to -Force | Out-Null }
            Copy-Item (Join-Path $from "*") $to -Recurse -Force
        }
    }

    if (Test-Path (Join-Path $preserve "config.json")) {
        Copy-Item (Join-Path $preserve "config.json") $configPath -Force
    }

    # Ensure VERSION matches release even if zipball lag
    Set-Content -Path (Join-Path $Root "VERSION") -Value $NewVersion -Encoding UTF8 -NoNewline

    Write-UpdateLog "Update files applied for $NewVersion"
    Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
}

# --- entry ---
if ($env:VASSALOPS_SKIP_UPDATE -eq "1") {
    Write-UpdateLog "Update check skipped (VASSALOPS_SKIP_UPDATE=1)"
    return @{ Applied = $false; Skipped = $true }
}

$local = Get-LocalVersion
Write-UpdateLog "Local VERSION: $local"

try {
    $release = Get-LatestRelease
} catch {
    Write-UpdateLog "No update check (GitHub Releases unreachable or none published): $($_.Exception.Message)"
    return @{ Applied = $false; Skipped = $true }
}

if (-not $release -or -not $release.tag_name) {
    Write-UpdateLog "No GitHub release found; continuing."
    return @{ Applied = $false; Skipped = $true }
}

$remoteTag = [string]$release.tag_name
$remoteVer = ($remoteTag -replace '^v', '')
if (-not (Test-IsNewerVersion $remoteVer $local)) {
    Write-UpdateLog "Already up to date ($local)."
    return @{ Applied = $false; Skipped = $true }
}

$notes = ""
if ($release.body) { $notes = [string]$release.body }
if (-not (Show-UpdatePrompt $local $remoteVer $notes)) {
    Write-UpdateLog "User declined update to $remoteVer"
    return @{ Applied = $false; Skipped = $true }
}

$zipUrl = Find-ReleaseZipUrl $release $remoteVer
if (-not $zipUrl) {
    Write-UpdateLog "Update aborted: no zip asset on release $remoteTag"
    return @{ Applied = $false; Skipped = $true }
}

try {
    Invoke-VassalOpsUpdate -ZipUrl $zipUrl -NewVersion $remoteVer
    Write-UpdateLog "Update to $remoteVer complete"
    return @{ Applied = $true; Version = $remoteVer }
} catch {
    Write-UpdateLog "Update failed: $($_.Exception.Message)"
    try {
        Add-Type -AssemblyName System.Windows.Forms | Out-Null
        [System.Windows.Forms.MessageBox]::Show(
            "Update failed. Continuing with your current install.`n$($_.Exception.Message)",
            "VassalOps Update",
            "OK",
            "Warning"
        ) | Out-Null
    } catch {}
    return @{ Applied = $false; Skipped = $true; Error = $_.Exception.Message }
}
