# AR-045 latest evaluation — closing-volume-reversal-costaware-megacap-v1

Decision: **accepted_research_candidate**.

## Primary Alpaca/qfa backtest
- Symbols: AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY
- Window: 2024-01-01 to 2025-12-31, daily.
- qfa run id: 1
- Pre-cost qfa Sharpe: 0.85504813; total return: 0.28153338; max drawdown: -0.10863205.
- Cost-adjusted Sharpe (5 bps one-way turnover haircut): 0.7552867; total return: 0.24112081; max drawdown: -0.11644541.
- Annualized one-way turnover: 32.32729808 vs parent AR-028 54.85876298.

## Random windows
- Count: 8
- Median cost-adjusted Sharpe: 1.18486774
- Positive Sharpe windows: 7 / 8
- Parent AR-028 median cost-adjusted Sharpe on same windows: 1.44344721

## Orthogonality
- Cost-adjusted daily return correlation vs AR-028: 0.45639725 over 499 periods.
- Additional retained-library correlations are in `latest.json`.

## Costs / data controls
qfa has no native cost/slippage flag, so 5 bps one-way target-weight turnover costs were applied externally to a qfa/Alpaca replay. No CSV or `--data-csv` was used. The qfa SQLite DB was temporary and removed (`db_artifact_retained=false`). No daemon or trades.
