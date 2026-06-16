#!/usr/bin/env bash
#
# Optional CoreML NPU setup for Apple Silicon macOS systems.
# Sets up a virtual environment and installs Apple's ml-stable-diffusion.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$ROOT_DIR/app/backend/mac/coreml_venv"
PYTHON_BIN="$VENV_DIR/bin/python"

echo ""
echo "  ============================================================"
echo "   Local AI Image Generator - Apple Silicon CoreML NPU Setup"
echo "  ============================================================"
echo ""

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "  [ERROR] This setup script is for macOS only." >&2
  exit 1
fi

if [[ "$(uname -m)" != "arm64" ]]; then
  echo "  [ERROR] CoreML NPU support requires Apple Silicon (M1/M2/M3/M4/etc. arm64)." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "  [ERROR] python3 is required. Install Python 3 first (via Homebrew or Xcode)." >&2
  exit 1
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "  Creating Python environment: $VENV_DIR"
  if ! python3 -m venv "$VENV_DIR"; then
    echo "  [ERROR] Could not create the virtual environment."
    exit 1
  fi
fi

echo "  Installing CoreML Stable Diffusion dependencies (numpy, coremltools, diffusers)..."
"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install numpy coremltools diffusers transformers huggingface-hub pillow

echo "  Installing Apple's python-coreml-stable-diffusion package..."
if ! "$PYTHON_BIN" -m pip install "git+https://github.com/apple/ml-stable-diffusion.git"; then
  echo "  [ERROR] Failed to install Apple's ml-stable-diffusion repository."
  echo "          Make sure 'git' is installed on your system."
  exit 1
fi

echo ""
echo "  Verifying CoreML environment..."
if ! "$PYTHON_BIN" -c "from python_coreml_stable_diffusion.pipeline import CoreMLStableDiffusionPipeline; print('  ANE (CoreML) Pipeline verified successfully!')"; then
  echo "  [ERROR] Verification failed. Please check the error details above."
  exit 1
fi

echo ""
echo "  ============================================================"
echo "   CoreML NPU setup complete."
echo "   Restart the launcher (./mac.sh) and download a CoreML model!"
echo "  ============================================================"
echo ""
