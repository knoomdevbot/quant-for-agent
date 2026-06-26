# Overnight residual reversal mega-cap tech v1

Research issue: AR-020. Parent: AR-005.

This model tests whether idiosyncratic overnight dislocations in mega-cap tech stocks reverse from the same day's open to close. It is intentionally different from AR-005: AR-005 uses multi-day pair residual mean reversion, while this idea uses single-name residual overnight gaps after removing an equal-weight mega-cap tech market component.

## Signal

- Universe: AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA.
- Estimate rolling beta to the equal-weight mega-cap tech market from prior close-to-close returns.
- Compute overnight gap: today's open / yesterday's close - 1.
- Compute residual gap: stock overnight gap - beta * market overnight gap.
- Compute prior-only rolling z-score of residual gaps.
- Fade large residual gaps: short positive residual dislocations and long negative residual dislocations.
- De-mean active scores, gross-normalize, and cap each name at 25% absolute weight.

## Evaluation limitation

The qfa daily backtest engine calls `generate_signals(context)` after a completed daily bar and applies weights to the next close-to-close return. It cannot exactly enter at today's open and exit the same close after observing today's open. Therefore:

- `model.py` is a qfa-compatible lagged close-to-close approximation.
- `evaluations/latest.json` also includes a direct Alpaca OHLC open-to-close harness that evaluates the intended same-day horizon using real Alpaca market data only.
- No `--data-csv` was used. No daemon was run. No trades were placed.

## Costs

qfa has no native cost/slippage CLI parameter in this repository. The primary direct harness result applies a 5 bps per-side round-trip haircut on event days; the qfa proxy result is gross/pre-cost and should be treated as integration smoke evidence only.

## Decision

See `evaluations/latest.md` and `evaluations/latest.json` for the durable result, random-window checks, and suggested research decision.
