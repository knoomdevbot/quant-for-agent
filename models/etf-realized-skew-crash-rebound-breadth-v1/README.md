# AR-071: ETF realized-skew crash-rebound breadth allocator

This qfa model researches a divergent child of AR-062 using realized downside skew, cross-ETF crash-day breadth, rebound breadth, volatility shock, and short-horizon reversal scores across liquid ETFs.

## Contract

- Entrypoint: `generate_signals(context)` in `model.py`
- Data: Alpaca/qfa real market data only
- CSV: not used; no `--data-csv`
- Daemon/trading: no daemon, no orders/trades
- Temporary DB only: `/tmp/qfa-ar-071.sqlite3`, removed after evaluation
- Durable artifacts: this model folder only

## Files

- `model.py` — qfa-compatible alpha model
- `config.yaml` — parameters and evaluation assumptions
- `metadata.yaml` — issue/model metadata and artifact policy
- `evaluate_ar071.py` — reproducible real-data evaluation harness
- `evaluations/latest.json` — compact machine-readable evaluation artifact
- `evaluations/latest.md` — human-readable evaluation summary
- `evaluations/runs/*.json` — immutable compact run artifact

## Model summary

The model stays in SHY outside stress/rebound regimes. After a recent broad crash-breadth event, it ranks risk ETFs by capitulation/reversal features: downside skew proxy, recent drawdown/negative return, rebound breadth, and volatility shock. It caps single ETF weights and keeps gross exposure at or below 1.0.

## Evaluation summary

See `evaluations/latest.md` and `evaluations/latest.json` for real Alpaca/qfa metrics, random-window robustness, external 5/10 bps one-way turnover costs, qfa temporary run IDs, and orthogonality checks.
