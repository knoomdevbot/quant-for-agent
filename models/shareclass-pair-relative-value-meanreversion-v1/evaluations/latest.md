# AR-132 evaluation — U.S. share-class pair relative-value mean reversion

Suggested decision: **reject**.

Data/protocol: Alpaca/qfa real daily OHLCV via AlpacaGateway; configured paper-data access used with credential values redacted. No CSV, no `--data-csv`, no daemon, no orders. Raw daily bars/equity curves/SQLite/helper evaluator were not retained.

Primary model: 120d lagged log-price-ratio z-score, entry |z|>=1, 3-day decay/holding, dollar-neutral within pair and gross-normalized across active pairs, 10 bps one-way turnover cost.

## Key metrics
- Selected pairs: 11 — GOOGL/GOOG, FOXA/FOX, NWSA/NWS, BATRA/BATRK, LBRDA/LBRDK, FWONA/FWONK, LILA/LILAK, LEN/LEN.B, HEI/HEI.A, UHAL/UHAL.B, BF.A/BF.B
- Full sample 10 bps Sharpe: -0.527; annual return -0.698%; annual vol 1.323%; max DD -6.265%
- Random windows (n=40): median Sharpe -0.534; p25 -0.850; worst -1.380; positive-window rate 5.0%
- Turnover: avg daily 0.089; activation 94.4%; hit rate 45.5%
- 5 bps sensitivity Sharpe: 0.319

- qfa CLI smoke (2024 selected pairs, real data, temp SQLite removed): Sharpe -0.136; total return -0.125%; max DD -0.929%; periods 250.
- Top pair abs contribution share: 0.25162668835830676

## Decision gates
```json
{
  "beats_generic_mr_momentum_baselines": true,
  "beats_raw_ratio_baseline": false,
  "low_proxy_redundancy": true,
  "not_dominated_by_one_pair": true,
  "p25_not_materially_negative": false,
  "positive_median_random_window_sharpe_after_10bps": false,
  "positive_window_rate_ge_55pct": false
}
```

## Baselines and ablations
See `latest.json` for compact numeric details. Required variants include raw ratio/no z-score, same-universe generic MR/momentum, 120d vs 252d, 1/3/5/10-day decay, exclude top pair, exclude GOOGL/GOOG where selected, and long-only diagnostic.

## Limitations
Exact prior-alpha stream correlations were unavailable without retaining or reconstructing non-AR-132 daily return streams; compact proxy correlations vs SPY/QQQ/IWM and same-universe generic MR/momentum are reported. Borrow availability/short fees are unavailable from daily bars. Universe is small and heterogeneous, and share-class economic equivalence is imperfect for tracking-stock structures.

No children spawned by this subagent if rejected.
