# range-compression-breakout-megacap-v1 (AR-057)

Mega-cap range-compression breakout continuation research model.

- Universe: AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY.
- Data: qfa/Alpaca real daily OHLCV only; CSV and `--data-csv` are not used.
- Signal: prior-only range compression rank, 40-day channel breakout, volume expansion, 3-session event decay, inverse-vol sizing, market-trend gate.
- Portfolio: long upside breakouts / short downside breakouts, gross normalized to 1 when active, 20% per-name cap.
- Costs: qfa has no native transaction cost; evaluation applies an external 5 bps one-way turnover haircut in a replay using the same Alpaca bars and signal function.

See `evaluations/latest.json` and `evaluations/latest.md` after evaluation.
