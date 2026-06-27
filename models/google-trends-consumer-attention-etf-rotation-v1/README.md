# AR-090 Google Trends consumer-attention ETF rotation

Research-only qfa alpha using real Google Trends data from `pytrends` and real Alpaca/qfa daily OHLCV. The model embeds compact monthly derived attention z-scores for predeclared US query terms (`travel`, `restaurant`, `buy car`, `luxury`, `retail sales`) and applies a one-month lag before the feature is tradable. Raw Google Trends values are not retained.

The allocator tilts long-only toward discretionary/retail/travel/risk ETFs when lagged consumer attention is positive and qfa price momentum confirms. It falls back to XLP/XLU/SHY/GLD when attention is weak or unavailable.

No CSV data, no `--data-csv`, no daemon, and no orders/trades are used. See `evaluations/latest.json` and `evaluations/latest.md` for results.
