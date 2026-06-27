# ETF stress recovery half-life allocator (AR-055)

This qfa model tests whether the speed of ETF stress recovery has allocation value independent of AR-043's instantaneous stress-breadth detector.

## Hypothesis

Volume-normalized high/low range shocks should be less harmful when they decay quickly over 2/5/10 sessions. The model allocates more to risk ETFs (`SPY`, `QQQ`, `IWM`, `XLE`) when recovery breadth is positive and shifts toward defensive ETFs (`TLT`, `GLD`, `XLU`) when broad stress persists.

## Implementation

- qfa-compatible entry point: `generate_signals(context)` in `model.py`.
- Inputs: daily OHLCV bars only.
- Universe: `SPY, QQQ, IWM, TLT, GLD, XLU, XLE`.
- Constraints: long-only, gross exposure roughly 0.78-1.00, 36% single-ETF cap.
- No daemon and no orders.

## Evaluation summary

Real Alpaca/qfa backtests were run without `--data-csv`. qfa lacks native costs, so evaluation applies an ex-post 5 bps one-way turnover haircut.

Primary post-cost metrics, 2021-01-04 to 2025-12-15:

- Sharpe: 0.27749142
- Annualized return: 0.0303924
- Annualized volatility: 0.14891902
- Max drawdown: -0.17356821

Random-window protocol: 9 one-year overlapping windows. Median post-cost Sharpe was 0.6543798, but p25 was -0.12145677 and worst was -0.41830409.

Orthogonality failed: daily equity-return correlation to AR-043 was 0.98065061, above the 0.60 falsifier.

## Suggested decision

Reject. The lower-tail random-window Sharpe is negative and the model is highly redundant with AR-043 despite different feature wording.

See `evaluations/latest.json` and `evaluations/latest.md` for run IDs, commands, metrics, and warnings.
