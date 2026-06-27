# AR-117 evaluation — country ETF stale-participation catch-up v1

Decision: **rejected**. Data: qfa/Alpaca real daily OHLCV only; no CSV, no --data-csv, no daemon, no orders.

Selected universe (10): EEM, FXI, EWZ, KWEB, EWJ, MCHI, INDA, EWY, VGK, EWT. Selection used only coverage/liquidity/history filters before performance review.

## Primary 5 bps metrics
- Sharpe: -1.039437
- Annualized return / vol: -0.073476 / 0.070689
- Max drawdown: -0.362578
- Mean daily turnover: 0.523663 (annualized 131.963114)
- Random windows: median Sharpe -0.901032, mean -0.87881, p25 -1.442698, worst -1.956451, positive-window rate 0.066667

## Stress costs
- 10 bps median/p25/worst Sharpe: -1.864152 / -2.117714 / -2.684893
- 20 bps median/p25/worst Sharpe: -3.017417 / -3.287959 / -5.141312

## Falsifier controls
Ablations covered simple 1-day and 3-day reversal, AR-112-style 63-day country relative strength, ETF TSMOM, defensive proxy, and turn-of-month equal-country exposure. Orthogonality to existing watchlist/top alphas is deferred because compact artifacts do not retain daily return series; proxy control correlations are in latest.json.

QFA native smoke: {'attempted': True, 'returncode': 0, 'temp_db_path': '/tmp/qfa-ar117-20260627T025416Z.sqlite3', 'db_retained': False, 'run_id': 1, 'summary': {}}. Temporary DB was removed/not retained.

Artifacts: `models/country-etf-stale-participation-catchup-v1/evaluations/runs/ar117_qfa_alpaca_real_20260627T025416Z.json` and `latest.json`.
