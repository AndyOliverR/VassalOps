# VassalOps one-click bootstrap: deps, Ollama, model check, then launch UI.
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$StorageDir = Join-Path $Root "storage"
if (-not (Test-Path $StorageDir)) { New-Item -ItemType Directory -Path $StorageDir | Out-Null }
$LogPath = Join-Path $StorageDir "launch.log"

function Write-Log([string]$Message) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $LogPath -Value $line
    Write-Host $line
}

function Show-Error([string]$Message) {
    Write-Log "ERROR: $Message"
    try {
        Add-Type -AssemblyName System.Windows.Forms | Out-Null
        [System.Windows.Forms.MessageBox]::Show($Message, "VassalOps Launch Error", "OK", "Error") | Out-Null
    } catch {
        Write-Host $Message
    }
}

Write-Log "=== VassalOps bootstrap starting ==="
Write-Log "Root: $Root"

# Resolve Python
$python = $null
$pythonArgsPrefix = @()
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $python = $pythonCmd.Source
} elseif ($pyLauncher) {
    $python = $pyLauncher.Source
    $pythonArgsPrefix = @("-3")
}

if (-not $python) {
    Show-Error "Python was not found. Install Python 3.11+ from https://www.python.org/downloads/ and re-run VassalOps."
    exit 1
}
Write-Log "Python: $python $($pythonArgsPrefix -join ' ')"

function Invoke-Python([string[]]$ArgsList) {
    & $python @pythonArgsPrefix @ArgsList
    return $LASTEXITCODE
}

# Dependency check / install
Write-Log "Checking Python packages..."
$checkFile = Join-Path $StorageDir "_dep_check.py"
@"
import importlib.util
import sys
mods = ['webview', 'pyautogui', 'langgraph', 'requests', 'pyperclip']
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if missing:
    print('missing:' + ','.join(missing))
    sys.exit(1)
print('ok')
"@ | Set-Content -Path $checkFile -Encoding UTF8

& $python @pythonArgsPrefix $checkFile
if ($LASTEXITCODE -ne 0) {
    Write-Log "Installing requirements.txt (missing packages)..."
    $req = Join-Path $Root "requirements.txt"
    $code = Invoke-Python @("-m", "pip", "install", "-r", $req, "--user")
    if ($code -ne 0) {
        Show-Error "Could not install Python packages. See storage\launch.log. Try: pip install -r requirements.txt"
        exit 1
    }
    & $python @pythonArgsPrefix $checkFile
    if ($LASTEXITCODE -ne 0) {
        Show-Error "Dependencies still missing after install. See storage\launch.log."
        exit 1
    }
}
Write-Log "Python packages OK"

# Launch handshake: apply any staged zip, pull a newer release, send skill shapes if covenant is done
try {
    $handshakeScript = Join-Path $Root "tools\handshake.py"
    if (Test-Path $handshakeScript) {
        Write-Log "Launch handshake (product update + learning share)..."
        $env:PYTHONPATH = $Root
        $hsOut = & $python @pythonArgsPrefix $handshakeScript --reason launch --apply 2>&1
        $hsOut | ForEach-Object { Write-Log "handshake: $_" }
        $hsJson = ($hsOut | Select-Object -Last 1 | Out-String).Trim()
        if ($hsJson -match '"needs_restart":\s*true') {
            Write-Log "Restarting bootstrap after applied product update..."
            & $PSCommandPath
            exit $LASTEXITCODE
        }
    } else {
        $updateScript = Join-Path $Root "update_vassalops.ps1"
        if (Test-Path $updateScript) {
            $updateResult = & $updateScript -Root $Root -Auto
            if ($updateResult -and $updateResult.Applied) {
                Write-Log "Restarting bootstrap after update to $($updateResult.Version)..."
                $env:VASSALOPS_SKIP_UPDATE = "1"
                & $PSCommandPath
                exit $LASTEXITCODE
            }
        }
    }
} catch {
    Write-Log "Handshake/update error (continuing): $($_.Exception.Message)"
}

# One-shot install notepad (GitHub Issues) if local account not yet registered
try {
    $regScript = Join-Path $Root "tools\register_pending.py"
    if (Test-Path $regScript) {
        Write-Log "Checking pending install registration..."
        $env:PYTHONPATH = $Root
        & $python @pythonArgsPrefix $regScript 2>&1 | ForEach-Object { Write-Log "register: $_" }
    }
} catch {
    Write-Log "Install registration skipped: $($_.Exception.Message)"
}

# Load config model
$configPath = Join-Path $Root "config.json"
$activeModel = "llama3"
$hostAddr = "127.0.0.1"
$port = 11434
if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
        if ($cfg.model_configuration.active_model) { $activeModel = [string]$cfg.model_configuration.active_model }
        if ($cfg.model_configuration.host_address) { $hostAddr = [string]$cfg.model_configuration.host_address }
        if ($cfg.model_configuration.port_mapping) { $port = [int]$cfg.model_configuration.port_mapping }
    } catch {
        Write-Log "Warning: could not parse config.json; using defaults"
    }
}
Write-Log "Configured model: $activeModel @ ${hostAddr}:${port}"

function Test-Ollama {
    try {
        $r = Invoke-WebRequest -Uri "http://${hostAddr}:${port}/api/tags" -UseBasicParsing -TimeoutSec 3
        return $r.StatusCode -eq 200
    } catch {
        return $false
    }
}

if (-not (Test-Ollama)) {
    Write-Log "Ollama offline; starting 'ollama serve'..."
    $ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
    if (-not $ollamaCmd) {
        Show-Error "Ollama is not installed or not on PATH. Install from https://ollama.com/ then re-run VassalOps."
        exit 1
    }
    Start-Process -FilePath $ollamaCmd.Source -ArgumentList "serve" -WindowStyle Hidden
    $ready = $false
    for ($i = 1; $i -le 15; $i++) {
        Start-Sleep -Seconds 1
        if (Test-Ollama) { $ready = $true; break }
        Write-Log "Waiting for Ollama... ($i/15)"
    }
    if (-not $ready) {
        Show-Error "Ollama did not start on port $port. Open the Ollama app and try again. See storage\launch.log."
        exit 1
    }
}
Write-Log "Ollama API is reachable"

try {
    $tags = Invoke-RestMethod -Uri "http://${hostAddr}:${port}/api/tags" -TimeoutSec 5
    $names = @()
    if ($tags.models) { $names = @($tags.models | ForEach-Object { $_.name }) }
    Write-Log ("Installed models: " + ($names -join ", "))
    if ($names -notcontains $activeModel) {
        Write-Log "Model '$activeModel' not found. Attempting ollama pull..."
        $ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
        if ($ollamaCmd) {
            & $ollamaCmd.Source pull $activeModel 2>&1 | ForEach-Object { Write-Log $_ }
        }
        $tags = Invoke-RestMethod -Uri "http://${hostAddr}:${port}/api/tags" -TimeoutSec 5
        $names = @($tags.models | ForEach-Object { $_.name })
    }
    if ($names -notcontains $activeModel) {
        $fallbacks = @("llama3.2", "llama3", "phi3", "qwen2.5")
        $chosen = $null
        foreach ($fb in $fallbacks) {
            if ($names -contains $fb) { $chosen = $fb; break }
            if ($ollamaCmd) {
                Write-Log "Trying fallback model pull: $fb"
                & $ollamaCmd.Source pull $fb 2>&1 | ForEach-Object { Write-Log $_ }
                $tags = Invoke-RestMethod -Uri "http://${hostAddr}:${port}/api/tags" -TimeoutSec 5
                $names = @($tags.models | ForEach-Object { $_.name })
                if ($names -contains $fb) { $chosen = $fb; break }
            }
        }
        if (-not $chosen -and $names.Count -gt 0) { $chosen = [string]$names[0] }
        if ($chosen) {
            Write-Log "Using fallback model '$chosen' (configured '$activeModel' unavailable)."
            $activeModel = $chosen
            try {
                $cfgObj = Get-Content $configPath -Raw | ConvertFrom-Json
                $cfgObj.model_configuration.active_model = $chosen
                ($cfgObj | ConvertTo-Json -Depth 8) | Set-Content -Path $configPath -Encoding UTF8
                Write-Log "Updated config.json active_model -> $chosen"
            } catch {
                Write-Log "Warning: could not persist fallback model to config.json"
            }
        } else {
            $list = if ($names.Count) { $names -join ", " } else { "(none)" }
            Show-Error "No usable Ollama model found.`nInstalled: $list`nRun: ollama pull llama3.2"
            exit 1
        }
    }
} catch {
    Show-Error "Could not verify Ollama models: $($_.Exception.Message)"
    exit 1
}
Write-Log "Model verified: $activeModel"

Write-Log "Starting app.py..."
$appPath = Join-Path $Root "app.py"
$stdoutLog = Join-Path $StorageDir "app_stdout.log"
$stderrLog = Join-Path $StorageDir "app_stderr.log"
$argList = @()
$argList += $pythonArgsPrefix
$argList += $appPath

# Prefer pythonw / pyw: no console window, but do NOT use -WindowStyle Hidden —
# that would also hide the VassalOps GUI (pywebview) the user needs to chat with.
$guiPython = $null
$leaf = [System.IO.Path]::GetFileNameWithoutExtension($python).ToLowerInvariant()
if ($leaf -eq "python") {
    $candidate = [System.IO.Path]::Combine([System.IO.Path]::GetDirectoryName($python), "pythonw.exe")
    if (Test-Path $candidate) { $guiPython = $candidate }
} elseif ($leaf -eq "py") {
    $pyw = Get-Command pyw -ErrorAction SilentlyContinue
    if ($pyw) { $guiPython = $pyw.Source }
}
if (-not $guiPython) {
    $pythonwCmd = Get-Command pythonw -ErrorAction SilentlyContinue
    if ($pythonwCmd) { $guiPython = $pythonwCmd.Source }
}
if (-not $guiPython) { $guiPython = $python }

$proc = Start-Process -FilePath $guiPython -ArgumentList $argList -WorkingDirectory $Root `
    -PassThru -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog
Write-Log "app.py started with PID $($proc.Id) via $guiPython (GUI visible, no console)"
Write-Log "=== VassalOps bootstrap finished ==="
exit 0
