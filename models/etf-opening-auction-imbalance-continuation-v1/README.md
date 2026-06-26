# etf-opening-auction-imbalance-continuation-v1

AR-087 qfa-compatible research alpha. It uses Alpaca/qfa real 1Min ETF OHLCV to test whether opening-auction / first-30-minute VWAP imbalance continues intraday.

## Signal

- Universe: SPY, QQQ, IWM, XLV, XLY, XLE, XLU, XLP, TLT, IEF, GLD, HYG, LQD, SHY.
- At roughly 10:01 New York time, measure first-30-minute return, early VWAP deviation, and relative first-30-minute volume versus trailing same-window history.
- Trade only when cross-ETF breadth confirms a directional imbalance; hold a capped continuation basket for 120 minutes and flatten intraday.
- Gross exposure <= 1.0; single ETF cap 0.16.

## Evaluation summary

Suggested decision: **rejected**.

Primary 2024-01-02..2025-12-15 after 10 bps one-way turnover proxy: Sharpe `-4.27938852`, annualized return `-0.10385271`, max drawdown `-0.19477831`, active-day fraction `0.32653061`.

Random/stress windows (14): median Sharpe `-5.84184963`, p25 Sharpe `-6.33759196`, worst Sharpe `-7.44248814`, positive-window rate `0.0`.

Controls: no CSV, no `--data-csv`, no daemon, no orders. Compact artifacts omit equity curves, weights tails, raw paths, and raw daily paths.
