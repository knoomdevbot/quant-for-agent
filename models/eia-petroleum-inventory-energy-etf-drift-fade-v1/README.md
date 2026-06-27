# AR-131 EIA petroleum inventory energy ETF drift/fade evaluation

Decision: **REJECT**.

Used Alpaca/qfa real daily OHLCV; no CSV, no `--data-csv`, no daemon, no orders. Calendar is a deterministic public approximation (normal Wednesday EIA Petroleum Status Report; Thursday shift around Mon/Tue/Wed US federal holidays), with no inventory-surprise data.

## Fixed primary universe
XLE, VDE, IYE, XOP, OIH, USO, BNO, DBC

Excluded: DBA (weak petroleum exposure); SPY/QQQ/GLD/TLT controls only; any failed coverage/liquidity symbols excluded before return review.

## Primary 10 bps one-way results
- Events: 530
- Median net event return: -0.000759
- Mean net event return: 0.003885
- P25 / worst: -0.012644 / -0.113532
- Hit rate: 0.477
- Event Sharpe: 0.267
- Max event-equity drawdown: -0.722570
- Random non-event median percentile: 1.000

## Controls
- Same-weekday/month placebo median: -0.001408, hit rate 0.418
- Holiday-shift exclusion median: -0.000627, hit rate 0.482
- Cost sensitivity median: 5 bps 0.000241; 10 bps -0.000759; 20 bps -0.002759

## Gate result
```json
{
  "median_event_return_gt_0": false,
  "p25_not_materially_negative": false,
  "hit_rate_ge_55pct": false,
  "placebo_rank_ge_0_85": true,
  "positive_year_rate_not_one_regime_dependent": false,
  "holiday_shift_exclusion_survives": false
}
```

Orthogonality deferred due rejection/unavailable comparable compact event streams; not used to rescue the result.
