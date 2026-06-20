# Optional OpenVINO NPU setup for Intel AI Boost systems.
# This does not modify the existing stable-diffusion.cpp backends.

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$venvDir = Join-Path $rootDir "app\tools\openvino-venv-win"
$pythonExe = Join-Path $venvDir "Scripts\python.exe"

Write-Host ""
Write-Host "  ============================================================"
Write-Host "   Local AI Image Generator - OpenVINO NPU Setup"
Write-Host "  ============================================================"
Write-Host ""

$npu = Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -like "*Intel(R) AI Boost*" -or ($_.Name -match "NPU" -and $_.PNPClass -eq "ComputeAccelerator") } |
  Select-Object -First 1

if (-not $npu) {
  Write-Host "  [ERROR] Intel AI Boost NPU was not detected on this system." -ForegroundColor Red
  exit 1
}

Write-Host "  Detected: $($npu.Name)"

$toolsDir = Join-Path $rootDir "app\tools"
$portablePythonDir = Join-Path $toolsDir "python"
$portablePythonExe = Join-Path $portablePythonDir "python.exe"

if (-not (Test-Path $portablePythonExe)) {
  $systemPython = Get-Command python -ErrorAction SilentlyContinue
  if (-not $systemPython) {
    Write-Host "  Python was not detected. Downloading portable Python 3.10..." -ForegroundColor Cyan
    $tempZip = Join-Path $toolsDir "python-standalone.tar.gz"
    $url = "https://github.com/astral-sh/python-build-standalone/releases/download/20240224/cpython-3.10.13+20240224-x86_64-pc-windows-msvc-shared-install_only.tar.gz"
    New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $url -OutFile $tempZip
    Write-Host "  Extracting portable Python..." -ForegroundColor Cyan
    tar.exe -xf $tempZip -C $toolsDir
    if (Test-Path $tempZip) {
      Remove-Item -Force $tempZip
    }
  }
}

$pythonCmd = "python"
if (Test-Path $portablePythonExe) {
  $pythonCmd = $portablePythonExe
  Write-Host "  Using portable Python: $portablePythonExe"
} else {
  Write-Host "  Using system Python..."
}

if (-not (Test-Path $pythonExe)) {
  Write-Host "  Creating Python environment: $venvDir"
  & $pythonCmd -m venv $venvDir
}

Write-Host "  Installing OpenVINO GenAI runtime..."
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install openvino openvino-genai pillow huggingface-hub

Write-Host ""
Write-Host "  Verifying OpenVINO NPU device..."
& $pythonExe -c "import openvino as ov; core=ov.Core(); print('Available devices:', core.available_devices); raise SystemExit(0 if 'NPU' in core.available_devices else 2)"

Write-Host ""
Write-Host "  ============================================================"
Write-Host "   OpenVINO NPU setup complete."
Write-Host "   Restart windows.bat, then download an OpenVINO NPU model."
Write-Host "  ============================================================"
Write-Host ""
