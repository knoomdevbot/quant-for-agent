# AR-016 evaluation: xsec-etf-defensive-rotation-v1

Created UTC: 2026-06-26T07:20:36Z

## Data and command

- Data source: Alpaca real market data via qfa AlpacaGateway; no CSV and no `--data-csv`.
- Symbols: SPY, QQQ, IWM, XLV, XLY, XLE, XLU, XLP, TLT, IEF, GLD
- Main range: 2023-01-01 to 2025-12-31 (1Day)
- qfa run id: 1
- DB used: `/tmp/qfa-ar016-<pid>.sqlite3` and `/tmp/qfa-ar016-random.sqlite3`; DB artifact retained: false.
- No daemon; no trades.

## Main metrics

- Sharpe: 0.98273672
- Total return: 0.37611705
- Annualized return: 0.11323847
- Annualized volatility: 0.11602649
- Max drawdown: -0.10455149
- Win rate: 0.45733333
- Periods: 750

## Random-window protocol

- Windows: 6
- Median Sharpe: 0.73896
- p25 Sharpe: 0.34084797
- Min/Max Sharpe: 0.20026631 / 1.85552058
- Median total return: 0.07706541
- Worst max drawdown: -0.10455149
- Positive Sharpe windows: 6 / 6 (rate 1.0)

## Turnover and costs/slippage

qfa in this repository has no native transaction-cost/slippage/trade storage. I reconstructed ex-post target-weight turnover by replaying `generate_signals` on Alpaca bars: mean daily one-way turnover 0.08849406, median daily one-way turnover 0.01302022, annualized one-way turnover 22.3005, max daily one-way turnover 1.0. Reported qfa performance metrics are pre-cost; requested assumption is 5 bps and should be implemented as a turnover haircut in the refinement pass.

## Orthogonality

moderate positive overlap with AR-003; mechanism is cross-sectional basket rotation rather than single-asset TSMOM, but return stream is not fully orthogonal.

- Attempted: True
- Parent: AR-003 tsmom-voltarget-liquid-etf-weekly-v1
- Overlap periods: 499
- Correlation: 0.62049013

## Suggested decision

watchlist_continue_research_not_accept_until_costed_turnover_validation

Rationale: Main-window Sharpe is positive (0.9827) and random-window median Sharpe is positive (0.7390), so the AR-016 falsifier is not triggered; however, edge is moderate, costs are not modeled, and parent return correlation is not negligible.

## Child ideas

- Refinement: AR-016-R1: cost-aware/monthly-rebalanced cross-sectional ETF defensive rotation; validate 5-10 bps turnover haircuts and parameter stability for lookbacks/top_n before acceptance.
- Divergent: AR-016-D1: yield-curve/credit-stress ETF allocation using bond duration, gold, and sector-defensive spreads rather than price relative-strength ranks.

Immutable run JSON: `evaluations/runs/qfa_real_alpaca_ar016_20260626T072036Z.json`
