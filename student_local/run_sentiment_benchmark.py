import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datasets import Dataset, load_dataset, load_from_disk
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from student_local.common import (
    DEFAULT_ADAPTER_MODEL,
    DEFAULT_BACKEND,
    DEFAULT_BASE_MODEL,
    DEFAULT_INSTRUCTION,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_MODEL,
    LABELS,
    get_hf_token,
    load_model_and_tokenizer,
    predict_sentiments_ollama,
    predict_sentiments,
)


LABEL_MAP = {0: "negative", 1: "neutral", 2: "positive"}
DEFAULT_DATASET_DIR = "student_local/data/fpb_full"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a small FPB benchmark with FinGPT.")
    parser.add_argument("--backend", choices=["hf", "ollama"], default=DEFAULT_BACKEND)
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--adapter-model", default=DEFAULT_ADAPTER_MODEL)
    parser.add_argument("--ollama-model", default=DEFAULT_OLLAMA_MODEL)
    parser.add_argument("--ollama-host", default=DEFAULT_OLLAMA_HOST)
    parser.add_argument("--hf-token", default=None)
    parser.add_argument("--instruction", default=DEFAULT_INSTRUCTION)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-samples", type=int, default=32)
    parser.add_argument("--dataset-dir", default=DEFAULT_DATASET_DIR)
    parser.add_argument("--request-timeout", type=int, default=180)
    parser.add_argument("--output-csv", default="student_local/outputs/fpb_benchmark.csv")
    parser.add_argument("--metrics-json", default="student_local/outputs/fpb_benchmark_metrics.json")
    parser.add_argument("--confusion-matrix-csv", default="student_local/outputs/fpb_benchmark_confusion_matrix.csv")
    parser.add_argument("--errors-csv", default="student_local/outputs/fpb_benchmark_errors.csv")
    return parser.parse_args()


def load_or_cache_fpb_dataset(dataset_dir: str) -> Dataset:
    dataset_path = Path(dataset_dir)
    if dataset_path.exists():
        cached = load_from_disk(str(dataset_path))
        if isinstance(cached, Dataset):
            return cached
        return cached["train"]

    dataset = load_dataset(
        "financial_phrasebank",
        "sentences_50agree",
        trust_remote_code=True,
    )["train"]
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.save_to_disk(str(dataset_path))
    return dataset


def load_fpb_subset(max_samples: int, dataset_dir: str) -> list[dict]:
    dataset = load_or_cache_fpb_dataset(dataset_dir=dataset_dir)
    test_split = dataset.train_test_split(test_size=0.2, seed=42)["test"]
    subset = test_split.select(range(min(max_samples, len(test_split))))
    rows = []
    for item in subset:
        rows.append({"text": item["sentence"], "label": LABEL_MAP[item["label"]]})
    return rows


def compute_metrics(y_true: list[str], y_pred: list[str]) -> dict:
    expected_labels = list(LABELS)
    extra_predictions = sorted(set(y_pred) - set(expected_labels))
    return {
        "samples": len(y_true),
        "accuracy": accuracy_score(y_true, y_pred),
        "f1_macro": f1_score(y_true, y_pred, labels=expected_labels, average="macro", zero_division=0),
        "f1_weighted": f1_score(y_true, y_pred, labels=expected_labels, average="weighted", zero_division=0),
        "labels": expected_labels,
        "extra_predictions": extra_predictions,
        "unparsed_predictions": sum(1 for item in y_pred if item == "unparsed"),
    }


def write_predictions_csv(output_csv: str, rows: list[dict], predictions: list[dict]) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["text", "label", "prediction", "raw_output"])
        writer.writeheader()
        for row, pred in zip(rows, predictions):
            writer.writerow(
                {
                    "text": row["text"],
                    "label": row["label"],
                    "prediction": pred["prediction"],
                    "raw_output": pred["raw_output"],
                }
            )
    print(f"saved predictions to: {output_path}")


def write_metrics_json(metrics_json: str, metrics: dict, args: argparse.Namespace) -> None:
    output_path = Path(metrics_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **metrics,
        "backend": args.backend,
        "base_model": args.base_model,
        "adapter_model": args.adapter_model if args.backend == "hf" else None,
        "dataset_dir": args.dataset_dir,
        "max_samples": args.max_samples,
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"saved metrics to: {output_path}")


def write_confusion_matrix_csv(confusion_matrix_csv: str, y_true: list[str], y_pred: list[str]) -> None:
    labels = list(LABELS) + sorted(set(y_pred) - set(LABELS))
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    output_path = Path(confusion_matrix_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["actual\\predicted", *labels])
        for label, counts in zip(labels, matrix):
            writer.writerow([label, *counts.tolist()])
    print(f"saved confusion matrix to: {output_path}")


def write_errors_csv(errors_csv: str, rows: list[dict], predictions: list[dict]) -> int:
    output_path = Path(errors_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    error_count = 0
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["text", "label", "prediction", "raw_output"])
        writer.writeheader()
        for row, pred in zip(rows, predictions):
            if row["label"] == pred["prediction"]:
                continue
            error_count += 1
            writer.writerow(
                {
                    "text": row["text"],
                    "label": row["label"],
                    "prediction": pred["prediction"],
                    "raw_output": pred["raw_output"],
                }
            )
    print(f"saved error cases to: {output_path}")
    return error_count


def main() -> None:
    args = parse_args()
    rows = load_fpb_subset(max_samples=args.max_samples, dataset_dir=args.dataset_dir)
    if args.backend == "ollama":
        predictions = predict_sentiments_ollama(
            texts=[row["text"] for row in rows],
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
        predictions = predict_sentiments(
            texts=[row["text"] for row in rows],
            tokenizer=tokenizer,
            model=model,
            instruction=args.instruction,
            batch_size=args.batch_size,
        )

    y_true = [row["label"] for row in rows]
    y_pred = [item["prediction"] for item in predictions]
    metrics = compute_metrics(y_true, y_pred)

    print(f"samples: {metrics['samples']}")
    print(f"accuracy: {metrics['accuracy']:.4f}")
    print(f"f1_macro: {metrics['f1_macro']:.4f}")
    print(f"f1_weighted: {metrics['f1_weighted']:.4f}")
    print(f"unparsed_predictions: {metrics['unparsed_predictions']}")

    write_predictions_csv(args.output_csv, rows, predictions)
    write_metrics_json(args.metrics_json, metrics, args)
    write_confusion_matrix_csv(args.confusion_matrix_csv, y_true, y_pred)
    error_count = write_errors_csv(args.errors_csv, rows, predictions)
    print(f"error_cases: {error_count}")


if __name__ == "__main__":
    main()
