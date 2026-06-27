# AR-076 — megacap-vol-contraction-breakout-continuation-v1

Research-only qfa alpha for mega-cap equities. The model follows completed-bar breakouts after realized range contraction when volume and residual strength confirm the move.

- Universe: AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY.
- Data/evaluation: Alpaca/qfa real daily OHLCV only; no CSV and no `--data-csv`.
- Safety: no daemon, no trades, no orders; temporary SQLite DB only during evaluation.
- Cost proxy: ex-post 5 bps one-way target-weight turnover haircut.

The signal is divergent from AR-068: it seeks short-horizon continuation after idiosyncratic volatility-contraction breakouts, not close-location reversal.

Evaluation artifacts are in `evaluations/latest.json`, `evaluations/latest.md`, and `evaluations/runs/`.
