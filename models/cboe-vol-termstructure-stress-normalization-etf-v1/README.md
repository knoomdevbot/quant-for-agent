# AR-145 — CBOE volatility term-structure stress/normalization ETF allocator

Status: **hold**.

## Feasibility result

CBOE source access was checked against the public daily-history endpoints for VIX, VIX3M, VIX9D, and VVIX. The endpoints returned CSV responses during this preflight, and no raw CBOE files were retained.

The end-to-end qfa/Alpaca performance evaluation was **not run** because this environment has no configured Alpaca credentials for real ETF daily bars. The qfa CLI therefore cannot retrieve Alpaca market data without falling back to a forbidden CSV-backed price path, which was not used.

## Timestamp discipline

The intended evaluator must join CBOE observations only after at least one full completed trading-session lag. The model wrapper expects pre-lagged features supplied in `context.metadata["cboe_vol_features"]`; it does not download, embed, or read raw CBOE histories.

## Required unblock condition

Configure approved Alpaca/qfa real ETF daily bar access, then rerun with:

- No `--data-csv` and no CSV-backed ETF prices.
- No qfa daemon and no orders.
- Fixed universe: SPY, QQQ, IWM, HYG, LQD, TLT, IEF, GLD, SHY.
- One-session-lagged public CBOE VIX, VIX3M, VIX9D, VVIX features.
- Primary 10 bps one-way turnover cost with 5/20 bps sensitivity.
- Controls versus simple VIX level, term-slope-only, no-VVIX, ETF TSMOM/reversal, shifted labels, and prior defensive/carry/stress families.

No children were spawned from this hold decision.
