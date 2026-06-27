# AR-094 — ETF option-implied volatility crush reversal allocator

## Summary

This folder contains a qfa-compatible research implementation for AR-094. The original hypothesis requires ETF option-implied volatility shock/crush data. In this qfa/Alpaca research setup, only ETF OHLCV bars were available; therefore `model.py` is explicitly labeled and implemented as a **realized high-low range / realized-volatility crush proxy**, not a true option-IV model.

## Universe

Candidate product pool and selected universe:

- SPY, QQQ, IWM, TLT, GLD, HYG, LQD, XLU, XLE, SHY

## Signal sketch

- Estimate fast/medium/slow range volatility from Alpaca OHLCV.
- Identify a prior elevated realized/range-volatility shock and a short-term normalization/crush.
- Allocate toward risk/rebound assets only when the proxy crush is confirmed and trend/credit brakes are not adverse.
- Otherwise retain a defensive sleeve in TLT, GLD, LQD, XLU, and SHY.

## Evaluation result

Suggested decision: **rejected**.

Primary 2021-01-04 to 2025-12-15 after 10 bps one-way turnover cost:

- Sharpe: -0.297205
- Annualized return: -0.02295729
- Annualized volatility: 0.06986772
- Max drawdown: -0.18497184
- Mean daily target turnover: 0.11140539

Ten random/varied windows after 10 bps one-way turnover cost:

- Median Sharpe: -0.35286478
- Mean Sharpe: -0.16043816
- p25 Sharpe: -0.70003851
- Worst Sharpe: -0.95711496
- Positive-window rate: 0.3
- Worst max drawdown: -0.14503703

Orthogonality check failed: max absolute correlation to retained volatility/regime alpha replays was 0.91935325.

## Artifacts

- `model.py`
- `config.yaml`
- `metadata.yaml`
- `evaluations/latest.json`
- `evaluations/latest.md`
- Immutable run JSON under `evaluations/runs/`

No CSV, daemon, orders, retained DB, or raw daily paths were used/retained.
