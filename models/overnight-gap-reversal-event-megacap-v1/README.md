# AR-018: Overnight Gap Reversal Event Mega-cap v1

Research-only qfa-compatible alpha using Alpaca real market data only.

## Hypothesis

Large overnight gaps in mega-cap equities that coincide with abnormal volume or intraday range can reflect news/liquidity shocks and opening-price overreaction. The intended trade fades the gap direction from the event-day open to the same-day close.

This is deliberately divergent from AR-004's volatility breakout continuation mechanism: it is contrarian, event/liquidity conditioned, and open-to-close mean reversion oriented.

## qfa compatibility limitation

The qfa daily backtest engine calls `generate_signals(context)` after a completed daily bar and applies weights to the next close-to-close return. It cannot exactly observe the event-day open and enter immediately at that open. Therefore:

- `model.py` implements a lagged, qfa-compatible event-gap proxy.
- `evaluations/latest.json` includes both qfa primary metrics and a direct Alpaca OHLC open-to-close harness for the intended same-day execution approximation.

## Data and safety

- Data source: Alpaca real OHLCV via qfa/AlpacaGateway.
- No `--data-csv` and no CSV fixtures.
- No daemon.
- No trades placed.
- Costs: qfa CLI has no cost/slippage parameter, so qfa metrics are pre-cost. The direct open-to-close harness applies a 5 bps one-way turnover cost.

## Evaluation

See:

- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/*.json`
