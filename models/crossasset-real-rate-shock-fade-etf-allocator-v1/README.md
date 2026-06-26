# crossasset-real-rate-shock-fade-etf-allocator-v1 (AR-109)

Research-only qfa-compatible ETF allocator for AR-109.  The model tests whether abrupt multi-day dislocations among duration (`TLT`/`IEF`/`SHY`), TIPS (`TIP`), gold/USD (`GLD`/`UUP`), credit (`LQD`/`HYG`), equity (`SPY`), and defensive utilities (`XLU`) fade after short stabilization.

## Fixed universe

Candidate and selected universe were fixed before performance review from the issue-specified pool: `TLT`, `IEF`, `SHY`, `TIP`, `GLD`, `UUP`, `LQD`, `HYG`, `SPY`, `XLU`.  These are broad Alpaca-covered ETFs with price-derived economic exposure to the required sleeves.  No return-ranked product selection was used.

## Signal summary

- Look for 5-day duration/TIPS/gold/USD relative shocks.
- Require a 1-2 bar stabilization check using close-location, short reversal, and volume-z controls.
- Allocate long-only, gross <= 1.0, across duration (`TLT`, `IEF`), inflation/gold (`TIP`, `GLD`), defensive (`XLU`, `LQD`), and residual `SHY`.
- Do not submit orders; `generate_signals(context)` only returns target weights.

## Evaluation controls

Evaluation artifacts use qfa/Alpaca real daily market data only.  No CSV input, no `--data-csv`, no qfa daemon, no orders, and no retained raw bars/SQLite/helper-script artifacts.  Primary cost gate is 10 bps one-way turnover with 5/20 bps sensitivity.
