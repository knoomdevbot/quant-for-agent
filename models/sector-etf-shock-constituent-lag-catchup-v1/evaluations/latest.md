# AR-128 evaluation latest

Decision: **rejected**.

Data: qfa/Alpaca real daily OHLCV, 2020-01-01 to 2026-06-26; raw bars not retained. Selected 93 of 93 candidate common stocks after coverage/liquidity/price filters.

Primary 10 bps metrics:

- Median random-window Sharpe: -4.774897
- P25 random-window Sharpe: -5.166348
- Worst random-window Sharpe: -7.294779
- Positive-window rate: 0.0
- Full-sample annualized return: -0.3682
- Full-sample annualized volatility: 0.0981
- Full-sample max drawdown: -0.940467
- Average daily turnover: 1.691546
- Activation rate: 0.954105

Cost sensitivity median window Sharpe: 5 bps -2.693909; 10 bps -4.774897; 20 bps -10.184427.

Gate verdict: rejected; no children queued. Exact prior-alpha stream correlations unavailable because retained prior artifacts are compact and omit aligned daily return streams. Proxy correlations are in latest.json.
