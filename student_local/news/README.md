# News Sentiment Factor

This folder defines the raw-news CSV contract for the local FinGPT sentiment reproduction layer.

## Input

`student_local/news/raw_news.csv`

Required columns:

```text
symbol,published_at,title,summary,source,url
```

`published_at` is mapped to `trade_date` by calendar date only. v1 does not adjust for pre-market, after-hours, holidays, or exchange calendars.

## Command

```bash
python student_local/build_news_sentiment_factor.py --input-csv student_local/news/raw_news_sample.csv --backend lexicon
```

This reads raw news rows, assigns one sentiment label per item, writes item-level sentiment rows, and aggregates them into daily news factors.

## Outputs

`student_local/outputs/news_sentiment_items.csv`

```text
symbol,published_at,trade_date,label,prob_negative,prob_neutral,prob_positive,sentiment_score,confidence,text_hash,source,url
```

`student_local/outputs/news_sentiment_daily.csv`

```text
symbol,date,news_count,positive_count,neutral_count,negative_count,sentiment_mean,sentiment_sum,sentiment_ewm_3,sentiment_ewm_5,negative_tail_ratio,confidence_mean
```

Current `hf` and `ollama` backends produce labels through the existing FinGPT/Ollama inference helpers. The probability columns are label-derived heuristic scores so the CSV schema stays stable before a calibrated probability backend is added.
