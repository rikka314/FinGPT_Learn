import argparse
import hashlib
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DEFAULT_BASE_MODEL = os.environ.get("FINGPT_BASE_MODEL", "NousResearch/Llama-2-7b-hf")
DEFAULT_ADAPTER_MODEL = os.environ.get(
    "FINGPT_ADAPTER_MODEL",
    "oliverwang15/FinGPT_v32_Llama2_Sentiment_Instruction_LoRA_FT",
)
DEFAULT_OLLAMA_MODEL = os.environ.get("FINGPT_OLLAMA_MODEL", "qwen3.5:9b")
DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11435")
DEFAULT_INSTRUCTION = (
    "What is the sentiment of this news? Please choose an answer from "
    "{negative/neutral/positive}."
)
LABELS = ("negative", "neutral", "positive")


REQUIRED_INPUT_COLUMNS = ("symbol", "published_at", "title", "summary", "source", "url")
ITEM_COLUMNS = (
    "symbol",
    "published_at",
    "trade_date",
    "label",
    "prob_negative",
    "prob_neutral",
    "prob_positive",
    "sentiment_score",
    "confidence",
    "text_hash",
    "source",
    "url",
)
DAILY_COLUMNS = (
    "symbol",
    "date",
    "news_count",
    "positive_count",
    "neutral_count",
    "negative_count",
    "sentiment_mean",
    "sentiment_sum",
    "sentiment_ewm_3",
    "sentiment_ewm_5",
    "negative_tail_ratio",
    "confidence_mean",
)
LABEL_PROBS = {
    "negative": {"prob_negative": 0.85, "prob_neutral": 0.10, "prob_positive": 0.05},
    "neutral": {"prob_negative": 0.10, "prob_neutral": 0.80, "prob_positive": 0.10},
    "positive": {"prob_negative": 0.05, "prob_neutral": 0.10, "prob_positive": 0.85},
    "unparsed": {"prob_negative": 0.34, "prob_neutral": 0.33, "prob_positive": 0.33},
}
POSITIVE_TERMS = {
    "beat",
    "beats",
    "growth",
    "upgrade",
    "raises",
    "record",
    "profit",
    "profits",
    "surge",
    "strong",
    "expand",
    "expands",
    "positive",
    "outperform",
    "improve",
    "improves",
    "exceeded",
    "exceeds",
}
NEGATIVE_TERMS = {
    "miss",
    "misses",
    "cut",
    "cuts",
    "downgrade",
    "loss",
    "losses",
    "weak",
    "fall",
    "falls",
    "drop",
    "drops",
    "lawsuit",
    "warning",
    "negative",
    "underperform",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build daily news sentiment factor CSVs.")
    parser.add_argument("--input-csv", default="student_local/news/raw_news.csv")
    parser.add_argument("--items-csv", default="student_local/outputs/news_sentiment_items.csv")
    parser.add_argument("--daily-csv", default="student_local/outputs/news_sentiment_daily.csv")
    parser.add_argument("--backend", choices=["lexicon", "hf", "ollama"], default="lexicon")
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--adapter-model", default=DEFAULT_ADAPTER_MODEL)
    parser.add_argument("--ollama-model", default=DEFAULT_OLLAMA_MODEL)
    parser.add_argument("--ollama-host", default=DEFAULT_OLLAMA_HOST)
    parser.add_argument("--instruction", default=DEFAULT_INSTRUCTION)
    parser.add_argument("--hf-token", default=None)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-input-length", type=int, default=384)
    parser.add_argument("--max-new-tokens", type=int, default=12)
    parser.add_argument("--request-timeout", type=int, default=180)
    return parser.parse_args()


def read_raw_news(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"raw news CSV not found: {path}")
    df = pd.read_csv(path)
    missing = [column for column in REQUIRED_INPUT_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"raw news CSV missing columns: {', '.join(missing)}")
    df = df.loc[:, REQUIRED_INPUT_COLUMNS].copy()
    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
    if df["published_at"].isna().any():
        bad_rows = df.index[df["published_at"].isna()].tolist()
        raise ValueError(f"published_at has invalid datetime values at rows: {bad_rows}")
    for column in ("title", "summary", "source", "url"):
        df[column] = df[column].fillna("").astype(str).str.strip()
    return df


def build_news_text(row: pd.Series) -> str:
    title = str(row.get("title") or "").strip()
    summary = str(row.get("summary") or "").strip()
    if title and summary:
        return f"{title}\n{summary}"
    return title or summary


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def predict_with_lexicon(texts: list[str]) -> list[dict]:
    results = []
    for text in texts:
        lowered = text.lower()
        tokens = {token.strip(".,:;!?()[]{}'\"").lower() for token in text.split()}
        positive_hits = len(tokens & POSITIVE_TERMS)
        negative_hits = len(tokens & NEGATIVE_TERMS)
        if ("no material" in lowered or "mostly operational" in lowered) and negative_hits == 0:
            label = "neutral"
        elif positive_hits > negative_hits:
            label = "positive"
        elif negative_hits > positive_hits:
            label = "negative"
        else:
            label = "neutral"
        results.append({"input": text, "raw_output": label, "prediction": label})
    return results


def run_sentiment_backend(args: argparse.Namespace, texts: list[str]) -> list[dict]:
    if args.backend == "lexicon":
        return predict_with_lexicon(texts)
    if args.backend == "ollama":
        from student_local.common import predict_sentiments_ollama

        return predict_sentiments_ollama(
            texts=texts,
            model=args.ollama_model,
            host=args.ollama_host,
            instruction=args.instruction,
            request_timeout=args.request_timeout,
        )

    from student_local.common import get_hf_token, load_model_and_tokenizer, predict_sentiments

    tokenizer, model = load_model_and_tokenizer(
        base_model=args.base_model,
        adapter_model=args.adapter_model,
        hf_token=get_hf_token(args.hf_token),
        load_in_4bit=True,
    )
    return predict_sentiments(
        texts=texts,
        tokenizer=tokenizer,
        model=model,
        instruction=args.instruction,
        batch_size=args.batch_size,
        max_input_length=args.max_input_length,
        max_new_tokens=args.max_new_tokens,
    )


def result_to_probabilities(label: str) -> dict[str, float]:
    normalized = label if label in LABELS else "unparsed"
    return dict(LABEL_PROBS[normalized])


def build_item_frame(raw_news: pd.DataFrame, backend_results: list[dict]) -> pd.DataFrame:
    rows = []
    for raw_row, result in zip(raw_news.itertuples(index=False), backend_results):
        text = build_news_text(pd.Series(raw_row._asdict()))
        label = str(result.get("prediction") or "unparsed").lower()
        probs = result_to_probabilities(label)
        sentiment_score = probs["prob_positive"] - probs["prob_negative"]
        confidence = max(probs.values())
        published_at = pd.Timestamp(raw_row.published_at)
        rows.append(
            {
                "symbol": raw_row.symbol,
                "published_at": published_at.isoformat(),
                "trade_date": published_at.date().isoformat(),
                "label": label if label in LABELS else "unparsed",
                **probs,
                "sentiment_score": sentiment_score,
                "confidence": confidence,
                "text_hash": hash_text(text),
                "source": raw_row.source,
                "url": raw_row.url,
            }
        )
    return pd.DataFrame(rows, columns=ITEM_COLUMNS)


def build_daily_frame(items: pd.DataFrame) -> pd.DataFrame:
    if items.empty:
        return pd.DataFrame(columns=DAILY_COLUMNS)

    grouped = (
        items.assign(
            positive_flag=(items["label"] == "positive").astype(int),
            neutral_flag=(items["label"] == "neutral").astype(int),
            negative_flag=(items["label"] == "negative").astype(int),
        )
        .groupby(["symbol", "trade_date"], as_index=False)
        .agg(
            news_count=("label", "size"),
            positive_count=("positive_flag", "sum"),
            neutral_count=("neutral_flag", "sum"),
            negative_count=("negative_flag", "sum"),
            sentiment_mean=("sentiment_score", "mean"),
            sentiment_sum=("sentiment_score", "sum"),
            confidence_mean=("confidence", "mean"),
        )
        .rename(columns={"trade_date": "date"})
        .sort_values(["symbol", "date"])
    )
    grouped["negative_tail_ratio"] = grouped["negative_count"] / grouped["news_count"]
    grouped["sentiment_ewm_3"] = grouped.groupby("symbol")["sentiment_mean"].transform(
        lambda series: series.ewm(span=3, adjust=False).mean()
    )
    grouped["sentiment_ewm_5"] = grouped.groupby("symbol")["sentiment_mean"].transform(
        lambda series: series.ewm(span=5, adjust=False).mean()
    )
    return grouped.loc[:, DAILY_COLUMNS]


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_csv)
    items_path = Path(args.items_csv)
    daily_path = Path(args.daily_csv)

    raw_news = read_raw_news(input_path)
    texts = [build_news_text(row) for _, row in raw_news.iterrows()]
    backend_results = run_sentiment_backend(args, texts)
    items = build_item_frame(raw_news, backend_results)
    daily = build_daily_frame(items)

    write_csv(items, items_path)
    write_csv(daily, daily_path)

    print(f"backend={args.backend}")
    print(f"raw_news_rows={len(raw_news)}")
    print(f"items_rows={len(items)}")
    print(f"daily_rows={len(daily)}")
    print(f"items_csv={items_path}")
    print(f"daily_csv={daily_path}")


if __name__ == "__main__":
    main()
