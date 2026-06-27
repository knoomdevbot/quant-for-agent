# AR-054: ETF stress-liquidity beta-reduced allocation

This model refines AR-043 by using the same daily OHLCV liquidity-stress inputs
(abnormal range, abnormal dollar volume, and close-location) but adds a SPY
trend/drawdown brake and a lower equity sleeve cap. During equity stress it tilts
more strongly toward GLD/XLU/TLT rather than retaining the higher equity beta in
AR-043.

## QFA contract

- Model: `model.py`
- Function: `generate_signals(context) -> dict[str, float]`
- Universe: SPY, QQQ, IWM, TLT, GLD, XLU, XLE
- Data: qfa/Alpaca real daily OHLCV only; no CSV-backed research.
- Trading: research-only; no daemon and no live trades.

## Evaluation summary

See `evaluations/latest.json` and `evaluations/latest.md` for full real-data
artifacts, commands, qfa run IDs, random windows, turnover-cost haircut, and
orthogonality checks.

Headline post-cost results (5 bps one-way turnover haircut):

- Primary 2021-01-04 to 2025-12-15 Sharpe: 0.27230672
- Primary annualized return: 0.02607036
- Primary max drawdown: -0.1893238
- 9 random windows median Sharpe: 0.36767384
- 9 random windows p25 Sharpe: -0.31652669
- Worst random-window Sharpe: -0.37918828
- Worst random-window max drawdown: -0.1567204

## Decision

Suggested decision: **reject**.

Reason: worst random-window drawdown improved only slightly versus AR-043, while
primary Sharpe, random p25 Sharpe, and worst random Sharpe deteriorated. The
available correlation check also shows high AR-043 correlation (0.90453842).
AR-008/AR-037/AR-039 correlations were explicitly marked unavailable where their
`latest.json` files did not retain equity curves.

## Important qfa limitation

qfa normalizes nonzero model weights to 100% gross. The model can reduce beta by
changing the risk/defensive sleeve mix, but cannot maintain a persistent partial
cash allocation unless it returns all-zero signals.
