# crossasset-commodity-inflation-impulse-allocator-v1 (AR-099)

Rule-based qfa model for a divergent commodity/inflation macro hypothesis. The model allocates among DBC, GLD, USO, XLE, TIP, TLT, IEF, SPY, QQQ, and XLU using daily Alpaca OHLCV history supplied by qfa.

## Signal intuition

- Measures medium/slow commodity and inflation-sensitive ETF impulse from DBC, USO, XLE, GLD, and TIP-vs-IEF behavior.
- Confirms defensive regimes using SPY/QQQ drawdown/volatility plus XLU/IEF relative strength.
- Allocates across inflation hedges, duration, defensive assets, and a limited equity sleeve.
- Long-only, gross-normalized to 1.0, with a 30% single-ETF cap and no leverage.

## qfa contract

`model.py` exposes:

```python
def generate_signals(context) -> dict[str, float]:
    ...
```

The function expects `context.symbols`, `context.prices`, and `context.as_of` as provided by qfa. It returns target portfolio weights for the requested symbols.

## Evaluation controls

Artifacts under `evaluations/` use only qfa/Alpaca real market data. They intentionally retain aggregate metrics only; raw daily paths, equity curves, and weight tails are pruned from compact JSON artifacts.

Controls: no CSV, no `--data-csv`, no daemon, no orders.
