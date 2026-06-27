# AR-123 tax-loss rebound ETF/large-cap sleeves

Rule-based qfa alpha model for a timestamp-safe late-December tax-loss rebound event study. The model exposes `generate_signals(context)` and uses only qfa daily OHLCV in the supplied context.

Decision: **rejected**. Rejected: primary combined loser basket is positive but does not beat the generic January/no-loser equal-selected baseline at 10 bps; evidence is sparse and baseline-sensitive.

Primary protocol: signal at Dec. 20-or-prior close, enter at the last December close, hold first five January trading days, 10 bps one-way cost with 5/20 bps sensitivities.

Selected universe was fixed before performance review from broad ETF and large-cap equity candidate pools using Alpaca coverage and liquidity/economic-exposure filters. See `evaluations/latest.json` for compact candidate-pool and metrics details.
