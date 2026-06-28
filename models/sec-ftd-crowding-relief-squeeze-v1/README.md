# SEC FTD crowding relief/squeeze allocator (AR-138)

**Decision:** rejected.

This model folder records a compact real-data evaluation of a timestamp-lagged SEC fails-to-deliver event signal. The candidate used official SEC FTD archives and configured Alpaca/qfa real daily OHLCV. No CSV market data, daemon, or orders were used.

## Result

- Selected universe: 97 symbols from a 178-symbol liquid broad universe; this missed the issue's minimum 100-symbol gate.
- Selected events: 508 over 2019-05-06 to 2026-01-30.
- Primary full-sample Sharpe: 0.509 after 10 bps one-way costs.
- Random-window median Sharpe: -0.016.
- Random-window p25 Sharpe: -0.856.
- Worst random-window Sharpe: -1.247.
- Positive random-window rate: 46%.
- Max drawdown: -47.6%.
- Turnover: 0.207.

The full-sample result did not survive random-window robustness and did not beat simple controls robustly. No direct FTD refinement child should be spawned from this rejected result.
