import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from huggingface_hub import HfApi


DEFAULT_BASE_MODEL = "NousResearch/Llama-2-7b-hf"
DEFAULT_ADAPTER_MODEL = "oliverwang15/FinGPT_v32_Llama2_Sentiment_Instruction_LoRA_FT"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether the Hugging Face FinGPT backend works.")
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--adapter-model", default=DEFAULT_ADAPTER_MODEL)
    parser.add_argument("--hf-token", default=None)
    parser.add_argument("--skip-access", action="store_true")
    parser.add_argument("--skip-load", action="store_true")
    return parser.parse_args()


def check_model_access(repo_id: str, token: str | None) -> bool:
    try:
        info = HfApi().model_info(repo_id=repo_id, token=token)
    except Exception as exc:
        print(f"access check failed: {repo_id}", flush=True)
        print(f"reason: {type(exc).__name__}: {exc}", flush=True)
        return False
    print(f"access check ok: {repo_id}", flush=True)
    print(f"sha: {info.sha}", flush=True)
    return True


def main() -> int:
    args = parse_args()
    hf_token = args.hf_token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")

    print(f"hf token configured: {bool(hf_token)}", flush=True)
    print(f"base model: {args.base_model}", flush=True)
    print(f"adapter model: {args.adapter_model}", flush=True)

    if args.skip_access:
        print("skip-access enabled: online repository access check not attempted.", flush=True)
    else:
        base_ok = check_model_access(args.base_model, hf_token)
        adapter_ok = check_model_access(args.adapter_model, hf_token)
        if not base_ok or not adapter_ok:
            return 1

    if args.skip_load:
        print("skip-load enabled: repository access checked, model loading not attempted.", flush=True)
        return 0

    print("importing local HF model utilities...", flush=True)
    from student_local.common import load_model_and_tokenizer, predict_sentiments

    print("loading base model and LoRA adapter...", flush=True)
    tokenizer, model = load_model_and_tokenizer(
        base_model=args.base_model,
        adapter_model=args.adapter_model,
        hf_token=hf_token,
        load_in_4bit=True,
    )
    print("model load ok: base model + LoRA adapter loaded with 4-bit quantization", flush=True)

    results = predict_sentiments(
        texts=["Apple shares rose after the company reported stronger than expected earnings."],
        tokenizer=tokenizer,
        model=model,
        batch_size=1,
    )
    print(f"sample prediction: {results[0]['prediction']}", flush=True)
    print(f"sample raw output: {results[0]['raw_output']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
