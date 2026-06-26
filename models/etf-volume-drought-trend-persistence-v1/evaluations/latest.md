# AR-082 evaluation — etf-volume-drought-trend-persistence-v1

- Data: Alpaca real daily OHLCV through qfa AlpacaGateway; no CSV; no `--data-csv`; no daemon; no orders.
- Universe: SPY, QQQ, IWM, TLT, GLD, XLU, XLE, SHY, HYG, LQD
- Primary window: 2020-01-02 to 2025-12-15; smoke: 2024-01-02 to 2024-06-28; random windows: 8.
- Costs: 5 bps one-way turnover proxy applied externally.

## Key metrics after costs

- Primary Sharpe: -0.04172902
- Annualized return / volatility: -0.00725942 / 0.08574252
- Primary max drawdown: -0.20146313
- Mean daily one-way turnover: 0.12484557
- Random-window median Sharpe: 0.20135101
- Random-window p25 Sharpe: -0.32576784
- Worst random-window Sharpe: -0.86928001
- Positive random-window rate: 0.625

## Orthogonality

Status: passed_low_overlap_or_low_corr; max abs correlation: 0.44439164. Correlations are against retained prior qfa real-data equity curves where available.

## Suggested decision

**REJECTED** — p25 Sharpe materially negative; drawdown severe/material.

## Warnings / failure modes

- qfa engine has no native transaction cost/slippage; 5 bps one-way cost proxy applied externally.
- Volume drought/range compression often falls back to SHY/defensive sleeve; economic edge may be defensive beta rather than trend persistence.
- Alpaca daily data only; no intraday participation timing or borrow/financing effects modeled.
- low-volume state is a no-opportunity proxy
- signals overlap with defensive rotation/carry sleeves
- costs consume sparse trend-persistence edge
- fallback dominates returns

Immutable run JSON: `/Users/moonk/quant-for-agent/models/etf-volume-drought-trend-persistence-v1/evaluations/runs/ar082_qfa_alpaca_real_20260626T143511Z.json`
