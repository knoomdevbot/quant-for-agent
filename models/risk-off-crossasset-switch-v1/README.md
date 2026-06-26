# risk-off-crossasset-switch-v1

AR-008 seed alpha: cross-asset risk-on/risk-off regime switch using liquid ETFs and OHLCV-only features.

## QFA contract

`model.py` exposes:

```python
def generate_signals(context):
    return {"SPY": 0.0, "QQQ": 0.0, "IWM": 0.0, "TLT": 0.0, "GLD": 0.0, "XLU": 0.0, "XLE": 0.0}
```

The model reads only `context.symbols`, `context.prices`, `context.as_of`, and optional `context.metadata["params"]`. It does not place orders and does not invoke the qfa daemon.

## Universe

- Risk-on: SPY, QQQ, IWM, XLE
- Risk-off: TLT, GLD, XLU

## Signal logic

The model computes:

- 60-day momentum and breadth across SPY, QQQ, IWM, XLE.
- 20-day SPY realized volatility.
- 20-day TLT/GLD relative strength versus SPY as a defensive stress confirmation.

Risk-on regime requires positive SPY 60-day momentum, at least half the risk-on bucket in positive 60-day trends, SPY realized volatility below 22%, and no strong defensive relative-strength stress. Otherwise the model switches to the defensive bucket.

Within the active bucket, positive 60-day momentum is scaled by inverse realized volatility, gross-normalized to 1.0, and capped at 0.45 absolute weight per ETF.

## Evaluation

Latest real-data qfa evaluation artifacts are under `evaluations/` after running Alpaca-backed qfa backtests without `--data-csv`.
