# residual-close-location-reversal-opportunity-balanced-v1

AR-068 research model: opportunity-balanced residual close-location reversal on mega-cap equities.

- Universe: AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY
- Data: Alpaca real daily OHLCV through qfa only; no CSV and no `--data-csv`.
- Contract: `model.py` exposes `generate_signals(context)`.
- Costs: qfa has no native costs; evaluation applies an ex-post 5 bps one-way turnover haircut.
- Safety: no daemon, no orders/trades, temporary SQLite DB only.

## Latest result

Decision: **rejected**. Primary 2024-2025 5 bps Sharpe: **-1.6332**; median random-window Sharpe: **-0.9621**; p25: **-1.8732**; worst: **-3.2054**; positive-window rate: **0.00**.

See `evaluations/latest.json` and `evaluations/latest.md`.
