# AR-129 latest evaluation

Decision: **rejected**. Data: Alpaca real daily OHLCV via qfa AlpacaGateway; no CSV, no `--data-csv`, no daemon, no orders.

## Primary 10 bps one-way cost
- Full-sample Sharpe: `-0.386086`; annualized return `-0.027148`; annualized vol `0.071205`; max drawdown `-0.278699`.
- Random-window Sharpe median/p25/worst: `-0.220313` / `-0.681884` / `-1.195085`; positive-window rate `0.3`.
- Avg monthly turnover `1.542879`; avg active names `56.0`; selected universe `143` names.

## Verdict
Rejected because the sector-neutral same-calendar-month effect did not clear robustness thresholds after costs and warmup. See `latest.json` for ablations, concentration, and proxy correlations. No children suggested.
