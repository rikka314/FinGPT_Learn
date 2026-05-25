# Forecaster Reading Notes

Do not start here for execution. Read this after you have run the sentiment workflow once.

## What FinGPT Forecaster Does

The Forecaster takes:
- company profile
- recent price movement
- recent news
- optional basic financials

It turns them into one long prompt and asks the model to generate:
- positive developments
- potential concerns
- a next-week movement prediction
- a short explanation

## The Three Files Worth Reading First

- `fingpt/FinGPT_Forecaster/prompt.py`
- `fingpt/FinGPT_Forecaster/data_infererence_fetch.py`
- `fingpt/FinGPT_Forecaster/app.py`

## Mental Model

`prompt.py`
- Defines the text template.
- This is where raw finance data becomes a language-model task.

`data_infererence_fetch.py`
- Pulls prices, news, and basics from external sources.
- This is the data plumbing layer.

`app.py`
- Wires user input, data fetch, prompt building, model call, and output display together.
- This is the end-to-end application layer.

## Why It Feels Harder Than Sentiment

- Inputs come from multiple sources, not one text column.
- The prompt is much longer.
- The output is partly structured and partly free-form.
- It depends on APIs and market data freshness, not only local datasets.
