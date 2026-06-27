# concentration-breadth-meanreversion-v1 (AR-116)

Rule-based research model for large-cap concentration mean reversion using cap-weight versus equal-weight/breadth proxies. Uses qfa/Alpaca real daily OHLCV only.

## Universe
Candidate pool: SPY, QQQ, RSP, QQQE, IWM, DIA, XLK, XLY, XLC, XLF, XLI, XLV, XLP, XLU, SHY, AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA.
Selected tradable universe: SPY, QQQ, RSP, QQQE, IWM, SHY. Sector ETFs and fixed Mag-7 names are diagnostics/signals, not default-basket reuse.

## Signal
Weekly prior-only z-score average of 20-day relative momentum in QQQ/RSP, SPY/RSP, QQQ/IWM, QQQ/QQQE and fixed Mag-7 basket/RSP. When stretch is high and the SPY OHLCV crisis brake is inactive, allocate toward RSP/QQQE/IWM with small beta-reduced shorts in QQQ/SPY.

## Evaluation
Real qfa/Alpaca daily OHLCV request covered 2017-01-01 through 2026-06-25; returned full candidate-set usable coverage starts in 2020-08, so the 30 random windows are coverage-limited within 2020-2026. External one-way turnover costs: 5 bps primary plus 10/20 bps sensitivity. No CSV, no `--data-csv`, no daemon, no orders.

Decision: **rejected**. Primary Sharpe -0.504439; random median Sharpe -0.653251, p25 -1.010749, worst -2.20112; max proxy correlation 0.186.

See `evaluations/latest.md` and `evaluations/latest.json`.
