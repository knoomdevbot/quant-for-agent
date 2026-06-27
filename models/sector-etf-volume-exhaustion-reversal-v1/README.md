# AR-095 — Sector ETF Volume Exhaustion Reversal

Model: `sector-etf-volume-exhaustion-reversal-v1`

## Hypothesis

Abnormal volume and range expansion in sector ETFs can reflect temporary, price-insensitive rebalance or rotation flows. When the next session fails to follow through, the exhausted sector move may reverse over the next close-to-close interval.

This is intentionally divergent from rejected parent AR-083: it uses short-horizon volume/range exhaustion reversal rather than breadth-confirmed defensive trend allocation.

## Universe

Candidate pool and selected universe are the same:

`SPY, QQQ, IWM, XLF, XLK, XLE, XLU, XLV, XLI, XLP`

## Signal

The qfa-compatible `generate_signals(context)` uses only OHLCV fields supplied by qfa/Alpaca:

1. Sector ETF abnormal volume z-score.
2. Range expansion z-score.
3. Exhaustion close-location value near high/low.
4. Failed follow-through on the next observed bar.
5. Market beta brake using recent SPY impulse and a partial SPY hedge.

## Evaluation

- Data: Alpaca real daily OHLCV via qfa/AlpacaGateway.
- No CSV input; no `--data-csv`; no daemon; no orders.
- Temporary SQLite DB used only for smoke test and removed.
- Cost/slippage proxy: 5 bps one-way applied to `0.5 * abs(target weight change)`.
- Windows: qfa smoke plus 10 varied windows from 2020-2025.

## Result

Suggested decision: **rejected**.

Cost-adjusted random-window metrics:

- Mean Sharpe: `-0.25417176`
- Median Sharpe: `-0.29281638`
- p25 Sharpe: `-0.79435349`
- Worst Sharpe: `-2.05827009`
- Positive-window rate: `0.4`
- Mean annualized return: `-0.00443112`
- Mean annualized volatility: `0.0267691`
- Worst max drawdown: `-0.05862576`

Primary 2024-2025 cost-adjusted metrics: Sharpe `0.158675`, annualized return `0.0031579`, annualized volatility `0.02129512`, max drawdown `-0.02815039`.

The alpha fails the stated falsifier because median and p25 random-period Sharpe are negative after costs. No refinement/direct extension is proposed.

## Artifacts

- `model.py`
- `config.yaml`
- `metadata.yaml`
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/ar095_qfa_alpaca_real_20260626T0914Z.json`
