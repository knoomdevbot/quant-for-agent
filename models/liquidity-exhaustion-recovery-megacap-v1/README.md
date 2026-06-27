# liquidity-exhaustion-recovery-megacap-v1

Research artifact for AR-046, divergent from AR-028.

## Hypothesis

Cross-sectional liquidity exhaustion breadth across liquid mega-cap equities may forecast short-horizon recovery at the basket level. Unlike AR-028, this model does not primarily fade isolated single-name close-location events; it waits for broad abnormal range/volume pressure across the universe and then allocates to a recovery basket.

## Signal

- Universe: AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY.
- Data: Alpaca/qfa daily OHLCV only; no CSV or `--data-csv`.
- Downside exhaustion: high-volume/high-range closes near lows across at least four names.
- Upside exhaustion: high-volume/high-range closes near highs across at least four names.
- Allocation: basket-level long after broad downside exhaustion, basket-level short after broad upside exhaustion, with 60% equal basket floor and 40% tilt to event contributors.

## Evaluation summary

Primary qfa/Alpaca backtest, 2024-01-01 to 2025-12-31:

- Pre-cost Sharpe: 0.84859942
- Pre-cost total return: 0.19136536
- Pre-cost max drawdown: -0.04429516
- 5 bps turnover-replay Sharpe: 0.80678607
- 5 bps turnover-replay total return: 0.17963289

Eight random/stress windows:

- Median pre-cost Sharpe: 0.249733915
- Median 5 bps cost-adjusted Sharpe: 0.19746282
- Positive cost-adjusted Sharpe windows: 4 / 8
- Worst cost-adjusted max drawdown: -0.07442596

Orthogonality checks from available retained equity curves:

- AR-028 daily return correlation: 0.463762
- tsmom-voltarget-liquid-etf-randomcost-v1 watchlist correlation: 0.183383
- Mega-cap equal-weight proxy correlation: 0.281591
- SPY correlation: 0.356519

## Decision

Suggested decision: `research_watchlist_not_trade`. The primary and median random-window Sharpe remain positive after a 5 bps turnover haircut and drawdown is acceptable, but the alpha is sparse, several windows are negative, and correlation to AR-028 is moderate.

No daemon was run and no trades were placed.
