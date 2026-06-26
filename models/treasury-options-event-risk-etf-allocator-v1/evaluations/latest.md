# AR-100 real-data evaluation

- Model: `treasury-options-event-risk-etf-allocator-v1`
- Data: Alpaca real OHLCV via qfa gateway; no CSV; no daemon; no orders.
- Universe: 27 selected ETFs from an ex-ante Treasury/event-risk candidate pool.
- Windows: 12 smoke/random/stress windows, 2020-2025 regimes.
- Cost proxy: 5/10/20 bps one-way daily turnover cost.
- Decision: **rejected**

## Key metrics

- Median Sharpe @10bps: -0.51698224
- Mean Sharpe @10bps: -0.54566344
- p25 Sharpe @10bps: -0.9265723
- Worst Sharpe @10bps: -1.71696814
- Positive-window rate @10bps: 0.08333333
- Worst max drawdown @10bps: -0.09130156
- Mean daily turnover: 0.11098161
- Mean activation rate: 0.32908224

## Rationale

- Random/stress-window distribution failed the AR-100 acceptance threshold after costs.
- No direct option-implied data was available, leaving a lagged realized-vol proxy.

## Artifact policy

- Compact summaries only; raw daily paths retained: false.
- Temporary SQLite DB and raw market data were not retained.
