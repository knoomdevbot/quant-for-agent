# AR-090 evaluation: Google Trends consumer-attention ETF rotation

**Suggested decision:** `rejected`.

Real external signal data was available via pytrends/Google Trends and was evaluated with Alpaca/qfa daily OHLCV only. No CSV, no `--data-csv`, no daemon, no orders. Temporary SQLite DB was deleted (`db_artifact_retained=false`).

## External signal
- Provider: pytrends unofficial client for Google Trends explore/interest_over_time endpoint
- Endpoint: Google Trends `interest_over_time` through pytrends.
- Query terms: travel, restaurant, buy car, luxury, retail sales
- Fetch time: 2026-06-26T15:25:26Z
- Raw observed range: 2020-01-01 to 2025-12-01 (72 monthly rows).
- Retention: raw Trends values not retained; only compact derived monthly z-score features in `model.py`.
- Lag: month M feature usable starting month M+1.

## QFA/Alpaca results
- Symbols: XLY, XRT, JETS, PEJ, ITB, IYT, QQQ, SPY, IWM, XLP, XLU, SHY, GLD, XLE
- Primary: 2021-01-04 to 2025-12-15
- Primary pre-cost Sharpe: `-0.02279294`
- Primary total return: `-0.068467`
- Primary max drawdown: `-0.30383707`
- Random windows: 8
- Median random Sharpe: `-0.04776364`
- p25 random Sharpe: `-0.4833305`
- Worst random Sharpe: `-0.96684423`
- Positive-window rate: `0.5`

## Decision rationale
Rejected: primary Sharpe is negative, p25 random-window Sharpe is materially negative, and max drawdown is large before applying transaction costs. A 5-10 bps one-way cost/slippage assumption would only worsen the result.

## Artifacts
- `model.py`
- `config.yaml`
- `metadata.yaml`
- `README.md`
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/ar090_qfa_alpaca_pytrends_real_20260626T153000Z.json`
