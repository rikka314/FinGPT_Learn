import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datasets import Dataset, DatasetDict, load_from_disk

from student_local.prepare_sentiment_subset import LABEL_MAP, convert_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check local Financial PhraseBank dataset state.")
    parser.add_argument("--full-dir", default="student_local/data/fpb_full")
    parser.add_argument("--mini-dir", default="student_local/data/fpb_mini")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--expected-train-samples", type=int, default=128)
    parser.add_argument("--expected-test-samples", type=int, default=32)
    return parser.parse_args()


def load_full_dataset(path: str) -> Dataset:
    dataset = load_from_disk(path)
    if isinstance(dataset, DatasetDict):
        return dataset["train"]
    return dataset


def compare_rows(actual, expected) -> tuple[bool, int | None]:
    if len(actual) != len(expected):
        return False, None
    for index, (actual_row, expected_row) in enumerate(zip(actual, expected)):
        if dict(actual_row) != dict(expected_row):
            return False, index
    return True, None


def main() -> int:
    args = parse_args()

    full = load_full_dataset(args.full_dir)
    mini = load_from_disk(args.mini_dir)
    if not isinstance(mini, DatasetDict):
        print(f"mini dataset is not a DatasetDict: {type(mini).__name__}")
        return 1

    print(f"full_dir: {args.full_dir}")
    print(f"full_rows: {len(full)}")
    print(f"full_columns: {full.column_names}")
    print(f"mini_dir: {args.mini_dir}")
    print(f"mini_splits: {list(mini.keys())}")
    print(f"mini_train_rows: {len(mini['train'])}")
    print(f"mini_test_rows: {len(mini['test'])}")
    print(f"mini_train_columns: {mini['train'].column_names}")
    print(f"mini_test_columns: {mini['test'].column_names}")

    split = full.train_test_split(test_size=args.test_size, seed=args.seed)
    expected_train_source = split["train"].select(
        range(min(args.expected_train_samples, len(split["train"])))
    )
    expected_test_source = split["test"].select(
        range(min(args.expected_test_samples, len(split["test"])))
    )
    expected_train = convert_rows(expected_train_source)
    expected_test = convert_rows(expected_test_source)

    train_match, train_mismatch_index = compare_rows(mini["train"], expected_train)
    test_match, test_mismatch_index = compare_rows(mini["test"], expected_test)

    print(f"seed: {args.seed}")
    print(f"test_size: {args.test_size}")
    print(f"expected_train_rows: {len(expected_train)}")
    print(f"expected_test_rows: {len(expected_test)}")
    print(f"mini_train_matches_seed_split: {train_match}")
    if train_mismatch_index is not None:
        print(f"mini_train_first_mismatch_index: {train_mismatch_index}")
    print(f"mini_test_matches_seed_split: {test_match}")
    if test_mismatch_index is not None:
        print(f"mini_test_first_mismatch_index: {test_mismatch_index}")

    label_counts: dict[str, int] = {}
    for row in full:
        label = LABEL_MAP[row["label"]]
        label_counts[label] = label_counts.get(label, 0) + 1
    print(f"full_label_counts: {label_counts}")

    if len(mini["train"]) != args.expected_train_samples:
        return 1
    if len(mini["test"]) != args.expected_test_samples:
        return 1
    if not train_match or not test_match:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
