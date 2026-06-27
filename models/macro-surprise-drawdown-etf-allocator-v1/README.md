# AR-063 — Macro-surprise drawdown-state ETF allocator

This qfa model tests whether drawdown-state plus OHLCV-derived macro surprise proxies can produce a return stream distinct from AR-051's momentum/correlation defensive ETF rotation.

## Mechanism

The allocator uses only qfa/Alpaca historical daily ETF bars available in `context.prices`:

- SPY 126/252-session drawdown state.
- SPY realized-volatility shock z-score.
- Cross-ETF macro proxy surprises: HYG-LQD credit shock, TLT-IEF duration shock, GLD-SPY gold stress shock, and defensive-sector relative strength (XLU/XLP/XLV vs SPY).
- A simple recovery state when the market remains in drawdown but 20-day SPY and credit proxies stabilize.

It maps these states into capped long-only ETF sleeves spanning equity, duration, gold, defensive sectors, credit, and cash-like SHY. It intentionally does not rank ETFs by slow momentum the way AR-051 does.

## Universe

`SPY, QQQ, TLT, IEF, GLD, XLU, XLP, XLV, HYG, LQD, SHY`

## qfa contract

`model.py` exposes:

```python
generate_signals(context) -> dict[str, float]
```

The function returns target weights keyed by qfa symbols and consumes only `AlphaContext.prices` OHLCV data at or before `context.as_of`.

## Evaluation protocol

The durable evaluation artifacts in `evaluations/` were produced with Alpaca real market data through qfa/AlpacaGateway only. CSV input and `--data-csv` were not used. No qfa daemon was run and no orders were placed.

External transaction-cost proxy: 5 bps one-way cost multiplied by daily target-weight turnover, because this qfa CLI version has no native cost/slippage flag.
