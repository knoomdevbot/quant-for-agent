# AR-054 evaluation: etf-stress-liquidity-beta-reduced-v1

- Data source: Alpaca real OHLCV via qfa/AlpacaGateway; no CSV and no `--data-csv`.
- Temporary DB: `/tmp/qfa-AR-054-*.sqlite3`; retained: false.
- Universe: SPY, QQQ, IWM, TLT, GLD, XLU, XLE; primary: 2021-01-04 to 2025-12-15; timeframe 1Day.
- Costs: qfa native costs unavailable; post-cost proxy subtracts 5 bps x one-way daily target turnover.
- Primary post-cost Sharpe: 0.27230672; annualized return: 0.02607036; max drawdown: -0.1893238.
- Random windows: median Sharpe 0.36767384, p25 Sharpe -0.31652669, worst Sharpe -0.37918828, worst max drawdown -0.1567204, positive-window rate 0.66666667.
- AR-043 same-window comparison: primary Sharpe 0.45490526, median random Sharpe 0.53294239, p25 Sharpe -0.1024685, worst Sharpe -0.21722247, worst max drawdown -0.1583319.
- Orthogonality: max abs correlation to available curves 0.90453842; status fails_available_model_threshold_high_correlation_to_AR043; AR008_unavailable. AR-008, AR-037, and AR-039 were explicitly unavailable because their latest.json files did not retain equity curves.
- Suggested decision: **reject**. Rejected: although worst random-window max drawdown improved slightly versus AR-043 (-0.1567204 vs -0.1583319), primary post-cost Sharpe fell to 0.27230672 vs AR-043 0.45490526, random p25 Sharpe worsened to -0.31652669 vs AR-043 -0.1024685, and available orthogonality failed with AR-043 correlation 0.90453842. AR-008/AR-037/AR-039 correlations were unavailable because their latest.json files do not retain equity curves.

## Warning
qfa normalizes nonzero weights to 100% gross, so the model cannot hold partial cash except by returning all-zero signals during warmup; beta reduction is implemented by risk/defensive sleeve caps rather than persistent cash.

## Suggested child idea
ETF defensive carry surprise allocator using rate-sensitive ETF carry/roll proxies: Different mechanism from liquidity stress: allocate among TLT/GLD/XLU/risk ETFs using medium-horizon realized carry and downside-volatility surprise rather than range/volume stress breadth.
