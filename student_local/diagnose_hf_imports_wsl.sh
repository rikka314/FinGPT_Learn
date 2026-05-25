#!/usr/bin/env bash
set -euo pipefail

source student_local/activate_wsl_env.sh
python -u student_local/diagnose_hf_imports.py
