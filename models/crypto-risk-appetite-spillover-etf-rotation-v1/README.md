# crypto-risk-appetite-spillover-etf-rotation-v1

Research model for AR-092. The model embeds compact derived BTC/ETH risk-appetite scores generated from real Alpaca crypto daily bars and applies a strict next-calendar-day availability lag. It rotates long-only among liquid risk-on, duration, gold, credit, and defensive ETFs using qfa-provided Alpaca ETF OHLCV for confirmation and sizing.

See `evaluations/latest.md` and `evaluations/latest.json` for metrics and provenance. Raw external and market data are not retained.
