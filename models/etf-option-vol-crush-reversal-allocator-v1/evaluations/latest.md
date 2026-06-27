# AR-094 evaluation latest

Decision: **rejected**.

Data: Alpaca/qfa real daily ETF OHLCV only. No option implied-volatility feed was available, so the implemented signal is an explicitly labeled realized range/volatility crush proxy, not true IV. No CSV, daemon, or orders. Temporary SQLite DB was deleted.

Primary 2021-01-04..2025-12-15, 10 bps one-way cost: Sharpe -0.297205, annualized return -0.02295729, annualized vol 0.06986772, max drawdown -0.18497184. Mean daily target turnover 0.11140539.

Random/varied windows at 10 bps: median Sharpe -0.35286478, mean Sharpe -0.16043816, p25 Sharpe -0.70003851, worst Sharpe -0.95711496, positive-window rate 0.3, worst max drawdown -0.14503703.

Orthogonality max abs corr: 0.91935325 (fail).

Run artifact: `models/etf-option-vol-crush-reversal-allocator-v1/evaluations/runs/ar094_qfa_alpaca_real_20260626T162138Z.json`.
