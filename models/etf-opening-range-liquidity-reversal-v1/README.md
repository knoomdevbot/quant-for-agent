# etf-opening-range-liquidity-reversal-v1

AR-085 research alpha. The model is a qfa-compatible intraday ETF opening-range liquidity reversal rule using Alpaca/qfa OHLCV bars only.

## Mechanism

The rule waits for the first 60 minutes of the regular US equity session, measures overnight/opening gaps against the prior close, requires a cross-ETF shock breadth filter, and fades ETFs whose opening shock does not extend beyond the opening range. Gross exposure is capped at 1.0 and per-symbol exposure is capped at 0.25. Defensive sleeves receive small balancing weights when a broad risk shock is active.

## Data and evaluation constraints

- Real Alpaca market data only through qfa/Alpaca tooling.
- No CSV fixtures and no `--data-csv`.
- No daemon and no orders.
- No daily-bar substitute was used for the intraday hypothesis.
- Costs are applied as an external event-turnover haircut because qfa has no native intraday slippage model.

## Latest decision

Rejected. A bounded real Alpaca/qfa 1Min evaluation over three shock/recent windows generated 51 active events but failed robustness: median 10 bps Sharpe was negative and p25 Sharpe was materially negative. The result is recorded honestly rather than inventing unavailable metrics or promoting the alpha.

## Files

- `model.py` exposes `generate_signals(context)`.
- `config.yaml` records parameters and constraints.
- `metadata.yaml` records provenance and decision status.
- `evaluations/latest.json` and `evaluations/latest.md` contain compact results.
- `evaluations/runs/*.json` contains immutable run snapshots.
