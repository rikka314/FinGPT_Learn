#!/usr/bin/env bash
# This file is intended to be sourced from an interactive shell.
# Avoid changing caller shell options such as `set -u`.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNTIME_ROOT="$REPO_ROOT/.runtime"
VENV_DIR="$RUNTIME_ROOT/venv"

if [[ ! -x "$VENV_DIR/bin/activate" ]]; then
  echo "Local runtime is missing. Run: bash student_local/setup_wsl_env.sh"
  return 1 2>/dev/null || exit 1
fi

export TMPDIR="$RUNTIME_ROOT/tmp"
export PIP_CACHE_DIR="$RUNTIME_ROOT/pip-cache"
export HF_HOME="$RUNTIME_ROOT/hf-home"
export HF_HUB_DISABLE_SYMLINKS_WARNING=1

source "$VENV_DIR/bin/activate"
