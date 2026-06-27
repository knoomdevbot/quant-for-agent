# AR-058 — Regime-gated liquidity exhaustion recovery

Refinement of AR-046 for a mega-cap basket: AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY.

The model keeps AR-046's broad abnormal range/volume close-location exhaustion trigger, but adds:

- equal-weight basket market trend gate (80-day lookback);
- realized-volatility percentile gate to avoid both quiet noise and highest crisis tails;
- deterministic 3-day signal decay and 3-day cooldown;
- sparse basket-level sizing with gross exposure 0.80 and per-name cap 0.16.

It exposes qfa-compatible `generate_signals(context)` and uses only OHLCV data supplied by qfa/Alpaca. It does not place orders and is research-only.

Evaluation artifacts are under `evaluations/`. Metrics use qfa/Alpaca real daily bars only, with no CSV and no `--data-csv`. Since qfa has no native cost flag, reported cost-adjusted metrics apply an external 5 bps one-way target-weight turnover haircut.
