# ETF volume-drought trend persistence allocator v1 (AR-082)

Rule-based qfa alpha for the AR-082 hypothesis: low-liquidity/volume-drought regimes after quiet consolidation may allow trend persistence across liquid ETFs. This is intentionally divergent from AR-074's macro-event liquidity-gap recovery/reversal mechanism.

## Universe

SPY, QQQ, IWM, TLT, GLD, XLU, XLE, SHY, HYG, LQD.

## Signal

For each ETF, `generate_signals(context)` computes:

- trailing volume percentile over 126 daily bars;
- realized high-low range compression versus a 126-day history;
- 20/60-day composite trend;
- 20-day realized volatility for inverse-volatility scaling.

ETFs qualify when volume is in drought, range is compressed, and trend is positive. Qualified scores are normalized long-only and capped at 35% per ETF. If fewer than two ETFs qualify, the model rotates to SHY plus defensive ETFs with positive trend rather than forcing risk exposure.

## Evaluation

Evaluation artifacts are in `evaluations/latest.json`, `evaluations/latest.md`, and `evaluations/runs/`. They use Alpaca real daily OHLCV through qfa only: no CSV, no `--data-csv`, no daemon, no orders, and only temporary SQLite databases that are deleted after run capture.
