# post-drawdown-residual-defensive-leadership-v1

Compact research artifact for AR-107. The model exposes `generate_signals(context)` and uses only OHLCV bars supplied by qfa/Alpaca-backed context.

## Hypothesis

After broad market drawdowns stop worsening, single-name leaders with positive SPY/sector residual momentum, resilient breadth/relative volume, and controlled beta/volatility may outperform for 5-20 trading days.

## Universe

Fixed ex ante: 119 liquid large-cap US single names plus SPY and 11 sector ETF proxies (XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY). The universe is documented in `model.py` and `evaluations/latest.json`; it was not selected by return ranking.

## Signal design

- Activation: SPY 126-day drawdown below -3.5% and recent 10-day drawdown low not worsening.
- Residual return: single-name return minus 0.45 * SPY return minus 0.55 * mapped sector ETF return.
- Rank inputs: 20-day residual momentum, 60-day residual momentum, 20-day residual breadth, and relative volume.
- Defensive inputs: beta/volatility eligibility and small score brakes only.
- Weekly rebalance; max gross 0.95, max name about 9%, sector cap target 28%.

## Evaluation summary

Real qfa/Alpaca daily data, no CSV, no `--data-csv`, no daemon, no orders. Compact artifacts retain metrics only, not raw bars, curves, return paths, or weight tails.

Primary 2020-01-01 to 2026-06-18:

| metric | pre-cost | 5 bps | 10 bps | 20 bps |
|---|---:|---:|---:|---:|
| Sharpe | 0.0901 | 0.0226 | -0.0449 | -0.1800 |
| Max DD | -0.1205 | -0.1241 | -0.1288 | -0.1418 |

Random/stress window 10 bps summary: median Sharpe -0.0230, p25 -0.5082, worst -1.9348, positive-window rate 0.50, median annualized turnover 12.8153x. Max available absolute correlation to SPY/sector proxies and retained-alpha artifacts was 0.3779.

## Decision

Rejected. Cost-adjusted random-window robustness failed and the primary 20 bps Sharpe was non-positive, despite acceptable proxy correlation and residual-dominant score attribution. No children were created.
