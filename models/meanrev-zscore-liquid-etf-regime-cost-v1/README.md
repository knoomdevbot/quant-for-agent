# meanrev-zscore-liquid-etf-regime-cost-v1

AR-011 refinement of AR-002: a cost-aware, regime-filtered liquid ETF 3-day z-score mean-reversion model.

## Hypothesis

Short-horizon ETF mean reversion may be more viable when adverse trend/volatility regimes are filtered, exposures are volatility-scaled, and turnover costs are explicitly penalized.

## Universe and data

- Universe: SPY, QQQ, IWM, TLT, GLD, SLV, XLF, XLK, XLE, XLV.
- Evaluation data: Alpaca real daily market data via qfa CLI / `AlpacaGateway`.
- CSV use: none; no `--data-csv`.
- Live trading: none; daemon not run; no orders placed.

## Model mechanics

- Computes trailing 3-day return z-scores.
- Uses a 60-sample z-score window and 1.5 entry threshold.
- Requires SPY above its 126-day SMA and SPY 20-day annualized realized volatility <= 28%.
- Requires per-asset 20-day annualized realized volatility <= 45%.
- Takes long oversold trades only when the asset remains above its 126-day SMA.
- Takes short overbought trades only when the asset is below its 126-day SMA.
- Scales raw scores by inverse realized volatility and caps concentration before gross normalization.

## Evaluation summary

Primary window: 2024-01-01 to 2025-12-31.
Random protocol: 30 sampled 252-trading-day windows from Alpaca daily bars spanning 2019-01-01 to 2025-12-31.
Cost proxy: external 5 bps one-way turnover haircut because this qfa version has no native cost/slippage option.

Suggested decision: **rejected**. Median random-window Sharpe after cost was negative, failing the AR-011 falsifier.

Key primary metrics:

- qfa/pre-cost Sharpe: 0.1718.
- qfa/pre-cost total return: 0.0191.
- qfa/pre-cost max drawdown: -0.1149.
- qfa/pre-cost win rate: 0.1040.
- cost-adjusted Sharpe: -0.3660.
- cost-adjusted annualized return: -0.0277.
- cost-adjusted max drawdown: -0.1432.
- median random-window cost-adjusted Sharpe: -0.0434.

See:

- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/qfa_real_alpaca_ar011_20260626T064008Z.json`
