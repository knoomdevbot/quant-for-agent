# AR-125 evaluation — common-stock ex-dividend post-date rebound/drift

Decision: **rejected**.

Hypothesis: Liquid dividend-paying U.S. common stocks may exhibit 1/3/5/10 day rebound or drift only after a conservative post-cash-dividend event decision date max(ex_date, process_date), reflecting dividend price adjustment/liquidity normalization/reinvestment flows.

Falsifier: Reject if post-event returns fail 10 bps costs, have weak p25/hit rate, are explained by placebo, market beta, momentum/reversal or dividend carry, concentrate in sectors/symbols/years, rely on special dividends/REITs/funds, or timestamp safety is insufficient.

Primary test: 5 trading-day long event sleeve, 10 bps, entry on first Alpaca daily bar strictly after `max(ex_date, process_date)`.

## Primary metrics

- Events: 3074 across 325 symbols
- Mean event return: -0.0011770121881230782
- Median event return: 0.00018491035692802613
- P25 event return: -0.0214512731579716
- Positive-window rate: 0.5029277813923227
- Sharpe proxy: -0.1753911810874578
- 20 bps stress mean: -0.002177012188123079

## Decision rationale

- primary 5d/10bps Sharpe not positive
- primary p25 event return materially negative
- primary positive-window rate below 55%
- 20 bps stress does not retain positive mean return
- does not beat matched placebo dates
- does not beat simple short-term reversal subset

## Baselines/orthogonality

- Placebo mean: 0.0017585413536889407
- Momentum baseline mean: -0.0021778233965882112
- Reversal baseline mean: 9.421405319989408e-05
- High dividend-yield/carry baseline mean: 0.00028371366698221
- SPY same-window correlation: 0.3279323226325744

No raw bars/equity curves/event tails retained. No CSV, no daemon, no orders.
