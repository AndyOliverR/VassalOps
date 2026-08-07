# First-run installer for lay users: deps, Ollama check, fallback model, Desktop shortcut.
# Run once:  Right-click → Run with PowerShell   OR   powershell -ExecutionPolicy Bypass -File install_vassalops.ps1
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

Write-Step "VassalOps install starting in $Root"

# Python
$python = $null
$pythonArgsPrefix = @()
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($pythonCmd) { $python = $pythonCmd.Source }
elseif ($pyLauncher) { $python = $pyLauncher.Source; $pythonArgsPrefix = @("-3") }

if (-not $python) {
    Write-Host "Python 3.11+ is required. Download: https://www.python.org/downloads/ (check Add to PATH)." -ForegroundColor Red
    exit 1
}
Write-Host "Python: $python"

Write-Step "Installing Python packages from requirements.txt"
& $python @pythonArgsPrefix -m pip install -r (Join-Path $Root "requirements.txt") --user
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip install failed. See errors above." -ForegroundColor Red
    exit 1
}

# Ollama
Write-Step "Checking Ollama"
$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollamaCmd) {
    Write-Host "Ollama not found on PATH. Install from https://ollama.com/ then re-run this installer." -ForegroundColor Yellow
} else {
    try {
        $null = Invoke-WebRequest -Uri "http://127.0.0.1:11434/api/tags" -UseBasicParsing -TimeoutSec 2
    } catch {
        Write-Host "Starting ollama serve..."
        Start-Process -FilePath $ollamaCmd.Source -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 3
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
        & $ollamaCmd.Source pull $activeModel
        $tags = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5
        $names = @($tags.models | ForEach-Object { $_.name })
    }

    if ($names -notcontains $activeModel) {
        $fallback = "llama3.2"
        Write-Host "Configured model missing. Trying fallback '$fallback'..."
        & $ollamaCmd.Source pull $fallback
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
$exe = Join-Path $Root "VassalOps.exe"
$target = if (Test-Path $exe) { $exe } else { $bat }
$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($shortcutPath)
$sc.TargetPath = $target
$sc.WorkingDirectory = $Root
$sc.WindowStyle = 7
$sc.Description = "VassalOps — local desktop agent"
$icon = Join-Path $Root "storage\dashboard\vassal_icon.ico"
if (Test-Path $icon) { $sc.IconLocation = $icon }
$sc.Save()
Write-Host "Shortcut: $shortcutPath -> $target"

Write-Step "Optional: build real VassalOps.exe launcher"
Write-Host "  powershell -ExecutionPolicy Bypass -File packaging\build_launcher.ps1"

Write-Host ""
Write-Host "Install complete. Double-click the Desktop VassalOps shortcut (or bootstrap_and_run.bat)." -ForegroundColor Green
Write-Host "Marketing spine: Your PC's workday — taught by you, approved by you, run locally."
