# AR-145 evaluation latest

Decision: rejected.

Primary 10 bps metrics: Sharpe 0.011, annual return -0.33%, annual vol 9.30%, max drawdown -27.80%, annual turnover 48.96.

Random windows: n=48, median Sharpe 0.214, p25 Sharpe -0.165, worst Sharpe -2.162, positive rate 64.6%.

Controls: simple VIX, term-slope-only, no-vol-of-vol, ETF momentum/reversal, and shifted external-feature controls are recorded in latest.json. The primary did not satisfy acceptance gates, so no children were spawned.

Provenance: public CBOE volatility histories were fetched transiently and transformed into one-session-lagged compact features. ETF prices came from qfa real provider daily bars. No CSV-backed ETF prices, daemon, or orders were used; no raw histories or equity curves were retained.
