# AR-099 evaluation latest

Suggested decision: **rejected**.

## Protocol
- Data: qfa AlpacaGateway real daily OHLCV, 2018-01-01 to 2025-12-31, universe DBC, GLD, USO, XLE, TIP, TLT, IEF, SPY, QQQ, XLU.
- Controls: no CSV, no `--data-csv`, no daemon, no orders.
- Costs: replayed target weights with one-way turnover costs of 5/10/20 bps.
- Random windows: 12 deterministic stress/random windows.

## Primary 2021-2025
- QFA no-cost Sharpe: 0.11540322; max drawdown: -0.2172047; total return: 0.0316564.
- 5 bps Sharpe: -0.03352459; max drawdown: -0.2231164; annualized return: -0.00734811.
- 10 bps Sharpe: -0.21572227.
- 20 bps Sharpe: -0.57934911.
- Mean daily turnover proxy: 0.13351875.

## Random-window summary at 5 bps
- Count: 12
- Median Sharpe: 0.0
- p25 Sharpe: -0.55347171
- Positive-window rate: 0.41666667
- Worst max drawdown: -0.2231164
- Sharpe values: [0.0, 0.0, -0.10583895, -0.49376783, -0.85562855, -0.87167703, -0.73258336, 0.94412186, 1.42806513, 0.85461629, 0.30381298, 0.00924136]

## Orthogonality
- Usable retained equity-curve artifacts: 40 / 89 considered.
- Max absolute correlation: 0.75815096.

## Rationale
Rejected: random-window median/p25 Sharpe failed after costs; no refinement/direct-extension child proposed because parent AR-087 is rejected and this result did not validate.

Immutable run artifact: `models/crossasset-commodity-inflation-impulse-allocator-v1/evaluations/runs/ar099_qfa_alpaca_real_20260626T164718Z.json`.
