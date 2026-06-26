# etf-relief-rally-exhaustion-reversal-v1 (AR-073)

Rule-based qfa alpha for AR-073. The model looks for a recent broad stress drawdown across risk-on ETFs followed by a fast relief rally with risk-on assets outperforming defensive ETFs. When active, it shorts the most over-extended/high-vol risk-on ETFs and buys lagging/defensive ETFs.

## qfa contract

`model.py` exposes:

```python
def generate_signals(context) -> dict[str, float]
```

The function consumes only `context.prices`, `context.symbols`, and `context.as_of`; it returns symbol weights. qfa's backtest layer gross-normalizes returned weights.

## Universe

SPY, QQQ, IWM, XLE, XLY, XLV, XLP, XLU, TLT, IEF, GLD, HYG, LQD, SHY.

## Signal summary

- Stress gate: 63-day broad risk-on drawdown.
- Relief gate: 10-day risk-on recovery, risk-on vs defensive spread, and positive relief breadth.
- Short sleeve: top stretched risk-on ETFs by 10/21-day return, volatility, z-score stretch, and residual drawdown.
- Long sleeve: defensive/lagging ETFs with stable returns.
- Risk: gross target <= 1.0 before qfa normalization; single-name cap 24%; mostly beta-reduced/short-biased during active events; otherwise SHY.

## Evaluation protocol

`evaluations/latest.json` and `evaluations/latest.md` are generated from qfa/Alpaca real daily bars only. No CSV, no `--data-csv`, no qfa daemon, and no order placement. Cost/slippage is applied as an external one-way turnover haircut at 5 and 10 bps.
