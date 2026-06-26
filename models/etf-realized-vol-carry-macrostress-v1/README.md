# AR-066 — ETF realized-volatility carry macro-stress rotation

Durable qfa alpha artifact for `etf-realized-vol-carry-macrostress-v1`.

## Model

`model.py` exposes `generate_signals(context)` and returns long-only target weights for:

`SPY, QQQ, IWM, TLT, GLD, XLU, XLE, SHY`

The signal uses only qfa/Alpaca OHLCV bars:

- 20/60 day realized downside volatility
- 20/60 day return-per-downside-volatility carry
- cross-ETF stress breadth
- drawdown recovery state
- defensive carry proxy from SHY/TLT/GLD behavior
- weekly rebalance anchor and 35% max single ETF cap

It deliberately avoids macro-calendar terms and AR-053's rejected next-day laggard-reversal proxy.

## Evaluation summary

- Data: Alpaca real daily OHLCV through qfa/AlpacaGateway; no CSV and no `--data-csv`.
- Safety: no daemon, no live orders/trades, temporary SQLite only.
- Primary period: 2021-01-04 to 2025-12-15.
- Random protocol: 10 random windows, 378 trading days each.
- Costs: ex-post 5 bps and 10 bps one-way turnover-cost proxy.

Decision: **REJECT**. The random-window median Sharpe was positive, but p25 Sharpe was materially negative and correlations to retained ETF stress/recovery models were too high.

Key latest metrics are in `evaluations/latest.md` and full curves/details are in `evaluations/latest.json` plus immutable run JSON under `evaluations/runs/`.

## Artifacts

- `model.py`
- `config.yaml`
- `metadata.yaml`
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/ar066_qfa_alpaca_real_20260626T121321Z.json`
