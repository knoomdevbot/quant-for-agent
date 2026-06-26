# AR-056 Evaluation — closing-volume-reversal-orthogonalized-megacap-v1

## Verdict

Suggested decision: **watchlist** (research candidate, not trade-ready).

The orthogonality constraints worked: primary daily return correlation was low versus AR-028, AR-045, SPY, and the equal-weight universe. The cost-adjusted primary and median random-window Sharpe were positive, but the model is extremely sparse and low-return, so it should be treated as a diagnostic/watchlist stream rather than a production candidate.

## Data and execution

- Data source: qfa + Alpaca real daily bars only; no CSV and no `--data-csv`.
- Universe: AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY.
- Primary window: 2024-01-01 to 2025-12-31.
- Random windows: 8 real-data windows from 2020-01-02 through 2025-12-15 ranges.
- qfa DBs: temporary SQLite files in `/tmp/qfa_ar056_*`; removed after JSON artifacts were written.
- qfa run ids: primary `1`; random windows `1,1,1,1,1,1,1,1` because each run used its own temporary DB.
- Costs: qfa has no native cost/slippage flag; applied external 5 bps one-way target-weight turnover haircut.

## Primary metrics

| Metric | Pre-cost qfa | 5 bps turnover haircut |
|---|---:|---:|
| Sharpe | 0.70992957 | 0.68366014 |
| Total return | 0.01427461 | 0.01326773 |
| Annualized return | 0.00716912 | 0.00666508 |
| Annualized vol | 0.01013397 | 0.00978616 |
| Max drawdown | 0.00000000 | -0.00050000 |
| Win rate | 0.00200000 | 0.00200000 |
| Periods | 500 | 500 |

Turnover: mean daily one-way `0.00400000`; annualized one-way `1.00800000`.

## Random-window results

- Count: 8
- Median cost-adjusted Sharpe: `0.56265677`
- Mean cost-adjusted Sharpe: `0.35349851`
- Positive cost-adjusted Sharpe windows: `6/8`
- Worst cost-adjusted max drawdown: `-0.01578459`

## Orthogonality checks (primary cost-adjusted daily returns)

- vs AR-028 original same-period replay: `-0.00179135`
- vs AR-045 cost-aware same-period replay: `0.14073653`
- vs SPY: `0.02505287`
- vs equal-weight watchlist universe: `0.01345002`
- Retained stream checks attempted for AR-046 / low-vol-quality / earnings-quality, but comparable retained curves were not available in this pass (`null`).

## Comparison context

Same-period replay after 5 bps turnover haircut:

- AR-045: Sharpe `0.65532911`, total return `0.20197114`, max drawdown `-0.12419245`, annualized one-way turnover `64.65459616`.
- AR-028: Sharpe `0.65897772`, total return `0.32129525`, max drawdown `-0.19409731`, annualized one-way turnover `109.71752596`.

AR-056 has much lower turnover/drawdown and much lower correlation, but also much lower absolute return and very sparse activity.

## Artifacts

- Model: `/Users/moonk/quant-for-agent/models/closing-volume-reversal-orthogonalized-megacap-v1/model.py`
- Config: `/Users/moonk/quant-for-agent/models/closing-volume-reversal-orthogonalized-megacap-v1/config.yaml`
- Metadata: `/Users/moonk/quant-for-agent/models/closing-volume-reversal-orthogonalized-megacap-v1/metadata.yaml`
- README: `/Users/moonk/quant-for-agent/models/closing-volume-reversal-orthogonalized-megacap-v1/README.md`
- Latest JSON: `/Users/moonk/quant-for-agent/models/closing-volume-reversal-orthogonalized-megacap-v1/evaluations/latest.json`
- Immutable summary JSON: `/Users/moonk/quant-for-agent/models/closing-volume-reversal-orthogonalized-megacap-v1/evaluations/runs/ar056_qfa_alpaca_real_20260626T111336Z.json`

## Recommendation

Keep on **watchlist** only. The hypothesis that orthogonality can reduce redundancy is supported; the hypothesis that it improves usable economic return is only weakly supported because the signal became too sparse. Next refinement should focus on raising opportunity count without surrendering the low AR-028/market correlation.
