# AR-105 Evaluation — residualized-macro-stress-relief-allocator-v1

- Created: 2026-06-26T17:21:41Z
- Decision: **rejected**

## Primary results

- Sharpe: 0.228328
- Annualized return: 0.011998
- Annualized volatility: 0.060177
- Max drawdown: -0.136113
- Mean daily turnover: 0.133745
- SPY beta: 0.249429
- Sleeve dominance: 0.797257

## Random/stress windows

- 10 bps Sharpe median: -0.440586
- 10 bps Sharpe p25: -1.4055
- 10 bps Sharpe worst: -1.600581

## Orthogonality

- Max absolute combined correlation: 0.860296
- Average absolute combined correlation: 0.724915
- AR-063 correlation: 0.855567
- AR-072 correlation: 0.860296

## Falsifier flags

- random_p25_sharpe_nonnegative: False
- max_corr_le_0_50: False
- spy_beta_within_cap: True
- sleeve_dominance_ok: False
- ar063_ar072_drawdown_turnover_useful: True

## Controls

- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false
- Credential provenance: configured paper-data access with values redacted.

## Limitations

- Daily close-to-close backtest omits intraday fills, spread variation, taxes, borrow, and market impact.
- Macro variables are ETF OHLCV proxies rather than point-in-time economic-release surprises.
- Compact artifacts intentionally omit raw daily bars, full equity curves, and weight tails.

## Artifact handles

- Latest JSON: `/Users/moonk/quant-for-agent/models/residualized-macro-stress-relief-allocator-v1/evaluations/latest.json`
- Immutable run JSON: `/Users/moonk/quant-for-agent/models/residualized-macro-stress-relief-allocator-v1/evaluations/runs/ar105_qfa_alpaca_real_20260626T172141Z.json`
