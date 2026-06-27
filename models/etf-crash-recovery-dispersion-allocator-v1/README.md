# AR-064 ETF crash-recovery dispersion allocator v1

Rule-based qfa alpha for the AR-064 divergent research issue.  The model avoids VIXY/convexity sleeves and uses only ETF OHLCV bars supplied by qfa/Alpaca.

## Mechanism

1. Measure broad realized-volatility shocks from SPY/QQQ/IWM returns.
2. Require cross-sectional ETF return dispersion compression versus its recent history.
3. For roughly ten sessions after a qualifying shock/compression event, allocate long-only to depressed risk ETFs showing short-term stabilization/reversal, excluding severe drawdown tails.
4. Otherwise allocate defensively among TLT/IEF/GLD/XLU/XLP by medium-term momentum/drawdown score.

Gross exposure is capped at 1.0 and single risk ETF weights are capped at 35% before qfa normalization.

## Evaluation protocol

The durable evaluation files in `evaluations/` were generated with Alpaca real market data via qfa primitives only. CSV data and `--data-csv` were not used. No daemon or order placement path was invoked. External turnover-cost haircuts of 10 bps and 20 bps one-way were applied because qfa native backtest transaction costs are not available in this repository version.

See:

- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/ar064_qfa_alpaca_real_*.json`
