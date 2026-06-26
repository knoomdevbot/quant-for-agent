# etf-carry-defensive-turnover-brake-v1

AR-060 refinement of AR-049. The model is a qfa-compatible ETF carry/defensive allocation exposing `generate_signals(context)`.

## Mechanism

- Universe: `SPY, QQQ, IWM, TLT, IEF, GLD, USO, FXE, FXY, UUP`.
- Features: 63/126/189 trading-day carry/defensive ranks, 126-day volatility, drawdown stress, and equity trend-beta penalty.
- Turnover brake: signals are anchored to the most recent Wednesday bar, so target weights remain unchanged between weekly rebalance anchors.
- Orthogonality brake: equity and commodity/currency carry sleeves are small and shrink when broad trend beta is elevated; residual exposure is left as cash.

## Evaluation

See:

- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/` immutable JSON artifacts

Evaluation uses Alpaca real daily OHLCV via qfa only; no CSV and no `--data-csv`.
