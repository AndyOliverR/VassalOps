# OPTIONAL developer packaging: thin VassalOps.exe that starts bootstrap_and_run.bat.
# Lay users should use bootstrap_and_run.bat / install_vassalops.ps1 instead.
#
# WARNING: Unsigned PyInstaller one-file EXEs are frequently flagged as malware by
# K7, Windows Defender, and other AVs (false positive). Before building:
#   1. Add a folder exclusion for this repo in your antivirus.
#   2. Do not point the Desktop shortcut at the EXE for daily use.
# Requires: pip install pyinstaller
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location (Join-Path $Root "packaging")

Write-Host ""
Write-Host "=== AV WARNING ===" -ForegroundColor Yellow
Write-Host "This builds an UNSIGNED PyInstaller EXE. K7/Defender often quarantine it."
Write-Host "Exclude this folder first: $Root"
Write-Host "Supported daily launch path remains: bootstrap_and_run.bat"
Write-Host "=================="
Write-Host ""

Write-Host "Installing PyInstaller if needed..."
python -m pip install --user pyinstaller | Out-Null

Write-Host "Building VassalOps.exe..."
$outDir = Join-Path $Root "packaging\out"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
python -m PyInstaller --noconfirm --clean --distpath $outDir --workpath (Join-Path $Root "packaging\build") vassalops_launcher.spec
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed. If you saw Permission denied on VassalOps.exe, antivirus likely locked/quarantined the file." -ForegroundColor Red
    throw "PyInstaller failed"
}

$built = Join-Path $outDir "VassalOps.exe"
$dest = Join-Path $Root "VassalOps.exe"
if (-not (Test-Path $built)) { throw "Built EXE missing: $built" }
Copy-Item -Force $built $dest
Write-Host "Copied launcher to $dest"
Write-Host "Keep using bootstrap_and_run.bat for the Desktop shortcut (install_vassalops.ps1 does this)."
Write-Host "Done."
