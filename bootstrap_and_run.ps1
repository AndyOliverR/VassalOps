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
        if ($names -notcontains $activeModel) {
            $list = if ($names.Count) { $names -join ", " } else { "(none)" }
            Show-Error "Configured model '$activeModel' is not available.`nInstalled: $list`nUpdate config.json model_configuration.active_model or run: ollama pull $activeModel"
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
$proc = Start-Process -FilePath $python -ArgumentList $argList -WorkingDirectory $Root -PassThru -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog
Write-Log "app.py started with PID $($proc.Id)"
Write-Log "=== VassalOps bootstrap finished ==="
exit 0
