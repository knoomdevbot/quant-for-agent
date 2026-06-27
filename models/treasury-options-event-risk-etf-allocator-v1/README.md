# treasury-options-event-risk-etf-allocator-v1

## Hypothesis

AR-100 tests whether Treasury/options-implied event risk can be approximated with tradable ETF market data and used to allocate across cash-like Treasury bills, duration, credit, gold/commodities, broad equities, sectors, and a volatility ETF proxy around macro-event-heavy windows.

Because qfa does not currently expose a reproducible option-implied-volatility feed, this version uses only real OHLCV bars and proxies event-risk repricing with realized range shocks, volume shocks, credit/duration/equity stress, and an ex-ante macro calendar gate.

## Candidate Pool and Selected Universe

Broad ex-ante pool: liquid event-sensitive ETFs across the Treasury curve, cash-like collateral, aggregate/credit/EM bonds, gold/silver/commodities/oil, broad equity indexes, defensive/cyclical sectors, and volatility proxies.

Selected universe: 27 ETFs: `BIL`, `SHV`, `SHY`, `IEI`, `IEF`, `TLH`, `TLT`, `AGG`, `LQD`, `HYG`, `EMB`, `GLD`, `SLV`, `DBC`, `USO`, `SPY`, `QQQ`, `IWM`, `DIA`, `XLU`, `XLP`, `XLV`, `XLE`, `XLF`, `XLK`, `XLI`, `VIXY`.

Selection filters: qfa real-data availability, liquidity, economic exposure to rate/event risk, history through Fed/inflation regimes, and no ex-post return selection.

## Signal Definition

The qfa `generate_signals(context)` model:

- Computes range and volume z-score shocks in rate, credit, equity, and gold sleeves.
- Applies an ex-ante event calendar gate for payroll/inflation/FOMC-heavy calendar zones.
- Raises cash/duration/defensive/gold allocations when event-risk and risk-off proxies are elevated.
- Allocates residual budget to credit and equity sleeves when risk-off proxies are lower.
- Enforces long-only gross exposure near 1.0 and caps single ETF weights at 35% before qfa normalization.

## Evaluation Summary

Real-data evaluation completed with qfa/Alpaca daily OHLCV, a qfa backtest-engine pass saved to a temporary SQLite DB, and a compact turnover-cost overlay. No CSV, no daemon, and no orders were used.

Key 10 bps cost-overlay results across 12 smoke/random/stress windows:

- Median Sharpe: -0.51698224
- Mean Sharpe: -0.54566344
- p25 Sharpe: -0.9265723
- Worst Sharpe: -1.71696814
- Positive-window rate: 0.08333333
- Worst max drawdown: -0.09130156
- Mean daily turnover: 0.11098161
- Mean activation rate: 0.32908224

Decision: **rejected**. The random/stress-window distribution failed the AR-100 acceptance threshold after costs, and the lack of direct option-implied data weakens the original mechanism.

## Orthogonality / Redundancy

No retained daily return streams were available in compact prior artifacts for numeric correlation/cointegration. Qualitatively, redundancy is moderate because the allocator overlaps defensive duration/gold/cash and ETF momentum behavior, even though the event-risk gate is differentiated.

## Known Risks

- Realized-volatility proxies can lag true option-implied event-risk repricing.
- The calendar gate is approximate, not an exact point-in-time release calendar.
- Cost sensitivity is material; 20 bps median Sharpe was much worse than 5 bps.
- Current ETF universe may have survivorship bias because delisted products were not included.

## Artifacts

- Config: `config.yaml`
- Metadata: `metadata.yaml`
- Latest evaluation JSON: `evaluations/latest.json`
- Latest evaluation Markdown: `evaluations/latest.md`
- Immutable run JSON: `evaluations/runs/ar100-realdata-20260626T170337Z.json`

Raw daily paths, raw market data, per-day weights, and temporary DB files are intentionally not retained.
