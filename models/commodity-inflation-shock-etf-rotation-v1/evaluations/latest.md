# AR-097 evaluation latest

Suggested decision: **reject**.

Rationale: median random-window Sharpe <= 0 after 5 bps costs; p25 random-window Sharpe < 0 after 5 bps costs; max orthogonality correlation > 0.60

## Key metrics
- Primary pre-cost Sharpe: 0.22216756
- Primary Sharpe after 5/10/20 bps: 0.15447886 / 0.08680012 / -0.04844216
- Primary 5 bps max drawdown: -0.18799409
- Average daily turnover proxy: 0.06510749
- Random windows: 10; median 5 bps Sharpe -0.05190803; p25 -0.39011228; positive-window rate 0.5
- Worst random 5 bps Sharpe: -0.75298558; worst random drawdown: -0.18245289
- Orthogonality status: computed_where_retained_curves_available; max abs correlation: 0.69312164

## Protocol
Used qfa/Alpaca real daily market data only, no CSV, no `--data-csv`, no daemon, no orders. The qfa CLI primary run used a temporary SQLite database under `/tmp`, removed after metrics capture. Daily equity paths and weight tails are not retained in durable artifacts.

## Artifacts
- Model: `/Users/moonk/quant-for-agent/models/commodity-inflation-shock-etf-rotation-v1/model.py`
- Config: `/Users/moonk/quant-for-agent/models/commodity-inflation-shock-etf-rotation-v1/config.yaml`
- Metadata: `/Users/moonk/quant-for-agent/models/commodity-inflation-shock-etf-rotation-v1/metadata.yaml`
- Latest JSON: `/Users/moonk/quant-for-agent/models/commodity-inflation-shock-etf-rotation-v1/evaluations/latest.json`
- Immutable run JSON: `/Users/moonk/quant-for-agent/models/commodity-inflation-shock-etf-rotation-v1/evaluations/runs/ar097_qfa_alpaca_real_20260626T164326Z.json`
