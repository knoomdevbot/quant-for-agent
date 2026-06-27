# etf-carry-defensive-orthogonal-v1

AR-049 refinement of AR-037. This qfa-compatible research model exposes `generate_signals(context)` and uses only daily OHLCV bars supplied by qfa/Alpaca.

The design explicitly constrains AR-015/AR-037 redundancy by:

- capping equity exposure to a small sleeve;
- suppressing exposure when broad trend beta is high;
- emphasizing duration, gold/USD/JPY defensive proxies, and cash residual;
- limiting single-name ETF concentration and leaving cash when budgets do not sum to one.

## Files

- `model.py` — qfa signal implementation.
- `config.yaml` — model/research configuration.
- `metadata.yaml` — summary metadata and latest metrics.
- `evaluations/latest.json` and `evaluations/latest.md` — latest real-data qfa evaluation.
- `evaluations/runs/ar049_qfa_alpaca_real_20260626T102842Z.json` — immutable latest run artifact.

## Latest result

Suggested decision: **watchlist_not_accepted**.

Primary qfa pre-cost Sharpe `0.51915481`, max drawdown `-0.0743553`. Across `8` random/rolling windows with a 5 bps turnover haircut, median Sharpe `0.33637069`, p25 `0.06529506`, worst `-0.40745962`, positive-window rate `0.75`, worst drawdown `-0.079501`.

Orthogonality improved versus AR-015 compared with AR-037: AR-049 correlation to retained AR-015 returns is `0.50633334` vs AR-037's recorded `0.73826394`. Parent AR-037 correlation remains `0.63994784`, so this is not accepted.

## Safety / data

Research-only. No daemon, no live trades. Alpaca real market data only; no CSV. Credentials are not stored in artifacts.
