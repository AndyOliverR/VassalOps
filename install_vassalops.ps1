# First-run installer for lay users: Python/Ollama (winget), deps, model, Desktop shortcut.
# Preferred entry: double-click INSTALL.bat
# Or: powershell -ExecutionPolicy Bypass -File install_vassalops.ps1
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Show-DoneDialog([string]$ShortcutPath) {
    $msg = "Install complete.`n`nDouble-click the VassalOps icon on your Desktop to start.`n`nShortcut:`n$ShortcutPath"
    try {
        Add-Type -AssemblyName System.Windows.Forms | Out-Null
        [System.Windows.Forms.MessageBox]::Show(
            $msg,
            "VassalOps Ready",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Information
        ) | Out-Null
    } catch {
        Write-Host $msg -ForegroundColor Green
    }
}

function Refresh-PathEnv {
    $machine = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user"
}

function Test-WingetAvailable {
    return [bool](Get-Command winget -ErrorAction SilentlyContinue)
}

function Install-WithWinget([string]$PackageId, [string]$DisplayName) {
    if (-not (Test-WingetAvailable)) { return $false }
    Write-Step "Installing $DisplayName via winget ($PackageId)..."
    Write-Host "This may take a few minutes. Approve any Windows prompts."
    $args = @(
        "install", "-e", "--id", $PackageId,
        "--accept-package-agreements", "--accept-source-agreements",
        "--disable-interactivity"
    )
    & winget @args
    Refresh-PathEnv
    return ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq -1978335189) # already installed
}

function Resolve-Python {
    Refresh-PathEnv
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd -and $pythonCmd.Source -notmatch 'WindowsApps\\python\.exe$') {
        return @{ Exe = $pythonCmd.Source; ArgsPrefix = @() }
    }
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return @{ Exe = $pyLauncher.Source; ArgsPrefix = @("-3") }
    }
    $candidates = @(
        "$env:LocalAppData\Programs\Python\Python312\python.exe",
        "$env:LocalAppData\Programs\Python\Python311\python.exe",
        "$env:LocalAppData\Programs\Python\Python313\python.exe",
        "C:\Program Files\Python312\python.exe",
        "C:\Program Files\Python311\python.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return @{ Exe = $c; ArgsPrefix = @() } }
    }
    return $null
}

function Resolve-Ollama {
    Refresh-PathEnv
    $cmd = Get-Command ollama -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $candidates = @(
        "$env:LocalAppData\Programs\Ollama\ollama.exe",
        "$env:ProgramFiles\Ollama\ollama.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    return $null
}

Write-Step "VassalOps install starting in $Root"

# --- Python ---
$py = Resolve-Python
if (-not $py) {
    $ok = Install-WithWinget "Python.Python.3.12" "Python 3.12"
    Start-Sleep -Seconds 2
    Refresh-PathEnv
    $py = Resolve-Python
    if (-not $py -and $ok) {
        # winget sometimes needs a new shell for PATH; probe common paths again
        Start-Sleep -Seconds 2
        $py = Resolve-Python
    }
}

if (-not $py) {
    Write-Host ""
    Write-Host "Python 3.11+ is still missing." -ForegroundColor Red
    Write-Host "Install from https://www.python.org/downloads/ (check 'Add python.exe to PATH'), then run INSTALL.bat again."
    try {
        Start-Process "https://www.python.org/downloads/"
    } catch {}
    exit 1
}

$python = $py.Exe
$pythonArgsPrefix = $py.ArgsPrefix
Write-Host "Python: $python $($pythonArgsPrefix -join ' ')"

Write-Step "Installing Python packages from requirements.txt"
& $python @pythonArgsPrefix -m pip install -r (Join-Path $Root "requirements.txt") --user
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip install failed. See errors above." -ForegroundColor Red
    exit 1
}

# --- Ollama ---
Write-Step "Checking Ollama"
$ollamaPath = Resolve-Ollama
if (-not $ollamaPath) {
    $null = Install-WithWinget "Ollama.Ollama" "Ollama"
    Start-Sleep -Seconds 3
    Refresh-PathEnv
    $ollamaPath = Resolve-Ollama
}

if (-not $ollamaPath) {
    Write-Host "Ollama not found. Opening https://ollama.com/ — install it, then run INSTALL.bat again." -ForegroundColor Yellow
    try { Start-Process "https://ollama.com/" } catch {}
} else {
    Write-Host "Ollama: $ollamaPath"
    try {
        $null = Invoke-WebRequest -Uri "http://127.0.0.1:11434/api/tags" -UseBasicParsing -TimeoutSec 2
    } catch {
        Write-Host "Starting ollama serve..."
        Start-Process -FilePath $ollamaPath -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 4
    }

    $configPath = Join-Path $Root "config.json"
    $activeModel = "llama3.2"
    if (Test-Path $configPath) {
        try {
            $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
            if ($cfg.model_configuration.active_model) { $activeModel = [string]$cfg.model_configuration.active_model }
        } catch {}
    }

    $tags = $null
    try { $tags = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5 } catch {}
    $names = @()
    if ($tags -and $tags.models) { $names = @($tags.models | ForEach-Object { $_.name }) }

    if ($names -notcontains $activeModel) {
        Write-Step "Pulling model '$activeModel' (may take a while)..."
        & $ollamaPath pull $activeModel
        $tags = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5
        $names = @($tags.models | ForEach-Object { $_.name })
    }

    if ($names -notcontains $activeModel) {
        $fallback = "llama3.2"
        Write-Host "Configured model missing. Trying fallback '$fallback'..."
        & $ollamaPath pull $fallback
        $tags = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5
        $names = @($tags.models | ForEach-Object { $_.name })
        if ($names -contains $fallback -and (Test-Path $configPath)) {
            try {
                $raw = Get-Content $configPath -Raw | ConvertFrom-Json
                $raw.model_configuration.active_model = $fallback
                ($raw | ConvertTo-Json -Depth 8) | Set-Content -Path $configPath -Encoding UTF8
                Write-Host "Updated config.json active_model -> $fallback"
            } catch {
                Write-Host "Could not rewrite config.json; set active_model manually to an installed model."
            }
        }
    }
}

Write-Step "Creating Desktop shortcut"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "VassalOps.lnk"
$bat = Join-Path $Root "bootstrap_and_run.bat"
# Always use the .bat — unsigned VassalOps.exe is a common AV false positive (K7/Defender).
$target = $bat
$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($shortcutPath)
$sc.TargetPath = $target
$sc.WorkingDirectory = $Root
$sc.WindowStyle = 7
$sc.Description = "VassalOps — local desktop agent (bootstrap_and_run.bat)"
$icon = Join-Path $Root "storage\dashboard\vassal_icon.ico"
if (Test-Path $icon) { $sc.IconLocation = $icon }
$sc.Save()
Write-Host "Shortcut: $shortcutPath -> $target"

Write-Step "Brand splash (walk / somersault)"
$splashPy = Join-Path $Root "tools\show_splash.py"
if (Test-Path $splashPy) {
    try {
        & $python @pythonArgsPrefix $splashPy
    } catch {
        Write-Host "Splash skipped: $($_.Exception.Message)"
    }
} else {
    Write-Host "Splash helper missing; continuing."
}

Write-Host ""
Write-Host "Antivirus tip: If K7/Defender quarantines teach/replay or a built EXE, add a folder exclusion for:" -ForegroundColor Yellow
Write-Host "  $Root"
Write-Host "Prefer this .bat shortcut; do not rely on an unsigned VassalOps.exe for daily use."

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Install complete." -ForegroundColor Green
Write-Host "  Click the VassalOps icon on your Desktop." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "On later launches, VassalOps may offer an update from GitHub Releases (your duties and config stay)."
Write-Host "Marketing spine: Your PC's workday — taught by you, approved by you, run locally."

Show-DoneDialog $shortcutPath
exit 0
