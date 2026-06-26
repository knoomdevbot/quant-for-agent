# AR-022 evaluation: ETF flow risk breadth regime v1

## Decision
- Suggested decision: **reject_do_not_extend_failed_hypothesis**
- Rationale: main-window Sharpe -0.0242, total return -5.40%; random-window median Sharpe -0.1867 with 3/7 positive windows. This triggers the non-positive random-period median Sharpe falsifier.

## Data and command
- Data source: Alpaca real market data via qfa AlpacaGateway; no CSV; `--data-csv` not used.
- Symbols: SPY, QQQ, IWM, XLF, XLY, XLI, SMH, HYG, TLT, IEF, GLD, XLU, XLP, XLV, LQD, SHY
- Main window: 2021-01-01 to 2025-12-31 (1Day)
- Temporary DB: `/tmp/qfa-ar022-primary-<pid>.sqlite3` and `/tmp/qfa-ar022-random-<pid>.sqlite3`; DB artifact retained: false.
- qfa run ids: primary `1`; random `[1, 2, 3, 4, 5, 6, 7]`.

## Main metrics
- Sharpe: -0.0242
- Total return: -5.40%
- Annualized return: -1.11%
- Annualized volatility: 12.71%
- Max drawdown: -35.11%
- Win rate: 47.01%
- Periods: 1253

## Random-window summary
- Windows: 7
- Median Sharpe: -0.1867
- Min / max Sharpe: -2.5515 / 0.4667
- Positive Sharpe windows: 3/7
- Worst max drawdown: -24.15%

## Costs/slippage
qfa has no native transaction-cost/slippage/turnover modeling in this repository version. Reported metrics are pre-cost; realistic ETF trading costs would further reduce the already negative gross performance.

## Orthogonality
```json
{
  "attempted": true,
  "comparison": "AR-006 turn-month-liquid-etf-seasonality-v1",
  "method": "Pearson correlation of daily equity-curve returns over overlapping qfa run timestamps versus retained AR-006 run JSON.",
  "correlation": 0.27767407,
  "overlap_periods": 499,
  "parent_run_json_path": "models/turn-month-liquid-etf-seasonality-v1/evaluations/runs/qfa_real_alpaca_20260626T062022Z.json",
  "interpretation": "Correlation is only a diagnostic; AR-022 is rejected on standalone and random-window performance regardless of parent overlap."
}
```

## Bad-result policy
Because the alpha is rejected, no refinement, direct inversion, or extension child is proposed.
