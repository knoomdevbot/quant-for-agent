# AR-089: Cross-asset overnight gap absorption allocator

Rule-based qfa alpha implementing `generate_signals(context)` for SPY, QQQ, IWM, TLT, IEF, GLD, HYG, LQD, SHY, XLE, XLU, and XLV.

## Mechanism

At each daily close the model measures the just-completed session's prior-close-to-open gap and open-to-close absorption/reversal. A positive score means a downside gap was absorbed intraday; a negative score means an upside gap was faded intraday. Scores are filtered by cross-asset gap dispersion, scaled by realized volatility, and tilted by credit-vs-duration confirmation. Weights are capped at 35% per ETF and 100% gross.

## Data and execution restrictions

Evaluation uses Alpaca/qfa real daily OHLCV only. No CSV files, no `--data-csv`, no daemon, and no orders/trades. The qfa CLI smoke uses a temporary SQLite DB that is deleted after provenance capture.

## Timestamp limitation

Daily OHLCV bars do not allow entry at a current open after seeing that open. The model is therefore point-in-time at the current daily close and evaluates next-session open-to-close returns as a research proxy for the intended short-horizon allocation.

## Artifacts

- `model.py` — qfa-compatible alpha contract.
- `config.yaml` — parameters and restrictions.
- `metadata.yaml` — issue metadata and artifact contract.
- `evaluations/latest.json` and `evaluations/latest.md` — compact real-data results.
- `evaluations/runs/*.json` — immutable compact run snapshots.
