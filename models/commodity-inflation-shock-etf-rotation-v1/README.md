# commodity-inflation-shock-etf-rotation-v1

AR-097 research artifact for a genuinely divergent macro/commodity ETF rotation idea from rejected parent AR-085.

## Hypothesis
Commodity, inflation-sensitive, and defensive ETFs may rotate after broad inflation/risk shocks using daily trend, realized volatility, and cross-asset confirmation. The selected qfa/Alpaca universe is GLD, USO, DBC, XLE, TIP, TLT, IEF, SPY, XLP, and XLU.

## Model
`model.py` exposes `generate_signals(context)` for qfa. It uses only daily OHLCV supplied in the qfa context:

- 20/60 day returns and realized volatility.
- Commodity trend/volatility confirmation using USO/DBC/XLE.
- TIPS-vs-duration confirmation, SPY drawdown/risk state, and GLD/defensive sleeves.
- Weekly rebalance anchor to reduce churn, long-only, gross exposure <= 1.0, max single ETF weight 30%.

The design intentionally avoids intraday opening-range/liquidity reversal features so it is not a refinement of AR-085.

## Evaluation summary
Latest evaluation used qfa/Alpaca real daily market data only; no CSV, no `--data-csv`, no daemon, and no orders. A temporary database under `/tmp` was removed after the run. Durable artifacts retain aggregate metrics only, not daily paths or weight tails.

Suggested decision: **reject**.

Key latest metrics:

- Primary pre-cost Sharpe: 0.22216756.
- Primary Sharpe after 5/10/20 bps: 0.15447886 / 0.08680012 / -0.04844216.
- Primary 5 bps max drawdown: -18.799409%.
- Average daily turnover proxy: 0.06510749.
- Random windows: 10; median 5 bps Sharpe -0.05190803; p25 -0.39011228; positive-window rate 50%.
- Worst random 5 bps Sharpe: -0.75298558; worst random drawdown -18.245289%.
- Orthogonality status: computed where retained compact curves were available; max absolute correlation 0.69312164.

Reject rationale: median random-window Sharpe was <= 0, p25 random-window Sharpe was negative after costs, and max available orthogonality correlation exceeded 0.60.

## Artifacts

- `model.py` — qfa-compatible signal model.
- `config.yaml` — model/evaluation configuration.
- `metadata.yaml` — artifact metadata and safety markers.
- `evaluations/latest.json` — compact machine-readable latest result.
- `evaluations/latest.md` — human-readable latest result.
- `evaluations/runs/ar097_qfa_alpaca_real_20260626T164326Z.json` — immutable run artifact.
