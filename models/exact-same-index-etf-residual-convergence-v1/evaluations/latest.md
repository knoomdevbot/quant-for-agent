# AR-133 real-data evaluation latest

- Data: qfa/Alpaca real daily OHLCV through configured paper-data access with values redacted; no CSV; no `--data-csv`; no daemon; no orders.
- Decision: **rejected** — Fast-falsified: median/p25 random-window Sharpe and positive-window rate/cost sensitivity failed strict gates; lagged residual deviations were only a few bps while turnover/costs dominated.
- Selected clusters: sp500_exact_substitutes, nasdaq100_exact_substitutes, russell2000_near_substitutes, total_us_market_near_substitutes, aggregate_bond_near_substitutes
- Primary 10 bps full: Sharpe -0.96884879, annualized return -0.02493936, vol 0.02573681, max DD -0.1654233, turnover 48.75571734, activation 0.86592179.
- Random windows 10 bps: median Sharpe -7.57522066, p25 -11.26252897, worst -15.69415071, mean -7.39695695, positive rate 0.2.
- Residual amplitude diagnostics: median log residual 0.00066969, p25 0.00035024, p90 0.1285066, entry count 6244.
- Orthogonality: deferred due rejection; no children spawned.
