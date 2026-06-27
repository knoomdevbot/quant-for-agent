# sector-etf-earnings-season-dispersion-reversal-v1

Research artifact for **AR-098**, a divergent child of rejected AR-086. This is a qfa-compatible, research-only sector ETF model exposing `generate_signals(context)`.

## Hypothesis

Sector ETFs with unusually large earnings-season residual dispersion shocks may mean-revert over several days as index-level hedges and sector flows normalize. The implementation is intentionally divergent from AR-086 fixed-income/carry allocation: it trades sector ETF residual reversal only.

## Model

- Universe: `XLK, XLY, XLP, XLV, XLF, XLI, XLE, XLU, XLB, XLRE, SPY`.
- Inputs: daily OHLCV close data supplied by qfa/Alpaca.
- Signal:
  1. Compute sector ETF close-to-close returns and residual returns versus SPY.
  2. Sum residuals over 5 trading days.
  3. Trade only in an ex-ante earnings-season proxy: Jan/Apr/Jul/Oct day >= 10 and Feb/May/Aug/Nov day <= 15.
  4. Require latest cross-sector residual dispersion to exceed its prior 60-day z-score threshold.
  5. Fade sector residual winners/losers with sector-dollar-neutral gross-normalized weights.
- No external earnings calendar, fundamentals, option data, local CSV, daemon, or order flow is used.

## Evaluation summary

Real-data qfa/Alpaca evaluation completed with 10 random/stress windows and external turnover-cost haircuts of 5/10/20 bps one-way.

Suggested decision: **rejected**.

Key 5 bps results:

- Primary 2021-01-04 to 2025-12-15 Sharpe: `0.07492903`; max drawdown: `-0.05401764`.
- Random-window median Sharpe: `-0.19363557`.
- Random-window p25 Sharpe: `-0.46529722`.
- Positive-window rate: `0.30`.
- Worst random-window Sharpe: `-1.21164913`.
- Primary annualized turnover proxy: `11.6444337` one-way.

The falsifier was triggered: random-window median Sharpe <= 0 and p25 materially negative after costs. Because AR-086 is rejected and AR-098 fails as a divergent sector-dispersion idea, no refinement/direct inversion/extension task is suggested.

## Artifacts

- `model.py` — qfa-compatible model implementation.
- `config.yaml` — model configuration and risk/evaluation flags.
- `metadata.yaml` — compact research metadata.
- `evaluations/latest.json` — compact machine-readable evaluation; no raw daily paths retained.
- `evaluations/latest.md` — human-readable evaluation summary.
- `evaluations/runs/20260626T164342Z_ar098_realdata_compact.json` — immutable compact evaluation run.

## Provenance / safety flags

Credentials were loaded from the configured secret profile with values redacted and mapped internally for qfa/Alpaca. The evaluation used Alpaca real daily market data only. No CSV input or `--data-csv` argument was used; no daemon was started; no orders were submitted. Temporary SQLite smoke-test storage was under `/tmp` and removed after the run.
