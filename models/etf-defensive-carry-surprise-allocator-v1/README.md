# etf-defensive-carry-surprise-allocator-v1

AR-067 qfa-compatible ETF defensive carry-surprise allocator.

## Hypothesis

A defensive carry-surprise allocator using rate-sensitive and defensive ETFs can produce a stream divergent from AR-054's liquidity-stress beta brake. The model uses medium-horizon return per downside volatility, duration carry proxies from TLT/IEF/SHY, GLD/XLU defensive momentum, downside-volatility surprise, and broad equity drawdown state.

## Universe

SPY, QQQ, IWM, TLT, IEF, SHY, GLD, XLU, XLE.

## QFA contract

`model.py` exposes `generate_signals(context)` and returns long-only target weights. It uses only OHLCV available in qfa context.

## Evaluation summary

See `evaluations/latest.json` and `evaluations/latest.md`. Latest suggested decision: **rejected**. Durable artifacts retain compact summary metrics only; no raw daily equity curves or weights tails are retained.
