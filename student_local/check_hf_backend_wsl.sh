#!/usr/bin/env bash
set -euo pipefail

source student_local/activate_wsl_env.sh
python -u student_local/check_hf_backend.py "$@"
