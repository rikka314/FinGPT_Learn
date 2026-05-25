#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNTIME_ROOT="$REPO_ROOT/.runtime"
VENV_DIR="$RUNTIME_ROOT/venv"

mkdir -p "$RUNTIME_ROOT/tmp" "$RUNTIME_ROOT/pip-cache" "$RUNTIME_ROOT/hf-home"

export TMPDIR="$RUNTIME_ROOT/tmp"
export PIP_CACHE_DIR="$RUNTIME_ROOT/pip-cache"
export HF_HOME="$RUNTIME_ROOT/hf-home"
export HF_HUB_DISABLE_SYMLINKS_WARNING=1

for stale_dir in "$RUNTIME_ROOT/miniforge3" "$RUNTIME_ROOT/conda"; do
  if [[ -d "$stale_dir" ]]; then
    rm -rf "$stale_dir"
  fi
done

if [[ ! -x "$VENV_DIR/bin/python" || ! -f "$VENV_DIR/bin/activate" ]]; then
  rm -rf "$VENV_DIR"
  VIRTUALENV_PYZ="$RUNTIME_ROOT/tmp/virtualenv.pyz"
  if [[ ! -f "$VIRTUALENV_PYZ" ]]; then
    if command -v curl >/dev/null 2>&1; then
      curl -fsSL https://bootstrap.pypa.io/virtualenv.pyz -o "$VIRTUALENV_PYZ"
    else
      wget -q https://bootstrap.pypa.io/virtualenv.pyz -O "$VIRTUALENV_PYZ"
    fi
  fi
  python3 "$VIRTUALENV_PYZ" "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cu128
python -m pip install \
  --no-cache-dir \
  transformers \
  peft \
  accelerate \
  bitsandbytes \
  "datasets<4" \
  evaluate \
  scikit-learn \
  pandas \
  sentencepiece \
  protobuf \
  ipykernel

echo "runtime root: $RUNTIME_ROOT"
echo "venv: $VENV_DIR"
python student_local/check_env.py
