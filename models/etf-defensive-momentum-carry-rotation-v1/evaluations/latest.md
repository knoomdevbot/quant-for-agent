# AR-059 Evaluation — ETF defensive momentum carry rotation

## Suggested decision

**rejected** — Rejected: retained-curve orthogonality check failed due to high correlation with ETF carry/defensive allocation watchlist stream (corr 0.7545773 vs AR-037), triggering AR-059 falsifier despite positive median random-window Sharpe.

## Key metrics

- Primary 2024-2025 qfa/pre-cost Sharpe: `0.85049833`
- Primary 2024-2025 5 bps cost-adjusted Sharpe: `0.81565891`
- Primary 5 bps cost-adjusted total return: `0.16055086`
- Primary max drawdown after cost: `-0.10615933`
- Random/stress windows: `12`; median Sharpe after cost `0.65170638`, p25 `-0.4840311`, worst `-1.00691431`
- Positive-window rate after cost: `0.66666667`
- Mean daily one-way turnover proxy, primary: `0.02704661`
- Orthogonality status: `high_correlation_failed`

## Execution notes

Alpaca/qfa real daily bars only. No CSV, no `--data-csv`, no daemon, no orders. Temporary SQLite DB path pattern `/tmp/qfa-AR-059-*.sqlite3`; DB artifact not retained.

Artifacts: `/Users/moonk/quant-for-agent/models/etf-defensive-momentum-carry-rotation-v1/evaluations/runs/ar059_qfa_alpaca_real_20260626T112909Z.json`, `/Users/moonk/quant-for-agent/models/etf-defensive-momentum-carry-rotation-v1/evaluations/latest.json`.
