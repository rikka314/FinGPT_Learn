import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datasets import Dataset, DatasetDict, load_dataset

from student_local.common import DEFAULT_INSTRUCTION


LABEL_MAP = {0: "negative", 1: "neutral", 2: "positive"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a small FPB dataset for local QLoRA.")
    parser.add_argument("--train-samples", type=int, default=128)
    parser.add_argument("--eval-samples", type=int, default=32)
    parser.add_argument("--output-dir", default="student_local/data/fpb_mini")
    return parser.parse_args()


def convert_rows(rows) -> list[dict]:
    return [
        {
            "input": row["sentence"],
            "output": LABEL_MAP[row["label"]],
            "instruction": DEFAULT_INSTRUCTION,
        }
        for row in rows
    ]


def main() -> None:
    args = parse_args()
    dataset = load_dataset(
        "financial_phrasebank",
        "sentences_50agree",
        trust_remote_code=True,
    )["train"]
    split = dataset.train_test_split(test_size=0.2, seed=42)
    train_rows = split["train"].select(range(min(args.train_samples, len(split["train"]))))
    eval_rows = split["test"].select(range(min(args.eval_samples, len(split["test"]))))

    prepared = DatasetDict(
        {
            "train": Dataset.from_list(convert_rows(train_rows)),
            "test": Dataset.from_list(convert_rows(eval_rows)),
        }
    )

    output_dir = Path(args.output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    prepared.save_to_disk(str(output_dir))
    print(f"saved dataset to: {output_dir}")
    print(prepared)


if __name__ == "__main__":
    main()
