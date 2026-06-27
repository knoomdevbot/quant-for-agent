# event-earnings-drift-megacap-20d-v1

AR-014 divergent child of AR-001: event-timed mega-cap post-earnings drift proxy.

The repository qfa/Alpaca path exposes OHLCV bars but not a point-in-time earnings calendar, so `model.py` uses an explicit proxy for earnings-like information shocks: abnormal overnight gap, abnormal close-to-close move, and abnormal volume. Signals are held for a 20-trading-day decaying post-event window.

Latest evaluation: `evaluations/latest.json` / `evaluations/latest.md`. Suggested decision: **rejected**.

Safety: research only; no daemon; no order placement; Alpaca real market data only; no CSV.
