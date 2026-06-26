# AR-113 — Mega-cap idiosyncratic volatility normalization v1

Research implementation for `megacap-idiosyncratic-vol-normalization-v1`.

## Hypothesis

Mega-cap stocks that show unusual idiosyncratic range/volatility expansion without same-day follow-through may normalize over the next 3-10 trading days after removing broad market and sector context.

## Model

`model.py` exposes the qfa contract:

```python
generate_signals(context) -> dict[str, float]
```

The signal uses daily OHLCV only:

- stock residual return versus SPY and mapped sector ETF using rolling beta approximations;
- same-day intraday range expansion z-score;
- absolute residual-stress z-score;
- close-location failed-follow-through filter;
- abnormal dollar-volume confirmation floor;
- top-six event basket with single-name/sector caps;
- 5-day decayed holdings in evaluation, with partial SPY/sector hedge approximation in generated targets.

## Universe

Candidate equities: AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY, XOM, UNH, HD, COST, PG, MA, V, JNJ, ABBV, NFLX, AMD, CRM, ORCL, KO, PEP.

Context: SPY plus sector ETFs XLK, XLY, XLC, XLF, XLV, XLE, XLP, XLI, XLU.

Selected equities after real-data availability/liquidity filters: AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY, XOM, UNH, COST, MA, V, JNJ, NFLX, AMD, CRM, ORCL, KO. HD, PG, ABBV, and PEP were excluded because trailing 252-day median dollar volume from the Alpaca pull was below the 50M filter.

## Evaluation

Real qfa/Alpaca daily OHLCV was pulled transiently through `AlpacaGateway`. No CSV, no `--data-csv`, no daemon, and no orders were used. Raw bars, daily paths, equity curves, and weights tails were not retained.

Primary compact evaluation at 10 bps one-way turnover cost:

- period: 2020-07-27 to 2026-06-25 (common Alpaca availability from this pull);
- Sharpe: **-1.0107**;
- annualized return: **-2.1333%**;
- annualized volatility: **2.1114%**;
- max drawdown: **-12.5028%**;
- mean daily turnover: **0.047242**;
- activation days: **208**; opportunities: **282**.

Random/stress windows at 10 bps: 9 windows, median Sharpe **-1.1664**, p25 Sharpe **-1.4272**, worst Sharpe **-1.5534**, positive-window rate **0.0**.

Cost sensitivity Sharpe: 5 bps **-0.7302**, 10 bps **-1.0107**, 20 bps **-1.5638**.

A native `qfa backtest run` smoke test was also run with real Alpaca daily OHLCV, no CSV/no daemon/no orders: run ID 1 in temporary DB `/tmp/ar113_qfa_smoke.sqlite3`, 2023-01-03 to 2024-04-30, Sharpe 0.9201 before the compact evaluator's external turnover-cost protocol.

Orthogonality: exact compact return streams for AR-028, AR-045, AR-056, AR-068, AR-004, AR-057, AR-076, AR-094, and AR-095 were not available. Transient proxy streams from the same real OHLCV gave low maximum absolute correlation (**0.1746**), so redundancy was not the reason for rejection; standalone performance was.

## Decision

Suggested decision: **rejected**.

The hypothesis is falsified in this compact real-data evaluation: primary and random/stress-window Sharpe are negative after 10 bps costs, p25 is materially negative, and 20 bps costs degrade further. The low proxy correlations suggest the construction is reasonably orthogonal but not profitable in this form.
