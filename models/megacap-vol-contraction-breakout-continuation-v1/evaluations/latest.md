# AR-076 Evaluation — megacap-vol-contraction-breakout-continuation-v1

- Status: completed_real_data_backtest
- Suggested decision: **rejected**
- Data: Alpaca/qfa real 1Day bars only; no CSV/no `--data-csv`; no daemon; no orders.
- Smoke qfa run id: `1`; primary qfa run id: `2`.
- Primary 5 bps Sharpe: `-1.08725717`; annualized return `-0.04080928`; max drawdown `-0.07934448`.
- Random windows: `8`; median Sharpe 5 bps `-0.48885616`; p25 `-0.65363044`; worst `-1.35077196`; positive-window rate `0.25`.
- Median annualized turnover proxy: `13.04518351`.
- Orthogonality: `pass_available_max_corr_le_0p60`; max available abs corr `0.13316654`.
- Raw daily/equity/weight paths retained: `false`; temporary DB retained: `false`.

Rationale: Fails falsifier: median random-window Sharpe <= 0 after 5 bps turnover haircut, p25 materially negative, high drawdown, or max available correlation > 0.60.

Immutable run: `/Users/moonk/quant-for-agent/models/megacap-vol-contraction-breakout-continuation-v1/evaluations/runs/ar076_qfa_alpaca_real_20260626T134344Z.json`
