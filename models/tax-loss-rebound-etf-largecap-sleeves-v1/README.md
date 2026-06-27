# tax-loss-rebound-etf-largecap-sleeves-v1

Rule-based qfa alpha for AR-123. It buys late-year YTD losers in two separated sleeves (broad ETFs and liquid large/mega-cap equities) only around the turn of the tax year.

- Signal date: last trading day on/before Dec 20.
- Entry: last trading day of December.
- Primary hold: first five January trading days.
- Sizing: equal weight within loser baskets; ETF and equity sleeves each receive 50% gross exposure when both are available.
- Data/evaluation: real qfa/Alpaca daily OHLCV only; no CSV, no daemon, no orders.

Latest decision: **rejected**. See `evaluations/latest.md` and `evaluations/latest.json`.
