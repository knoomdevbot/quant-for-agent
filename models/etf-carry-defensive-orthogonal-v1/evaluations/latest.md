# AR-049 Evaluation — etf-carry-defensive-orthogonal-v1

Created: `2026-06-26T10:28:42.443210+00:00`

## Protocol

- qfa-compatible model: `models/etf-carry-defensive-orthogonal-v1/model.py`
- Data: Alpaca real market data through qfa `AlpacaGateway`; `--data-csv` was not used.
- No daemon, no live trades.
- Symbols: `SPY,QQQ,IWM,TLT,IEF,GLD,USO,FXE,FXY,UUP`; timeframe: `1Day`.
- Runs: one smoke, one primary, and `8` random/rolling real-data qfa windows. Each qfa run used a temporary SQLite DB removed after JSON capture; qfa run id is `1` in each temporary DB.
- Costs: qfa CLI has no native cost/slippage argument. Evaluation therefore reports qfa pre-cost metrics and an ex-post 5 bps one-way turnover haircut from generated target-weight changes.

## Primary qfa pre-cost metrics

- Window: `2022-01-03` to `2025-12-15`
- Sharpe: `0.51915481`
- Total return: `0.12077708`
- Annualized return / vol: `0.02944915` / `0.05929362`
- Max drawdown: `-0.0743553`
- Win rate: `0.45252525`
- Periods: `990`

## Cost / turnover proxy

- Average daily one-way turnover: `0.04744627`
- Median daily one-way turnover: `0.02807896`
- Annualized turnover proxy: `11.95646129`
- Estimated annual drag at 5 bps: `0.00597823`
- Primary 5 bps cost-adjusted Sharpe: `0.41835312`
- Primary 5 bps cost-adjusted max drawdown: `-0.079501`

## Random-window 5 bps cost-adjusted validation

- Median Sharpe: `0.33637069`
- p25 Sharpe: `0.06529506`
- Worst Sharpe: `-0.40745962`
- Positive window rate: `0.75`
- Worst max drawdown: `-0.079501`

## Orthogonality checks

Method: `Pearson correlation of daily qfa equity-curve returns versus retained latest.json artifacts with sufficient overlap.`

- `etf-carry-defensive-allocation-v1`: correlation `0.63994784` over `990` overlapping periods (`/Users/moonk/quant-for-agent/models/etf-carry-defensive-allocation-v1/evaluations/latest.json`).
- `tsmom-voltarget-liquid-etf-randomcost-v1`: correlation `0.50633334` over `489` overlapping periods (`/Users/moonk/quant-for-agent/models/tsmom-voltarget-liquid-etf-randomcost-v1/evaluations/latest.json`).
- `turn-month-vol-gated-etf-v1`: correlation `0.44666218` over `990` overlapping periods (`/Users/moonk/quant-for-agent/models/turn-month-vol-gated-etf-v1/evaluations/latest.json`).

## Decision

Suggested decision: **`watchlist_not_accepted`**.

Rationale: Watchlist/not accepted: random-window 5 bps costed Sharpe is positive and drawdown controlled, and correlation to AR-015 is reduced, but performance is modest/regime fragile and qfa costs are ex-post rather than native.

## Warnings / failure modes

- Correlation to parent AR-037 remains moderate (`0.63994784`), so this is a refinement but not fully independent.
- AR-015 correlation improved from AR-037's retained `0.73826394` to `0.50633334`, but redundancy is not eliminated.
- Worst random-window costed Sharpe is negative (`-0.40745962`); performance is regime-fragile.
- qfa costs/slippage are ex-post, not native execution simulation.

## Bad-result pruning / children

Non-rejected but not accepted. If pursued, use at most one child that changes data driver (e.g., explicit macro yield/curve-carry data if qfa supports it). Avoid direct OHLCV-only parameter refinements unless the controller specifically wants more orthogonality work.
