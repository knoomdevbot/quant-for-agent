# AR-026 evaluation: stress-gap-reversal-etf-v1

Decision: **rejected** — Do not promote; archive as failed stress-gap reversal research reference.

- Data: Alpaca real market data via qfa/AlpacaGateway, no CSV, no trades.
- Symbols: SPY, QQQ, IWM, TLT, GLD, XLU, XLE
- Range: 2021-01-01 to 2026-06-24; timeframe 1Day.
- qfa proxy run id: 1; temporary DB not retained.
- Primary intended open-to-close after 5 bps per-side costs: Sharpe -0.202, total return -8.36%, max drawdown -15.98%, win rate 6.85%, periods 1373, event days 189.
- qfa close-to-close gross proxy: Sharpe 0.062, total return 0.98%, max drawdown -21.80%.
- Random windows (10 x 126 trading days): median Sharpe -0.575, median total return -1.73%, median max drawdown -2.98%.

## Limitation
qfa's daily engine cannot enter at the current open and exit later. The qfa model is therefore a lagged close-to-close approximation; the intended same-day open-to-close horizon is measured by the direct Alpaca OHLC research harness.

## Rationale
Primary intended open-to-close after-cost Sharpe -0.202, total return -8.36%, max drawdown -15.98%; random-window median Sharpe -0.575. Fails AR-026 falsifier.
