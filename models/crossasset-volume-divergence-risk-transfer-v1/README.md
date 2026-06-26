# crossasset-volume-divergence-risk-transfer-v1

AR-081 tests whether cross-asset ETF dollar-volume divergence identifies risk-transfer regimes. The model compares 20-day vs 60-day relative dollar-volume z-scores for risk-on ETFs, defensive/duration/gold ETFs, and credit ETFs, then allocates long-only gross exposure up to 1.0 with a 0.35 single-ETF cap.

## Signal

- Risk-on volume spread: SPY/QQQ/IWM/XLE/XLV relative-volume strength versus TLT/IEF/GLD/XLU/SHY.
- Credit imbalance: HYG volume leadership versus LQD.
- Confirmation/risk control: 20-day price trend and realized-volatility scaling.

## Evaluation

Real Alpaca daily OHLCV through qfa/Alpaca only. No CSV input, no daemon, and no orders. Latest evaluation: `evaluations/latest.json`; immutable run: `evaluations/runs/ar081_qfa_alpaca_real_20260626T140733Z.json`.

Decision: **reject** — Fails robustness threshold: p25 Sharpe/drawdown/orthogonality not adequate after turnover haircut.
