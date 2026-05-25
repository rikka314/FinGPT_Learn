import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from student_local.common import (
    DEFAULT_ADAPTER_MODEL,
    DEFAULT_BACKEND,
    DEFAULT_BASE_MODEL,
    DEFAULT_INSTRUCTION,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_MODEL,
    get_hf_token,
    load_model_and_tokenizer,
    predict_sentiments_ollama,
    predict_sentiments,
)


DEFAULT_EXAMPLES = [
    "FINANCING OF ASPOCOMP'S GROWTH Aspocomp is aggressively pursuing its growth strategy by increasingly focusing on technologically more demanding HDI printed circuit boards.",
    "According to Gran, the company has no plans to move all production to Russia, although that is where the company is growing.",
    "A tinyurl link takes users to a scamming site promising that users can earn thousands of dollars by becoming a Google Cash advertiser.",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local FinGPT sentiment inference.")
    parser.add_argument("--backend", choices=["hf", "ollama"], default=DEFAULT_BACKEND)
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--adapter-model", default=DEFAULT_ADAPTER_MODEL)
    parser.add_argument("--ollama-model", default=DEFAULT_OLLAMA_MODEL)
    parser.add_argument("--ollama-host", default=DEFAULT_OLLAMA_HOST)
    parser.add_argument("--instruction", default=DEFAULT_INSTRUCTION)
    parser.add_argument("--hf-token", default=None)
    parser.add_argument("--batch-size", type=int, default=3)
    parser.add_argument("--max-input-length", type=int, default=384)
    parser.add_argument("--request-timeout", type=int, default=180)
    parser.add_argument("--text", action="append", default=[])
    parser.add_argument("--text-file", default=None)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def load_inputs(args: argparse.Namespace) -> list[str]:
    texts = list(args.text)
    if args.text_file:
        with open(args.text_file, "r", encoding="utf-8") as handle:
            texts.extend([line.strip() for line in handle if line.strip()])
    return texts or list(DEFAULT_EXAMPLES)


def main() -> None:
    args = parse_args()
    texts = load_inputs(args)
    if args.backend == "ollama":
        results = predict_sentiments_ollama(
            texts=texts,
            model=args.ollama_model,
            host=args.ollama_host,
            instruction=args.instruction,
            request_timeout=args.request_timeout,
        )
    else:
        tokenizer, model = load_model_and_tokenizer(
            base_model=args.base_model,
            adapter_model=args.adapter_model,
            hf_token=get_hf_token(args.hf_token),
            load_in_4bit=True,
        )
        results = predict_sentiments(
            texts=texts,
            tokenizer=tokenizer,
            model=model,
            instruction=args.instruction,
            batch_size=args.batch_size,
            max_input_length=args.max_input_length,
        )
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    for idx, item in enumerate(results, start=1):
        print(f"[{idx}] prediction: {item['prediction']}")
        print(f"input: {item['input']}")
        print(f"raw output: {item['raw_output']}")
        print()


if __name__ == "__main__":
    main()
