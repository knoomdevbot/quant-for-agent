# post-gap-residual-continuation-megacap-v1 (AR-069)

Research-only qfa alpha model for a mega-cap residual overnight-gap continuation basket. The model exposes `generate_signals(context)` and never places orders.

## Hypothesis

Large overnight repricing with idiosyncratic residual strength may reflect gradual information diffusion. The model therefore follows the residual gap direction for 3-5 sessions instead of fading close-location/liquidity-exhaustion pressure.

## Universe

`AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY`

## Signal design

- Overnight gap proxy: daily `open / previous close - 1` from Alpaca OHLCV.
- Residual gap: symbol gap minus equal-weight basket gap.
- Event trigger: residual-gap z-score and abnormal log-volume z-score.
- Holding path: 5-session decayed event stack `[1.00, 0.75, 0.55, 0.35, 0.20]`.
- Sizing: cross-sectional dollar-neutral, gross-normalized, inverse-vol scaled, single-name capped.
- Risk brake: reduce exposure in high basket-volatility regimes.

## Evaluation

Real Alpaca daily OHLCV only; no CSV, no `--data-csv`, no daemon, no orders. Temporary SQLite DBs under `/tmp` were used and removed. Durable artifacts are compact and do not retain raw daily equity curves or weight tails.

Primary window: 2024-01-01 to 2025-12-31. Random/stress protocol: 8 deterministic calendar/stress windows from 2019-2025. Costs: ex-post one-way turnover haircut of 5 bps (`cost_return = gross_return - turnover * 0.0005`).

## Results

Suggested decision: **rejected**.

Key 5 bps cost-adjusted metrics:

- Primary Sharpe: `-0.7400`
- Primary annualized return: `-0.1115`
- Primary annualized volatility: `0.1455`
- Primary max drawdown: `-0.2824`
- Annualized turnover proxy: `90.4861`
- Random median Sharpe: `-0.2764`
- Random p25 Sharpe: `-1.0204`
- Worst-period Sharpe: `-1.8315`
- Positive-window rate: `37.50%`

Orthogonality was good but did not rescue performance: max peer absolute correlation vs AR-056/AR-045/AR-028 was `0.0588`; SPY correlation was `-0.0858`; equal-weight mega-cap proxy correlation was `-0.0477`.

## Artifacts

- Model: `models/post-gap-residual-continuation-megacap-v1/model.py`
- Config: `models/post-gap-residual-continuation-megacap-v1/config.yaml`
- Metadata: `models/post-gap-residual-continuation-megacap-v1/metadata.yaml`
- Latest JSON: `models/post-gap-residual-continuation-megacap-v1/evaluations/latest.json`
- Latest Markdown: `models/post-gap-residual-continuation-megacap-v1/evaluations/latest.md`
- Immutable run JSON: `models/post-gap-residual-continuation-megacap-v1/evaluations/runs/ar069_qfa_alpaca_real_20260626T124127Z.json`

## Divergent child if revisited

`intraday-open-gap-reversal-with-news-volume-v1`: test explicit same-day open-to-close reversal around abnormal gap/volume events; different horizon and contrarian mechanism, requiring intraday/open execution validation.
