# broad-etf-tsmom-correlation-cluster-riskbudget-v1

AR-104 recovery artifact for a broad ETF time-series momentum allocator with rolling-correlation cluster risk budgets.

## Model

- Contract: qfa-compatible `generate_signals(context) -> dict[str, float]`.
- Inputs: historical OHLCV bars supplied by qfa real-data context.
- Universe: 28 liquid ETFs across broad equity, sectors, rates/duration, TIPS, credit, commodities, precious metals, and currency/defensive proxies.
- Signal: positive multi-week TSMOM using 63/126/189 day lookbacks, inverse-vol scaling, rolling-correlation cluster labels, macro cluster caps, and a modest SPY drawdown taper.
- Trading: research-only signals; no daemon and no orders.

## Real-data controls

- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false

Evaluation used Alpaca real market data through qfa. Credentials were used only ephemerally for data access and were not printed or stored. Compact artifacts intentionally do not retain raw bars, equity curves, or daily weight paths.

## Evaluation summary

Bounded recovery used a compact real-data protocol: one primary window plus six deterministic pseudo-random windows. Costs are external one-way turnover haircuts at 5/10/20 bps because the local qfa backtester has no native transaction-cost model.

Primary window: 2022-01-03 to 2025-12-31.

Primary metrics:

- Pre-cost qfa Sharpe: 0.3151; max drawdown: -0.1004.
- 5 bps Sharpe: 0.1326; max drawdown: -0.1152.
- 10 bps Sharpe: -0.0500; max drawdown: -0.1464.
- 20 bps Sharpe: -0.4147; max drawdown: -0.2291.
- Primary annualized one-way turnover proxy: 36.2495x.
- Primary mean max macro-cluster gross: 0.4852; p95: 0.7213.

Random-window metrics at 10 bps:

- Median Sharpe: -0.17854859
- p25 Sharpe: -0.5751906
- Worst Sharpe: -2.48863265
- Positive-window rate: 0.5
- Worst max drawdown including primary: -0.14644236
- Median annualized one-way turnover: 36.61366227x

Orthogonality checks from available retained equity curves:

- AR-015 correlation: 0.65292187 over 499 overlapping periods.
- AR-036: unavailable because no retained usable equity curve was found.
- AR-062 correlation: 0.74805495 over 749 overlapping periods.
- Max available absolute correlation: 0.74805495.

## Decision

Suggested decision: **rejected**.

Rationale: 10 bps costed Sharpe was negative in the primary window, random-window median/p25/worst Sharpe failed the robustness gate, turnover was high, macro-cluster concentration remained elevated, and available retained-stream correlation exceeded the 0.60 target.

No direct refinement or extension child was created for this rejected hypothesis.
