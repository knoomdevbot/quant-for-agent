# AR-124 evaluation latest

Decision: **rejected**

## Summary
- Median random-window Sharpe (10 bps): -2.4434936465256367
- p25 random-window Sharpe: -3.1916911357773055
- Positive-window rate: 0.025
- Primary reversal Sharpe (10 bps): -2.002535095275242
- Max drawdown: -0.979847874331161
- Turnover avg daily: 1.1241381283696275
- Activation: 0.5984819734345351
- Failed gates: median random-window Sharpe <= 0, p25 random-window Sharpe < 0, positive-window rate < 55%, primary did not beat all mandatory ablations, 20 bps cost sensitivity destroys result

Artifacts use qfa/Alpaca real daily OHLCV only, no CSV/--data-csv, no daemon, no orders, and no retained raw bars/equity paths/weights.
