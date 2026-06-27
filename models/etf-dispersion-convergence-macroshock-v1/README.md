# ETF dispersion convergence after macro shock days v1

AR-032 tests a genuinely divergent mechanism from rejected AR-011. The signal is cross-sectional and event-conditioned:

- Detect days with unusually high ETF return dispersion versus a 60-session history.
- Require cross-asset macro disagreement among SPY, TLT, and GLD.
- For the next session, buy ETF laggards and short ETF leaders relative to the same-day cross-sectional basket return.
- Gross-normalize active weights to 1.0 and cap individual absolute weights at 20%.

Data policy: Alpaca real daily market data through qfa only; no CSV fixtures and no `--data-csv`. No daemon and no trades.

Evaluation artifacts are under `evaluations/` after completion.

## Latest evaluation

Rejected on Alpaca/qfa real data. Primary qfa pre-cost Sharpe was 0.54337974, but after an external 5 bps one-way turnover haircut Sharpe fell to -0.06454124. Across 8 deterministic one-year random windows, median cost-adjusted Sharpe was -0.94532961. No refinement/direct extension child was created under the bad-result policy.
