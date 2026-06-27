# AR-075 Evaluation — sector-etf-dispersion-dislocation-meanreversion-v1

- Status: completed_real_data_backtest
- Suggested decision: **rejected**
- Data: Alpaca/qfa real 1Day bars only; no CSV/no `--data-csv`; no daemon; no orders.
- Primary 5 bps Sharpe: `0.43709188`; annualized return `0.01924321`; max drawdown `-0.02449612`.
- Random windows: `10`; median Sharpe 5 bps `-0.414531`; p25 `-0.76493942`; worst `-0.94985866`; positive-window rate `0.2`.
- Median annualized turnover proxy: `34.46978216`.
- Orthogonality: `limited_no_retained_curves`; max available abs corr `None`.

Rationale: Fails falsifier: median random-window Sharpe <= 0 after 5 bps turnover haircut, p25 materially negative, drawdown unacceptable, or max available correlation > 0.60.

Immutable run: `/Users/moonk/quant-for-agent/models/sector-etf-dispersion-dislocation-meanreversion-v1/evaluations/runs/ar075_qfa_alpaca_real_20260626T132259Z.json`
