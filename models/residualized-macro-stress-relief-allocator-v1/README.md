# AR-105 — residualized macro stress relief allocator

Durable qfa alpha artifact for `residualized-macro-stress-relief-allocator-v1`.

## Hypothesis

Stress and post-stress recovery are different flows.  This model separates:

- **Defensive-stress sleeve:** duration, quality credit, gold, defensive sectors, low-volatility equity, and cash proxy exposure when drawdown, volatility, credit, and breadth stress are elevated.
- **Relief-rebound sleeve:** beta-capped risk, credit, cyclicals, commodities, quality, and momentum exposure only after stress-abatement confirmation from breadth, credit, volatility, and SPY rebound features.

The combined portfolio is long-only, capped at gross 1.0, with a 0.25 estimated SPY beta cap implemented by replacing excess beta with SHY/IEF.  Sleeve budgets and single ETF weights are capped to reduce one-sleeve dominance.

## QFA contract

`model.py` exposes `generate_signals(context)` and returns target weights by symbol.  It uses only historical OHLCV bars provided in `context.prices` by qfa/Alpaca.

## Data and safety controls

- Real market data through qfa/Alpaca only.
- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false
- Credential provenance: configured paper-data access with values redacted.

## Evaluation notes

Evaluation artifacts are compact and intentionally omit raw daily bars, full equity curves, and weight tails.  The evaluator records primary and matched random/stress windows, 5/10/20 bps one-way turnover-cost proxies, sleeve attribution, SPY beta, correlations against retained AR-063/AR-072 streams where available, and broad proxy correlations.
