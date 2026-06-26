# AR-083 — Sector ETF breadth-confirmed defensive trend allocator

Rule-based qfa-compatible allocator for `SPY, QQQ, IWM, XLF, XLK, XLE, XLU, XLV, XLI, XLP`.

## Hypothesis

Sector uptrend breadth and defensive/cyclical leadership can identify persistent allocation regimes that are different from AR-075 residual sector dislocation mean reversion.

## Signal

- Composite 20/60/126-day sector trend score.
- Sector breadth: fraction of sector ETFs with positive composite trend.
- Defensive leadership spread: 60-day equal-weight return of `XLU/XLV/XLP` minus cyclical/growth ETFs.
- SPY 126-day trend filter.
- 20-day realized-volatility scaling and 35% per-symbol cap.

## Evaluation protocol

Evaluated with qfa/Alpaca real daily data only. No CSV input, no `--data-csv`, no daemon, no trades/orders. Costs are an external 5 bps one-way target-weight turnover haircut because the qfa CLI does not expose native cost flags.

See `evaluations/latest.json` and `evaluations/latest.md` for run handles and metrics.
