# AR-078 evaluation: intraday Treasury announcement reversion

**Decision:** rejected  
**Data:** Alpaca real 1-minute OHLCV via qfa/AlpacaGateway; no CSV; no `--data-csv`.  
**Safety:** no daemon, no orders, temporary SQLite only, no DB retained.  
**Raw artifacts:** compact summaries only; `raw_daily_paths_retained:false`.

## Evaluation setup

- Symbols: SHY, IEF, TLT, TIP, LQD, HYG, GLD, SPY.
- Events: 59 explicit FOMC/CPI timestamps, 2023-01-12 through 2025-12-10.
- Timestamp policy: FOMC 14:00 America/New_York; CPI 08:30 America/New_York; converted to UTC.
- Signal: 60-minute post-announcement duration shock, 60-minute hold.
- Costs: 5, 10, and 20 bps one-way proxy; primary is 10 bps. Net event return subtracts `2 * one_way_bps * gross`.
- qfa probe: 1Min Alpaca run succeeded on a temporary DB, but qfa CLI has no event-calendar/metadata argument; model returns zero weights without metadata.

## Primary metrics

| Cost proxy | Events | Active events | Sharpe | Mean event return | Sum event return | Win rate | Max drawdown |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 bps | 59 | 50 | -2.2528 | -0.000897 | -0.052925 | 20.34% | -5.09% |
| 10 bps | 59 | 50 | -3.8119 | -0.001600 | -0.094389 | 8.47% | -8.78% |
| 20 bps | 59 | 50 | -6.1276 | -0.003005 | -0.177317 | 5.08% | -15.91% |

## 10 bps breakdown

| Slice | N | Sharpe | Mean | Win rate |
|---|---:|---:|---:|---:|
| FOMC | 24 | -3.0462 | -0.001306 | 16.67% |
| CPI | 35 | -4.3453 | -0.001801 | 2.86% |
| 2023 | 20 | -3.0791 | -0.001692 | 15.00% |
| 2024 | 20 | -4.5695 | -0.001766 | 5.00% |
| 2025 | 19 | -4.5195 | -0.001328 | 5.26% |

## Random-window falsifier

20 deterministic random pseudo-event schedules used the same local FOMC/CPI times on non-event Alpaca trading dates.

- Median random-event Sharpe at 10 bps: **-4.0834**
- p25: -4.6487
- Worst: -5.2263
- Positive random schedules: 0%

This satisfies the falsifier `median random-event Sharpe <= 0 after costs`. The real event schedule is also negative.

## Orthogonality

Mechanism and horizon are distinct from AR-070 daily event-gated curve-shock logic. However, native qfa event metadata is unsupported and custom intraday event returns are negative, so orthogonality does not justify keeping the model.

## Suggested decision and child

**Reject.** Do not refine, directly invert, or extend this reversal rule. At most consider one genuinely divergent child: Treasury ETF announcement liquidity continuation using volume/depth confirmation rather than price reversal.
