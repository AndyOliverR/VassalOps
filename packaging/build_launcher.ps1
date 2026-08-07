# Build a real VassalOps.exe launcher (replaces the old stub VassalOpsLaunch.exe).
# Requires: pip install pyinstaller
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location (Join-Path $Root "packaging")

Write-Host "Installing PyInstaller if needed..."
python -m pip install --user pyinstaller | Out-Null

Write-Host "Building VassalOps.exe..."
$outDir = Join-Path $Root "packaging\out"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
python -m PyInstaller --noconfirm --clean --distpath $outDir --workpath (Join-Path $Root "packaging\build") vassalops_launcher.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$built = Join-Path $outDir "VassalOps.exe"
$dest = Join-Path $Root "VassalOps.exe"
if (-not (Test-Path $built)) { throw "Built EXE missing: $built" }
Copy-Item -Force $built $dest
Write-Host "Copied launcher to $dest"
Write-Host "Point your Desktop shortcut at VassalOps.exe (or bootstrap_and_run.bat)."
Write-Host "Done."
