# single-name-month-of-year-seasonality-largecap-v1

Research artifact for AR-129. The model ranks a fixed liquid large-cap/common-stock universe by lagged same-calendar-month median returns, using only prior years/months available before each monthly rebalance. Scores are sector-neutralized and sector-gross capped.

## Data and safety
- Source: qfa `AlpacaGateway` real daily OHLCV.
- No CSV, no `--data-csv`, no qfa daemon, no orders.
- No raw bars, caches, equity curves, SQLite DBs, or helper scripts are retained.

## Universe
Selected 143 symbols from a broad current large-cap/common-stock candidate map by Alpaca coverage, median dollar volume, median price, and sector mapping before performance review. Limitation: current static membership is survivorship-biased and not point-in-time.

## Latest result
Decision: **rejected**. Primary 10 bps one-way cost: Sharpe `-0.386086`, annualized return `-0.027148`, vol `0.071205`, max drawdown `-0.278699`. Random-window Sharpe median/p25/worst: `-0.220313` / `-0.681884` / `-1.195085`; positive-window rate `0.3`; avg monthly turnover `1.542879`; avg active names `56.0`.

Rejected: after-cost performance was negative and failed the required random-window robustness thresholds; no children are spawned. See `evaluations/latest.json` for cost sensitivity, ablations, concentration, and orthogonality/proxy checks.
