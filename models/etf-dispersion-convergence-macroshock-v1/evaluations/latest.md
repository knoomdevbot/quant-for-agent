# AR-032 evaluation latest

- Status: completed real-data qfa/Alpaca backtest
- Suggested decision: rejected
- Reason: Fails acceptance: primary or median random-window Sharpe is not positive after 5 bps one-way turnover costs.
- Data source: Alpaca real daily market data via qfa; no CSV and no `--data-csv`
- Symbols: SPY, QQQ, IWM, TLT, GLD, SLV, XLF, XLK, XLE, XLV
- Primary range: 2024-01-01 to 2025-12-31
- qfa DB: /tmp/qfa_ar032.sqlite3 (db_artifact_retained=false)
- qfa run ids: primary 1; random windows [2, 3, 4, 5, 6, 7, 8, 9]

## Primary metrics

- qfa/pre-cost Sharpe: 0.54337974
- qfa/pre-cost total return: 0.02409252
- qfa/pre-cost max drawdown: -0.02072956
- qfa/pre-cost win rate: 0.032
- qfa/pre-cost periods: 500
- external 5 bps cost Sharpe: -0.06454124
- external 5 bps cost total return: -0.00338541
- external 5 bps cost max drawdown: -0.03048611
- external 5 bps cost win rate: 0.032
- external 5 bps cost periods: 500

## Random-window summary, 8 one-year windows

- Median pre-cost Sharpe: -0.58542174
- Median cost-adjusted Sharpe: -0.94532961
- Mean cost-adjusted Sharpe: -0.75344628
- Min/Max cost-adjusted Sharpe: -2.03342102 / 0.58286993
- Median active-day fraction: 0.03392829

## Costs/slippage and orthogonality

- Costs: qfa has no native cost parameter; applied external 5 bps one-way target-weight turnover haircut.
- Orthogonality: unavailable — No canonical accepted-alpha return stream with overlapping timestamped returns found in retained latest artifacts.

Immutable run JSON: `/Users/moonk/quant-for-agent/models/etf-dispersion-convergence-macroshock-v1/evaluations/runs/qfa_real_alpaca_ar032_20260626T082206Z.json`
