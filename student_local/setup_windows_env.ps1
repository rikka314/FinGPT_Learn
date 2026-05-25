$ErrorActionPreference = "Stop"

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    throw "conda was not found in PATH."
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeRoot = Join-Path $repoRoot ".runtime"
$envPrefix = Join-Path $runtimeRoot "conda\fingpt310win"
if (-not (Test-Path $envPrefix)) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $envPrefix) | Out-Null
    conda create -y --override-channels -c conda-forge --prefix $envPrefix python=3.10
}

conda run --prefix $envPrefix python -m pip install --upgrade pip
conda run --prefix $envPrefix python -m pip install torch --index-url https://download.pytorch.org/whl/cu128
conda run --prefix $envPrefix python -m pip install `
    transformers `
    peft `
    accelerate `
    bitsandbytes `
    "datasets<4" `
    evaluate `
    scikit-learn `
    pandas `
    sentencepiece `
    protobuf `
    ipykernel

conda run --prefix $envPrefix python student_local/check_env.py
