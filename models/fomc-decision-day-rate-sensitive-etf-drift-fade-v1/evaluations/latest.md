# AR-130 FOMC decision-day rate-sensitive ETF drift/fade event study

Suggested decision: **REJECT**.

## Protocol
- Data: qfa/Alpaca real daily OHLCV via configured paper-data access.
- No CSV, no `--data-csv`, no daemon, no orders; raw daily bars not retained.
- Selected universe fixed before performance review: TLT, IEF, SHY, LQD, HYG, GLD, SPY, QQQ, XLF, XLRE. Optional TIP/UUP/XLU excluded despite clean coverage/liquidity to avoid post-hoc broadening.
- Primary predeclared leg: prior close to scheduled FOMC decision-day close, equal-weight basket, 10 bps one-way cost (20 bps round-trip).

## Primary metrics, 10 bps one-way
- Events: 83 from 2016-01-27 through 2026-06-17; activation 3.15%.
- Median net event return: -0.1601%; mean -0.1047%; p25 -0.4989%; worst -2.3795%.
- Hit rate: 42.17%; positive-year rate by yearly sum: 27.27%; max event-equity drawdown: -8.91%.
- Cost sensitivity medians: 5 bps -0.0601%; 10 bps -0.1601%; 20 bps -0.3601%.

## Placebos / controls
- Same-month/same-weekday placebo median: -0.1536%.
- Random matched non-FOMC median percentile: 0.300; mean percentile: 0.712.
- Ex any calendar-overlap median: -0.1892%; event count 22.
- Max absolute proxy correlation: 1.000. Orthogonality to accepted library unavailable due event-study stream mismatch.

## Gate outcome
{
  "median_event_return_gt_0": false,
  "hit_rate_ge_55pct": false,
  "placebo_rank_ge_0_85": false,
  "p25_not_materially_negative": false,
  "positive_year_rate_not_one_regime_dependent": false,
  "ex_calendar_overlap_positive_median": false,
  "no_high_redundancy": false
}

The alpha is rejected because the predeclared primary leg fails one or more acceptance gates. Diagnostic post-decision legs are reported in JSON only and were not used to rescue the result.
