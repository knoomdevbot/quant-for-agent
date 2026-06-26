# ETF Realized-Volatility Asymmetry Defensive Allocator v1 (AR-088)

Rule-based qfa alpha testing whether downside/upside realized-volatility asymmetry across equity, duration, credit, gold, and defensive sector ETFs can identify defensive allocation regimes.

## Contract

`model.py` exposes:

```python
generate_signals(context) -> dict[str, float]
```

The model consumes only OHLCV bars supplied by qfa/Alpaca in `context.prices`. It is long-only, caps single ETF weights, and normalizes gross exposure to <= 1.0. It does not place orders and does not run a daemon.

## Universe

SPY, QQQ, TLT, IEF, GLD, XLU, XLP, XLV, HYG, LQD, SHY.

## Features

- 63-day rolling upside and downside semivolatility.
- Downside/upside semivolatility ratio z-score over a 126-day history.
- 21-vs-126-day realized-volatility trend.
- Equity/credit stress confirmation using HYG-vs-IEF behavior and SPY drawdown.
- Defensive allocation sleeves: duration, gold, XLU/XLP/XLV, and SHY.

## Real-data evaluation summary

Artifacts are in `evaluations/`. The evaluation used Alpaca/qfa real daily OHLCV only, no CSV, no `--data-csv`, no daemon, no orders, and a temporary SQLite DB that was removed after extracting qfa run IDs and compact metrics.

Key 10 bps one-way turnover-cost results:

- Primary 2021-01-04 to 2025-12-15 Sharpe: -0.05070501; annualized return: -0.00671737; max drawdown: -0.26525629.
- Random/stress windows: median Sharpe 0.20576377; p25 Sharpe -0.17351568; positive-window rate 0.7; worst Sharpe -1.22196659.
- Orthogonality failed: max absolute replay correlation 0.90004171 vs retained defensive/correlation-breakdown models.

Suggested decision: **rejected**. The hypothesis failed the stated robustness/orthogonality falsifiers; no refinement or direct-extension child is proposed.
