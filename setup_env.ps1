<#
.SYNOPSIS
  Creates ONE clean, consolidated Python virtual environment for FinNews and
  installs a known-good, pinned set of ML + app dependencies.

.DESCRIPTION
  The project previously had two competing venvs (venv\ and references\.venv)
  with mismatched versions of transformers / torch, and accelerate was only
  in one of them. The notebook kernel loaded transformers from the venv that
  HAD NO accelerate, causing:

      ImportError: Using the `Trainer` with `PyTorch` requires `accelerate>=0.26.0`

  This script fixes that for good by:
    1. Locating a usable Python 3.11 or 3.12 (NOT 3.14 — too new for stable
       torch/accelerate wheels). If none is found, it prints install links.
    2. Creating a single .venv at the repo root.
    3. Upgrading pip, then installing pinned, mutually-compatible versions.
    4. Running a verification import so you know it worked.

  Run from a PowerShell window at the repo root:

      cd C:\Users\18sur\Desktop\Suriya\FinNews
      powershell -ExecutionPolicy Bypass -File .\setup_env.ps1

  After it succeeds, select the kernel ".venv\Scripts\python.exe" in Jupyter
  and the dashboard with:  streamlit run src\finnews\dashboard.py
#>

param(
    [string]$PyExe = "",       # optional: explicit python.exe path
    [switch]$SkipVenvCreate    # optional: reuse existing .venv
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot
Write-Host "Repo root: $repoRoot" -ForegroundColor Cyan

# ── 1. Locate a usable Python (3.11 or 3.12 preferred; reject 3.14) ────────
function Test-UsablePython([string]$exe) {
    if (-not (Test-Path $exe)) { return $false }
    $v = & $exe --version 2>&1
    if ($v -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]; $minor = [int]$Matches[2]
        $ver = "$major.$minor"
        if ($major -eq 3 -and ($minor -eq 11 -or $minor -eq 12)) {
            Write-Host "  [ok] $exe -> Python $ver is supported" -ForegroundColor Green
            return $true
        }
        Write-Host "  [skip] $exe -> Python $ver (need 3.11 or 3.12)" -ForegroundColor Yellow
        return $false
    }
    return $false
}

if ($PyExe -ne "") {
    $candidates = @($PyExe)
} else {
    # Search py launcher, common install paths, and PATH.
    $candidates = @()
    foreach ($c in @("3.11", "3.12")) {
        try {
            $p = & py -p $c 2>$null
            if ($p) { $candidates += $p }
        } catch {}
    }
    $candidates += @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Python\python311\python.exe",
        "$env:LOCALAPPDATA\Python\python312\python.exe",
        "C:\Python311\python.exe",
        "C:\Python312\python.exe",
        "python.exe"
    )
}

$chosen = $null
foreach ($c in $candidates) {
    if (Test-UsablePython $c) { $chosen = $c; break }
}

if (-not $chosen) {
    Write-Host ""
    Write-Host "No Python 3.11 or 3.12 found." -ForegroundColor Red
    Write-Host "Python 3.14 (your only install) is too new for stable torch/" -ForegroundColor Yellow
    Write-Host "accelerate wheels. Install Python 3.11 (64-bit) from:" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/release/python-3119/" -ForegroundColor Cyan
    Write-Host "Check 'Add Python to PATH' during install, then re-run this script."
    exit 1
}
Write-Host "Using Python: $chosen" -ForegroundColor Green

# ── 2. Create the consolidated .venv at repo root ─────────────────────────
$venvDir = Join-Path $repoRoot ".venv"
if ((-not $SkipVenvCreate) -and (Test-Path $venvDir)) {
    Write-Host "Removing existing .venv to start fresh..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $venvDir
}
if (-not (Test-Path $venvDir)) {
    Write-Host "Creating .venv..." -ForegroundColor Cyan
    & $chosen -m venv $venvDir
}
$venvPy = Join-Path $venvDir "Scripts\python.exe"
Write-Host "Venv Python: $venvPy" -ForegroundColor Green

# ── 3. Upgrade pip, then install pinned deps ──────────────────────────────
Write-Host "Upgrading pip..." -ForegroundColor Cyan
& $venvPy -m pip install --upgrade pip wheel setuptools 2>&1 | Out-Host

# Install everything EXCEPT torch first (torch gets special GPU/CPU treatment).
Write-Host "Installing pinned dependencies (this can take a few minutes)..." -ForegroundColor Cyan
& $venvPy -m pip install -r (Join-Path $repoRoot "requirements-pinned.txt") 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip install reported errors. See output above." -ForegroundColor Red
    exit 1
}

# ── 3b. Detect NVIDIA GPU and install the right torch build ───────────────
# Default `pip install torch` gives a CPU-only wheel on Windows. If an NVIDIA
# GPU is present, pull the CUDA build from PyTorch's index so training uses
# the GPU (10-50x faster for FinBERT).
Write-Host ""
Write-Host "Detecting GPU..." -ForegroundColor Cyan
$hasNvidia = $false
try {
    $smi = & nvidia-smi --query-gpu=name --format=csv,noheader 2>&1
    if ($LASTEXITCODE -eq 0 -and $smi) {
        $hasNvidia = $true
        Write-Host "  NVIDIA GPU found: $smi" -ForegroundColor Green
    }
} catch {}

if ($hasNvidia) {
    Write-Host "  CUDA torch index: cu128 (required for RTX 50-series / Blackwell GPUs)" -ForegroundColor Cyan
    & $venvPy -m pip install torch --index-url https://download.pytorch.org/whl/cu128 2>&1 | Out-Host
} else {
    Write-Host "  No NVIDIA GPU detected. Installing CPU torch build." -ForegroundColor Yellow
    Write-Host "  (Training will be slow; fine for inference/dashboard.)" -ForegroundColor Yellow
    & $venvPy -m pip install torch --index-url https://download.pytorch.org/whl/cpu 2>&1 | Out-Host
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "torch install reported errors. See output above." -ForegroundColor Red
    exit 1
}

# ── 4. Verify the critical imports ────────────────────────────────────────
Write-Host ""
Write-Host "Verifying imports..." -ForegroundColor Cyan
$verify = @'
import sys
import importlib
pkgs = [
    ("torch",         "torch"),
    ("transformers",  "transformers"),
    ("accelerate",    "accelerate"),
    ("datasets",      "datasets"),
    ("streamlit",     "streamlit"),
    ("plotly",        "plotly"),
    ("pandas",        "pandas"),
    ("sklearn",       "scikit-learn"),
    ("safetensors",   "safetensors"),
]
ok = True
for mod, name in pkgs:
    try:
        m = importlib.import_module(mod)
        v = getattr(m, "__version__", "?")
        loc = getattr(m, "__file__", "?")
        print(f"  [ok]   {name:<13} {v:<10} {loc}")
    except Exception as e:
        print(f"  [FAIL] {name:<13} {e}")
        ok = False

# Torch GPU check - the most common "installed but slow" problem
import torch
if torch.cuda.is_available():
    print(f"\n  GPU READY: {torch.cuda.get_device_name(0)} (CUDA {torch.version.cuda})")
    print(f"  Training will use the GPU.")
else:
    print(f"\n  NOTE: torch is CPU-only (CUDA not available).")
    print(f"  Training will be slow. If you have an NVIDIA GPU, install the cu128")
    print(f"  torch build:  python -m pip install torch --index-url https://download.pytorch.org/whl/cu128")

if not ok:
    print("\nSome imports failed.", file=sys.stderr)
    sys.exit(1)
print("\nAll critical imports succeeded.")
'@
$tmp = Join-Path $env:TEMP "finnews_verify.py"
Set-Content -Path $tmp -Value $verify -Encoding UTF8
& $venvPy $tmp
if ($LASTEXITCODE -ne 0) {
    Write-Host "Verification failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "    Dashboard:         & '$venvDir\Scripts\python.exe' -m streamlit run src\finnews\dashboard.py" -ForegroundColor Cyan
