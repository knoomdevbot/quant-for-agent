# AR-037 evaluation: ETF carry defensive allocation v1

- Created UTC: 2026-06-26T08:35:45Z
- Data source: Alpaca real market data via qfa AlpacaGateway; no CSV; `--data-csv` not used.
- Symbols: SPY, QQQ, IWM, TLT, IEF, GLD, USO, FXE, FXY, UUP
- Primary window: 2022-01-03 to 2025-12-15 (`1Day`)
- qfa run ids: primary `1`, random `[1, 1, 1, 1, 1, 1, 1, 1]`
- Temporary DBs: `/tmp/ar037_primary_*.sqlite3` and `/tmp/ar037_win*_*.sqlite3`; deleted after JSON capture (`db_artifact_retained=false`).

## Primary qfa metrics, pre-cost

- Sharpe: `1.0840131`
- Total return: `0.36382821`
- Max drawdown: `-0.07786466`
- Win rate: `0.47474747`
- Periods: `990`
- Final equity: `136382.821`

## Random windows

- Count: `8`
- Median Sharpe: `0.60892376`
- Positive Sharpe fraction: `0.625`
- Worst max drawdown: `-0.07786466`

## Costs/slippage

qfa has no native transaction-cost/slippage argument. Metrics above are pre-cost. A 5 bps one-way turnover proxy estimates mean daily turnover `0.02870383` and annualized cost drag `0.00361668`.

## Orthogonality

{
  "status": "computed",
  "computed": true,
  "method": "Pearson correlation of daily qfa equity returns from retained run artifacts when available",
  "correlations": [
    {
      "path": "/Users/moonk/quant-for-agent/models/tsmom-voltarget-liquid-etf-randomcost-v1/evaluations/runs/qfa_real_alpaca_ar015_20260626T072547Z.json",
      "overlap_periods": 489,
      "correlation": 0.73826394,
      "model_name": "AR-015 tsmom-voltarget-liquid-etf-randomcost-v1"
    }
  ]
}

## Decision

- Suggested decision: **watchlist_not_accepted**
- Rationale: Watchlist / not accepted: primary and random-window median Sharpe are positive pre-cost, but measured correlation to parent AR-015 retained qfa returns is high (0.7383), so orthogonality is not yet proven.
