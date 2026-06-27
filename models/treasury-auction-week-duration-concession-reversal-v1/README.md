# Treasury auction-week duration concession reversal ETF allocator (AR-108)

Research-only qfa-compatible alpha model. The allocator tests whether scheduled Treasury auction and quarterly refunding supply windows create temporary duration ETF concessions that reverse after stabilization confirmation.

## Universe

Fixed before performance review from the issue-specific ETF pool:

- Duration / curve: `TLT`, `IEF`, `SHY`, `TIP`
- Credit: `LQD`, `HYG`
- Defensive / regime proxies: `SPY`, `GLD`, `UUP`

Selection was based on clean Alpaca daily coverage and economic exposure, not realized returns.

## Signal

The model gates exposure to deterministic coupon-supply windows: second-week and last-week monthly auction/reopening approximations plus expanded Feb/May/Aug/Nov quarterly refunding windows. If `TLT`/`IEF` underperform `SHY` over five sessions and the latest `TLT` bar shows close-location/return/volume stabilization, it allocates long duration (`TLT`/`IEF`/`TIP`) with gross exposure capped at 1.0. Risk-off skips use recent `SPY` and `HYG` losses.

## Evaluation

Evaluation uses real qfa/Alpaca daily bars only. No CSV, no `--data-csv`, no qfa daemon, and no orders/trades. The latest compact evaluation is in `evaluations/latest.json` and `evaluations/latest.md`; immutable compact run JSONs are under `evaluations/runs/`.

## Known limitations

The auction/refunding calendar is a reproducible approximation rather than a stored official Treasury auction calendar. Daily bars do not observe auction microstructure, and prior alpha compact artifacts often do not retain daily return streams for direct watchlist correlations.
