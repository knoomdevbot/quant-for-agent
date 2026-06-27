# AR-025 evaluation: risk-off-crossasset-randomcost-v1

- Data: Alpaca real market data via qfa AlpacaGateway; no CSV; `--data-csv` not used.
- Primary window: 2021-01-04 to 2025-12-15, 1Day, symbols SPY, QQQ, IWM, TLT, GLD, XLU, XLE.
- qfa run IDs: primary `1`; random windows `1` through `1` in per-run temporary DBs.
- DB: temporary SQLite DB per run; `db_artifact_retained=false`.
- Costs: qfa native costs unavailable; ex-post 5 bps one-way turnover haircut estimated.

## Primary qfa metrics (pre-cost)

- Sharpe: -0.040519
- Total return: -7.72%
- Max drawdown: -32.34%
- Win rate: 47.34%
- Periods: 1242

## Cost haircut estimate

- Mean daily one-way turnover: 0.123684
- Estimated annual cost drag at 5 bps: 1.56%
- Approx cost-haircut Sharpe: -0.148414
- Approx cost-haircut annualized return: -3.18%

## Random-window validation

- Windows: 8
- Median Sharpe pre-cost: -0.262673
- Median total return pre-cost: -3.24%
- Positive-Sharpe windows: 3/8
- Worst max drawdown: -19.50%

## Orthogonality

Computed from retained qfa equity curves. Highest correlations: 0.75261559 to `risk-off-crossasset-switch-v1`; 0.63086396 to `tsmom-voltarget-liquid-etf-randomcost-v1`.

## Decision

- Suggested decision: `rejected`
- Rationale: primary qfa Sharpe, approximate cost-haircut Sharpe, and median random-window qfa Sharpe are non-positive.
- Bad-result policy: no refinement, direct inversion, or extension of this failed risk-off switch was created. Divergent child created: `alpha_research/issues/AR-044.md`.

## Immutable run

`/Users/moonk/quant-for-agent/models/risk-off-crossasset-randomcost-v1/evaluations/runs/ar025_qfa_alpaca_real_20260626T081003Z.json`
