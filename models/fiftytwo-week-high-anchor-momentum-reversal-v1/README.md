# AR-128: 52-week high/low anchored momentum-reversal split

Research-only qfa artifact for `fiftytwo-week-high-anchor-momentum-reversal-v1`.

## Model

`model.py` exposes `generate_signals(context) -> dict[str, float]` and consumes only `context.prices` daily OHLCV plus `context.symbols`. It does not fetch data, read CSVs, start daemons, or place orders.

Signal construction:
- Monthly cross-sectional ranker.
- Uses 252-trading-day high/low extrema shifted at least one bar (current bar excluded).
- Equity and ETF sleeves are scored separately.
- Long candidates: close near lagged 52-week high (`close / lagged_high >= 0.92`) and positive 126-day momentum.
- Diagnostic underweights: close near lagged 52-week low (`close / lagged_low <= 1.12`) and negative 126-day momentum.
- Scores blend high proximity rank, 126-day momentum rank, and a small realized-volatility penalty; output is capped at 8% per symbol and gross-normalized.

## Evaluation

Latest real-data evaluation: `evaluations/latest.json` and `evaluations/latest.md`.

Run used Alpaca/qfa real daily OHLCV from 2018-01-01 through 2026-06-26 with 10 bps one-way primary costs and 20 bps stress. No raw bars, daily returns, equity curves, or weight tails are retained in artifacts.

## Decision

Suggested decision: **reject for now**. Equity sleeve was positive but weaker than simple momentum/TSMOM/low-vol controls on random windows; ETF sleeve was negative and failed the redundancy stress test versus ETF momentum.

## Limitations

- Static current liquid equity/ETF universe introduces survivorship and delisting bias.
- Liquidity screen is an OHLCV dollar-volume proxy, not live executable ADV.
- Orthogonality checks are compact proxy correlations/ablations rather than full alpha-library stream correlations.
