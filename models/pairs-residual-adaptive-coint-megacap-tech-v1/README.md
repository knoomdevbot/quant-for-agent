# AR-019: Adaptive Residual Pair Cointegration Filters

Research-only qfa-compatible alpha using Alpaca real market data only.

## Hypothesis

Refine AR-005 by selecting mega-cap tech equity pairs with rolling return correlation and cointegration-like residual stability filters. Eligible pairs require high recent correlation, bounded residual AR(1) persistence, short half-life, and repeated residual zero crossings before entering residual z-score mean reversion trades.

## Data and safety

- Data source: Alpaca real OHLCV via qfa/AlpacaGateway.
- No CSV fixtures and no `--data-csv`.
- No daemon.
- No trades placed.
- qfa metrics are pre-cost because the qfa backtest CLI has no native cost/slippage parameter.

## Evaluation outcome

Rejected. The primary qfa backtest had negative pre-cost Sharpe and the six random-window median Sharpe was non-positive. Applying realistic costs/slippage would further reduce results.

See:

- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/ar019_qfa_real_alpaca_primary_plus_random6_20260626T074621Z.json`
