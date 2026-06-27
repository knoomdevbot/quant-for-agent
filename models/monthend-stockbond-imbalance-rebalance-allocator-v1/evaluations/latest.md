# AR-125 evaluation latest

Decision: **rejected** — fails incremental 10bps random/baseline hurdle; edge not robust versus generic ToM or simple sleeve rules.

Primary 10 bps metrics: Sharpe -0.341036, annualized return -0.012261, annualized vol 0.034438, max drawdown -0.155864, turnover 256.0, events 408, activation 0.145941.

Random month-subset 10 bps: median Sharpe -0.329847, p25 -0.698312, worst -1.790418, positive-window rate 0.27, samples 100.

Baseline Sharpes (10 bps): generic ToM 0.063772; unconditional equity 0.063772; unconditional bond -1.399883; prior-month momentum -1.375786; prior-month reversal -0.341036; duration/carry proxy -0.745336; 20d imbalance -0.221369; placebo dates -0.342568.

Data/guardrails: Alpaca/qfa real daily OHLCV only, paper-data credentials redacted; no CSV, no `--data-csv`, no daemon, no orders, no raw daily paths retained.
